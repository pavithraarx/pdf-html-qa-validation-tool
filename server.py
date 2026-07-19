"""
server.py  —  Flask backend for the batch PDF→HTML QA Tool
"""

import os, sys, json, uuid, threading, webbrowser, zipfile, re, io, tempfile
from pathlib import Path
from datetime import date, datetime
from types import SimpleNamespace
from flask import Flask, request, jsonify, send_from_directory, send_file, render_template_string
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from qa_engine import run_checks, Issue
from report import generate_report

BASE      = Path(__file__).parent
REPORTS   = BASE / "reports"
STATIC    = BASE / "static"
AUDIT_DIR = BASE / "audits"
for _d in (REPORTS, STATIC, AUDIT_DIR):
    _d.mkdir(exist_ok=True)

VALIDATOR_VERSION = "2.1.0-dashboard-batch"


def _cache_get(*args, **kwargs):
    # Cache disabled intentionally: uploaded files are kept in memory only.
    return None


def _cache_put(*args, **kwargs) -> None:
    # Cache disabled intentionally.
    return None


def _write_audit(uid: str, result: dict) -> None:
    errors = sum(1 for i in result["issues"] if i.severity == "error")
    with open(AUDIT_DIR / f"{uid}.json", "w") as f:
        json.dump({
            "document_id":       uid,
            "validated_at":      date.today().isoformat(),
            "validator_version": VALIDATOR_VERSION,
            "result":            "PASS" if errors == 0 else "FAIL",
        }, f, indent=2)

app = Flask(__name__, static_folder=str(STATIC))


# In-memory stores.
# _jobs:    { job_id: { status, progress, label, result } }
# _batches: { batch_id: { batch_id, created_at, pairs, jobs } }
_jobs: dict = {}
_batches: dict = {}
_prepared_pairs: dict = {}
_id_counter = [0]
_batch_counter = [0]
_id_lock = threading.Lock()


def _next_qa_id():
    with _id_lock:
        _id_counter[0] += 1
        return f"QA-{_id_counter[0]:04d}"


def _next_batch_id():
    with _id_lock:
        _batch_counter[0] += 1
        return f"BATCH-{date.today().strftime('%Y%m%d')}-{_batch_counter[0]:03d}"


CRITICAL_CATEGORIES = {
    "Changed Text",
    "Missing Text",
    "Extra Text",
    "Title Mismatch",
    "Missing Title",
    "Broken Image",
    "Missing Image",
    "Image Mismatch",
    "Image Content Mismatch",
    "Garbled Text",
    "Encoding / Mojibake",
    "Unexpected Closing Tag",
    "Unclosed Tag",
    "HTML Parse Error",
    "Missing Punctuation",
    "Extra Punctuation",
    "Punctuation Mismatch",
}

MAJOR_CATEGORIES = {
    "Missing Heading Tag",
    "Heading Level Mismatch",
    "Missing B Tag",
    "Missing Required B Tag",
    "Missing Strong/Bold Tag",
    "Unexpected Strong/Bold Tag",
    "Missing Emphasis/Italic Tag",
    "Unexpected Emphasis/Italic Tag",
    "Bullet Marker Mismatch",
    "Missing Bullet Marker",
    "Missing List Item Tag",
    "Style Attribute Mismatch",
    "Tag Attribute Mismatch",
    "Text Outside Expected HTML Tags",
    "Broken Link",
}

MINOR_CATEGORIES = {
    "Filename Mismatch",
    "Placeholder Text",
    "Placeholder",
    "Image Order Mismatch",
}

CONTENT_CATEGORIES = {
    "Changed Text", "Missing Text", "Extra Text", "Missing Punctuation",
    "Extra Punctuation", "Punctuation Mismatch", "Garbled Text", "Encoding / Mojibake",
}
STRUCTURE_CATEGORIES = {
    "Missing Heading Tag", "Heading Level Mismatch", "Missing B Tag",
    "Missing Required B Tag", "Missing Strong/Bold Tag", "Unexpected Strong/Bold Tag",
    "Missing Emphasis/Italic Tag", "Unexpected Emphasis/Italic Tag",
    "Bullet Marker Mismatch", "Missing Bullet Marker", "Missing List Item Tag",
    "Tag Attribute Mismatch", "Unexpected Closing Tag", "Unclosed Tag", "HTML Parse Error",
}
STYLE_CATEGORIES = {"Style Attribute Mismatch"}
IMAGE_CATEGORIES = {
    "Broken Image", "Missing Image", "Image Mismatch", "Image Content Mismatch",
    "Image Order Mismatch",
}
METADATA_CATEGORIES = {"Filename Mismatch", "Title Mismatch", "Missing Title", "Broken Link"}


def _display_severity(issue) -> str:
    """Map engine severity/categories to the user-facing Critical/Major/Minor scale."""
    category = getattr(issue, "category", "") or ""
    raw = (getattr(issue, "severity", "") or "").lower()

    if category in CRITICAL_CATEGORIES:
        return "Critical"
    if category in MAJOR_CATEGORIES:
        return "Major"
    if category in MINOR_CATEGORIES:
        return "Minor"

    # Safe fallback: engine errors are content-breaking unless explicitly mapped.
    if raw == "error":
        return "Critical"
    if raw == "warning":
        return "Major"
    return "Minor"


def _issue_area(issue) -> str:
    category = getattr(issue, "category", "") or ""
    if category in CONTENT_CATEGORIES:
        return "Content"
    if category in STRUCTURE_CATEGORIES:
        return "Structure"
    if category in STYLE_CATEGORIES:
        return "Style"
    if category in IMAGE_CATEGORIES:
        return "Image"
    if category in METADATA_CATEGORIES:
        return "Metadata"
    return "Other"


def _issue_to_dict(issue) -> dict:
    sev = _display_severity(issue)
    return {
        "category": getattr(issue, "category", "") or "",
        "severity": sev,
        "engine_severity": getattr(issue, "severity", "") or "",
        "area": _issue_area(issue),
        "line": getattr(issue, "line", None),
        "message": getattr(issue, "message", "") or "",
        "snippet": getattr(issue, "snippet", "") or "",
        "expected": getattr(issue, "expected", "") or "",
        "actual": getattr(issue, "actual", "") or "",
    }


