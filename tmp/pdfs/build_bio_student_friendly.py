from __future__ import annotations

from pathlib import Path

import fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from teachersaid.library.bio_immunsystem import build_content
from teachersaid.schema.blocks import InfoBlock, TaskBlock
from teachersaid.schema.enums import Role
from teachersaid.schema.richtext import plain_text


OUT = Path("output/pdf/student_friendly_bio")
RASTER = OUT / "raster"
OUT.mkdir(parents=True, exist_ok=True)
RASTER.mkdir(parents=True, exist_ok=True)


def register_font():
    font_dir = Path("C:/Windows/Fonts")
    regular = font_dir / "calibri.ttf"
    bold = font_dir / "calibrib.ttf"
    italic = font_dir / "calibrii.ttf"
    if regular.exists():
        pdfmetrics.registerFont(TTFont("TAFont", str(regular)))
        pdfmetrics.registerFont(TTFont("TAFont-Bold", str(bold if bold.exists() else regular)))
        pdfmetrics.registerFont(TTFont("TAFont-Italic", str(italic if italic.exists() else regular)))
        pdfmetrics.registerFontFamily(
            "TAFont",
            normal="TAFont",
            bold="TAFont-Bold",
            italic="TAFont-Italic",
            boldItalic="TAFont-Bold",
        )
        return "TAFont", "TAFont-Bold", "TAFont-Italic"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


BASE, BOLD, ITALIC = register_font()

INK = colors.HexColor("#22343a")
MUTED = colors.HexColor("#607177")
LINE = colors.HexColor("#cad8d3")
MINT = colors.HexColor("#e9f7f0")
MINT_DARK = colors.HexColor("#197a62")
BLUE = colors.HexColor("#2d6e9f")
BLUE_SOFT = colors.HexColor("#edf5fb")
YELLOW = colors.HexColor("#f4c95d")
YELLOW_SOFT = colors.HexColor("#fff6d9")
RED = colors.HexColor("#bd5b57")
RED_SOFT = colors.HexColor("#fff0ee")
PURPLE = colors.HexColor("#715c9e")
PURPLE_SOFT = colors.HexColor("#f4f0fb")
GREEN = colors.HexColor("#3b8a55")
PAPER = colors.HexColor("#fffdf8")
WHITE = colors.white
PAGE_WIDTH = 172 * mm
CARD_INNER = 158 * mm


sample = getSampleStyleSheet()


def style(name, size=10.4, leading=13.2, color=INK, font=BASE, space_after=3, align=TA_LEFT):
    return ParagraphStyle(
        name,
        parent=sample["Normal"],
        fontName=font,
        fontSize=size,
        leading=leading,
        textColor=color,
        spaceAfter=space_after,
        alignment=align,
    )


S = {
    "title": style("title", 25, 28, INK, BOLD, 2),
    "subtitle": style("subtitle", 11.6, 14, MUTED, BASE, 7),
    "h1": style("h1", 16.5, 19, MINT_DARK, BOLD, 7),
    "h2": style("h2", 12.8, 15.5, INK, BOLD, 3),
    "body": style("body", 10.4, 13.6, INK, BASE, 4),
    "small": style("small", 8.8, 10.6, MUTED, BASE, 1),
    "chip": style("chip", 8.8, 10.5, WHITE, BOLD, 0, TA_CENTER),
    "num": style("num", 11.5, 13, WHITE, BOLD, 0, TA_CENTER),
    "question": style("question", 11, 14.2, INK, BOLD, 3),
    "task": style("task", 10.4, 13.5, INK, BASE, 4),
    "hint": style("hint", 9.4, 12, colors.HexColor("#5f4b00"), BASE, 2),
    "footer": style("footer", 8.5, 10, MUTED, BASE, 0),
}


def p(text, sty="body"):
    return Paragraph(text, S[sty])


def text_of(value) -> str:
    return plain_text(value) if value is not None else ""


