"""ReportLab base: fonts, styles, shared flowables. The ONLY module that touches
ReportLab primitives directly. No HTML→PDF anywhere (deliberately rejected).

Carlito is used when the .ttf is available (the proven Strahlung approach); we
fall back to Helvetica so the demo renders on any machine.
"""

from __future__ import annotations

import html
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from ..schema.richtext import RichText, to_runs

_CARLITO_DIRS = [
    "/usr/share/fonts/truetype/crosextra",
    "/usr/share/fonts/truetype/carlito",
    "/usr/share/fonts",
]


def _register_fonts() -> str:
    """Register Carlito if present; return the base font family name to use."""
    candidates = {
        "Carlito": "Carlito-Regular.ttf",
        "Carlito-Bold": "Carlito-Bold.ttf",
        "Carlito-Italic": "Carlito-Italic.ttf",
        "Carlito-BoldItalic": "Carlito-BoldItalic.ttf",
    }
    found: dict[str, str] = {}
    for d in _CARLITO_DIRS:
        base = Path(d)
        if not base.exists():
            continue
        for name, fn in candidates.items():
            if name in found:
                continue
            for p in base.rglob(fn):
                found[name] = str(p)
                break
    if "Carlito" in found:
        try:
            pdfmetrics.registerFont(TTFont("Carlito", found["Carlito"]))
            pdfmetrics.registerFont(
                TTFont("Carlito-Bold", found.get("Carlito-Bold", found["Carlito"]))
            )
            pdfmetrics.registerFont(
                TTFont("Carlito-Italic", found.get("Carlito-Italic", found["Carlito"]))
            )
            pdfmetrics.registerFont(
                TTFont(
                    "Carlito-BoldItalic",
                    found.get("Carlito-BoldItalic", found["Carlito"]),
                )
            )
            pdfmetrics.registerFontFamily(
                "Carlito",
                normal="Carlito",
                bold="Carlito-Bold",
                italic="Carlito-Italic",
                boldItalic="Carlito-BoldItalic",
            )
            return "Carlito"
        except Exception:
            pass
    return "Helvetica"


BASE_FONT = _register_fonts()
PAGE_MARGIN = 18 * mm


def styles() -> dict[str, ParagraphStyle]:
    ss = getSampleStyleSheet()
    bold = f"{BASE_FONT}-Bold" if BASE_FONT == "Carlito" else "Helvetica-Bold"

    def mk(name, **kw):
        return ParagraphStyle(name, parent=ss["Normal"], fontName=BASE_FONT, **kw)

    return {
        "title": ParagraphStyle("ta_title", parent=ss["Title"], fontName=bold,
                                fontSize=18, spaceAfter=2 * mm),
        "subtitle": mk("ta_subtitle", fontSize=11, textColor=colors.HexColor("#444444"),
                       spaceAfter=4 * mm),
        "kernfrage": mk("ta_kernfrage", fontSize=11, textColor=colors.HexColor("#33506e"),
                        spaceAfter=4 * mm, leading=15),
        "heading": ParagraphStyle("ta_heading", parent=ss["Heading2"], fontName=bold,
                                  fontSize=13, spaceBefore=5 * mm, spaceAfter=2 * mm,
                                  textColor=colors.HexColor("#1f3a52")),
        "body": mk("ta_body", fontSize=10.5, leading=15, alignment=TA_LEFT, spaceAfter=2 * mm),
        "prompt": mk("ta_prompt", fontSize=10.5, leading=15, spaceBefore=2 * mm,
                     spaceAfter=1.5 * mm),
        "key_fact": mk("ta_keyfact", fontSize=10.5, leading=15, leftIndent=4 * mm,
                       textColor=colors.HexColor("#1f3a52"), spaceAfter=2 * mm),
        "callout": mk("ta_callout", fontSize=10, leading=14),
        "teacher": mk("ta_teacher", fontSize=9.5, leading=13,
                      textColor=colors.HexColor("#5a3a00")),
        "answer": mk("ta_answer", fontSize=9.5, leading=13,
                     textColor=colors.HexColor("#0a5a2a")),
        "watch": mk("ta_watch", fontSize=9.5, leading=13,
                    textColor=colors.HexColor("#8a1c1c")),
        "meta": mk("ta_meta", fontSize=8.5, leading=11, textColor=colors.HexColor("#777777")),
        "label": ParagraphStyle("ta_label", parent=ss["Normal"], fontName=bold,
                                fontSize=9, textColor=colors.HexColor("#555555"),
                                spaceBefore=1.5 * mm),
    }