def _counts_by_severity(issue_dicts: list[dict]) -> dict:
    return {
        "critical": sum(1 for i in issue_dicts if i.get("severity") == "Critical"),
        "major": sum(1 for i in issue_dicts if i.get("severity") == "Major"),
        "minor": sum(1 for i in issue_dicts if i.get("severity") == "Minor"),
    }


def _file_overall_severity(counts: dict) -> str:
    """One file-level severity shown on the batch front page."""
    critical = counts.get("critical", 0)
    major = counts.get("major", 0)
    minor = counts.get("minor", 0)

    if critical >= 1 or major >= 5:
        return "Critical"
    if major >= 1 or minor >= 8:
        return "Major"
    if minor >= 1:
        return "Minor"
    return "Passed"


def _issue_for_report(issue):
    """Return a report-friendly issue object with Critical/Major/Minor severity."""
    d = _issue_to_dict(issue)
    return SimpleNamespace(
        category=d["category"],
        severity=d["severity"],
        line=d["line"],
        message=d["message"],
        snippet=d["snippet"],
        expected=d["expected"],
        actual=d["actual"],
        area=d["area"],
    )


def _summarize_result(result: dict, pair: dict, uid: str, report_path: str, file_no=None) -> dict:
    issue_dicts = [_issue_to_dict(i) for i in result.get("issues", [])]
    counts = _counts_by_severity(issue_dicts)
    total = len(issue_dicts)
    file_severity = _file_overall_severity(counts)
    status = "Passed" if total == 0 else "Failed"

    type_counts = {}
    area_counts = {}
    for issue in issue_dicts:
        type_counts[issue["category"]] = type_counts.get(issue["category"], 0) + 1
        area_counts[issue["area"]] = area_counts.get(issue["area"], 0) + 1

    return {
        "unique_id": uid,
        "file_no": file_no,
        "pair_id": pair.get("pair_id", ""),
        "pdf_name": pair.get("pdf_name") or Path(pair.get("pdf_path", "")).name,
        "html_name": pair.get("html_name") or Path(pair.get("html_path", "")).name,
        "language": result.get("language", ""),
        "status": status,
        "file_severity": file_severity,
        "issue_count": total,
        "critical_count": counts["critical"],
        "major_count": counts["major"],
        "minor_count": counts["minor"],
        "type_counts": type_counts,
        "area_counts": area_counts,
        "report_path": report_path,
        "issues": issue_dicts,
    }


def _register_batch_pair(batch_id: str, pair: dict) -> None:
    if not batch_id:
        return
    batch = _batches.setdefault(batch_id, {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "pairs": {},
        "jobs": [],
    })
    if pair.get("pair_id"):
        batch["pairs"][pair["pair_id"]] = pair


def _register_batch_job(batch_id: str, job_id: str, result: dict) -> None:
    if not batch_id:
        return
    batch = _batches.setdefault(batch_id, {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "pairs": {},
        "jobs": [],
    })
    if job_id not in batch["jobs"]:
        batch["jobs"].append(job_id)


def _batch_summary(batch_id: str) -> dict:
    batch = _batches.get(batch_id) or {"jobs": []}
    results = []
    for jid in batch.get("jobs", []):
        job = _jobs.get(jid)
        if job and job.get("status") == "done" and job.get("result"):
            results.append(job["result"])

    total_files = len(batch.get("pairs", {})) or len(results)
    completed = len(results)
    failed = sum(1 for r in results if r.get("status") == "Failed")
    passed = sum(1 for r in results if r.get("status") == "Passed")

    return {
        "batch_id": batch_id,
        "total_files": total_files,
        "completed_files": completed,
        "passed_files": passed,
        "failed_files": failed,
        "critical_issues": sum(r.get("critical_count", 0) for r in results),
        "major_issues": sum(r.get("major_count", 0) for r in results),
        "minor_issues": sum(r.get("minor_count", 0) for r in results),
        "results": results,
    }


BATCH_COLUMNS = [
    "Batch No", "File No", "PDF File", "HTML File", "File Status", "File Severity",
    "Total File Errors", "Critical Count", "Major Count", "Minor Count", "Language",
    "Error Type", "Error Severity", "Error Area", "HTML Line #", "Description",
    "Expected", "Actual", "Excerpt / Snippet",
]


def _cell(ws, row, col, value="", bold=False, bg=None, fg="000000", wrap=False, align="left"):
    thin = Side(border_style="thin", color="D0D5EE")
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name="Arial", size=10, bold=bold, color=fg)
    if bg:
        c.fill = PatternFill("solid", start_color=bg)
    c.alignment = Alignment(horizontal=align, vertical="top", wrap_text=wrap)
    c.border = Border(left=thin, right=thin, top=thin, bottom=thin)
    return c

