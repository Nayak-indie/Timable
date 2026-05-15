"""
🧠 PDF EXPORT — Baby-level explanation
======================================
Turns our timetable data into a clean, printable PDF.
"""
"""
pdf_export.py — Minimal PDF export for Timable
"""
from io import BytesIO
from typing import Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics

from layout_rules import (
    is_break_period,
    get_break_label,
)
from layout_rules import get_break_name
from models import SchoolConfig


def _light_theme_table_style(num_rows: int, num_cols: int) -> TableStyle:
    """Light theme: white/gray grid, black text."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ])


def _compact_table_style() -> TableStyle:
    """Compact, low-padding table style for denser timetables."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e6e6")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfbfb")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 0.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
    ])


def _make_slot_paragraph(subject: str, code: str = "", *, for_teacher: bool = False) -> Paragraph:
    """Return a compact two-line Paragraph for a timetable slot.

    - subject: main line (bold)
    - code: secondary small line (teacher id or class id)
    """
    subj_text = subject or ""
    code_text = code or ""
    slot_html = f"<b>{subj_text}</b>"
    if code_text:
        slot_html += f"<br/><font size=7>{code_text}</font>"
    para_style = ParagraphStyle(
        name="SlotCardCompact",
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=8,
        leading=9,
    )
    return Paragraph(slot_html, para_style)


def _make_free_paragraph_for_height(row_height: float) -> Paragraph:
    """Create a compact 'FREE\nPERIOD' Paragraph that scales to row height (points)."""
    # heuristics to derive font sizes from row height
    subj_font = max(5, min(9, int(row_height * 0.45)))
    code_font = max(4, min(7, int(row_height * 0.32)))
    return _make_slot_paragraph_with_sizes("FREE", "PERIOD", subj_font, code_font)


def _make_slot_paragraph_with_sizes(subject: str, code: str = "", subj_size: float = 8.0, code_size: float = 7.0) -> Paragraph:
    slot_html = f"<b><font size={subj_size}>{subject}</font></b>"
    if code:
        slot_html += f"<br/><font size={code_size}>{code}</font>"
    para_style = ParagraphStyle(
        name="SlotCardCompactSized",
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=subj_size,
        leading=max(subj_size, code_size) + 1,
    )
    return Paragraph(slot_html, para_style)


def _fit_slot_paragraph(subject: str, code: str, col_width: float, row_height: float, max_subj: float = 10.0, max_code: float = 8.0):
    """Return a Paragraph sized to fit within col_width and row_height by reducing fonts.

    - `col_width` and `row_height` are in points.
    - Returns a Paragraph instance.
    """
    # paddings used in _compact_table_style: left/right = 1 each
    horiz_padding = 2.0
    avail_w = max(4.0, col_width - horiz_padding)

    subj_size = max(6.0, min(max_subj, 9.0))
    code_size = max(5.0, min(max_code, 8.0))

    # conservative vertical padding
    vert_padding = 1.0 + 1.0
    avail_h = max(6.0, row_height - vert_padding)

    # try to reduce sizes until both fit width; also ensure combined heights fit
    while subj_size >= 6.0:
        subj_w = pdfmetrics.stringWidth(subject or "", "Helvetica-Bold", subj_size)
        code_w = pdfmetrics.stringWidth(code or "", "Helvetica", code_size)
        combined_h = subj_size + code_size * 0.9 + 1.0
        if subj_w <= avail_w and code_w <= avail_w and combined_h <= avail_h:
            break
        # reduce larger line first
        if subj_w > avail_w and subj_size > 6.0:
            subj_size -= 0.5
            continue
        if code_w > avail_w and code_size > 5.0:
            code_size -= 0.5
            continue
        # otherwise reduce both slowly
        subj_size -= 0.5
        code_size = max(5.0, code_size - 0.25)

    subj_size = max(6.0, subj_size)
    code_size = max(5.0, code_size)

    return _make_slot_paragraph_with_sizes(subject, code, subj_size, code_size)


