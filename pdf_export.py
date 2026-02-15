"""
🧠 PDF EXPORT — Baby-level explanation
======================================
Turns our timetable data into a clean, printable PDF.
"""
"""
pdf_export.py — Minimal PDF export for Timable
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

def export_timetable_pdf(timetable, config, filename="timetable.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    data = [["Class", "Day", "Period", "Subject", "Teacher"]]
    for (class_id, day, period), (subject, teacher_id) in timetable.items():
        data.append([class_id, config.days[day], str(period+1), subject, teacher_id])
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 12),
        ("BACKGROUND", (0,1), (-1,-1), colors.beige),
    ]))
    doc.build([table])

from io import BytesIO
from typing import Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

from models import SchoolConfig, get_break_name


def _light_theme_table_style(num_rows: int, num_cols: int) -> TableStyle:
    """Light theme: white/gray grid, black text."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ])


def export_class_timetables_pdf(
    class_timetables: Dict[str, Dict[Tuple[int, int], Tuple[str, str]]],
    config: SchoolConfig,
) -> bytes:
    """
    Creates a PDF with one table per class.
    class_timetables: class_id -> (day_idx, period_idx) -> (subject, teacher_id)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    for class_id in sorted(class_timetables.keys()):
        tt = class_timetables[class_id]
        # Rows = days, Cols = [Day, Period 1, Period 2, ...]
        period_cols = [f"P{p+1}" + (f" ({get_break_name(config, p)})" if p in config.break_period_indices else "") for p in range(config.periods_per_day)]
        header = ["Day"] + period_cols
        rows = [header]
        for d in range(len(config.days)):
            row = [config.days[d]]
            for p in range(config.periods_per_day):
                if p in config.break_period_indices:
                    row.append(get_break_name(config, p))
                else:
                    cell = tt.get((d, p), ("", ""))
                    subj, _ = cell
                    row.append(subj if subj else "Free period")
            rows.append(row)

        t = Table(rows, colWidths=[2*cm] + [2.2*cm] * config.periods_per_day)
        t.setStyle(_light_theme_table_style(len(rows), len(header)))
        story.append(Paragraph(f"<b>Class: {class_id}</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.3*cm))
        story.append(t)
        story.append(Spacer(1, 0.8*cm))

    doc.build(story)
    return buffer.getvalue()


def export_teacher_timetables_pdf(
    teacher_timetables: Dict[str, Dict[Tuple[int, int], Tuple[str, str]]],
    config: SchoolConfig,
) -> bytes:
    """
    Creates a PDF with one table per teacher.
    teacher_timetables: teacher_id -> (day_idx, period_idx) -> (class_id, subject)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    for teacher_id in sorted(teacher_timetables.keys()):
        tt = teacher_timetables[teacher_id]
        period_cols = [f"P{p+1}" + (f" ({get_break_name(config, p)})" if p in config.break_period_indices else "") for p in range(config.periods_per_day)]
        header = ["Day"] + period_cols
        rows = [header]
        for d in range(len(config.days)):
            row = [config.days[d]]
            for p in range(config.periods_per_day):
                if p in config.break_period_indices:
                    row.append(get_break_name(config, p))
                else:
                    cell = tt.get((d, p), ("", ""))
                    cid, subj = cell
                    val = f"{cid}: {subj}" if cid else "Free period"
                    row.append(val)
            rows.append(row)

        t = Table(rows, colWidths=[2*cm] + [2.2*cm] * config.periods_per_day)
        t.setStyle(_light_theme_table_style(len(rows), len(header)))
        story.append(Paragraph(f"<b>Teacher: {teacher_id}</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.3*cm))
        story.append(t)
        story.append(Spacer(1, 0.8*cm))

    doc.build(story)
    return buffer.getvalue()


def class_timetable_to_grid(
    class_timetable: Dict[Tuple[str, int, int], Tuple[str, str]],
    class_id: str,
    config: SchoolConfig,
) -> Dict[Tuple[int, int], Tuple[str, str]]:
    """Extract one class's timetable as (day_idx, period_idx) -> (subject, teacher)."""
    result = {}
    for (cid, d, p), (subj, tid) in class_timetable.items():
        if cid == class_id:
            result[(d, p)] = (subj, tid)
    return result


def flat_to_class_timetables(
    flat: Dict[Tuple[str, int, int], Tuple[str, str]],
) -> Dict[str, Dict[Tuple[int, int], Tuple[str, str]]]:
    """Convert (class_id, day, period) -> (subject, teacher) to class_id -> (day, period) -> (subject, teacher)."""
    result: Dict[str, Dict[Tuple[int, int], Tuple[str, str]]] = {}
    for (cid, d, p), (subj, tid) in flat.items():
        if cid not in result:
            result[cid] = {}
        result[cid][(d, p)] = (subj, tid)
    return result
