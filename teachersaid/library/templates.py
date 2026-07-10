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

    # --- Oberstufe (Sek II) — the parametric goldmine, all 4 Inhaltsbereiche ---------
    ParametricTask(
        id="mat-os-kurvendiskussion", title="Kurvendiskussion (Polynomfunktion 3. Grades)",
        subject="Mathematik", klasse=7,
        kompetenzbereich="Grundlagen der Differentialrechnung anhand von Polynomfunktionen",
        content_area="Analysis", recipe="polynomial_curve",
        prompt_template="Führe eine Kurvendiskussion durch: Bestimme alle Extrem- und "
                        "Wendepunkte von $f(x) = {fx}$.",
        serves=[Serves(competence_id="MAT.OS.7.GRU.06", relation="exercises")],
        dimensions=["FO"], cognitive_level="analyze", kind="calculation", est_minutes=10),
    ParametricTask(
        id="mat-os-integral", title="Bestimmtes Integral (Hauptsatz)",
        subject="Mathematik", klasse=8, kompetenzbereich="Grundlagen der Integralrechnung",
        content_area="Analysis", recipe="definite_integral",
        prompt_template="Berechne das bestimmte Integral der Funktion $f(x) = {f}$ über dem "
                        "Intervall $[{lo};\\,{hi}]$.",
        serves=[Serves(competence_id="MAT.OS.8.GRU2.01", relation="exercises")],
        dimensions=["FO"], cognitive_level="apply", kind="calculation", est_minutes=6),
    ParametricTask(
        id="mat-os-lgs2", title="Lineares Gleichungssystem (2 Variablen)",
        subject="Mathematik", klasse=5, kompetenzbereich="Gleichungen und Gleichungssysteme",
        content_area="Algebra und Geometrie", recipe="linear_system_2",
        prompt_template="Löse das lineare Gleichungssystem $ {eq1} $ und $ {eq2} $.",
        serves=[Serves(competence_id="MAT.OS.5.GLE.02", relation="exercises")],
        dimensions=["FO"], cognitive_level="apply", kind="calculation", est_minutes=6),
    ParametricTask(
        id="mat-os-lgs3", title="Lineares Gleichungssystem (3 Variablen)",
        subject="Mathematik", klasse=6,
        kompetenzbereich="Vektoren und analytische Geometrie in ³; Vektoren in n",
        content_area="Algebra und Geometrie", recipe="linear_system_3",
        prompt_template="Löse das lineare Gleichungssystem mit drei Variablen: "
                        "$ {eq1} $; $ {eq2} $; $ {eq3} $.",
        serves=[Serves(competence_id="MAT.OS.6.VEK2.03", relation="exercises")],
        dimensions=["FO"], cognitive_level="apply", kind="calculation", est_minutes=8),
    ParametricTask(
        id="mat-os-binomial", title="Binomialverteilung",
        subject="Mathematik", klasse=7, kompetenzbereich="Diskrete Wahrscheinlichkeitsverteilungen",
        content_area="Wahrscheinlichkeit und Statistik", recipe="binomial_distribution",
        prompt_template="Ein Bernoulli-Experiment mit Trefferwahrscheinlichkeit $p = {p}$ wird "
                        "{n}-mal durchgeführt. Berechne $P(X = {k})$, $P(X \\leq {k})$, den "
                        "Erwartungswert und die Standardabweichung.",
        serves=[Serves(competence_id="MAT.OS.7.DIS.05", relation="exercises")],
        dimensions=["DM"], cognitive_level="apply", kind="calculation", est_minutes=8),
    ParametricTask(
        id="mat-os-skalarprodukt", title="Skalarprodukt und Winkel (Vektoren in der Ebene)",
        subject="Mathematik", klasse=5, kompetenzbereich="Vektoren und analytische Geometrie in ²",
        content_area="Algebra und Geometrie", recipe="vector_dot_angle",
        prompt_template="Gegeben sind die Vektoren $ {va} $ und $ {vb} $. Berechne das "
                        "Skalarprodukt, die Beträge und den eingeschlossenen Winkel.",
        serves=[Serves(competence_id="MAT.OS.5.VEK.03", relation="exercises")],
        dimensions=["FO"], cognitive_level="apply", kind="calculation", est_minutes=7),

    # --- Chemie (Oberstufe) — the quantitative engine: correct by construction from
    # the grounded atomic masses + conservation of atoms (pipeline/chemistry.py) -------
    ParametricTask(
        id="che-os-molmasse", title="Molare Masse einer Verbindung",
        subject="Chemie", klasse=7, kompetenzbereich="Substanz und Energie",
        content_area="Größen", recipe="molar_mass",
        prompt_template="Berechne die molare Masse der Verbindung {formel}. "
                        "Verwende die Atommassen aus dem Periodensystem.",
        serves=[Serves(competence_id="CHE.OS.7.SUB.01", relation="exercises")],
        dimensions=["EG"], cognitive_level="apply", kind="calculation", est_minutes=5),
    ParametricTask(
        id="che-os-reaktionsgleichung", title="Reaktionsgleichung ausgleichen",
        subject="Chemie", klasse=7, kompetenzbereich="Substanz und Energie",
        content_area="Größen", recipe="equation_balance",
        prompt_template="Gleiche die folgende Reaktionsgleichung aus (Massenerhaltung): {schema}",
        serves=[Serves(competence_id="CHE.OS.7.SUB.01", relation="exercises")],
        dimensions=["EG"], cognitive_level="apply", kind="calculation", est_minutes=5),
    ParametricTask(
        id="che-os-stoechiometrie", title="Stöchiometrische Massenberechnung",
        subject="Chemie", klasse=7, kompetenzbereich="Substanz und Energie",
        content_area="Größen", recipe="stoichiometry",
        prompt_template="Bei der Reaktion {reaktion} werden {masse} g {edukt} vollständig "
                        "umgesetzt. Berechne die Masse an {produkt}, die dabei entsteht.",
        serves=[Serves(competence_id="CHE.OS.7.SUB.03", relation="exercises")],
        dimensions=["EG"], cognitive_level="apply", kind="calculation", est_minutes=8),

    # --- Chemie (Unterstufe, 4. Kl.) — qualitative recipes, still correct by
    # construction (derived structure / curated truth in grounding/chemistry.py) -------
    ParametricTask(
        id="che-us-stoffklassen", title="Reinstoff oder Gemisch?",
        subject="Chemie", klasse=4,
        kompetenzbereich="Erkenntnisse gewinnen und interpretieren (E)",
        recipe="substance_classification",
        prompt_template="Ordne den folgenden Stoff ein: Ist {stoff} ein Element, eine "
                        "Verbindung oder ein Gemisch? Begründe deine Entscheidung.",
        serves=[Serves(competence_id="CHE.US.x.ERK.03", relation="exercises")],
        dimensions=["E"], cognitive_level="apply", kind="open_response", est_minutes=4),
    ParametricTask(
        id="che-us-trennverfahren", title="Trennverfahren wählen",
        subject="Chemie", klasse=4,
        kompetenzbereich="Erkenntnisse gewinnen und interpretieren (E)",
        recipe="separation_method",
        prompt_template="Mit welchem Trennverfahren lässt sich das Gemisch „{gemisch}“ "
                        "trennen? Erkläre, welche Eigenschaft der Bestandteile dabei genutzt wird.",
        serves=[Serves(competence_id="CHE.US.x.ERK.02", relation="exercises")],
        dimensions=["E"], cognitive_level="apply", kind="open_response", est_minutes=4),
    ParametricTask(
        id="che-us-reaktionstyp", title="Reaktionstyp bestimmen",
        subject="Chemie", klasse=4,
        kompetenzbereich="Erkenntnisse gewinnen und interpretieren (E)",
        recipe="reaction_type",
        prompt_template="Bestimme den Reaktionstyp der folgenden Reaktion: {reaktion}. "
                        "Begründe deine Zuordnung.",
        serves=[Serves(competence_id="CHE.US.x.ERK.03", relation="exercises")],
        dimensions=["E"], cognitive_level="apply", kind="open_response", est_minutes=5),
    ParametricTask(
        id="che-us-teilchenanzahl", title="Atome auf der Teilchenebene zählen",
        subject="Chemie", klasse=4,
        kompetenzbereich="Erkenntnisse gewinnen und interpretieren (E)",
        recipe="atom_count",
        prompt_template="Wie viele Atome jeder Sorte enthält ein Molekül {formel}? "
                        "Wie viele Atome sind es insgesamt?",
        serves=[Serves(competence_id="CHE.US.x.ERK.03", relation="exercises")],
        dimensions=["E"], cognitive_level="apply", kind="open_response", est_minutes=4),
    ParametricTask(
        id="che-us-saeure-base", title="Sauer, basisch oder neutral?",
        subject="Chemie", klasse=4,
        kompetenzbereich="Standpunkte begründen, Entscheidungen treffen und reflektiert handeln (S)",
        recipe="acid_base_neutral",
        prompt_template="Ist die Lösung von „{stoff}“ sauer, basisch oder neutral? "
                        "Begründe deine Einschätzung.",
        serves=[Serves(competence_id="CHE.US.x.STA.02", relation="exercises")],
        dimensions=["S"], cognitive_level="apply", kind="open_response", est_minutes=4),

    # --- Latein (Unterstufe, 3./4. Kl.) — Wortbildung: correct by CURATION. Every
    # prefix+base combination the recipes emit is a curated, attested Latin word in
    # grounding/latin.py (select, never author — no synthesized Latin). The Matura demand
    # map names Wortbildung (trennen) the most frequent IT task family (Documents/
    # matura-latein-coverage.md); the Klasse-3 Anwendungsbereich names
    # "Wortbildungselemente" explicitly. Material Latin, instructions German (the
    # target-language convention). -----------------------------------------------------
    ParametricTask(
        id="lat-us-wortbildung", title="Wortbildung: Komposita zerlegen",
        subject="Latein", klasse=3,
        kompetenzbereich="Sprach- und textbezogene Kompetenzen",
        recipe="wortbildung_decompose",
        prompt_template="Zerlege das lateinische Verb „{wort}“ in Präfix und Grundverb "
                        "und gib die Bedeutung des zusammengesetzten Verbs an.",
        serves=[Serves(competence_id="LAT.US.3.SPR.01", relation="exercises")],
        dimensions=["SPR"], cognitive_level="apply", kind="open_response", est_minutes=3),
    ParametricTask(
        id="lat-us-wortbildung-bedeutung", title="Wortbildung: Bedeutungen erschließen",
        subject="Latein", klasse=4,
        kompetenzbereich="Sprach- und textbezogene Kompetenzen",
        recipe="wortbildung_meaning",
        prompt_template="Bilde aus dem Grundverb {basis} und dem Präfix {praefix} das "
                        "zusammengesetzte Verb und erschließe seine Bedeutung.",
        serves=[Serves(competence_id="LAT.US.4.SPR.01", relation="exercises")],
        dimensions=["SPR"], cognitive_level="apply", kind="open_response", est_minutes=3),
    ParametricTask(
        id="lat-us-wortbildung-zuordnung", title="Wortbildung: Komposita zuordnen",
        subject="Latein", klasse=3,
        kompetenzbereich="Sprach- und textbezogene Kompetenzen",
        recipe="wortbildung_matching",
        prompt_template="Ordne die zusammengesetzten Verben (1–4) ihren Bedeutungen (A–D) "
                        "zu: {liste}",
        serves=[Serves(competence_id="LAT.US.3.SPR.01", relation="exercises")],
        dimensions=["SPR"], cognitive_level="understand", kind="matching", est_minutes=4),
]


