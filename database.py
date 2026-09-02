"""
database.py — SQLite persistence for the Source→HTML QA Tool.

Stores:
- users with email, username, role, status, and password hashes
- admin-created invite links
- admin-mediated password reset requests/links
- run/batch history
- file-pair summaries
- issue details for history/report UI
- audit logs

Generated Excel/audit files remain in batch_runs/.
"""

import hashlib
import json
import os
import secrets
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("QA_TOOL_DB", BASE_DIR / "qa_tool.db"))


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row is not None else None


def _table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {r["name"] for r in con.execute(f"PRAGMA table_info({table})").fetchall()}
    except Exception:
        return set()


def _add_col(con: sqlite3.Connection, table: str, col: str, ddl: str) -> None:
    if col not in _table_columns(con, table):
        con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")


def init_db() -> None:
    with get_db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                status TEXT NOT NULL DEFAULT 'active',
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login_at TEXT,
                created_by_admin_id INTEGER,
                FOREIGN KEY(created_by_admin_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                token_hash TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                expires_at TEXT NOT NULL,
                used_at TEXT,
                created_by_admin_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(created_by_admin_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username_snapshot TEXT,
                email_snapshot TEXT,
                token_hash TEXT UNIQUE,
                status TEXT NOT NULL DEFAULT 'requested',
                requested_at TEXT NOT NULL,
                link_generated_at TEXT,
                expires_at TEXT,
                used_at TEXT,
                cancelled_at TEXT,
                generated_by_admin_id INTEGER,
                request_ip TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(generated_by_admin_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                username_snapshot TEXT,
                email_snapshot TEXT,
                source_type TEXT NOT NULL,
                source_zip_name TEXT,
                html_zip_name TEXT,
                batch_dir TEXT NOT NULL,
                reports_dir TEXT NOT NULL,
                audits_dir TEXT NOT NULL,
                metadata_dir TEXT NOT NULL,
                batch_report_path TEXT,
                total_files INTEGER NOT NULL DEFAULT 0,
                prepared_files INTEGER NOT NULL DEFAULT 0,
                running_files INTEGER NOT NULL DEFAULT 0,
                completed_files INTEGER NOT NULL DEFAULT 0,
                passed_files INTEGER NOT NULL DEFAULT 0,
                failed_files INTEGER NOT NULL DEFAULT 0,
                critical_count INTEGER NOT NULL DEFAULT 0,
                major_count INTEGER NOT NULL DEFAULT 0,
                minor_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'uploaded',
                status_message TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                last_updated_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS file_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair_id TEXT NOT NULL UNIQUE,
                run_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                file_no INTEGER NOT NULL,
                source_type TEXT NOT NULL,
                source_name TEXT NOT NULL,
                html_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                status_message TEXT,
                file_severity TEXT,
                language TEXT,
                issue_count INTEGER NOT NULL DEFAULT 0,
                critical_count INTEGER NOT NULL DEFAULT 0,
                major_count INTEGER NOT NULL DEFAULT 0,
                minor_count INTEGER NOT NULL DEFAULT 0,
                report_path TEXT,
                audit_path TEXT,
                job_id TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_pair_id INTEGER NOT NULL,
                run_id TEXT NOT NULL,
                category TEXT,
                severity TEXT,
                engine_severity TEXT,
                area TEXT,
                html_line TEXT,
                message TEXT,
                expected TEXT,
                actual TEXT,
                snippet TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(file_pair_id) REFERENCES file_pairs(id) ON DELETE CASCADE,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                actor_username TEXT,
                actor_email TEXT,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                details TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_runs_user_created ON runs(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_file_pairs_run ON file_pairs(run_id, file_no);
            CREATE INDEX IF NOT EXISTS idx_file_pairs_status ON file_pairs(status);
            CREATE INDEX IF NOT EXISTS idx_issues_file_pair ON issues(file_pair_id);
            CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_password_resets_status ON password_resets(status, requested_at DESC);
            CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id, requested_at DESC);
            """
        )

        # Migration support for older qa_tool.db versions.
        for col, ddl in {
            "email": "TEXT",
            "role": "TEXT NOT NULL DEFAULT 'user'",
            "status": "TEXT NOT NULL DEFAULT 'active'",
            "created_by_admin_id": "INTEGER",
            "display_name": "TEXT",
            "is_admin": "INTEGER NOT NULL DEFAULT 0",
            "is_active": "INTEGER NOT NULL DEFAULT 1",
            "last_login_at": "TEXT",
        }.items():
            _add_col(con, "users", col, ddl)

        for col, ddl in {
            "username_snapshot": "TEXT",
            "email_snapshot": "TEXT",
            "prepared_files": "INTEGER NOT NULL DEFAULT 0",
            "running_files": "INTEGER NOT NULL DEFAULT 0",
            "status_message": "TEXT",
            "started_at": "TEXT",
            "last_updated_at": "TEXT",
        }.items():
            _add_col(con, "runs", col, ddl)

        for col, ddl in {
            "status_message": "TEXT",
        }.items():
            _add_col(con, "file_pairs", col, ddl)

        for col, ddl in {
            "actor_username": "TEXT",
            "actor_email": "TEXT",
            "target_type": "TEXT",
            "target_id": "TEXT",
            "ip_address": "TEXT",
        }.items():
            _add_col(con, "audit_logs", col, ddl)

        con.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

        # Backfill older user rows.
        con.execute("UPDATE users SET email = COALESCE(email, username) WHERE email IS NULL OR email = ''")
        con.execute("UPDATE users SET display_name = COALESCE(display_name, username) WHERE display_name IS NULL OR display_name = ''")
        con.execute("UPDATE users SET role = CASE WHEN is_admin = 1 THEN 'admin' ELSE COALESCE(role, 'user') END WHERE role IS NULL OR role = '' OR is_admin = 1")
        con.execute("UPDATE users SET status = CASE WHEN is_active = 1 THEN COALESCE(status, 'active') ELSE 'disabled' END WHERE status IS NULL OR status = ''")

        # Mark any unfinished active work as interrupted on startup.
        mark_interrupted_on_startup(con)


def mark_interrupted_on_startup(con: sqlite3.Connection | None = None) -> None:
    own = con is None
    if own:
        con = get_db()
    assert con is not None
    ts = now_iso()
    con.execute(
        """
        UPDATE file_pairs
        SET status = 'interrupted', status_message = 'Server stopped before this file completed.',
            error_message = COALESCE(error_message, 'Server stopped before this file completed.'),
            finished_at = COALESCE(finished_at, ?)
        WHERE status IN ('running', 'queued')
        """,
        (ts,),
    )
    con.execute(
        """
        UPDATE runs
        SET status = 'interrupted', status_message = 'Server stopped before this run completed.',
            finished_at = COALESCE(finished_at, ?), last_updated_at = ?
        WHERE status IN ('running', 'queued')
        """,
        (ts, ts),
    )
    con.execute(
        """
        UPDATE runs
        SET status = 'interrupted', status_message = 'Files were uploaded/prepared, but the server stopped before QA completed.',
            finished_at = COALESCE(finished_at, ?), last_updated_at = ?
        WHERE status IN ('prepared', 'uploaded')
          AND run_id IN (SELECT DISTINCT run_id FROM file_pairs WHERE status = 'interrupted')
        """,
        (ts, ts),
    )
    if own:
        con.commit(); con.close()


def has_users() -> bool:
    with get_db() as con:
        row = con.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        return int(row["c"] or 0) > 0


def _public_user_select() -> str:
    return "id, email, username, display_name, role, status, created_at, last_login_at, created_by_admin_id, is_admin, is_active"



def ensure_fixed_admin(email: str, username: str, password_hash: str, display_name: str = "System Admin") -> int:
    """Create/synchronize the one allowed admin account.

    The admin identity comes from server configuration. The password is stored
    only as a Werkzeug hash in SQLite. Any other admin rows are automatically
    demoted to normal users so the portal always has exactly one admin.
    """
    email = (email or "admin@company.local").strip().lower()
    username = (username or "admin").strip().lower()
    display_name = display_name or username
    ts = now_iso()
    with get_db() as con:
        # Prefer an existing configured admin/user row, then any existing admin.
        target = con.execute(
            "SELECT * FROM users WHERE lower(email)=? OR lower(username)=? ORDER BY id LIMIT 1",
            (email, username),
        ).fetchone()
        if target is None:
            target = con.execute(
                "SELECT * FROM users WHERE role='admin' OR is_admin=1 ORDER BY id LIMIT 1"
            ).fetchone()

        if target is None:
            cur = con.execute(
                """
                INSERT INTO users (email, username, display_name, password_hash, role, status, is_admin, is_active, created_at)
                VALUES (?, ?, ?, ?, 'admin', 'active', 1, 1, ?)
                """,
                (email, username, display_name, password_hash, ts),
            )
            admin_id = int(cur.lastrowid)
        else:
            admin_id = int(target["id"])

            # Free unique email/username if old non-admin rows conflict with the configured admin identity.
            conflicts = con.execute(
                "SELECT id, email, username FROM users WHERE id<>? AND (lower(email)=? OR lower(username)=?)",
                (admin_id, email, username),
            ).fetchall()
            for row in conflicts:
                rid = int(row["id"])
                old_email = (row["email"] or f"user{rid}@disabled.local")
                old_username = (row["username"] or f"user{rid}")
                con.execute(
                    "UPDATE users SET email=?, username=? WHERE id=?",
                    (f"disabled_{rid}_{old_email}", f"disabled_{rid}_{old_username}", rid),
                )

            con.execute(
                """
                UPDATE users
                SET email=?, username=?, display_name=?, password_hash=?, role='admin',
                    status='active', is_admin=1, is_active=1
                WHERE id=?
                """,
                (email, username, display_name, password_hash, admin_id),
            )

        # Enforce single-admin rule.
        con.execute("UPDATE users SET role='user', is_admin=0 WHERE id<>? AND (role='admin' OR is_admin=1)", (admin_id,))
        con.execute("UPDATE invites SET role='user' WHERE role='admin'")
        return admin_id


def get_fixed_admin() -> Optional[dict]:
    with get_db() as con:
        return row_to_dict(con.execute(
            f"SELECT {_public_user_select()}, CASE WHEN role='admin' OR is_admin=1 THEN 1 ELSE 0 END AS is_admin FROM users WHERE role='admin' OR is_admin=1 ORDER BY id LIMIT 1"
        ).fetchone())

def create_user(email: str, username: str, password_hash: str, role: str = "user", created_by_admin_id: int | None = None, display_name: str | None = None) -> int:
    # Invites are for normal users only. Admin is fixed and seeded by server config.
    role = "user"
    email = (email or "").strip().lower()
    username = (username or "").strip().lower()
    with get_db() as con:
        cur = con.execute(
            """
            INSERT INTO users (email, username, display_name, password_hash, role, status, is_admin, is_active, created_at, created_by_admin_id)
            VALUES (?, ?, ?, ?, ?, 'active', ?, 1, ?, ?)
            """,
            (email, username, display_name or username, password_hash, role, 1 if role == "admin" else 0, now_iso(), created_by_admin_id),
        )
        return int(cur.lastrowid)


def get_user_by_login(login: str) -> Optional[dict]:
    login = (login or "").strip().lower()
    with get_db() as con:
        row = con.execute(
            f"SELECT *, CASE WHEN role='admin' OR is_admin=1 THEN 1 ELSE 0 END AS is_admin FROM users WHERE (lower(username)=? OR lower(email)=?) AND status='active' AND is_active=1",
            (login, login),
        ).fetchone()
        return row_to_dict(row)


def get_user_by_username(username: str) -> Optional[dict]:
    return get_user_by_login(username)


def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_db() as con:
        row = con.execute(
            f"SELECT {_public_user_select()}, CASE WHEN role='admin' OR is_admin=1 THEN 1 ELSE 0 END AS is_admin FROM users WHERE id = ? AND status='active' AND is_active=1",
            (user_id,),
        ).fetchone()
        return row_to_dict(row)


def get_any_user_by_id(user_id: int) -> Optional[dict]:
    with get_db() as con:
        row = con.execute(
            f"SELECT {_public_user_select()}, CASE WHEN role='admin' OR is_admin=1 THEN 1 ELSE 0 END AS is_admin FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return row_to_dict(row)


def update_last_login(user_id: int) -> None:
    with get_db() as con:
        con.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_iso(), user_id))


def set_user_password(user_id: int, password_hash: str) -> None:
    with get_db() as con:
        con.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


def list_users() -> list[dict]:
    with get_db() as con:
        rows = con.execute(
            """
            SELECT u.id, u.email, u.username, u.display_name, u.role, u.status, u.created_at, u.last_login_at,
                   u.created_by_admin_id,
                   (SELECT COUNT(*) FROM runs r WHERE r.user_id = u.id) AS total_runs,
                   (SELECT COUNT(*) FROM runs r WHERE r.user_id = u.id AND r.status = 'done') AS completed_runs,
                   (SELECT COUNT(*) FROM runs r WHERE r.user_id = u.id AND r.status IN ('failed','error','interrupted')) AS problem_runs
            FROM users u
            ORDER BY u.created_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def set_user_status(user_id: int, status: str) -> None:
    status = "active" if status == "active" else "disabled"
    with get_db() as con:
        con.execute("UPDATE users SET status = ?, is_active = ? WHERE id = ?", (status, 1 if status == "active" else 0, user_id))


def set_user_role(user_id: int, role: str) -> None:
    role = role if role in {"admin", "user"} else "user"
    with get_db() as con:
        con.execute("UPDATE users SET role = ?, is_admin = ? WHERE id = ?", (role, 1 if role == "admin" else 0, user_id))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_invite(email: str, role: str, created_by_admin_id: int, expires_hours: int = 72) -> dict:
    email = (email or "").strip().lower()
    # The portal supports exactly one fixed admin. Invites always create normal user accounts.
    role = "user"
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    created_at = now_iso()
    expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat(timespec="seconds")
    with get_db() as con:
        cur = con.execute(
            """
            INSERT INTO invites (email, role, token_hash, status, expires_at, created_by_admin_id, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?, ?)
            """,
            (email, role, token_hash, expires_at, created_by_admin_id, created_at),
        )
        invite_id = int(cur.lastrowid)
    return {"id": invite_id, "email": email, "role": role, "token": token, "expires_at": expires_at, "created_at": created_at}


def get_invite_by_token(token: str) -> Optional[dict]:
    token_hash = _hash_token(token or "")
    with get_db() as con:
        row = con.execute("SELECT * FROM invites WHERE token_hash = ?", (token_hash,)).fetchone()
        inv = row_to_dict(row)
    if not inv:
        return None
    if inv.get("status") != "pending":
        inv["valid"] = False; inv["invalid_reason"] = "Invite has already been used or cancelled."
    elif datetime.fromisoformat(inv["expires_at"]) < datetime.now():
        inv["valid"] = False; inv["invalid_reason"] = "Invite link has expired."
    else:
        inv["valid"] = True; inv["invalid_reason"] = ""
    return inv


def consume_invite(token: str, username: str, password_hash: str) -> int:
    inv = get_invite_by_token(token)
    if not inv or not inv.get("valid"):
        raise ValueError((inv or {}).get("invalid_reason") or "Invalid invite link.")
    username = (username or "").strip().lower()
    with get_db() as con:
        cur = con.execute(
            """
            INSERT INTO users (email, username, display_name, password_hash, role, status, is_admin, is_active, created_at, created_by_admin_id)
            VALUES (?, ?, ?, ?, ?, 'active', ?, 1, ?, ?)
            """,
            (inv["email"], username, username, password_hash, inv["role"], 1 if inv["role"] == "admin" else 0, now_iso(), inv["created_by_admin_id"]),
        )
        user_id = int(cur.lastrowid)
        con.execute("UPDATE invites SET status='used', used_at=? WHERE id=?", (now_iso(), inv["id"]))
        return user_id


def list_invites(limit: int = 200) -> list[dict]:
    with get_db() as con:
        rows = con.execute(
            """
            SELECT i.id, i.email, i.role, i.status, i.expires_at, i.used_at, i.created_at,
                   u.username AS invited_by_username, u.email AS invited_by_email
            FROM invites i
            LEFT JOIN users u ON u.id = i.created_by_admin_id
            ORDER BY i.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def cancel_invite(invite_id: int) -> None:
    with get_db() as con:
        con.execute("UPDATE invites SET status='cancelled' WHERE id=? AND status='pending'", (invite_id,))


# ---------------------------------------------------------------------------
# Password resets — admin-mediated, same trust model as invites.
#
# Flow:
#   1. A user submits "forgot password" with their login. If the account
#      exists, a row is inserted here with status='requested' (no token
#      yet). The public endpoint never reveals whether the account exists
#      or returns anything usable to reset the password.
#   2. An admin reviews pending requests and clicks "Generate Reset Link",
#      which mints a token (status='link_generated') the same way invite
#      links are minted, for the admin to share through a trusted channel.
#   3. The user opens the link and sets a new password (status='used').
# ---------------------------------------------------------------------------

def create_password_reset_request(login: str, request_ip: str = "") -> Optional[dict]:
    user = get_user_by_login(login)
    if not user:
        return None
    with get_db() as con:
        cur = con.execute(
            """
            INSERT INTO password_resets (user_id, username_snapshot, email_snapshot, status, requested_at, request_ip)
            VALUES (?, ?, ?, 'requested', ?, ?)
            """,
            (user["id"], user.get("username", ""), user.get("email", ""), now_iso(), request_ip or ""),
        )
        return {"id": int(cur.lastrowid), "user_id": user["id"]}


def list_password_reset_requests(status: str | None = "requested", limit: int = 200) -> list[dict]:
    with get_db() as con:
        if status:
            rows = con.execute(
                """
                SELECT pr.*, u.username AS current_username, u.email AS current_email, u.status AS user_status
                FROM password_resets pr LEFT JOIN users u ON u.id = pr.user_id
                WHERE pr.status = ?
                ORDER BY pr.requested_at DESC LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT pr.*, u.username AS current_username, u.email AS current_email, u.status AS user_status
                FROM password_resets pr LEFT JOIN users u ON u.id = pr.user_id
                ORDER BY pr.requested_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_password_reset_request(request_id: int) -> Optional[dict]:
    with get_db() as con:
        row = con.execute("SELECT * FROM password_resets WHERE id=?", (request_id,)).fetchone()
        return row_to_dict(row)


def generate_password_reset_link(request_id: int, admin_id: int, expires_hours: int = 2) -> dict:
    req = get_password_reset_request(request_id)
    if not req:
        raise ValueError("Password reset request not found.")
    if req.get("status") not in {"requested", "link_generated"}:
        raise ValueError("This request has already been used or cancelled.")
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat(timespec="seconds")
    with get_db() as con:
        con.execute(
            """
            UPDATE password_resets
            SET token_hash=?, status='link_generated', link_generated_at=?, expires_at=?, generated_by_admin_id=?
            WHERE id=?
            """,
            (token_hash, now_iso(), expires_at, admin_id, request_id),
        )
    return {"id": request_id, "token": token, "expires_at": expires_at}


def cancel_password_reset_request(request_id: int) -> None:
    with get_db() as con:
        con.execute(
            "UPDATE password_resets SET status='cancelled', cancelled_at=? WHERE id=? AND status IN ('requested','link_generated')",
            (now_iso(), request_id),
        )


def get_password_reset_by_token(token: str) -> Optional[dict]:
    token_hash = _hash_token(token or "")
    with get_db() as con:
        row = con.execute("SELECT * FROM password_resets WHERE token_hash = ?", (token_hash,)).fetchone()
        pr = row_to_dict(row)
    if not pr:
        return None
    if pr.get("status") != "link_generated":
        pr["valid"] = False; pr["invalid_reason"] = "Reset link has already been used or cancelled."
    elif not pr.get("expires_at") or datetime.fromisoformat(pr["expires_at"]) < datetime.now():
        pr["valid"] = False; pr["invalid_reason"] = "Reset link has expired. Ask your administrator for a new one."
    else:
        pr["valid"] = True; pr["invalid_reason"] = ""
    return pr


def consume_password_reset(token: str, new_password_hash: str) -> int:
    pr = get_password_reset_by_token(token)
    if not pr or not pr.get("valid"):
        raise ValueError((pr or {}).get("invalid_reason") or "Invalid reset link.")
    user_id = int(pr["user_id"])
    with get_db() as con:
        con.execute("UPDATE users SET password_hash=? WHERE id=?", (new_password_hash, user_id))
        con.execute("UPDATE password_resets SET status='used', used_at=? WHERE id=?", (now_iso(), pr["id"]))
    return user_id


def create_run(run: dict) -> None:
    with get_db() as con:
        con.execute(
            """
            INSERT INTO runs (
                run_id, user_id, username_snapshot, email_snapshot, source_type, source_zip_name, html_zip_name,
                batch_dir, reports_dir, audits_dir, metadata_dir, batch_report_path,
                total_files, prepared_files, status, status_message, created_at, last_updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run["run_id"], run["user_id"], run.get("username_snapshot", ""), run.get("email_snapshot", ""), run["source_type"],
                run.get("source_zip_name", ""), run.get("html_zip_name", ""), run["batch_dir"], run["reports_dir"],
                run["audits_dir"], run["metadata_dir"], run.get("batch_report_path", ""), int(run.get("total_files", 0)),
                int(run.get("prepared_files", run.get("total_files", 0))), run.get("status", "prepared"), run.get("status_message", ""),
                run.get("created_at") or now_iso(), now_iso(),
            ),
        )


def update_run_status(run_id: str, status: str, status_message: str = "", finished: bool = False) -> None:
    with get_db() as con:
        if finished:
            con.execute(
                "UPDATE runs SET status=?, status_message=?, finished_at=?, last_updated_at=? WHERE run_id=?",
                (status, status_message, now_iso(), now_iso(), run_id),
            )
        else:
            con.execute(
                "UPDATE runs SET status=?, status_message=?, last_updated_at=? WHERE run_id=?",
                (status, status_message, now_iso(), run_id),
            )


def update_run_counts(run_id: str) -> None:
    with get_db() as con:
        row = con.execute(
            """
            SELECT
              COUNT(*) AS total_files,
              SUM(CASE WHEN status IN ('done', 'error', 'interrupted') THEN 1 ELSE 0 END) AS completed_files,
              SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_files,
              SUM(CASE WHEN status = 'done' AND issue_count = 0 THEN 1 ELSE 0 END) AS passed_files,
              SUM(CASE WHEN status = 'done' AND issue_count > 0 THEN 1 ELSE 0 END) AS failed_files,
              SUM(CASE WHEN status = 'done' THEN critical_count ELSE 0 END) AS critical_count,
              SUM(CASE WHEN status = 'done' THEN major_count ELSE 0 END) AS major_count,
              SUM(CASE WHEN status = 'done' THEN minor_count ELSE 0 END) AS minor_count,
              SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_files,
              SUM(CASE WHEN status = 'interrupted' THEN 1 ELSE 0 END) AS interrupted_files
            FROM file_pairs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
        total = int(row["total_files"] or 0)
        completed = int(row["completed_files"] or 0)
        running = int(row["running_files"] or 0)
        error_files = int(row["error_files"] or 0)
        interrupted_files = int(row["interrupted_files"] or 0)
        if total > 0 and completed >= total:
            status = "interrupted" if interrupted_files else ("failed" if error_files else "done")
            finished_at = now_iso()
        elif running > 0:
            status = "running"; finished_at = None
        else:
            status = "prepared"; finished_at = None
        con.execute(
            """
            UPDATE runs
            SET total_files=?, prepared_files=?, running_files=?, completed_files=?, passed_files=?, failed_files=?,
                critical_count=?, major_count=?, minor_count=?, status=?, finished_at=COALESCE(?, finished_at), last_updated_at=?
            WHERE run_id=?
            """,
            (
                total, total, running, completed, int(row["passed_files"] or 0), int(row["failed_files"] or 0) + error_files,
                int(row["critical_count"] or 0), int(row["major_count"] or 0), int(row["minor_count"] or 0), status,
                finished_at, now_iso(), run_id,
            ),
        )


def set_batch_report_path(run_id: str, path: str) -> None:
    with get_db() as con:
        con.execute("UPDATE runs SET batch_report_path=?, last_updated_at=? WHERE run_id=?", (path, now_iso(), run_id))


def insert_file_pairs(run_id: str, user_id: int, source_type: str, pairs: list[dict]) -> list[dict]:
    inserted = []
    with get_db() as con:
        for idx, p in enumerate(pairs, start=1):
            file_no = int(p.get("file_no") or idx)
            cur = con.execute(
                """
                INSERT INTO file_pairs (pair_id, run_id, user_id, file_no, source_type, source_name, html_name, status, status_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 'Prepared and waiting to run.', ?)
                """,
                (p["pair_id"], run_id, user_id, file_no, source_type, p.get("source_name") or p.get("pdf_name") or "", p.get("html_name") or "", now_iso()),
            )
            inserted.append({**p, "file_pair_db_id": int(cur.lastrowid), "file_no": file_no})
    return inserted


def get_run_for_user(run_id: str, user_id: int) -> Optional[dict]:
    with get_db() as con:
        row = con.execute(
            """
            SELECT r.*, u.username AS ran_by, u.email AS ran_by_email, u.display_name AS ran_by_display_name
            FROM runs r JOIN users u ON u.id = r.user_id
            WHERE r.run_id = ? AND r.user_id = ?
            """,
            (run_id, user_id),
        ).fetchone()
        return row_to_dict(row)


def get_run_by_id(run_id: str) -> Optional[dict]:
    with get_db() as con:
        row = con.execute(
            """
            SELECT r.*, u.username AS ran_by, u.email AS ran_by_email, u.display_name AS ran_by_display_name
            FROM runs r JOIN users u ON u.id = r.user_id
            WHERE r.run_id = ?
            """,
            (run_id,),
        ).fetchone()
        return row_to_dict(row)


def list_runs_for_user(user_id: int, limit: int = 100) -> list[dict]:
    with get_db() as con:
        rows = con.execute(
            """
            SELECT r.*, u.username AS ran_by, u.email AS ran_by_email, u.display_name AS ran_by_display_name
            FROM runs r JOIN users u ON u.id = r.user_id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def list_all_runs(limit: int = 250) -> list[dict]:
    with get_db() as con:
        rows = con.execute(
            """
            SELECT r.*, u.username AS ran_by, u.email AS ran_by_email, u.display_name AS ran_by_display_name
            FROM runs r JOIN users u ON u.id = r.user_id
            ORDER BY r.created_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_problem_runs(limit: int = 250) -> list[dict]:
    with get_db() as con:
        rows = con.execute(
            """
            SELECT r.*, u.username AS ran_by, u.email AS ran_by_email
            FROM runs r JOIN users u ON u.id = r.user_id
            WHERE r.status IN ('failed','error','interrupted')
            ORDER BY r.last_updated_at DESC, r.created_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_file_pair_running(file_pair_id: int, job_id: str) -> None:
    with get_db() as con:
        con.execute(
            """
            UPDATE file_pairs SET status='running', status_message='QA is running.', job_id=?, started_at=?, error_message=NULL WHERE id=?
            """,
            (job_id, now_iso(), file_pair_id),
        )


def update_file_pair_done(file_pair_id: int, data: dict) -> None:
    with get_db() as con:
        con.execute(
            """
            UPDATE file_pairs
            SET status='done', status_message='QA completed.', file_severity=?, language=?, issue_count=?,
                critical_count=?, major_count=?, minor_count=?, report_path=?, audit_path=?, error_message=NULL, finished_at=?
            WHERE id=?
            """,
            (
                data.get("file_severity"), data.get("language"), int(data.get("issue_count", 0)), int(data.get("critical_count", 0)),
                int(data.get("major_count", 0)), int(data.get("minor_count", 0)), data.get("report_path", ""), data.get("audit_path", ""),
                now_iso(), file_pair_id,
            ),
        )


def update_file_pair_error(file_pair_id: int, message: str) -> None:
    with get_db() as con:
        con.execute(
            """
            UPDATE file_pairs SET status='error', status_message='QA failed.', error_message=?, finished_at=? WHERE id=?
            """,
            (message, now_iso(), file_pair_id),
        )


def get_file_pair_for_user(file_pair_id: int, user_id: int) -> Optional[dict]:
    with get_db() as con:
        row = con.execute(
            """
            SELECT fp.*, u.username AS ran_by, u.email AS ran_by_email, u.display_name AS ran_by_display_name
            FROM file_pairs fp JOIN runs r ON r.run_id = fp.run_id JOIN users u ON u.id = fp.user_id
            WHERE fp.id = ? AND r.user_id = ?
            """,
            (file_pair_id, user_id),
        ).fetchone()
        return row_to_dict(row)


def get_file_pair_by_id(file_pair_id: int) -> Optional[dict]:
    with get_db() as con:
        row = con.execute(
            """
            SELECT fp.*, u.username AS ran_by, u.email AS ran_by_email, u.display_name AS ran_by_display_name
            FROM file_pairs fp JOIN users u ON u.id = fp.user_id WHERE fp.id=?
            """,
            (file_pair_id,),
        ).fetchone()
        return row_to_dict(row)


def get_file_pair_by_pair_id(pair_id: str) -> Optional[dict]:
    with get_db() as con:
        row = con.execute("SELECT * FROM file_pairs WHERE pair_id=?", (pair_id,)).fetchone()
        return row_to_dict(row)


def list_file_pairs_for_run(run_id: str) -> list[dict]:
    with get_db() as con:
        rows = con.execute(
            """
            SELECT fp.*, u.username AS ran_by, u.email AS ran_by_email, u.display_name AS ran_by_display_name
            FROM file_pairs fp JOIN users u ON u.id = fp.user_id
            WHERE fp.run_id=? ORDER BY fp.file_no ASC
            """,
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def replace_issues_for_file_pair(file_pair_id: int, run_id: str, issues: list[dict]) -> None:
    with get_db() as con:
        con.execute("DELETE FROM issues WHERE file_pair_id=?", (file_pair_id,))
        con.executemany(
            """
            INSERT INTO issues (file_pair_id, run_id, category, severity, engine_severity, area, html_line, message, expected, actual, snippet, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    file_pair_id, run_id, i.get("category", ""), i.get("severity", ""), i.get("engine_severity", ""), i.get("area", ""),
                    str(i.get("line", "") if i.get("line") is not None else ""), i.get("message", ""), i.get("expected", ""), i.get("actual", ""),
                    i.get("snippet", ""), now_iso(),
                )
                for i in issues
            ],
        )


def list_issues_for_file_pair(file_pair_id: int) -> list[dict]:
    with get_db() as con:
        rows = con.execute("SELECT * FROM issues WHERE file_pair_id=? ORDER BY id ASC", (file_pair_id,)).fetchall()
        return [dict(r) for r in rows]


def list_issues_for_run(run_id: str) -> list[dict]:
    with get_db() as con:
        rows = con.execute(
            """
            SELECT i.*, fp.file_no, fp.source_name, fp.html_name
            FROM issues i JOIN file_pairs fp ON fp.id=i.file_pair_id
            WHERE i.run_id=? ORDER BY fp.file_no ASC, i.id ASC
            """,
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def add_audit_log(user_id: Optional[int], action: str, details: Any = None, target_type: str = "", target_id: str = "", ip_address: str = "") -> None:
    if details is None:
        details_text = ""
    elif isinstance(details, str):
        details_text = details
    else:
        details_text = json.dumps(details, ensure_ascii=False)
    actor_username = ""
    actor_email = ""
    if user_id:
        u = get_any_user_by_id(int(user_id))
        if u:
            actor_username = u.get("username", "")
            actor_email = u.get("email", "")
    with get_db() as con:
        con.execute(
            """
            INSERT INTO audit_logs (user_id, actor_username, actor_email, action, target_type, target_id, details, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, actor_username, actor_email, action, target_type, str(target_id or ""), details_text, ip_address, now_iso()),
        )


def list_audit_logs(limit: int = 300) -> list[dict]:
    with get_db() as con:
        rows = con.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def admin_summary() -> dict:
    with get_db() as con:
        users = con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        active_users = con.execute("SELECT COUNT(*) c FROM users WHERE status='active'").fetchone()["c"]
        pending_invites = con.execute("SELECT COUNT(*) c FROM invites WHERE status='pending'").fetchone()["c"]
        pending_resets = con.execute("SELECT COUNT(*) c FROM password_resets WHERE status IN ('requested','link_generated')").fetchone()["c"]
        runs = con.execute("SELECT COUNT(*) c FROM runs").fetchone()["c"]
        completed = con.execute("SELECT COUNT(*) c FROM runs WHERE status='done'").fetchone()["c"]
        failed = con.execute("SELECT COUNT(*) c FROM runs WHERE status IN ('failed','error')").fetchone()["c"]
        interrupted = con.execute("SELECT COUNT(*) c FROM runs WHERE status='interrupted'").fetchone()["c"]
        critical = con.execute("SELECT COALESCE(SUM(critical_count),0) c FROM runs").fetchone()["c"]
    return {
        "users": int(users or 0), "active_users": int(active_users or 0), "pending_invites": int(pending_invites or 0),
        "pending_resets": int(pending_resets or 0),
        "runs": int(runs or 0), "completed_runs": int(completed or 0), "failed_runs": int(failed or 0),
        "interrupted_runs": int(interrupted or 0), "critical_issues": int(critical or 0),
    }