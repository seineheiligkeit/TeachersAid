from pathlib import Path

from PIL import Image as PILImage
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUT = Path("output/pdf/codex_strahlung_final")
ASSETS = OUT / "assets"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

ACCENT = Path("output/imagegen/strahlung-header-accent.png")


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

INK = colors.HexColor("#20343b")
TEAL = colors.HexColor("#1f8a8a")
TEAL_DARK = colors.HexColor("#156a6c")
YELLOW = colors.HexColor("#f3c553")
BLUE = colors.HexColor("#2d5b7c")
RED = colors.HexColor("#b14b48")
GREEN = colors.HexColor("#3c7d57")
MIST = colors.HexColor("#eef5f3")
WARM = colors.HexColor("#fff7df")
LINE = colors.HexColor("#c8d0cf")
LIGHT = colors.HexColor("#f7f9f8")


def make_header_crop():
    if not ACCENT.exists():
        return None
    img = PILImage.open(ACCENT).convert("RGB")
    w, h = img.size
    crop = img.crop((0, int(h * 0.08), w, int(h * 0.55)))
    crop = crop.resize((2200, 410))
    path = ASSETS / "header_accent_crop.jpg"
    crop.save(path, quality=92)
    return path


def make_spectrum(path: Path):
    labels = ["Radio", "Mikro", "IR", "sichtbar", "UV", "Röntgen", "Gamma"]
    palette = ["#d9ecec", "#d9ecec", "#d9ecec", "#f5e28a", "#f6c06f", "#e98882", "#d46666"]
    fig, ax = plt.subplots(figsize=(9.5, 2.25))
    ax.set_facecolor("white")
    for i, (label, col) in enumerate(zip(labels, palette)):
        ax.barh([0], [1], left=i, height=0.46, color=col, edgecolor="#31474d", linewidth=1.1)
        ax.text(i + 0.5, 0, label, ha="center", va="center", fontsize=10, color="#20343b", weight="bold")
    ax.axvline(5, ymin=0.05, ymax=0.95, color="#b14b48", linewidth=2.2, linestyle="--")
    ax.text(4.96, 0.46, "Ionisierungsschwelle", ha="right", va="bottom", fontsize=9, color="#b14b48")
    ax.annotate("", xy=(7.02, -0.48), xytext=(-0.02, -0.48), arrowprops=dict(arrowstyle="->", lw=1.6, color="#20343b"))
    ax.text(3.5, -0.64, "Energie nimmt zu", ha="center", va="top", fontsize=10, color="#20343b")
    ax.text(2.5, 0.38, "nicht-ionisierend", ha="center", fontsize=9, color="#3c7d57")
    ax.text(6, 0.38, "ionisierend", ha="center", fontsize=9, color="#b14b48")
    ax.set_xlim(-0.05, 7.05)
    ax.set_ylim(-0.78, 0.62)
    ax.axis("off")
    fig.tight_layout(pad=0.25)
    fig.savefig(path, dpi=220, transparent=False)
    plt.close(fig)


def make_dose(path: Path):
    fig, ax = plt.subplots(figsize=(9.5, 2.45))
    ax.set_facecolor("white")
    # Log-style placement: the exact values matter less than the orders of magnitude.
    items = [
        ("Banane", "0,1 µSv", 0.45, -0.43, "#f3c553"),
        ("Thorax-\nRöntgen", "20 µSv", 3.15, 0.38, "#84b6bd"),
        ("Flug", "40 µSv", 3.78, -0.43, "#4f91a5"),
        ("Jahr in AT", "2-3 mSv", 6.4, 0.38, "#2d5b7c"),
    ]
    ax.annotate("", xy=(7.05, 0), xytext=(0.1, 0), arrowprops=dict(arrowstyle="->", lw=1.8, color="#20343b"))
    ax.text(3.6, 0.72, "Dosis: Größenordnungen vergleichen, nicht Bauchgefühl", ha="center", fontsize=10.5, color="#20343b")
    for name, label, x, y, col in items:
        ax.plot([x, x], [0, y * 0.72], color="#9aa6a6", lw=1)
        ax.scatter([x], [0], s=70, color=col, edgecolor="#20343b", zorder=3)
        ax.text(x, y, name, ha="center", va="center", fontsize=9.5, color="#20343b", weight="bold")
        ax.text(x, y - (0.25 if y < 0 else -0.25), label, ha="center", va="center", fontsize=9, color="#516166")
    ax.text(0.1, -0.82, "µSv", ha="left", fontsize=8, color="#667")
    ax.text(6.25, -0.82, "mSv", ha="left", fontsize=8, color="#667")
    ax.set_xlim(-0.05, 7.1)
    ax.set_ylim(-0.9, 0.78)
    ax.axis("off")
    fig.tight_layout(pad=0.25)
    fig.savefig(path, dpi=220)
    plt.close(fig)


