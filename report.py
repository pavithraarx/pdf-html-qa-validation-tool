"""
report.py — Generate per-file Excel QA reports.
Supports user-facing severity values: Critical / Major / Minor.
"""

import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

C_HEADER_BG  = "1E2240"
C_HEADER_FG  = "FFFFFF"
C_ALT_ROW    = "F8F9FF"
C_BORDER     = "D0D5EE"
C_META_BG    = "EEF1FF"
C_META_LABEL = "5B6BA0"
C_TITLE_BG   = "1E2240"

SEV_COLORS = {
    "Critical": ("E53935", "FFF0F0"),
    "Major":    ("B45309", "FFFBF0"),
    "Minor":    ("2563EB", "F0F7FF"),
    "Passed":   ("15803D", "EDFFF4"),
    # Backward-compatible engine values
    "error":    ("E53935", "FFF0F0"),
    "warning":  ("B45309", "FFFBF0"),
    "info":     ("2563EB", "F0F7FF"),
}

THIN = Side(border_style="thin", color=C_BORDER)
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

COLUMNS = [
    ("Unique ID",         14),
    ("Source PDF",        30),
    ("HTML File Path",    40),
    ("Language",          12),
    ("Error Type",        28),
    ("Severity",          12),
    ("HTML Line #",       12),
    ("Description",       54),
    ("Expected",          38),
    ("Actual / Shown",    38),
    ("Excerpt / Snippet", 56),
]


def _cell(ws, row, col, value="", bold=False, fg=None, bg=None,
          align="left", wrap=False, size=10, italic=False):
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name="Arial", bold=bold, color=fg or "000000",
                  size=size, italic=italic)
    if bg:
        c.fill = PatternFill("solid", start_color=bg)
    c.alignment = Alignment(horizontal=align, vertical="top", wrap_text=wrap)
    c.border = BORDER
    return c


def _sev(issue):
    return str(getattr(issue, "severity", "") or "").strip() or "Minor"


def generate_report(
    pdf_path: str,
    html_path: str,
    issues: list,
    language: str,
    unique_id: str,
    output_path: str,
):
    wb = Workbook()
    ws = wb.active
    ws.title = "QA Report"
    ws.sheet_view.showGridLines = False

    pdf_name = os.path.basename(pdf_path)
    html_abs = os.path.abspath(html_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(COLUMNS))
    tc = ws.cell(row=1, column=1, value=f"QA Report · {pdf_name} · Generated {now}")
    tc.font = Font(name="Arial", bold=True, color=C_HEADER_FG, size=12)
    tc.fill = PatternFill("solid", start_color=C_TITLE_BG)
    tc.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 30

    total = len(issues)
    critical = sum(1 for i in issues if _sev(i) == "Critical")
    major = sum(1 for i in issues if _sev(i) == "Major")
    minor = sum(1 for i in issues if _sev(i) == "Minor")

    META = [
        ("ID", unique_id),
        ("Source PDF", pdf_name),
        ("Language", language),
        ("Total Issues", str(total)),
        ("Critical", str(critical)),
        ("Major", str(major)),
        ("Minor", str(minor)),
    ]
    col = 1
    ws.row_dimensions[2].height = 22
    for label, val in META:
        if col > len(COLUMNS):
            break
        c = ws.cell(row=2, column=col, value=f"{label}: {val}")
        c.font = Font(name="Arial", size=9, italic=True, color=C_META_LABEL)
        c.fill = PatternFill("solid", start_color=C_META_BG)
        c.alignment = Alignment(horizontal="left", vertical="center")
        c.border = BORDER
        col += 1
    while col <= len(COLUMNS):
        c = ws.cell(row=2, column=col)
        c.fill = PatternFill("solid", start_color=C_META_BG)
        c.border = BORDER
        col += 1

    ws.row_dimensions[3].height = 22
    for ci, (label, _) in enumerate(COLUMNS, 1):
        _cell(ws, 3, ci, label, bold=True, fg=C_HEADER_FG, bg=C_HEADER_BG,
              align="center", size=10)

    for ci, (_, width) in enumerate(COLUMNS, 1):
        ws.column_dimensions[get_column_letter(ci)].width = width

    if not issues:
        row = 4
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(COLUMNS))
        c = ws.cell(row=row, column=1, value="✓ No issues found — content matches source perfectly.")
        c.font = Font(name="Arial", size=10, bold=True, color="1B7F3A")
        c.fill = PatternFill("solid", start_color="EDFFF4")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDER
        ws.row_dimensions[row].height = 28
    else:
        sev_order = {"Critical": 0, "Major": 1, "Minor": 2, "error": 0, "warning": 1, "info": 2}
        sorted_issues = sorted(issues, key=lambda i: (sev_order.get(_sev(i), 3), getattr(i, "line", None) or 99999))

        for r_offset, issue in enumerate(sorted_issues):
            row = 4 + r_offset
            sev = _sev(issue)
            sev_fg, sev_bg = SEV_COLORS.get(sev, ("000000", "FFFFFF"))

            row_data = [
                unique_id,
                pdf_name,
                html_abs,
                language,
                getattr(issue, "category", "") or "",
                sev,
                getattr(issue, "line", None) or "—",
                getattr(issue, "message", "") or "",
                getattr(issue, "expected", "") or "",
                getattr(issue, "actual", "") or "",
                getattr(issue, "snippet", "") or "",
            ]

            for ci, value in enumerate(row_data, 1):
                wrap = ci in (3, 8, 9, 10, 11)
                align = "center" if ci in (1, 4, 6, 7) else "left"
                c = _cell(ws, row, ci, value, bg=sev_bg, align=align, wrap=wrap)
                if ci == 6:
                    c.font = Font(name="Arial", bold=True, color=sev_fg, size=10)
                if ci == 5:
                    side = Side(border_style="medium", color=sev_fg)
                    c.border = Border(left=side, right=THIN, top=THIN, bottom=THIN)

            text_len = max(
                len(str(getattr(issue, "message", "") or "")),
                len(str(getattr(issue, "expected", "") or "")),
                len(str(getattr(issue, "actual", "") or "")),
                len(str(getattr(issue, "snippet", "") or "")),
            )
            ws.row_dimensions[row].height = max(22, min(120, 18 + (text_len // 80) * 14))

    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:{get_column_letter(len(COLUMNS))}3"
    wb.save(output_path)
    return output_path