def generate_batch_report(batch_id: str, output_path: str) -> str:
    """
    Batch Excel report with 3 readable sheets.

    Sheet 1: Overall Summary
    Sheet 2: File Based Summary
    Sheet 3: Individual File Errors

    No frozen panes.
    No Excel grouping/outline.
    No hidden rows.
    """

    summary = _batch_summary(batch_id)
    raw_results = sorted(summary.get("results", []), key=lambda x: x.get("file_no") or 99999)

    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "Overall Summary"
    ws_files = wb.create_sheet("File Based Summary")
    ws_errors = wb.create_sheet("Individual File Errors")

    for ws in [ws_summary, ws_files, ws_errors]:
        ws.sheet_view.showGridLines = False
        ws.freeze_panes = None

    COLORS = {
        "navy": "0F172A",
        "white": "FFFFFF",
        "muted": "64748B",
        "light_bg": "F8FAFC",
        "section_bg": "EAF1FF",
        "section_fg": "1E3A8A",
        "header_bg": "1E293B",
        "header_fg": "FFFFFF",
        "border": "D0D7E2",

        "Critical_bg": "FEE2E2",
        "Critical_fg": "DC2626",
        "Critical_band": "FCA5A5",

        "Major_bg": "FFEDD5",
        "Major_fg": "C2410C",
        "Major_band": "FDBA74",

        "Minor_bg": "FEF9C3",
        "Minor_fg": "A16207",
        "Minor_band": "FDE68A",

        "Passed_bg": "DCFCE7",
        "Passed_fg": "15803D",
        "Passed_band": "86EFAC",

        "label_bg": "F1F5F9",
        "expected_bg": "EFF6FF",
        "actual_bg": "FFF7ED",
        "context_bg": "F8FAFC",
    }

    thin = Side(border_style="thin", color=COLORS["border"])
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def safe_text(value):
        value = "" if value is None else str(value)
        value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
        if value.startswith(("=", "+", "-", "@")):
            value = "'" + value
        return value

    def short_text(value, limit=240):
        value = safe_text(value)
        if len(value) <= limit:
            return value
        return value[:limit].rstrip() + "..."

    def count_issues(issues, severity):
        return sum(1 for i in issues if (i.get("severity") or "").lower() == severity.lower())

    def derive_file_severity(critical, major, minor):
        if critical > 0:
            return "Critical"
        if major > 0:
            return "Major"
        if minor > 0:
            return "Minor"
        return "Passed"

    def derive_status(issue_count):
        return "Passed" if issue_count == 0 else "Failed"

    def sev_style(severity):
        severity = severity or "Minor"

        if severity == "Critical":
            return {"bg": COLORS["Critical_bg"], "fg": COLORS["Critical_fg"], "band": COLORS["Critical_band"]}
        if severity == "Major":
            return {"bg": COLORS["Major_bg"], "fg": COLORS["Major_fg"], "band": COLORS["Major_band"]}
        if severity == "Passed":
            return {"bg": COLORS["Passed_bg"], "fg": COLORS["Passed_fg"], "band": COLORS["Passed_band"]}

        return {"bg": COLORS["Minor_bg"], "fg": COLORS["Minor_fg"], "band": COLORS["Minor_band"]}

    def style_cell(
        cell,
        bg=None,
        fg="000000",
        bold=False,
        size=10,
        align="left",
        vertical="top",
        wrap=True,
        italic=False,
    ):
        cell.font = Font(name="Aptos", size=size, bold=bold, italic=italic, color=fg)

        if bg:
            cell.fill = PatternFill("solid", start_color=bg, end_color=bg)

        cell.alignment = Alignment(horizontal=align, vertical=vertical, wrap_text=wrap)
        cell.border = border
        return cell

    def write_cell(
        ws,
        row,
        col,
        value="",
        bg=None,
        fg="000000",
        bold=False,
        size=10,
        align="left",
        vertical="top",
        wrap=True,
        italic=False,
    ):
        cell = ws.cell(row=row, column=col, value=safe_text(value))
        return style_cell(
            cell,
            bg=bg,
            fg=fg,
            bold=bold,
            size=size,
            align=align,
            vertical=vertical,
            wrap=wrap,
            italic=italic,
        )

    def merge_row(
        ws,
        row,
        start_col,
        end_col,
        text,
        bg,
        fg="000000",
        bold=True,
        size=11,
        height=None,
        align="left",
    ):
        ws.merge_cells(start_row=row, start_column=start_col, end_row=row, end_column=end_col)

        cell = ws.cell(row=row, column=start_col, value=safe_text(text))
        style_cell(cell, bg=bg, fg=fg, bold=bold, size=size, align=align, vertical="center", wrap=True)

        for col in range(start_col + 1, end_col + 1):
            style_cell(ws.cell(row=row, column=col), bg=bg, fg=fg, bold=bold, size=size)

        if height:
            ws.row_dimensions[row].height = height

        return cell

    def merge_detail_row(ws, row, label, value, bg, max_col, label_fg="334155"):
        write_cell(
            ws,
            row,
            1,
            label,
            bg=bg,
            fg=label_fg,
            bold=True,
            size=9,
            align="right",
            vertical="top",
            wrap=True,
        )

        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=max_col)

        cell = ws.cell(row=row, column=2, value=safe_text(value) or "—")
        style_cell(cell, bg=bg, fg="0F172A", bold=False, size=9, align="left", vertical="top", wrap=True)

        for col in range(3, max_col + 1):
            style_cell(ws.cell(row=row, column=col), bg=bg, fg="0F172A", size=9, wrap=True)

        length = len(safe_text(value))
        if length > 450:
            ws.row_dimensions[row].height = 90
        elif length > 220:
            ws.row_dimensions[row].height = 60
        else:
            ws.row_dimensions[row].height = 34

    def issue_sort_key(issue):
        order = {"Critical": 0, "Major": 1, "Minor": 2}
        return (
            order.get(issue.get("severity"), 9),
            issue.get("line") or 999999,
            issue.get("category") or "",
        )

    # Normalize result data
    results = []

    for r in raw_results:
        issues = r.get("issues") or []

        critical = r.get("critical_count")
        major = r.get("major_count")
        minor = r.get("minor_count")

        if critical is None:
            critical = count_issues(issues, "Critical")
        if major is None:
            major = count_issues(issues, "Major")
        if minor is None:
            minor = count_issues(issues, "Minor")

        issue_count = r.get("issue_count")
        if issue_count is None:
            issue_count = len(issues)

        file_severity = r.get("file_severity") or derive_file_severity(critical, major, minor)
        status = r.get("status") or derive_status(issue_count)

        if issue_count == 0:
            status = "Passed"
            file_severity = "Passed"
        else:
            status = "Failed"

        results.append({
            **r,
            "issues": issues,
            "issue_count": issue_count,
            "critical_count": critical,
            "major_count": major,
            "minor_count": minor,
            "file_severity": file_severity,
            "status": status,
        })

    # Common counts
    total_files = len(results) or summary.get("total_files", 0)
    completed_files = len(results) or summary.get("completed_files", 0)
    passed_files = sum(1 for r in results if r.get("issue_count", 0) == 0)
    failed_files = sum(1 for r in results if r.get("issue_count", 0) > 0)

    total_issues = sum(r.get("issue_count", 0) for r in results)
    total_critical = sum(r.get("critical_count", 0) for r in results)
    total_major = sum(r.get("major_count", 0) for r in results)
    total_minor = sum(r.get("minor_count", 0) for r in results)

    category_counter = Counter()
    for r in results:
        for issue in r.get("issues") or []:
            category_counter[issue.get("category") or "Unknown"] += 1

    file_sev_counter = Counter(r.get("file_severity") or "Passed" for r in results)

    # -------------------------
    # SHEET 1: OVERALL SUMMARY
    # -------------------------

    for col, width in {
        1: 24,
        2: 16,
        3: 24,
        4: 16,
        5: 24,
        6: 16,
    }.items():
        ws_summary.column_dimensions[get_column_letter(col)].width = width

    row = 1

    merge_row(
        ws_summary,
        row,
        1,
        6,
        f"PDF to HTML QA Validation Report · {batch_id}",
        COLORS["navy"],
        COLORS["white"],
        bold=True,
        size=15,
        height=32,
    )

    row += 1
    merge_row(
        ws_summary,
        row,
        1,
        6,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}    |    Overall Summary",
        "EEF2FF",
        COLORS["muted"],
        bold=False,
        size=10,
        height=24,
    )

    row += 2

    merge_row(ws_summary, row, 1, 6, "BATCH OVERVIEW", COLORS["section_bg"], COLORS["section_fg"], True, 11, 24)

    row += 1

    overview_items = [
        ("Total Files", total_files),
        ("Completed Files", completed_files),
        ("Passed Files", passed_files),
        ("Failed Files", failed_files),
        ("Total Errors", total_issues),
        ("Batch ID", batch_id),
    ]

    for idx, (label, value) in enumerate(overview_items):
        col = 1 if idx % 2 == 0 else 4

        write_cell(ws_summary, row, col, label, bg=COLORS["label_bg"], fg=COLORS["muted"], bold=True, align="center")
        ws_summary.merge_cells(start_row=row, start_column=col + 1, end_row=row, end_column=col + 2)

        cell = ws_summary.cell(row=row, column=col + 1, value=safe_text(value))
        style_cell(cell, bg=COLORS["white"], fg="000000", bold=True, size=11, align="center", vertical="center")

        for c in range(col + 2, col + 3):
            style_cell(ws_summary.cell(row=row, column=c), bg=COLORS["white"])

        if idx % 2 == 1:
            row += 1

    row += 2

    merge_row(ws_summary, row, 1, 6, "ERROR SEVERITY DISTRIBUTION", COLORS["section_bg"], COLORS["section_fg"], True, 11, 24)
    row += 1

    severity_rows = [
        ("Critical Errors", total_critical, "Critical"),
        ("Major Errors", total_major, "Major"),
        ("Minor Errors", total_minor, "Minor"),
    ]

    for label, value, sev in severity_rows:
        s = sev_style(sev)
        write_cell(ws_summary, row, 1, label, bg=s["bg"], fg=s["fg"], bold=True)
        write_cell(ws_summary, row, 2, value, bg=s["bg"], fg=s["fg"], bold=True, align="center")
        ws_summary.row_dimensions[row].height = 24
        row += 1

    row += 1

    merge_row(ws_summary, row, 1, 6, "FILE SEVERITY DISTRIBUTION", COLORS["section_bg"], COLORS["section_fg"], True, 11, 24)
    row += 1

    for sev in ["Critical", "Major", "Minor", "Passed"]:
        s = sev_style(sev)
        write_cell(ws_summary, row, 1, sev, bg=s["bg"], fg=s["fg"], bold=True)
        write_cell(ws_summary, row, 2, file_sev_counter.get(sev, 0), bg=s["bg"], fg=s["fg"], bold=True, align="center")
        ws_summary.row_dimensions[row].height = 24
        row += 1

    row += 1

    merge_row(ws_summary, row, 1, 6, "ERROR CATEGORY BREAKDOWN", COLORS["section_bg"], COLORS["section_fg"], True, 11, 24)
    row += 1

    write_cell(ws_summary, row, 1, "Error Type", bg=COLORS["header_bg"], fg=COLORS["header_fg"], bold=True, align="center")
    write_cell(ws_summary, row, 2, "Count", bg=COLORS["header_bg"], fg=COLORS["header_fg"], bold=True, align="center")
    row += 1

    if category_counter:
        for category, count in category_counter.most_common():
            write_cell(ws_summary, row, 1, category, bg=COLORS["white"])
            write_cell(ws_summary, row, 2, count, bg=COLORS["white"], bold=True, align="center")
            row += 1
    else:
        merge_row(ws_summary, row, 1, 6, "No errors found in this batch.", COLORS["Passed_bg"], COLORS["Passed_fg"], True, 10, 26)
        row += 1

    row += 2

    merge_row(ws_summary, row, 1, 6, "COLOR KEY", COLORS["section_bg"], COLORS["section_fg"], True, 11, 24)
    row += 1

    color_key = [
        ("Critical", "Content, image, title, filename, or correctness issue that can affect meaning or usability."),
        ("Major", "Structure, tag, list, or formatting issue that affects conversion quality."),
        ("Minor", "Low-risk formatting or cosmetic issue."),
        ("Passed", "No issue found for the file."),
    ]

    for sev, meaning in color_key:
        s = sev_style(sev)
        write_cell(ws_summary, row, 1, sev, bg=s["bg"], fg=s["fg"], bold=True, align="center")
        ws_summary.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)

        cell = ws_summary.cell(row=row, column=2, value=meaning)
        style_cell(cell, bg=COLORS["white"], fg="000000", size=9, wrap=True)

        for c in range(3, 7):
            style_cell(ws_summary.cell(row=row, column=c), bg=COLORS["white"])

        ws_summary.row_dimensions[row].height = 28
        row += 1

    # -------------------------
    # SHEET 3: INDIVIDUAL FILE ERRORS
    # Build this before Sheet 2 so Sheet 2 can link to exact rows.
    # -------------------------

    for col, width in {
        1: 8,
        2: 28,
        3: 14,
        4: 14,
        5: 12,
        6: 20,
        7: 20,
        8: 20,
        9: 20,
        10: 20,
        11: 20,
    }.items():
        ws_errors.column_dimensions[get_column_letter(col)].width = width

    error_max_col = 11
    detail_row_by_file_no = {}

    row = 1

    merge_row(
        ws_errors,
        row,
        1,
        error_max_col,
        f"Individual File Errors · {batch_id}",
        COLORS["navy"],
        COLORS["white"],
        bold=True,
        size=15,
        height=32,
    )

    row += 1
    merge_row(
        ws_errors,
        row,
        1,
        error_max_col,
        "Each file is shown separately. For every error, the Expected, Actual, and Context are displayed below the error summary.",
        "EEF2FF",
        COLORS["muted"],
        bold=False,
        size=10,
        height=28,
    )

    row += 3

    if not results:
        merge_row(ws_errors, row, 1, error_max_col, "No completed QA results found.", COLORS["light_bg"], COLORS["muted"], True, 11, 26)
    else:
        for result in results:
            file_no = result.get("file_no") or "—"
            detail_row_by_file_no[file_no] = row

            file_severity = result.get("file_severity") or "Passed"
            s = sev_style(file_severity)

            pdf_name = result.get("pdf_name") or "—"
            html_name = result.get("html_name") or "—"

            merge_row(
                ws_errors,
                row,
                1,
                error_max_col,
                f"FILE {file_no} — {pdf_name}  →  {html_name}",
                s["band"],
                s["fg"],
                bold=True,
                size=11,
                height=32,
            )

            row += 1

            file_meta = (
                f"Status: {result.get('status') or '—'}    |    "
                f"File Severity: {file_severity}    |    "
                f"Total Errors: {result.get('issue_count', 0)}    |    "
                f"Critical: {result.get('critical_count', 0)}    "
                f"Major: {result.get('major_count', 0)}    "
                f"Minor: {result.get('minor_count', 0)}    |    "
                f"Language: {result.get('language') or '—'}"
            )

            merge_row(ws_errors, row, 1, error_max_col, file_meta, s["bg"], s["fg"], True, 9, 26)
            row += 1

            merge_detail_row(ws_errors, row, "PDF", pdf_name, COLORS["light_bg"], error_max_col)
            row += 1

            merge_detail_row(ws_errors, row, "HTML", html_name, COLORS["light_bg"], error_max_col)
            row += 2

            issues = sorted(result.get("issues") or [], key=issue_sort_key)

            if not issues:
                merge_row(
                    ws_errors,
                    row,
                    1,
                    error_max_col,
                    "No issues found for this file.",
                    COLORS["Passed_bg"],
                    COLORS["Passed_fg"],
                    bold=True,
                    size=10,
                    height=28,
                )
                row += 3
                continue

            for idx, issue in enumerate(issues, 1):
                issue_severity = issue.get("severity") or "Minor"
                issue_style = sev_style(issue_severity)

                category = issue.get("category") or "—"
                area = issue.get("area") or "—"
                line = issue.get("line") or "—"
                message = issue.get("message") or "—"
                expected = issue.get("expected") or "—"
                actual = issue.get("actual") or "—"
                snippet = issue.get("snippet") or message or "—"

                # Error title row
                merge_row(
                    ws_errors,
                    row,
                    1,
                    error_max_col,
                    f"Error {idx}: {category} · {issue_severity}",
                    issue_style["bg"],
                    issue_style["fg"],
                    bold=True,
                    size=10,
                    height=24,
                )

                row += 1

                headers = ["#", "Error Type", "Severity", "Area", "HTML Line", "Description"]
                for col, header in enumerate(headers, 1):
                    write_cell(
                        ws_errors,
                        row,
                        col,
                        header,
                        bg=COLORS["header_bg"],
                        fg=COLORS["header_fg"],
                        bold=True,
                        size=9,
                        align="center",
                        vertical="center",
                    )

                ws_errors.merge_cells(start_row=row, start_column=6, end_row=row, end_column=error_max_col)
                style_cell(
                    ws_errors.cell(row=row, column=6),
                    bg=COLORS["header_bg"],
                    fg=COLORS["header_fg"],
                    bold=True,
                    size=9,
                    align="center",
                    vertical="center",
                )

                for col in range(7, error_max_col + 1):
                    style_cell(ws_errors.cell(row=row, column=col), bg=COLORS["header_bg"], fg=COLORS["header_fg"])

                ws_errors.row_dimensions[row].height = 22
                row += 1

                write_cell(ws_errors, row, 1, idx, bg=COLORS["white"], bold=True, align="center", vertical="center")
                write_cell(ws_errors, row, 2, category, bg=issue_style["bg"], fg=issue_style["fg"], bold=True, vertical="center")
                write_cell(ws_errors, row, 3, issue_severity, bg=issue_style["bg"], fg=issue_style["fg"], bold=True, align="center", vertical="center")
                write_cell(ws_errors, row, 4, area, bg=COLORS["white"], align="center", vertical="center")
                write_cell(ws_errors, row, 5, line, bg=COLORS["white"], align="center", vertical="center")

                ws_errors.merge_cells(start_row=row, start_column=6, end_row=row, end_column=error_max_col)
                desc_cell = ws_errors.cell(row=row, column=6, value=short_text(message, 300))
                style_cell(desc_cell, bg=COLORS["white"], fg="000000", size=9, wrap=True)

                for col in range(7, error_max_col + 1):
                    style_cell(ws_errors.cell(row=row, column=col), bg=COLORS["white"])

                ws_errors.row_dimensions[row].height = 44
                row += 1

                merge_detail_row(ws_errors, row, "Expected", expected, COLORS["expected_bg"], error_max_col)
                row += 1

                merge_detail_row(ws_errors, row, "Actual", actual, COLORS["actual_bg"], error_max_col)
                row += 1

                merge_detail_row(ws_errors, row, "Context", snippet, COLORS["context_bg"], error_max_col)
                row += 1

                merge_row(ws_errors, row, 1, error_max_col, "", COLORS["white"], "000000", False, 8, 10)
                row += 1

            row += 3

    # -------------------------
    # SHEET 2: FILE BASED SUMMARY
    # -------------------------

    for col, width in {
        1: 8,
        2: 44,
        3: 16,
        4: 16,
        5: 12,
        6: 12,
        7: 12,
        8: 12,
        9: 16,
        10: 18,
    }.items():
        ws_files.column_dimensions[get_column_letter(col)].width = width

    row = 1

    merge_row(
        ws_files,
        row,
        1,
        10,
        f"File Based Summary · {batch_id}",
        COLORS["navy"],
        COLORS["white"],
        bold=True,
        size=15,
        height=32,
    )

    row += 1
    merge_row(
        ws_files,
        row,
        1,
        10,
        "One row per file. Use the Details Link column to jump to the file's error section.",
        "EEF2FF",
        COLORS["muted"],
        bold=False,
        size=10,
        height=24,
    )

    row += 2

    headers = [
        "No",
        "File Pair",
        "Status",
        "File Severity",
        "Errors",
        "Critical",
        "Major",
        "Minor",
        "Language",
        "Details Link",
    ]

    header_row = row

    for col, header in enumerate(headers, 1):
        write_cell(
            ws_files,
            row,
            col,
            header,
            bg=COLORS["header_bg"],
            fg=COLORS["header_fg"],
            bold=True,
            size=9,
            align="center",
            vertical="center",
        )

    ws_files.row_dimensions[row].height = 24
    row += 1

    if not results:
        merge_row(ws_files, row, 1, 10, "No completed QA results found.", COLORS["light_bg"], COLORS["muted"], True, 10, 26)
    else:
        for result in results:
            file_no = result.get("file_no") or "—"
            file_severity = result.get("file_severity") or "Passed"
            s = sev_style(file_severity)

            file_pair = f"{result.get('pdf_name', '')}\n→ {result.get('html_name', '')}"

            values = [
                file_no,
                file_pair,
                result.get("status") or "—",
                file_severity,
                result.get("issue_count", 0),
                result.get("critical_count", 0),
                result.get("major_count", 0),
                result.get("minor_count", 0),
                result.get("language") or "—",
                "Open Details",
            ]

            for col, value in enumerate(values, 1):
                bg = s["bg"] if col in (3, 4) else COLORS["white"]
                fg = s["fg"] if col in (3, 4) else "000000"

                cell = write_cell(
                    ws_files,
                    row,
                    col,
                    value,
                    bg=bg,
                    fg=fg,
                    bold=col in (1, 3, 4, 5, 6, 7, 8, 10),
                    size=9,
                    align="center" if col != 2 else "left",
                    vertical="center",
                    wrap=True,
                )

                if col == 10:
                    target_row = detail_row_by_file_no.get(file_no)
                    if target_row:
                        cell.hyperlink = f"#'Individual File Errors'!A{target_row}"
                        cell.font = Font(name="Aptos", size=9, bold=True, color="2563EB", underline="single")

            ws_files.row_dimensions[row].height = 42
            row += 1

    end_row = row - 1

    if end_row >= header_row:
        ws_files.auto_filter.ref = f"A{header_row}:J{end_row}"

    # Page setup for all sheets
    for ws in [ws_summary, ws_files, ws_errors]:
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.page_margins.left = 0.25
        ws.page_margins.right = 0.25
        ws.page_margins.top = 0.5
        ws.page_margins.bottom = 0.5
        ws.sheet_view.zoomScale = 90
        ws.freeze_panes = None

    wb.save(output_path)
    return output_path