_MARK_WRAP = {
    "bold": ("<b>", "</b>"),
    "italic": ("<i>", "</i>"),
    "term": ("<b>", "</b>"),
    "code": ('<font face="Courier">', "</font>"),
}


def richtext_markup(value: RichText) -> str:
    """RichText → ReportLab inline markup (escaped), marks → <b>/<i>/font, math → inline image."""
    from . import inline_math

    parts: list[str] = []
    for run in to_runs(value):
        if run.ref_block:
            parts.append(f"<i>(siehe {html.escape(run.ref_block)})</i>")
            continue
        if run.math:
            m = inline_math.render(run.text)
            if m:
                path, w, h = m
                parts.append(f'<img src="{html.escape(path)}" width="{w:.1f}" '
                             f'height="{h:.1f}" valign="-2"/>')
            else:                                    # not configured → readable fallback
                parts.append(f"<i>{html.escape(run.text)}</i>")
            continue
        txt = html.escape(run.text)
        if run.mark and run.mark in _MARK_WRAP:
            o, c = _MARK_WRAP[run.mark]
            txt = f"{o}{txt}{c}"
        parts.append(txt)
    return "".join(parts)


def para(value: RichText, style: ParagraphStyle) -> Paragraph:
    """Treat `value` as RichText (escaped, marks → tags)."""
    return Paragraph(richtext_markup(value), style)


def raw_para(markup: str, style: ParagraphStyle) -> Paragraph:
    """For already-built inline markup — does NOT re-escape. Combine literal tags
    with richtext_markup(...) of any dynamic RichText part."""
    return Paragraph(markup, style)


def ruled_lines(n: int, width: float, gap_mm: float = 8.0) -> Table:
    """n answer lines as a borderless table with bottom rules."""
    rows = [[""] for _ in range(n)]
    t = Table(rows, colWidths=[width], rowHeights=[gap_mm * mm] * n)
    t.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def answer_box(min_height_mm: float, width: float) -> Table:
    t = Table([[""]], colWidths=[width], rowHeights=[min_height_mm * mm])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#999999"))]))
    return t


def grid_table(data: list[list[str]], width: float, header: bool = True) -> Table:
    ncols = max(len(r) for r in data)
    col_w = width / ncols
    t = Table(data, colWidths=[col_w] * ncols)
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("FONTNAME", (0, 0), (-1, -1), BASE_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        bold = f"{BASE_FONT}-Bold" if BASE_FONT == "Carlito" else "Helvetica-Bold"
        cmds += [
            ("FONTNAME", (0, 0), (-1, 0), bold),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
        ]
    t.setStyle(TableStyle(cmds))
    return t


def wrapped_table(data: list[list], col_widths: list[float], *, header: bool = True) -> Table:
    """A table whose cells WRAP (Paragraph cells) — for longer text than grid_table.
    A cell may be a plain string (escaped here) or a pre-built Paragraph (e.g. raw_para
    when you need inline markup)."""
    bold = f"{BASE_FONT}-Bold" if BASE_FONT == "Carlito" else "Helvetica-Bold"
    cell = ParagraphStyle("ta_cell", fontName=BASE_FONT, fontSize=9, leading=12)
    head = ParagraphStyle("ta_cellh", fontName=bold, fontSize=9, leading=12)
    body = []
    for i, row in enumerate(data):
        st = head if (header and i == 0) else cell
        body.append([c if isinstance(c, Paragraph) else Paragraph(html.escape(str(c)), st)
                     for c in row])
    t = Table(body, colWidths=col_widths)
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")))
    t.setStyle(TableStyle(cmds))
    return t


def spacer(h_mm: float = 2.0) -> Spacer:
    return Spacer(1, h_mm * mm)