class Icon(Flowable):
    def __init__(self, kind: str, color=MINT_DARK, size=12 * mm):
        super().__init__()
        self.kind = kind
        self.color = color
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        c = self.canv
        s = self.size
        c.saveState()
        c.setFillColor(self.color)
        c.setStrokeColor(self.color)
        c.setLineWidth(1.4)
        c.circle(s / 2, s / 2, s / 2, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setStrokeColor(WHITE)
        c.setLineWidth(1.7)
        k = self.kind
        if k == "virus":
            c.circle(s / 2, s / 2, s * 0.18, stroke=1, fill=0)
            for dx, dy in [(0.22, 0.5), (0.78, 0.5), (0.5, 0.22), (0.5, 0.78), (0.31, 0.31), (0.69, 0.69)]:
                c.line(s / 2, s / 2, s * dx, s * dy)
                c.circle(s * dx, s * dy, s * 0.035, stroke=0, fill=1)
        elif k == "shield":
            path = c.beginPath()
            path.moveTo(s * 0.5, s * 0.82)
            path.lineTo(s * 0.76, s * 0.68)
            path.lineTo(s * 0.7, s * 0.35)
            path.curveTo(s * 0.66, s * 0.2, s * 0.54, s * 0.12, s * 0.5, s * 0.1)
            path.curveTo(s * 0.46, s * 0.12, s * 0.34, s * 0.2, s * 0.3, s * 0.35)
            path.lineTo(s * 0.24, s * 0.68)
            path.close()
            c.drawPath(path, stroke=1, fill=0)
            c.line(s * 0.39, s * 0.45, s * 0.48, s * 0.35)
            c.line(s * 0.48, s * 0.35, s * 0.65, s * 0.57)
        elif k == "pill":
            c.roundRect(s * 0.25, s * 0.38, s * 0.5, s * 0.22, s * 0.11, stroke=1, fill=0)
            c.line(s * 0.5, s * 0.38, s * 0.5, s * 0.6)
        elif k == "data":
            c.line(s * 0.28, s * 0.28, s * 0.75, s * 0.28)
            c.line(s * 0.28, s * 0.28, s * 0.28, s * 0.75)
            c.line(s * 0.33, s * 0.36, s * 0.47, s * 0.5)
            c.line(s * 0.47, s * 0.5, s * 0.6, s * 0.42)
            c.line(s * 0.6, s * 0.42, s * 0.73, s * 0.67)
        elif k == "claim":
            c.roundRect(s * 0.27, s * 0.38, s * 0.46, s * 0.27, 2, stroke=1, fill=0)
            c.line(s * 0.38, s * 0.34, s * 0.45, s * 0.38)
            c.line(s * 0.4, s * 0.55, s * 0.62, s * 0.55)
            c.line(s * 0.4, s * 0.48, s * 0.56, s * 0.48)
        elif k == "write":
            c.line(s * 0.3, s * 0.3, s * 0.7, s * 0.7)
            c.line(s * 0.62, s * 0.72, s * 0.72, s * 0.62)
            c.line(s * 0.26, s * 0.26, s * 0.38, s * 0.3)
        else:
            c.circle(s / 2, s / 2, s * 0.22, stroke=1, fill=0)
        c.restoreState()


def rounded_box(flowables, bg=WHITE, stroke=LINE, pad=6, width=PAGE_WIDTH):
    t = Table([[flowables]], colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.8, stroke),
                ("LEFTPADDING", (0, 0), (-1, -1), pad),
                ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                ("TOPPADDING", (0, 0), (-1, -1), pad),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
            ]
        )
    )
    return t


def chip(text, color=MINT_DARK, width=26 * mm):
    t = Table([[p(text, "chip")]], colWidths=[width], rowHeights=[6.2 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0, color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def num(text, color=MINT_DARK):
    t = Table([[p(text, "num")]], colWidths=[8.2 * mm], rowHeights=[8.2 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0, color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def lines(n, width=CARD_INNER, gap=7.0 * mm):
    t = Table([[""] for _ in range(n)], colWidths=[width], rowHeights=[gap] * n)
    t.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.55, colors.HexColor("#9aa8a5")),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def answer_box(height_mm=45, width=CARD_INNER):
    t = Table([[""]], colWidths=[width], rowHeights=[height_mm * mm])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#9aa8a5")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ]
        )
    )
    return t


def response_for(task: TaskBlock):
    if task.payload is not None and task.payload.kind == "true_false_justify":
        return []
    mode = task.response.mode
    if mode == "lines":
        return [lines(task.response.n)]
    if mode == "box":
        return [answer_box(task.response.min_height_mm)]
    if mode == "table":
        rows = [[p(f"<b>{col}</b>") for col in task.response.columns]]
        rows += [["" for _ in task.response.columns] for _ in range(task.response.rows)]
        col_width = CARD_INNER / len(task.response.columns)
        t = Table(rows, colWidths=[col_width] * len(task.response.columns), rowHeights=[9 * mm] + [15 * mm] * task.response.rows)
        t.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.55, LINE),
                    ("BACKGROUND", (0, 0), (-1, 0), MINT),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return [t]
    if mode == "artifact":
        return [
            rounded_box(
                [p(f"<b>Produkt:</b> {task.response.produces}", "hint")],
                bg=YELLOW_SOFT,
                stroke=YELLOW,
                width=CARD_INNER,
            ),
            Spacer(1, 2 * mm),
            answer_box(55),
        ]
    return []


