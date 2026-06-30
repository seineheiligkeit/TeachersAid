"""ReportLab base: fonts, styles, shared flowables. The ONLY module that touches
ReportLab primitives directly. No HTML→PDF anywhere (deliberately rejected).

Carlito is used when the .ttf is available (the proven Strahlung approach); we
fall back to Helvetica so the demo renders on any machine.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from ..schema.richtext import RichText, to_runs

_FONT_DIRS = [
    "/usr/share/fonts/truetype/crosextra",
    "/usr/share/fonts/truetype/carlito",
    "/usr/share/fonts",
    # Windows (the user's machine): Carlito ships with LibreOffice; Calibri (its
    # metric twin) ships with Office. Either gives proper Unicode coverage —
    # including subscripts — that the Helvetica fallback lacks.
    str(Path.home() / "AppData/Local/Microsoft/Windows/Fonts"),
    "C:/Windows/Fonts",
]

# Each family: (registered-name → on-disk filenames to try, in order). The first
# family whose regular weight is found wins. Carlito is preferred; Calibri is the
# metric-compatible Windows fallback.
_FONT_FAMILIES = [
    ("Carlito", {
        "Carlito": ["Carlito-Regular.ttf", "Carlito.ttf"],
        "Carlito-Bold": ["Carlito-Bold.ttf"],
        "Carlito-Italic": ["Carlito-Italic.ttf"],
        "Carlito-BoldItalic": ["Carlito-BoldItalic.ttf"],
    }),
    ("Calibri", {
        "Calibri": ["calibri.ttf"],
        "Calibri-Bold": ["calibrib.ttf"],
        "Calibri-Italic": ["calibrii.ttf"],
        "Calibri-BoldItalic": ["calibriz.ttf"],
    }),
]


def _find_font(filenames: list[str]) -> str | None:
    for d in _FONT_DIRS:
        base = Path(d)
        if not base.exists():
            continue
        for fn in filenames:
            hit = base / fn
            if hit.exists():
                return str(hit)
            for p in base.rglob(fn):
                return str(p)
    return None


def _register_fonts() -> str:
    """Register the first available real font family; return its base name.

    Falls back to Helvetica so the demo renders on any machine. Helvetica lacks
    subscript glyphs, but `richtext_markup` normalises those to <sub>/<super>
    markup, so chemistry/units (CO₂, m²) stay correct regardless of the font."""
    for family, members in _FONT_FAMILIES:
        regular = _find_font(members[family])
        if not regular:
            continue
        try:
            pdfmetrics.registerFont(TTFont(family, regular))
            for member, names in members.items():
                if member == family:
                    continue
                pdfmetrics.registerFont(TTFont(member, _find_font(names) or regular))
            pdfmetrics.registerFontFamily(
                family,
                normal=family,
                bold=f"{family}-Bold",
                italic=f"{family}-Italic",
                boldItalic=f"{family}-BoldItalic",
            )
            return family
        except Exception:
            continue
    return "Helvetica"


BASE_FONT = _register_fonts()
PAGE_MARGIN = 18 * mm


def styles() -> dict[str, ParagraphStyle]:
    ss = getSampleStyleSheet()
    bold = "Helvetica-Bold" if BASE_FONT == "Helvetica" else f"{BASE_FONT}-Bold"

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

# Unicode sub/superscripts (CO₂, H₂O, m², x³ …) are tofu in fonts without those
# glyphs (e.g. the Helvetica fallback). Map them to ReportLab <sub>/<super> markup
# over the *plain* digit/operator, so they render correctly in ANY font.
_SUB_TRANS = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎", "0123456789+-=()")
_SUP_TRANS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ", "0123456789+-=()n")
_SUB_RE = re.compile("[₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎]+")
_SUP_RE = re.compile("[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ]+")


def _normalize_scripts(escaped: str) -> str:
    """Replace runs of sub/superscript Unicode with <sub>/<super> markup. Runs on
    already-html-escaped text (these chars survive escaping; the tags are literal)."""
    escaped = _SUB_RE.sub(lambda m: f"<sub>{m.group().translate(_SUB_TRANS)}</sub>", escaped)
    escaped = _SUP_RE.sub(lambda m: f"<super>{m.group().translate(_SUP_TRANS)}</super>", escaped)
    return escaped


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
        txt = _normalize_scripts(html.escape(run.text))
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


def numbered_text(text: str, body_style: ParagraphStyle, width: float) -> Table:
    """An authentic text with line numbers (Deutsch source text): a borderless two-column
    table [Zeile-Nr | Zeile] with a light rule, so tasks can reference "Zeile N"."""
    num_style = ParagraphStyle("zeilennr", fontName=BASE_FONT, fontSize=8,
                               textColor=colors.HexColor("#999999"), alignment=2)
    rows = []
    i = 0
    for line in text.split("\n"):
        if line.strip():                       # number only non-blank lines (verse lines)
            i += 1
            rows.append([para(str(i), num_style), para(line, body_style)])
        else:                                  # blank line = stanza/paragraph gap, no number
            rows.append([para(" ", num_style), para(" ", body_style)])
    numw = 12 * mm
    t = Table(rows, colWidths=[numw, width - numw])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 5),
        ("LEFTPADDING", (1, 0), (1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LINEBEFORE", (1, 0), (1, -1), 0.5, colors.HexColor("#cccccc")),
    ]))
    return t


def grid_table(data: list[list], width: float, header: bool = True,
               weights: list[float] | None = None) -> Table:
    """A content table whose cells WRAP (every cell is a Paragraph, so text can never overflow a
    cell horizontally — it grows vertically and the row gets taller instead). `weights` sets
    relative column widths (default = equal); the widths always sum to `width`, so the table can
    never exceed the frame. A cell may be a plain string (escaped + wrapped here) or a pre-built
    Paragraph (e.g. `raw_para`, when you need inline markup)."""
    ncols = max(len(r) for r in data)
    if weights and len(weights) == ncols and sum(weights) > 0:
        col_w = [width * w / sum(weights) for w in weights]
    else:
        col_w = [width / ncols] * ncols
    bold = f"{BASE_FONT}-Bold" if BASE_FONT == "Carlito" else "Helvetica-Bold"
    cell = ParagraphStyle("gt_cell", fontName=BASE_FONT, fontSize=9, leading=12)
    head = ParagraphStyle("gt_head", fontName=bold, fontSize=9, leading=12)
    body = []
    for i, row in enumerate(data):
        st = head if (header and i == 0) else cell
        cells = list(row) + [""] * (ncols - len(row))          # pad short rows to ncols
        body.append([c if isinstance(c, Paragraph) else Paragraph(html.escape(str(c)), st)
                     for c in cells])
    t = Table(body, colWidths=col_w)
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")))
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


def connect_blocks(left: list[str], right: list[str], width: float) -> Table:
    """Two columns of loose, BOXED blocks with an open gap between — the student draws connecting
    lines (matching tasks: *connect*, don't write pairs). Each item is its own bordered block; the
    right column is shuffled, so matches run diagonally across the gap. Cells wrap (Paragraphs)."""
    cell = ParagraphStyle("cb_cell", fontName=BASE_FONT, fontSize=9, leading=12)
    m = max(len(left), len(right), 1)
    left = list(left) + [""] * (m - len(left))
    right = list(right) + [""] * (m - len(right))
    lw, gw = width * 0.42, width * 0.16
    rw = width - lw - gw
    rows = [[Paragraph(html.escape(str(lft)), cell), "", Paragraph(html.escape(str(rgt)), cell)]
            for lft, rgt in zip(left, right)]
    t = Table(rows, colWidths=[lw, gw, rw])
    grey, light, bg = colors.HexColor("#888888"), colors.HexColor("#cccccc"), colors.HexColor("#f6f8fb")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (0, -1), 0.7, grey), ("INNERGRID", (0, 0), (0, -1), 0.7, light),
        ("BOX", (2, 0), (2, -1), 0.7, grey), ("INNERGRID", (2, 0), (2, -1), 0.7, light),
        ("BACKGROUND", (0, 0), (0, -1), bg), ("BACKGROUND", (2, 0), (2, -1), bg),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def spacer(h_mm: float = 2.0) -> Spacer:
    return Spacer(1, h_mm * mm)