def _safe_relpath(name: str, fallback: str) -> Path:
    name = (name or fallback or "uploaded_file").replace("\\", "/").lstrip("/")
    parts = []
    for part in name.split("/"):
        part = part.strip()
        if not part or part in {".", ".."}:
            continue
        if part.startswith("__MACOSX") or part.startswith("."):
            continue
        parts.append(part)
    if not parts:
        parts = [Path(fallback or "uploaded_file").name]
    return Path(*parts)


def _normalized_pair_key(name_or_path) -> str:
    return re.sub(r"[^a-z0-9]+", "", Path(str(name_or_path)).stem.lower())


def _read_uploaded_file_items(file_storage, relpath: str):
    """Return uploaded/extracted files as in-memory byte items, never on disk."""
    original_name = file_storage.filename or "uploaded_file"
    uploaded_bytes = file_storage.read()
    if Path(original_name).suffix.lower() != ".zip":
        safe_rel = _safe_relpath(relpath, original_name)
        return [{
            "filename": safe_rel.name,
            "relpath": safe_rel.as_posix(),
            "data": uploaded_bytes,
        }]

    items = []
    try:
        with zipfile.ZipFile(io.BytesIO(uploaded_bytes)) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                zip_name = info.filename.replace("\\", "/")
                if zip_name.startswith("__MACOSX/"):
                    continue
                if Path(zip_name).name.startswith("."):
                    continue
                safe_rel = _safe_relpath(zip_name, Path(zip_name).name)
                with z.open(info) as src:
                    data = src.read()
                items.append({
                    "filename": safe_rel.name,
                    "relpath": safe_rel.as_posix(),
                    "data": data,
                })
    except zipfile.BadZipFile:
        raise ValueError(f"Invalid ZIP file: {original_name}")
    return items