HEADER = make_header_crop()
SPECTRUM = ASSETS / "spectrum_final.png"
DOSE = ASSETS / "dose_ladder.png"
make_spectrum(SPECTRUM)
make_dose(DOSE)

sample = getSampleStyleSheet()


def style(name, size=10.5, leading=13.5, color=INK, font=BASE, space_after=4, align=TA_LEFT):
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


STYLES = {
    "title": style("title", 27, 30, INK, BOLD, 3),
    "subtitle": style("subtitle", 12, 15, colors.HexColor("#516166"), BASE, 7),
    "h1": style("h1", 17, 20, TEAL_DARK, BOLD, 7),
    "body": style("body", 10.6, 14.2, INK, BASE, 4),
    "small": style("small", 8.8, 11.2, colors.HexColor("#617074"), BASE, 2),
    "label": style("label", 8.7, 10.5, colors.white, BOLD, 0, TA_CENTER),
    "num": style("num", 10.5, 12, colors.white, BOLD, 0, TA_CENTER),
    "task": style("task", 10.7, 14.3, INK, BASE, 5),
    "question": style("question", 11.2, 14.8, INK, BOLD, 5),
    "tip": style("tip", 9.6, 12.4, colors.HexColor("#5e4a00"), BASE, 2),
    "cardhead": style("cardhead", 11.5, 14, TEAL_DARK, BOLD, 3),
}


def p(text, sty="body"):
    return Paragraph(text, STYLES[sty])


def badge(text, bg=TEAL_DARK, width=28 * mm):
    table = Table([[p(text, "label")]], colWidths=[width], rowHeights=[6.4 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0, bg),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def num_badge(text, bg=TEAL_DARK):
    table = Table([[p(text, "num")]], colWidths=[7.5 * mm], rowHeights=[7.5 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0, bg),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def card(flowables, bg=LIGHT, stroke=LINE, pad=7, width=172 * mm):
    table = Table([[flowables]], colWidths=[width])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.65, stroke),
                ("LEFTPADDING", (0, 0), (-1, -1), pad),
                ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                ("TOPPADDING", (0, 0), (-1, -1), pad),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
            ]
        )
    )
    return table


def lines(n, width=172 * mm, gap=7.2 * mm):
    table = Table([[""] for _ in range(n)], colWidths=[width], rowHeights=[gap] * n)
    table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.55, colors.HexColor("#9aa6a6")),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def answer_box(height=38 * mm, width=172 * mm):
    table = Table([[""]], colWidths=[width], rowHeights=[height])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#9aa6a6")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ]
        )
    )
    return table


def task(num, title, prompt, response_flowables, minutes, level, dim, accent=TEAL_DARK):
    head = Table(
        [[num_badge(str(num), accent), p(f"<b>{title}</b> <font color=\"#617074\">({minutes} min · {level} · {dim})</font>", "question")]],
        colWidths=[10 * mm, 162 * mm],
    )
    head.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return KeepTogether([head, p(prompt, "task")] + response_flowables + [Spacer(1, 5 * mm)])


def true_false_table():
    rows = [[p("<b>Aussage</b>"), p("<b>richtig/falsch</b>"), p("<b>Begründung/Korrektur</b>")]]
    for statement in [
        "UV-Strahlung ist ungefährlich, weil sie nicht ionisierend ist.",
        "Je höher die Energie, desto eher kann Strahlung Atome verändern.",
        "Wenn ich mit dem Handy telefoniere, werde ich radioaktiv.",
    ]:
        rows.append([p(statement), "", ""])
    table = Table(rows, colWidths=[66 * mm, 35 * mm, 71 * mm], rowHeights=[10 * mm, 17 * mm, 17 * mm, 17 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.55, LINE),
                ("BACKGROUND", (0, 0), (-1, 0), MIST),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(BASE, 8.5)
    canvas.setFillColor(colors.HexColor("#667276"))
    canvas.drawString(20 * mm, 12 * mm, "TeachersAid Entwurf · Physik 4. Klasse · Strahlung und Radioaktivität")
    canvas.drawRightString(190 * mm, 12 * mm, f"Seite {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#d8dfdc"))
    canvas.line(20 * mm, 17 * mm, 190 * mm, 17 * mm)
    canvas.restoreState()


