"""Curated parametric Maths templates + a worksheet builder.

The variant analogue of the master/block library: a small set of vetted `ParametricTask`s
(prompt + a code-backed `recipe`), each anchored to a real Lehrplan competence. `make_variants`
turns one template into N correct-by-construction practice items; `variant_worksheet` wraps
them into an assemble-ready `WorksheetContent`. Curated (code, not LLM), so the maths is exact.
"""

from __future__ import annotations

from datetime import date

from ..schema.blocks import Serves
from ..schema.parametric import ParametricTask
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

PARAM_TEMPLATES: list[ParametricTask] = [
    ParametricTask(
        id="mat-lineare-gleichung", title="Lineare Gleichungen lösen",
        subject="Mathematik", klasse=2, kompetenzbereich="2: Variablen und Funktionen",
        recipe="linear_equation",
        prompt_template="Löse die folgende Gleichung nach $x$ auf: ${eq}$",
        serves=[Serves(competence_id="MAT.US.2.VAR.02", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=4),
    ParametricTask(
        id="mat-bruch-addition", title="Brüche addieren",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="fraction_add",
        prompt_template="Berechne und kürze so weit wie möglich: ${f1} + {f2}$",
        serves=[Serves(competence_id="MAT.US.2.ZAH.03", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=4),
    ParametricTask(
        id="mat-prozent", title="Prozentrechnung",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="percentage",
        prompt_template="Wie viel sind {pct} % von {base}?",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=3),
    ParametricTask(
        id="mat-prozentsatz", title="Prozentsatz bestimmen",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="percentage_rate",
        prompt_template="Wie viel Prozent sind {part} von {base}?",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=3),
    ParametricTask(
        id="mat-dreisatz", title="Direkte Proportionalität (Dreisatz)",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="proportion",
        prompt_template="{n1} {einheit} kosten {v1} €. Wie viel kosten {n2} {einheit}?",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["MOD"], cognitive_level="apply", kind="modelling_task", est_minutes=4),
    ParametricTask(
        id="mat-bruch-multiplikation", title="Brüche multiplizieren",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="fraction_multiply",
        prompt_template="Berechne und kürze so weit wie möglich: ${f1} \\cdot {f2}$",
        serves=[Serves(competence_id="MAT.US.2.ZAH.03", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=4),
    ParametricTask(
        id="mat-gleichung-beidseitig", title="Gleichungen mit Variablen auf beiden Seiten",
        subject="Mathematik", klasse=3, kompetenzbereich="2: Variablen und Funktionen",
        recipe="linear_equation_both_sides",
        prompt_template="Löse die folgende Gleichung nach $x$ auf: ${eq}$",
        serves=[Serves(competence_id="MAT.US.3.VAR.03", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=5),
    ParametricTask(
        id="mat-rechteck", title="Rechteck: Fläche & Umfang",
        subject="Mathematik", klasse=1, kompetenzbereich="3: Figuren und Körper",
        recipe="rectangle",
        prompt_template="Berechne Flächeninhalt und Umfang eines Rechtecks mit Länge {l} cm "
                        "und Breite {w} cm.",
        serves=[Serves(competence_id="MAT.US.1.FIG.02", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=4),
    ParametricTask(
        id="mat-pythagoras", title="Satz des Pythagoras",
        subject="Mathematik", klasse=4, kompetenzbereich="3: Figuren und Körper",
        recipe="pythagoras",
        prompt_template="Ein rechtwinkliges Dreieck hat die Katheten $a = {a}$ cm und "
                        "$b = {b}$ cm. Berechne die Länge der Hypotenuse $c$.",
        serves=[Serves(competence_id="MAT.US.4.FIG.01", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=5),
    ParametricTask(
        id="mat-kennzahlen", title="Statistische Kennzahlen",
        subject="Mathematik", klasse=1, kompetenzbereich="4: Daten und Zufall",
        recipe="mean_median",
        prompt_template="Berechne Mittelwert, Median und Spannweite der Datenreihe: {vals}.",
        serves=[Serves(competence_id="MAT.US.1.DAT.02", relation="exercises")],
        dimensions=["DAR"], cognitive_level="apply", kind="calculation", est_minutes=5),
]


def find_template(template_id: str) -> ParametricTask | None:
    return next((t for t in PARAM_TEMPLATES if t.id == template_id), None)


def variant_worksheet(template: ParametricTask, n: int = 6, *, today: date | None = None,
                      seed0: int = 1):
    """Build an assemble-ready WorksheetContent of N variants. Returns (content, resolution)."""
    from ..grounding import lehrplan_store as ls
    from ..pipeline.parametrize import make_variants
    from ..pipeline.resolve import resolve_kompetenzbereich

    res = resolve_kompetenzbereich(template.subject, template.klasse,
                                   template.kompetenzbereich, today=today)
    blocks = make_variants(template, n, seed0=seed0)
    title = template.title or template.id
    meta = WorksheetMeta(
        title=f"Übungsblatt: {title} ({n} Varianten)", subject=template.subject,
        stufe="Unterstufe", klasse=template.klasse,
        kernfrage=f"Übung: {title}", fassung=res.fassung,
        lehrplan_label=f"{template.subject} · {template.klasse}. Kl. · {template.kompetenzbereich}")
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(template.subject),
        intro=[], sections=[Baustein(id="uebung", title=title, blocks=blocks)], assets=[])
    return content, res