def payload_for(task: TaskBlock):
    payload = task.payload
    if payload is None:
        return []
    if payload.kind == "true_false_justify":
        rows = [[p("<b>Aussage</b>"), p("<b>prüfbar?</b>"), p("<b>Begründung</b>")]]
        for statement in payload.statements:
            rows.append([p(statement), "", ""])
        t = Table(rows, colWidths=[68 * mm, 28 * mm, 62 * mm], rowHeights=[9 * mm] + [16 * mm] * len(payload.statements))
        t.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.55, LINE),
                    ("BACKGROUND", (0, 0), (-1, 0), MINT),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return [t]
    if payload.kind == "decision_scenario":
        return [
            rounded_box([p(text_of(payload.stem), "hint")], bg=YELLOW_SOFT, stroke=YELLOW, width=CARD_INNER),
            Spacer(1, 2 * mm),
        ]
    return []


def info_card(block: InfoBlock, icon_kind: str, color, bg):
    rows = [[Icon(icon_kind, color, 13 * mm), [p(text_of(block.content), "body")]]]
    table = Table(rows, colWidths=[16 * mm, 156 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.75, color),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


LEVEL_META = {
    "understand": ("Verstehen", "virus", MINT_DARK, MINT),
    "apply": ("Anwenden", "data", BLUE, BLUE_SOFT),
    "analyze": ("Untersuchen", "pill", PURPLE, PURPLE_SOFT),
    "evaluate": ("Beurteilen", "claim", RED, RED_SOFT),
    "create": ("Gestalten", "write", GREEN, MINT),
}


def task_card(task: TaskBlock, idx: int):
    label, icon_kind, color, bg = LEVEL_META.get(task.cognitive_level, ("Aufgabe", "shield", MINT_DARK, MINT))
    header = Table(
        [
            [
                num(str(idx), color),
                [
                    p(f"<b>{label}</b> · {task.est_minutes} min · {', '.join(task.dimensions)}", "small"),
                    p(text_of(task.prompt), "question"),
                ],
            ]
        ],
        colWidths=[11 * mm, 161 * mm],
    )
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    body = [header] + payload_for(task) + response_for(task)
    return KeepTogether([rounded_box(body, bg=WHITE, stroke=color, pad=6), Spacer(1, 4 * mm)])


def station(title: str, subtitle: str, icon_kind: str, color, bg):
    left = Icon(icon_kind, color, 15 * mm)
    table = Table([[left, [p(title, "h1"), p(subtitle, "small")]]], colWidths=[18 * mm, 154 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.75, color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [table, Spacer(1, 5 * mm)]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(BASE, 8.3)
    canvas.setFillColor(MUTED)
    canvas.drawString(19 * mm, 11 * mm, "TeachersAid Designstudie · Biologie 4. Klasse · Immunsystem und Impfungen")
    canvas.drawRightString(190 * mm, 11 * mm, f"Seite {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(19 * mm, 16 * mm, 190 * mm, 16 * mm)
    canvas.restoreState()


def cover(content):
    meta = content.meta
    story = []
    hero = Table(
        [
            [
                [p("Biologie · 4. Klasse", "small"), p(meta.title, "title"), p(meta.subtitle, "subtitle")],
                Icon("shield", MINT_DARK, 28 * mm),
            ]
        ],
        colWidths=[138 * mm, 34 * mm],
    )
    hero.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), MINT),
                ("BOX", (0, 0), (-1, -1), 0.9, MINT_DARK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story += [hero, Spacer(1, 5 * mm)]
    story += [
        rounded_box(
            [
                p(f"<b>Kernfrage:</b> {text_of(meta.kernfrage)}", "h2"),
                p("Heute arbeitest du wie ein Gesundheits-Detektiv: unterscheiden, Daten deuten, Aussagen prüfen und eine eigene Position begründen.", "body"),
            ],
            bg=YELLOW_SOFT,
            stroke=YELLOW,
        ),
        Spacer(1, 5 * mm),
    ]
    map_row = Table(
        [[chip("1 Erreger", MINT_DARK, 34 * mm), chip("2 Impfung", BLUE, 34 * mm), chip("3 Belege", PURPLE, 34 * mm), chip("4 Urteil", RED, 34 * mm)]],
        colWidths=[43 * mm] * 4,
    )
    map_row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story += [map_row, Spacer(1, 6 * mm)]
    return story


def build():
    content = build_content()
    tasks = [b for sec in content.sections for b in sec.blocks if b.role == Role.TASK and b.modality == "printable"]
    intro = [b for b in content.intro if b.role == Role.INFO and b.modality == "printable"]
    pdf = OUT / "immunsystem_student_friendly.pdf"
    doc = BaseDocTemplate(
        str(pdf),
        pagesize=A4,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title="Immunsystem und Impfungen - student friendly design",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="student", frames=[frame], onPage=footer)])

    story = cover(content)
    icon_plan = [("virus", MINT_DARK, MINT), ("pill", BLUE, BLUE_SOFT), ("shield", GREEN, MINT)]
    for block, (icon_kind, color, bg) in zip(intro, icon_plan):
        story.append(info_card(block, icon_kind, color, bg))
        story.append(Spacer(1, 3 * mm))

    story += station("Station 1: Virus oder Bakterium?", "Erst sauber unterscheiden, dann entscheiden, was helfen kann.", "virus", MINT_DARK, MINT)
    story.append(task_card(tasks[0], 1))
    story.append(task_card(tasks[1], 2))
    story.append(PageBreak())

    story += station("Station 2: Daten lesen", "Was zeigt ein Verlauf - und was zeigt er nicht?", "data", BLUE, BLUE_SOFT)
    story.append(task_card(tasks[2], 3))
    story.append(PageBreak())
    story += station("Station 3: Aussagen prüfen", "Nicht jede Aussage ist naturwissenschaftlich prüfbar.", "claim", PURPLE, PURPLE_SOFT)
    story.append(task_card(tasks[3], 4))
    story.append(PageBreak())

    story += station("Station 4: Resistenz verstehen", "Variation, Selektion und Vermehrung - Evolution im Kleinen.", "pill", PURPLE, PURPLE_SOFT)
    story.append(task_card(tasks[4], 5))
    story += station("Station 5: Entscheiden und begründen", "Fachwissen wird stark, wenn daraus eine gute Empfehlung wird.", "shield", RED, RED_SOFT)
    story.append(task_card(tasks[5], 6))
    story.append(PageBreak())

    story += station("Station 6: Fair argumentieren", "Zeige beide Seiten und begründe dann deinen eigenen Standpunkt.", "write", GREEN, MINT)
    story.append(task_card(tasks[6], 7))
    story.append(
        rounded_box(
            [
                p("<b>Abschluss-Check:</b>", "h2"),
                p("Ich kann Viren und Bakterien unterscheiden · Ich kann erklären, warum Antibiotika nicht gegen Viren wirken · Ich kann eine Impf-Aussage fair beurteilen.", "body"),
            ],
            bg=YELLOW_SOFT,
            stroke=YELLOW,
        )
    )

    doc.build(story)
    return pdf


def rasterise(pdf: Path):
    for old in RASTER.glob("*.png"):
        old.unlink()
    doc = fitz.open(pdf)
    out = []
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(matrix=fitz.Matrix(140 / 72, 140 / 72), alpha=False)
        path = RASTER / f"{pdf.stem}.p{i}.png"
        pix.save(path)
        out.append(path)
    return out


if __name__ == "__main__":
    pdf_path = build()
    print(pdf_path.resolve())
    for page in rasterise(pdf_path):
        print(page.resolve())