def build():
    pdf = OUT / "strahlung_codex_final_student.pdf"
    doc = BaseDocTemplate(
        str(pdf),
        pagesize=A4,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title="Strahlung und Radioaktivität - Codex Designstudie",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=footer)])

    story = []
    if HEADER:
        story.append(Image(str(HEADER), width=172 * mm, height=32 * mm))
        story.append(Spacer(1, 5 * mm))

    story += [
        p("Strahlung und Radioaktivität", "title"),
        p("Warum Energie über Gefahr entscheidet - nicht Durchdringung", "subtitle"),
        card(
            [
                p("<b>Kernfrage:</b> Was macht Strahlung gefährlich - und was nicht?", "cardhead"),
                p(
                    "Arbeite mit Größenordnungen, nicht mit Bauchgefühl. Trenne drei Fragen: "
                    "<b>Welche Energie?</b> <b>Welche Dosis?</b> <b>Welche Aussage ist belegt?</b>",
                    "body",
                ),
            ],
            bg=MIST,
            stroke=TEAL,
        ),
        Spacer(1, 4 * mm),
    ]

    path = Table([[badge("1 · Unterscheiden", TEAL_DARK), badge("2 · Begründen", BLUE), badge("3 · Bewerten", RED)]], colWidths=[56 * mm] * 3)
    path.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story += [path, Spacer(1, 5 * mm), p("Der wichtige Unterschied", "h1"), Image(str(SPECTRUM), width=172 * mm, height=41 * mm)]
    story += [
        card(
            [
                p(
                    "<b>Merksatz:</b> Durchdringung allein sagt wenig über Gefahr. Entscheidend sind Energie und Dosis. "
                    "Nicht-ionisierend bedeutet nicht automatisch harmlos.",
                    "body",
                )
            ],
            bg=WARM,
            stroke=YELLOW,
        ),
        Spacer(1, 5 * mm),
    ]
    story.append(
        task(
            1,
            "Zufall und viele Atome",
            "Beim radioaktiven Zerfall kann man für ein einzelnes Atom nicht sagen, wann es zerfällt - "
            "für sehr viele Atome aber sehr genau, wie viele pro Sekunde zerfallen. Erkläre, warum das kein Widerspruch ist.",
            [lines(3)],
            8,
            "verstehen",
            "W",
            TEAL_DARK,
        )
    )
    story.append(PageBreak())

    story += [
        p("Mini-Auftrag: Eine Anwendung verständlich machen", "h1"),
        task(
            2,
            "Info-Karte",
            "Entwirf eine kleine Info-Karte (5-6 Sätze) für jüngere Schüler:innen zu einer aktuellen Anwendung von Strahlung "
            "(z. B. PET im Krankenhaus, Bestrahlung von Lebensmitteln, C-14-Datierung). Erkläre Nutzen UND Grenze.",
            [
                card(
                    [
                        p("<b>Deine Karte soll enthalten:</b>", "cardhead"),
                        p("1. Wofür wird die Strahlung genutzt?  2. Was ist der Nutzen?  3. Wo liegt eine Grenze oder ein Risiko?", "body"),
                    ],
                    bg=MIST,
                    stroke=TEAL,
                    width=172 * mm,
                ),
                Spacer(1, 2 * mm),
                answer_box(70 * mm),
            ],
            12,
            "entwickeln",
            "W",
            TEAL_DARK,
        ),
    ]
    story.append(PageBreak())

    story += [p("Fall 1: Durchdringung ist nicht dasselbe wie Gefahr", "h1")]
    compare = Table(
        [[p("<b>WLAN / Funk</b><br/>durchdringt Wände<br/><font color=\"#3c7d57\">niedrige Energie</font>"), p("<b>Gamma</b><br/>durchdringt Materie<br/><font color=\"#b14b48\">sehr hohe Energie</font>")]],
        colWidths=[84 * mm, 84 * mm],
    )
    compare.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#edf7f5")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#fff0ee")),
                ("BOX", (0, 0), (-1, -1), 0.65, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.65, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story += [compare, Spacer(1, 6 * mm)]
    story.append(
        task(
            3,
            "Erklären",
            "WLAN-Signale gehen durch Wände, schaden dir aber nicht - Gammastrahlung dagegen ist gefährlich. "
            "Beide durchdringen Materie. Erkläre den Unterschied.",
            [lines(4)],
            6,
            "analysieren",
            "S/W",
            BLUE,
        )
    )
    story.append(
        task(
            4,
            "Fallen erkennen",
            "Entscheide richtig/falsch und begründe oder korrigiere.",
            [true_false_table()],
            9,
            "bewerten",
            "S",
            BLUE,
        )
    )
    story.append(PageBreak())

    story += [p("Fall 2: Dosis in Größenordnungen denken", "h1"), Image(str(DOSE), width=172 * mm, height=44 * mm), Spacer(1, 3 * mm)]
    story.append(
        task(
            5,
            "Ordnen und erklären",
            "Dosen zum Vergleich: 1 Banane ≈ 0,1 µSv · Thorax-Röntgen ≈ 20 µSv · Transatlantikflug ≈ 40 µSv · "
            "natürliche Jahresdosis in Österreich ≈ 2-3 mSv. Ordne \"eine Banane essen\", \"einmal fliegen\" "
            "und \"ein Jahr leben\" nach Dosis und erkläre, warum Größenordnungen wichtiger sind als Bauchgefühl.",
            [lines(5)],
            10,
            "analysieren",
            "S",
            RED,
        )
    )
    story.append(
        task(
            6,
            "Eine Schlagzeile prüfen",
            "Eine Schlagzeile behauptet: \"Handystrahlung macht krank!\" Welche EINE Frage würdest du stellen, "
            "bevor du das glaubst - und warum entscheidet gerade diese Frage über die Glaubwürdigkeit?",
            [
                card(
                    [p("<b>Hinweis:</b> Funk/Mikrowellen sind nicht-ionisierend; ein gesicherter physikalischer Effekt ist Erwärmung.", "tip")],
                    bg=WARM,
                    stroke=YELLOW,
                    width=172 * mm,
                ),
                Spacer(1, 2 * mm),
                lines(4),
            ],
            11,
            "bewerten",
            "S",
            RED,
        )
    )
    story.append(PageBreak())

    story += [
        p("Optional: Wenn ein Zählrohr verfügbar ist", "h1"),
        card(
            [
                p(
                    "<b>Sicherheitsrahmen:</b> Nur mit zugelassener Schulquelle und nach den Regeln der Lehrkraft. "
                    "Ohne Gerät kann diese Aufgabe als Trockenübung mit vorgegebenen Messwerten gemacht werden.",
                    "body",
                )
            ],
            bg=colors.HexColor("#eef4ff"),
            stroke=BLUE,
        ),
        Spacer(1, 5 * mm),
    ]
    protocol = Table(
        [[p("<b>Abstand</b>"), p("<b>Zählrate</b>"), p("<b>Beobachtung</b>")], ["", "", ""], ["", "", ""], ["", "", ""]],
        colWidths=[40 * mm, 40 * mm, 92 * mm],
        rowHeights=[9 * mm, 13 * mm, 13 * mm, 13 * mm],
    )
    protocol.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.55, LINE),
                ("BACKGROUND", (0, 0), (-1, 0), MIST),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(
        task(
            7,
            "Messen und protokollieren",
            "Miss die Zählrate in verschiedenen Abständen zu einer schwachen Schulquelle. Protokolliere Abstand "
            "und Zählrate und beschreibe, wie die Rate mit dem Abstand zusammenhängt.",
            [answer_box(55 * mm), Spacer(1, 3 * mm), protocol],
            22,
            "anwenden",
            "E",
            GREEN,
        )
    )
    story += [
        Spacer(1, 4 * mm),
        card([p("<b>Exit-Ticket:</b> Schreibe einen Satz, der den Unterschied zwischen \"durchdringt\" und \"gefährlich\" erklärt.", "cardhead"), lines(2)], bg=MIST, stroke=TEAL),
    ]

    doc.build(story)
    return pdf


if __name__ == "__main__":
    print(build().resolve())