def find_template(template_id: str) -> ParametricTask | None:
    return next((t for t in PARAM_TEMPLATES if t.id == template_id), None)


def variant_worksheet(template: ParametricTask, n: int = 6, *, today: date | None = None,
                      seed0: int = 1):
    """Build an assemble-ready WorksheetContent of N variants. Returns (content, resolution)."""
    from ..grounding import lehrplan_store as ls
    from ..pipeline.parametrize import make_variants
    from ..pipeline.resolve import resolve_kompetenzbereich

    stufe = ls.stufe_for_klasse(template.klasse)  # Klasse fixes the stage (1–4 / 5–8)
    res = resolve_kompetenzbereich(template.subject, template.klasse,
                                   template.kompetenzbereich, today=today)
    blocks = make_variants(template, n, seed0=seed0)
    title = template.title or template.id
    meta = WorksheetMeta(
        title=f"Übungsblatt: {title} ({n} Varianten)", subject=template.subject,
        stufe=stufe, klasse=template.klasse,
        kernfrage=f"Übung: {title}", fassung=res.fassung,
        lehrplan_label=f"{template.subject} · {template.klasse}. Kl. · {template.kompetenzbereich}")
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(template.subject, stufe),
        intro=[], sections=[Baustein(id="uebung", title=title, blocks=blocks)], assets=[])
    return content, res