def _write_prepared_pair_to_temp(prepared: dict, tmpdir: str):
    """Materialize one prepared pair into a temp folder for qa_engine, then caller deletes it."""
    tmp = Path(tmpdir)
    pdf_item = prepared["pdf"]
    html_item = prepared["html"]
    assets = prepared.get("assets", [])

    pdf_path = tmp / Path(pdf_item["filename"]).name
    html_path = tmp / Path(html_item["filename"]).name
    pdf_path.write_bytes(pdf_item["data"])
    html_path.write_bytes(html_item["data"])

    images_dir = tmp / "Images"
    images_dir.mkdir(exist_ok=True)
    asset_by_basename = {}

    for asset in assets:
        asset_name = Path(asset["filename"]).name
        asset_path = images_dir / asset_name
        # Keep the first asset for duplicate basenames, matching the old behavior.
        if not asset_path.exists():
            asset_path.write_bytes(asset["data"])
        asset_by_basename.setdefault(asset_name.lower(), asset_path)

    # Rewrite HTML image srcs by basename to the temp Images folder.
    try:
        from bs4 import BeautifulSoup
        raw = html_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        changed = False
        for img in soup.find_all("img"):
            src = img.get("src", "")
            basename = Path(src).name.lower()
            if not basename:
                continue
            asset_path = asset_by_basename.get(basename)
            if not asset_path:
                continue
            new_src = os.path.relpath(asset_path, html_path.parent).replace("\\", "/")
            if img.get("src") != new_src:
                img["src"] = new_src
                changed = True
        if changed:
            html_path.write_text(str(soup), encoding="utf-8")
    except Exception as e:
        print(f"Warning: could not rewrite temp HTML image paths: {e}")

    return str(pdf_path), str(html_path)