def _compute_compact_dimensions(num_rows: int, max_cell_chars: int, usable_height: float):
    """Return (subj_size, code_size, row_height, header_size, spacer_before, spacer_after)

    Iteratively reduce font sizes to try to fit the timetable into usable_height.
    """
    # start with reasonably small sizes
    subj_size = 8.0
    code_size = 6.5
    min_subj = 6.0
    min_code = 5.0

    # paddings (cm converted to points later by Spacer usage) but we'll keep small spacers
    spacer_before = 0.15 * cm
    spacer_after = 0.25 * cm

    # estimate header height (points)
    header_size = subj_size + 4

    def estimate_height(s_size, c_size):
        # estimate row height in points: subject line + code line + small gap
        row_h = s_size + c_size * 0.9
        total = header_size + (num_rows - 1) * row_h + (spacer_before + spacer_after)
        return total, row_h

    total, row_h = estimate_height(subj_size, code_size)
    # reduce until fits or hit minimums
    while total > usable_height and (subj_size > min_subj or code_size > min_code):
        if subj_size > min_subj:
            subj_size -= 0.5
        if code_size > min_code:
            code_size -= 0.5
        header_size = subj_size + 4
        total, row_h = estimate_height(subj_size, code_size)

    return subj_size, code_size, row_h, header_size, spacer_before, spacer_after