@app.route("/")
def index():
    return send_from_directory(str(STATIC), "index.html")


@app.route("/advanced")
def advanced_page():
    return send_from_directory(str(STATIC), "index.html")


@app.route("/simple")
def simple_page():
    return send_from_directory(str(STATIC), "index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """
    Accepts PDF/HTML files or ZIPs and prepares pairs in memory only.
    Nothing is written to uploads/ or any permanent upload folder.
    """
    session_id = str(uuid.uuid4())[:8]

    files = request.files.getlist("files")
    relpaths = request.form.getlist("relpaths")

    if len(relpaths) != len(files):
        relpaths = [f.filename for f in files]

    items = []
    for f, relpath in zip(files, relpaths):
        if not f or not f.filename:
            continue
        try:
            items.extend(_read_uploaded_file_items(f, relpath))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    pdfs = {}
    htmls = {}
    assets = []
    image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}

    for item in items:
        ext = Path(item["filename"]).suffix.lower()
        key = _normalized_pair_key(item["filename"])
        if ext == ".pdf":
            pdfs.setdefault(key, []).append(item)
        elif ext in (".html", ".htm"):
            htmls.setdefault(key, []).append(item)
        elif ext in image_exts:
            assets.append(item)

    pairs = []
    unmatched = []

    common_keys = sorted(set(pdfs) & set(htmls))
    for key in common_keys:
        pdf_list = pdfs[key]
        html_list = htmls[key]
        count = min(len(pdf_list), len(html_list))

        for idx in range(count):
            pdf_item = pdf_list[idx]
            html_item = html_list[idx]
            pair_id = f"{session_id}_{key}_{idx}"

            _prepared_pairs[pair_id] = {
                "pdf": pdf_item,
                "html": html_item,
                "assets": assets,
                "pdf_name": pdf_item["filename"],
                "html_name": html_item["filename"],
                "session": session_id,
            }

            pairs.append({
                "pair_id": pair_id,
                "pdf_name": pdf_item["filename"],
                "html_name": html_item["filename"],
                # Kept only for frontend compatibility; /run uses pair_id + memory store.
                "pdf_path": f"memory://{pair_id}/pdf",
                "html_path": f"memory://{pair_id}/html",
                "image_count": len(assets),
            })

        for extra_pdf in pdf_list[count:]:
            unmatched.append(extra_pdf["filename"])
        for extra_html in html_list[count:]:
            unmatched.append(extra_html["filename"])

    # Convenience fallback: exactly one PDF and exactly one HTML, even if names differ.
    all_pdfs = [p for plist in pdfs.values() for p in plist]
    all_htmls = [h for hlist in htmls.values() for h in hlist]

    if not pairs and len(all_pdfs) == 1 and len(all_htmls) == 1:
        pdf_item = all_pdfs[0]
        html_item = all_htmls[0]
        pair_id = f"{session_id}_single_pair"

        _prepared_pairs[pair_id] = {
            "pdf": pdf_item,
            "html": html_item,
            "assets": assets,
            "pdf_name": pdf_item["filename"],
            "html_name": html_item["filename"],
            "session": session_id,
        }

        pairs.append({
            "pair_id": pair_id,
            "pdf_name": pdf_item["filename"],
            "html_name": html_item["filename"],
            "pdf_path": f"memory://{pair_id}/pdf",
            "html_path": f"memory://{pair_id}/html",
            "image_count": len(assets),
        })
        unmatched = []
    else:
        for key in sorted(set(pdfs) - set(htmls)):
            unmatched.extend(p["filename"] for p in pdfs[key])
        for key in sorted(set(htmls) - set(pdfs)):
            unmatched.extend(h["filename"] for h in htmls[key])

    print("UPLOAD DEBUG")
    print("  items:", len(items))
    print("  pdf keys:", sorted(pdfs.keys())[:10], "... total", sum(len(v) for v in pdfs.values()))
    print("  html keys:", sorted(htmls.keys())[:10], "... total", sum(len(v) for v in htmls.values()))
    print("  assets:", len(assets))
    print("  pairs:", len(pairs))
    print("  unmatched:", len(unmatched))

    batch_id = _next_batch_id()
    _batches[batch_id] = {
        "batch_id": batch_id,
        "session": session_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "pairs": {p["pair_id"]: p for p in pairs},
        "jobs": [],
    }

    return jsonify({"pairs": pairs, "unmatched": unmatched, "session": session_id, "batch_id": batch_id})


@app.route("/run", methods=["POST"])
def run():
    """
    Kick off QA for one prepared in-memory pair. Returns { job_id }.
    The pair is written only to a TemporaryDirectory for the duration of the job.
    """
    data = request.json or {}
    pair_id = data.get("pair_id", "")
    batch_id = data.get("batch_id", "")
    file_no = data.get("file_no")

    prepared = _prepared_pairs.get(pair_id)
    if not prepared:
        return jsonify({"error": "Prepared file pair not found. Please prepare pairs again."}), 400

    pair_info = {
        "pair_id": pair_id,
        "pdf_path": f"memory://{pair_id}/pdf",
        "html_path": f"memory://{pair_id}/html",
        "pdf_name": data.get("pdf_name") or prepared.get("pdf_name", ""),
        "html_name": data.get("html_name") or prepared.get("html_name", ""),
        "file_no": file_no,
    }
    _register_batch_pair(batch_id, pair_info)

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "progress": 0, "label": "Starting…",
                     "result": None, "error": None}

    def worker():
        try:
            def prog(pct, label):
                _jobs[job_id]["progress"] = pct
                _jobs[job_id]["label"]    = label

            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path, html_path = _write_prepared_pair_to_temp(prepared, tmpdir)

                result = run_checks(pdf_path, html_path, progress_cb=prog)

                uid = _next_qa_id()
                _write_audit(uid, result)
                report_path = str(REPORTS / f"{uid}_{Path(prepared.get('pdf_name', 'report')).stem}.xlsx")

                report_issues = [_issue_for_report(i) for i in result["issues"]]
                generate_report(
                    pdf_path=pdf_path,
                    html_path=html_path,
                    issues=report_issues,
                    language=result["language"],
                    unique_id=uid,
                    output_path=report_path,
                )

                summary_result = _summarize_result(result, pair_info, uid, report_path, file_no=file_no)

            # At this point the temp PDF/HTML/images are deleted. Only report/audit remain.
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["result"] = summary_result
            _register_batch_job(batch_id, job_id, summary_result)

        except Exception as e:
            import traceback
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"]  = str(e) + "\n\n" + traceback.format_exc()

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Unknown job"}), 404
    return jsonify(job)


@app.route("/download/<job_id>")
def download(job_id):
    job = _jobs.get(job_id)
    if not job or job["status"] != "done":
        return "Not ready", 404
    path = job["result"]["report_path"]
    return send_file(path, as_attachment=True,
                     download_name=Path(path).name)


@app.route("/batch-summary/<batch_id>")
def batch_summary_route(batch_id):
    if batch_id not in _batches:
        return jsonify({"error": "Unknown batch"}), 404
    return jsonify(_batch_summary(batch_id))


@app.route("/download-batch/<batch_id>")
def download_batch(batch_id):
    if batch_id not in _batches:
        return "Unknown batch", 404
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", batch_id)
    output_path = str(REPORTS / f"{safe_name}_All_Files_QA_Report.xlsx")
    generate_batch_report(batch_id, output_path)
    return send_file(output_path, as_attachment=True, download_name=Path(output_path).name)


# ── Plain-HTML fallback (no JavaScript fetch/async/drag-drop at all) ─────────
# If the main page's JavaScript fails silently for any reason (locked-down
# corporate browser settings, an extension interfering, etc.), this gives a
# guaranteed-to-work path: a plain <form> that does a normal full-page POST.
# Everything runs synchronously in the request - submit, wait for the page
# to reload, see results. No fetch, no JSON parsing, no drag-and-drop API.

SIMPLE_PAGE = """
<!DOCTYPE html><html><head><meta charset="utf-8">
<title>QA Tool</title>
<style>
body{font-family:Arial,sans-serif;background:#0d1021;color:#e8eaf6;padding:32px;max-width:900px;margin:0 auto}
h1{font-size:20px}
h2{font-size:16px;margin-bottom:8px}
.box{background:#141828;border:1px solid #2a3060;border-radius:10px;padding:24px;margin:20px 0}
.upload-zone{background:#1c2240;border:1.5px solid #2a3060;border-radius:8px;padding:16px;margin:14px 0}
.upload-zone label{display:block;font-weight:700;margin-bottom:8px}
input[type=file]{display:block;margin:6px 0;color:#e8eaf6;width:100%}
button{background:linear-gradient(135deg,#5b8aff,#7c5cfc);color:#fff;border:none;
  border-radius:8px;padding:12px 20px;font-size:14px;font-weight:700;cursor:pointer;margin-top:10px}
table{width:100%;border-collapse:collapse;margin-top:12px;font-size:13px}
th,td{border:1px solid #2a3060;padding:8px;text-align:left;vertical-align:top}
th{background:#1c2240}
.error{color:#ff5c5c;font-weight:700}
.warning{color:#ffb547;font-weight:700}
.ok{color:#52d68a;font-weight:700}
a.dl{color:#5b8aff;text-decoration:none;font-weight:600}
.hint{color:#7880b0;font-size:13px}
.count{color:#5b8aff;font-size:12px;margin-top:4px}
</style></head><body>
<h1>PDF → HTML QA Tool</h1>
<p class="hint">Upload all your source PDFs in one go, and all your converted HTML files in
another - they don't need to be in the same folder. Files are matched into pairs by
filename (report.pdf + report.html = one pair), wherever they came from.</p>

<div class="box">
<form method="POST" action="/run-batch" enctype="multipart/form-data">

  <div class="upload-zone">
    <label>Step 1 — Source PDFs (select as many as you like)</label>
    <input type="file" name="pdf_files" id="pdfInput" multiple accept=".pdf" required
           onchange="document.getElementById('pdfCount').textContent = this.files.length + ' PDF(s) selected'">
    <div class="count" id="pdfCount"></div>
  </div>

  <div class="upload-zone">
    <label>Step 2 — Converted HTML files (select as many as you like)</label>
    <input type="file" name="html_files" id="htmlInput" multiple accept=".html,.htm" required
           onchange="document.getElementById('htmlCount').textContent = this.files.length + ' HTML file(s) selected'">
    <div class="count" id="htmlCount"></div>
  </div>

  <div class="upload-zone">
    <label>Step 3 (optional) — Supporting images, if your HTML references any</label>
    <input type="file" name="image_files" id="imgInput" multiple
           onchange="document.getElementById('imgCount').textContent = this.files.length + ' image file(s) selected'">
    <div class="count" id="imgCount"></div>
    <p class="hint">Only needed if you want image checks to work. Select the image
    files directly (subfolder structure isn't preserved in this mode).</p>
  </div>

  <button type="submit">Upload & Run QA on All Pairs</button>
</form>
</div>

{% if results %}
<div class="box">
<h2>Results</h2>
{% for r in results %}
  <h3>{{ r.pdf_name }} ↔ {{ r.html_name }}</h3>
  <p>{{ r.unique_id }} · {{ r.language }} ·
     <span class="error">{{ r.error_count }} errors</span> ·
     <span class="warning">{{ r.warn_count }} warnings</span> ·
     {% if r.report_file %}<a class="dl" href="/download-direct/{{ r.report_file }}">Download Excel report</a>{% endif %}</p>
  {% if r.issues %}
  <table>
    <tr><th>Type</th><th>Severity</th><th>Line</th><th>Description</th></tr>
    {% for i in r.issues %}
    <tr><td>{{ i.category }}</td><td class="{{ i.severity }}">{{ i.severity|upper }}</td>
        <td>{{ i.line or "—" }}</td><td>{{ i.message }}</td></tr>
    {% endfor %}
  </table>
  {% else %}
  <p class="ok">✓ No issues found.</p>
  {% endif %}
{% endfor %}
</div>
{% endif %}

{% if unmatched %}
<div class="box">
<h2>Unmatched files</h2>
<p>These didn't find a filename match on the other side:</p>
<ul>{% for f in unmatched %}<li>{{ f }}</li>{% endfor %}</ul>
</div>
{% endif %}

</body></html>
"""


@app.route("/run-batch", methods=["POST"])
def run_batch():
    return "Plain form batch upload is disabled. Use the main batch UI.", 410


@app.route("/download-direct/<filename>")
def download_direct(filename):
    return send_file(str(REPORTS / filename), as_attachment=True, download_name=filename)


if __name__ == "__main__":
    port = 7331
    threading.Timer(1.3, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    print(f"\n{'='*52}")
    print(f"  PDF → HTML Batch QA Tool  —  http://localhost:{port}")
    print(f"{'='*52}\n")
    app.run(port=port, debug=False, threaded=True)