def export_class_timetables_pdf(
    class_timetables: Dict[str, Dict[Tuple[int, int], Tuple[str, str]]],
    config: SchoolConfig,
) -> bytes:
    """
    Creates a PDF with one table per class.
    class_timetables: class_id -> (day_idx, period_idx) -> (subject, teacher_id)
    """
    buffer = BytesIO()
    # reduced margins for aggressive compactness
    left_right_margin = 1.0 * cm
    top_margin = 0.8 * cm
    bottom_margin = 0.8 * cm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=left_right_margin,
        rightMargin=left_right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )
    styles = getSampleStyleSheet()
    story = []
    page_width, page_height = A4
    usable_height = page_height - doc.topMargin - doc.bottomMargin
    remaining_height = usable_height

    for class_id in sorted(class_timetables.keys()):
        tt = class_timetables[class_id]
        # first pass: build a raw rows structure of strings to measure content
        period_cols = [f"P{p+1}" for p in range(config.periods_per_day)]
        header = ["Day"] + period_cols
        raw_rows = [header]
        max_cell_chars = 0
        for d in range(len(config.days)):
            row = [config.days[d]]
            for p in range(config.periods_per_day):
                if p in config.break_periods:
                    label = get_break_label(p) or ""
                    row.append(("__BREAK__", label))
                    max_cell_chars = max(max_cell_chars, len(label))
                else:
                    cell = tt.get((d, p), ("", ""))
                    subj, tid = cell
                    subj_text = subj if subj else ""
                    tid_text = tid if tid else ""
                    row.append((subj_text, tid_text))
                    max_cell_chars = max(max_cell_chars, len(subj_text) + len(tid_text))
            raw_rows.append(row)

        # adaptive widths: break columns ultra-thin, others compact
        period_widths = []
        for p in range(config.periods_per_day):
            if is_break_period(p):
                period_widths.append(0.35 * cm)
            else:
                base = 1.4 * cm
                extra = min(0.8 * cm, (max_cell_chars / 30.0) * 0.8 * cm)
                period_widths.append(base + extra)

        col_widths = [2 * cm] + period_widths

        # estimate block height and compute compact font/row sizes to try to fit into page
        num_rows = len(raw_rows)
        subj_size, code_size, est_row_height, header_height, spacer_before, spacer_after = _compute_compact_dimensions(num_rows, max_cell_chars, usable_height)

        # build final rows converting raw cells to Paragraphs and merge break runs into spans
        rows = [header]
        spans = []
        # compute per-row heights (allows subtle per-row scaling based on content)
        row_heights = [header_height]
        for r_idx, r in enumerate(raw_rows[1:], start=1):
            # find longest cell in this row to decide if row needs slight expansion
            longest = 0
            for cell in r[1:]:
                if isinstance(cell, tuple) and cell[0] == "__BREAK__":
                    label = cell[1]
                    longest = max(longest, len(label))
                else:
                    subj_text, tid_text = cell
                    longest = max(longest, len(subj_text) + len(tid_text))

            # row-specific height scaling (small, bounded)
            scale = 1.0 + min(0.35, longest / 50.0)
            this_row_h = est_row_height * scale
            row_heights.append(this_row_h)

            row = [r[0]]
            p = 0
            col_index = 1
            while p < config.periods_per_day:
                cell = r[1 + p]
                if isinstance(cell, tuple) and cell[0] == "__BREAK__":
                    # merge consecutive break periods into one spanning cell
                    label = cell[1]
                    end_p = p
                    while end_p + 1 < config.periods_per_day and isinstance(r[1 + end_p + 1], tuple) and r[1 + end_p + 1][0] == "__BREAK__":
                        end_p += 1
                    span_cols = end_p - p + 1
                    vertical_text = "<br/>".join(list(label)) if label else ""
                    if len(label) > 0:
                        break_font = min(max(5, int(code_size)), max(5, int((this_row_h) / max(1, len(label)) * 0.9)))
                    else:
                        break_font = max(5, int(code_size))
                    para_style = ParagraphStyle(
                        name="VerticalBreak",
                        alignment=TA_CENTER,
                        fontName="Helvetica-Bold",
                        fontSize=break_font,
                        leading=break_font,
                    )
                    row.append(Paragraph(vertical_text, para_style))
                    for _ in range(span_cols - 1):
                        row.append("")
                    spans.append((col_index, r_idx, col_index + span_cols - 1, r_idx))
                    col_index += span_cols
                    p = end_p + 1
                else:
                    subj_text, tid_text = cell
                    if not subj_text and not tid_text:
                        row.append(_make_free_paragraph_for_height(this_row_h))
                    else:
                        col_w = col_widths[col_index]
                        row.append(_fit_slot_paragraph(subj_text, tid_text, col_w, this_row_h, subj_size, code_size))
                    col_index += 1
                    p += 1
            rows.append(row)

        # recompute block height now as sum of row heights plus spacers
        block_height = sum(row_heights) + spacer_before + spacer_after

        # if doesn't fit on the current page, start a new page
        if remaining_height < block_height:
            story.append(PageBreak())
            remaining_height = usable_height

        # Title styling (grayscale) and keep title + table together
        title_size = max(9, int(subj_size + 1))
        title_style = ParagraphStyle(
            name="TimetableTitle",
            fontName="Helvetica-Bold",
            fontSize=title_size,
            leading=title_size + 1,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#333333"),
        )

        # Center single timetable on a fresh page if it would otherwise leave excessive whitespace
        if remaining_height == usable_height and block_height > usable_height / 2 and block_height <= usable_height:
            top_space = (usable_height - block_height) / 2.0
            tbl = Table(rows, colWidths=col_widths, repeatRows=1, rowHeights=row_heights)
            tbl.setStyle(_compact_table_style())
            kept = [Spacer(1, top_space), Paragraph(f"Class: {class_id}", title_style), Spacer(1, spacer_before), tbl, Spacer(1, usable_height - top_space - block_height)]
            story.append(KeepTogether(kept))
            story.append(PageBreak())
            remaining_height = usable_height
            continue

        # append the timetable block normally
        tbl = Table(rows, colWidths=col_widths, repeatRows=1, rowHeights=row_heights)
        tbl.setStyle(_compact_table_style())
        kept = [Paragraph(f"Class: {class_id}", title_style), Spacer(1, spacer_before), tbl, Spacer(1, spacer_after)]
        story.append(KeepTogether(kept))
        remaining_height -= block_height

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
    # teacher PDFs: slightly reduced margins but prioritize readability/stability
    left_right_margin = 1.0 * cm
    top_margin = 1.0 * cm
    bottom_margin = 1.0 * cm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=left_right_margin,
        rightMargin=left_right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )
    styles = getSampleStyleSheet()
    story = []
    page_width, page_height = A4
    usable_height = page_height - doc.topMargin - doc.bottomMargin
    remaining_height = usable_height

    for teacher_id in sorted(teacher_timetables.keys()):
        tt = teacher_timetables[teacher_id]
        # two-pass construction: measure then build with sizes
        period_cols = [f"P{p+1}" for p in range(config.periods_per_day)]
        # two-pass measure: build raw rows to estimate max cell width needs
        header = ["Day"] + period_cols
        raw_rows = [header]
        max_cell_chars = 0
        for d in range(len(config.days)):
            row = [config.days[d]]
            for p in range(config.periods_per_day):
                if p in config.break_periods:
                    label = get_break_label(p) or ""
                    row.append(("__BREAK__", label))
                    max_cell_chars = max(max_cell_chars, len(label))
                else:
                    cell = tt.get((d, p), ("", ""))
                    # teacher_timetables map to (class_id, subject)
                    cid_text, subj_text = cell
                    subj_text = subj_text or ""
                    cid_text = cid_text or ""
                    row.append((subj_text, cid_text))
                    max_cell_chars = max(max_cell_chars, len(subj_text) + len(cid_text))
            raw_rows.append(row)

        # simpler teacher table layout: safer wrapping and minor autoscale to avoid overflow
        period_widths = []
        for p in range(config.periods_per_day):
            if is_break_period(p):
                period_widths.append(0.5 * cm)
            else:
                base = 1.8 * cm
                extra = min(0.9 * cm, (max_cell_chars / 30.0) * 0.6 * cm)
                period_widths.append(base + extra)

        col_widths = [2 * cm] + period_widths

        # simple sizing: use small readable fonts and slightly reduce if too wide
        subj_base = 9
        code_base = 8
        min_subj = 6
        min_code = 6

        # build rows with break merging and autosizing
        rows = [header]
        spans = []
        row_height = subj_base + code_base
        for r_idx, r in enumerate(raw_rows[1:], start=1):
            row = [r[0]]
            p = 0
            col_index = 1
            # compute a conservative this_row_h
            this_row_h = max(12, int((subj_base + code_base) * 0.9))
            while p < config.periods_per_day:
                cell = r[1 + p]
                if isinstance(cell, tuple) and cell[0] == "__BREAK__":
                    # merge consecutive breaks
                    label = cell[1]
                    end_p = p
                    while end_p + 1 < config.periods_per_day and isinstance(r[1 + end_p + 1], tuple) and r[1 + end_p + 1][0] == "__BREAK__":
                        end_p += 1
                    span_cols = end_p - p + 1
                    para = Paragraph(label, ParagraphStyle(name="TeacherBreak", fontName="Helvetica-Bold", fontSize=7, leading=7, alignment=TA_CENTER))
                    row.append(para)
                    for _ in range(span_cols - 1):
                        row.append("")
                    spans.append((col_index, r_idx, col_index + span_cols - 1, r_idx))
                    col_index += span_cols
                    p = end_p + 1
                else:
                    subj_text, cid_text = cell
                    if not subj_text and not cid_text:
                        row.append(_make_free_paragraph_for_height(this_row_h))
                    else:
                        col_w = col_widths[col_index]
                        row.append(_fit_slot_paragraph(subj_text, cid_text, col_w, this_row_h, subj_base, code_base))
                    col_index += 1
                    p += 1
            rows.append(row)

        # estimate block height conservatively
        num_rows = len(rows)
        header_height = subj_base + 4
        est_row_height = max(10, int((subj_base + code_base) * 1.0))
        spacer_before = 0.25 * cm
        spacer_after = 0.4 * cm
        block_height = header_height + (num_rows - 1) * est_row_height + spacer_before + spacer_after
        row_heights = [header_height] + [est_row_height] * (num_rows - 1)

        if remaining_height < block_height:
            story.append(PageBreak())
            remaining_height = usable_height

        # simpler title style
        title_style = ParagraphStyle(name="TeacherTitle", fontName="Helvetica-Bold", fontSize=10, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#222222"))
        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(_compact_table_style())
        # apply spans
        if spans:
            for sc, sr, ec, er in spans:
                tbl.setStyle(TableStyle([("SPAN", (sc, sr), (ec, er))]))
        kept = [Paragraph(f"Teacher: {teacher_id}", title_style), Spacer(1, spacer_before), tbl, Spacer(1, spacer_after)]
        story.append(KeepTogether(kept))
        remaining_height -= block_height

        title_size = max(9, int(subj_base + 1))
        title_style = ParagraphStyle(
            name="TimetableTitle",
            fontName="Helvetica-Bold",
            fontSize=title_size,
            leading=title_size + 1,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#333333"),
        )

        if remaining_height == usable_height and block_height > usable_height / 2 and block_height <= usable_height:
            top_space = (usable_height - block_height) / 2.0
            tbl = Table(rows, colWidths=col_widths, repeatRows=1, rowHeights=row_heights)
            tbl.setStyle(_compact_table_style())
            if spans:
                for sc, sr, ec, er in spans:
                    tbl.setStyle(TableStyle([("SPAN", (sc, sr), (ec, er))]))
            kept = [Spacer(1, top_space), Paragraph(f"Teacher: {teacher_id}", title_style), Spacer(1, spacer_before), tbl, Spacer(1, usable_height - top_space - block_height)]
            story.append(KeepTogether(kept))
            story.append(PageBreak())
            remaining_height = usable_height
            continue

        tbl = Table(rows, colWidths=col_widths, repeatRows=1, rowHeights=row_heights)
        tbl.setStyle(_compact_table_style())
        if spans:
            for sc, sr, ec, er in spans:
                tbl.setStyle(TableStyle([("SPAN", (sc, sr), (ec, er))]))
        kept = [Paragraph(f"Teacher: {teacher_id}", title_style), Spacer(1, spacer_before), tbl, Spacer(1, spacer_after)]
        story.append(KeepTogether(kept))
        remaining_height -= block_height

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
