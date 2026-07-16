"""Curated parametric Maths templates + a worksheet builder.

The variant analogue of the master/block library: a small set of vetted `ParametricTask`s
(prompt + a code-backed `recipe`), each anchored to a real Lehrplan competence. `make_variants`
turns one template into N correct-by-construction practice items; `variant_worksheet` wraps
them into an assemble-ready `WorksheetContent`. Curated (code, not LLM), so the maths is exact.
"""

from __future__ import annotations

from datetime import date

from ..schema.blocks import Gloss, InfoBlock, Serves
from ..schema.mixer import ParametricMixerProfile, Textlast
from ..schema.parametric import ParametricTask
from ..schema.response import LinesResponse
from ..schema.worksheet import Baustein, TeacherOverview, WorksheetContent, WorksheetMeta

PARAM_TEMPLATES: list[ParametricTask] = [
    ParametricTask(
        id="mat-lineare-gleichung", title="Lineare Gleichungen lösen",
        subject="Mathematik", klasse=2, kompetenzbereich="2: Variablen und Funktionen",
        recipe="linear_equation",
        prompt_template="Löse die folgende Gleichung nach $x$ auf: ${eq}$",
        context_frame="Gleichungen umzuformen brauchst du überall dort, wo eine "
                      "unbekannte Größe aus einer Formel bestimmt wird.",
        serves=[Serves(competence_id="MAT.US.2.VAR.02", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=4),
    ParametricTask(
        id="mat-bruch-addition", title="Brüche addieren",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="fraction_add",
        prompt_template="Berechne und kürze so weit wie möglich: ${f1} + {f2}$",
        context_frame="Mit Brüchen rechnest du immer dann, wenn Anteile zusammenkommen — "
                      "beim Kochen, Messen und Teilen.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.03", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=4),
    ParametricTask(
        id="mat-prozent", title="Prozentrechnung",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="percentage",
        prompt_template="Wie viel sind {pct} % von {base}?",
        context_frame="Prozente begegnen dir bei Rabatten, bei Zinsen und in jeder "
                      "Statistik.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=3),
    ParametricTask(
        id="mat-prozentsatz", title="Prozentsatz bestimmen",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="percentage_rate",
        prompt_template="Wie viel Prozent sind {part} von {base}?",
        context_frame="Welcher Anteil ist das in Prozent? Diese Frage stellt sich bei "
                      "Noten, Umfragen und Nährwertangaben.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=3),
    ParametricTask(
        id="mat-dreisatz", title="Direkte Proportionalität (Dreisatz)",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="proportion",
        prompt_template="{n1} {einheit} kosten {v1} €. Wie viel kosten {n2} {einheit}?",
        context_frame="Der Dreisatz hilft beim Einkaufen und Umrechnen: von bekannten "
                      "Mengen auf gesuchte schließen.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["MOD"], cognitive_level="apply", kind="modelling_task", est_minutes=4),
    ParametricTask(
        id="mat-bruch-multiplikation", title="Brüche multiplizieren",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="fraction_multiply",
        prompt_template="Berechne und kürze so weit wie möglich: ${f1} \\cdot {f2}$",
        context_frame="Anteile von Anteilen — etwa die Hälfte eines Drittels — "
                      "berechnest du durch Multiplizieren von Brüchen.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.03", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=4),
    ParametricTask(
        id="mat-gleichung-beidseitig", title="Gleichungen mit Variablen auf beiden Seiten",
        subject="Mathematik", klasse=3, kompetenzbereich="2: Variablen und Funktionen",
        recipe="linear_equation_both_sides",
        prompt_template="Löse die folgende Gleichung nach $x$ auf: ${eq}$",
        context_frame="Stehen auf beiden Seiten Variablen, bringt geschicktes Umformen "
                      "Ordnung in die Gleichung.",
        serves=[Serves(competence_id="MAT.US.3.VAR.03", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=5),
    ParametricTask(
        id="mat-rechteck", title="Rechteck: Fläche & Umfang",
        subject="Mathematik", klasse=1, kompetenzbereich="3: Figuren und Körper",
        recipe="rectangle",
        prompt_template="Berechne Flächeninhalt und Umfang eines Rechtecks mit Länge {l} cm "
                        "und Breite {w} cm.",
        prompt_simple="Ein Rechteck ist {l} cm lang und {w} cm breit. Rechne aus, wie groß "
                      "die Fläche ist. Rechne dann aus, wie lang der Rand rund um das "
                      "Rechteck ist (der Umfang).",
        glossary=[
            Gloss(term="Flächeninhalt",
                  explanation="wie viel Platz die Fläche einnimmt"),
            Gloss(term="Umfang",
                  explanation="die Länge der Linie rund um die Figur herum"),
        ],
        context_frame="Flächen und Umfänge braucht man beim Planen von Räumen, Gärten "
                      "und Sportfeldern.",
        serves=[Serves(competence_id="MAT.US.1.FIG.02", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=4),
    ParametricTask(
        id="mat-pythagoras", title="Satz des Pythagoras",
        subject="Mathematik", klasse=4, kompetenzbereich="3: Figuren und Körper",
        recipe="pythagoras",
        prompt_template="Berechne die fehlende Seitenlänge des rechtwinkligen Dreiecks "
                        "(siehe Skizze). Gegeben: {gegeben}. Gesucht: {gesucht}.",
        prompt_simple="Das Dreieck hat einen rechten Winkel (siehe Skizze). Eine Seite "
                      "fehlt. Rechne sie aus. Du kennst schon: {gegeben}. Gesucht ist: "
                      "{gesucht}.",
        glossary=[
            Gloss(term="rechter Winkel",
                  explanation="der Winkel in der Ecke eines Rechtecks; er wird in der "
                              "Skizze mit einem kleinen Quadrat markiert"),
            Gloss(term="Hypotenuse",
                  explanation="die längste Seite im rechtwinkligen Dreieck; sie liegt "
                              "dem rechten Winkel gegenüber"),
            Gloss(term="Kathete",
                  explanation="eine der beiden kürzeren Seiten, die den rechten Winkel "
                              "einschließen"),
        ],
        context_frame="Mit dem Satz des Pythagoras bestimmen Handwerker und Vermesser "
                      "Längen, die sich nicht direkt messen lassen.",
        serves=[Serves(competence_id="MAT.US.4.FIG.01", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=5),
    ParametricTask(
        id="mat-quader-oberflaeche", title="Quadernetz: Oberflächeninhalt",
        subject="Mathematik", klasse=1, kompetenzbereich="3: Figuren und Körper",
        recipe="quader_oberflaeche",
        prompt_template="Das Netz gehört zu einem Quader mit a = {a} cm, b = {b} cm und "
                        "c = {c} cm. Berechne den Oberflächeninhalt O.",
        context_frame="Ein Körpernetz zeigt alle Flächen eines Körpers in der Ebene und "
                      "macht ihre Flächenpaare sichtbar.",
        serves=[Serves(competence_id="MAT.US.1.FIG.03", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=6),
    ParametricTask(
        id="mat-kreis", title="Kreis: Umfang & Flächeninhalt",
        subject="Mathematik", klasse=4, kompetenzbereich="3: Figuren und Körper",
        recipe="kreis_umfang_flaeche",
        prompt_template="Ein Kreis hat den Radius r = {r} cm (siehe Skizze). Berechne seinen "
                        "Umfang und seinen Flächeninhalt (auf zwei Nachkommastellen gerundet).",
        prompt_simple="Ein Kreis hat den Radius r = {r} cm (siehe Skizze). Rechne aus, wie "
                      "lang die Linie rund um den Kreis ist (der Umfang). Rechne dann aus, "
                      "wie groß die Fläche ist. Runde auf zwei Stellen nach dem Komma.",
        glossary=[
            Gloss(term="Radius",
                  explanation="der Abstand von der Mitte des Kreises bis zum Rand"),
            Gloss(term="Umfang",
                  explanation="die Länge der Linie rund um den Kreis herum"),
            Gloss(term="Flächeninhalt",
                  explanation="wie viel Platz die Fläche des Kreises einnimmt"),
        ],
        serves=[Serves(competence_id="MAT.US.4.FIG.02", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation", est_minutes=5),
    ParametricTask(
        id="mat-kennzahlen", title="Statistische Kennzahlen",
        subject="Mathematik", klasse=1, kompetenzbereich="4: Daten und Zufall",
        recipe="mean_median",
        prompt_template="Berechne Mittelwert, Median und Spannweite der Datenreihe: {vals}.",
        prompt_simple="Hier ist eine Reihe von Zahlen: {vals}. Rechne drei Werte aus. "
                      "Rechne zuerst den Mittelwert aus. Rechne dann den Median aus. "
                      "Rechne zuletzt die Spannweite aus.",
        glossary=[
            Gloss(term="Mittelwert",
                  explanation="der Durchschnitt: alle Zahlen zusammenzählen und durch "
                              "ihre Anzahl teilen"),
            Gloss(term="Median",
                  explanation="der mittlere Wert, wenn man alle Zahlen der Größe nach "
                              "ordnet"),
            Gloss(term="Spannweite",
                  explanation="der Abstand zwischen der größten und der kleinsten Zahl"),
        ],
        context_frame="Kennzahlen wie Mittelwert und Median fassen eine Datenreihe in "
                      "wenigen Werten zusammen.",
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

    # --- Physik (Unterstufe, 3. Kl.) — the parametric pack: correct by construction from
    # sympy.physics.units, every answer DIMENSIONALLY VERIFIED (pipeline/physics.py). The
    # recipe builds the whole item text into {gegeben}+{frage}; the kind is open_response
    # (a core kind, so no subject-model change) — students show the Rechenweg on the lines.
    ParametricTask(
        id="phy-us-bewegung", title="Gleichförmige Bewegung (v = s/t)",
        subject="Physik", klasse=3, kompetenzbereich="Mechanik", recipe="uniform_motion",
        prompt_template="{gegeben} {frage}",
        serves=[Serves(competence_id="PHY.US.3.MEC.01", relation="exercises")],
        dimensions=["W"], cognitive_level="apply", kind="open_response", est_minutes=5,
        context_frame="Diese Aufgaben trainieren den Zusammenhang von Weg, Zeit und "
                      "Geschwindigkeit bei gleichförmiger Bewegung — mit Einheiten."),
    ParametricTask(
        id="phy-us-ohm", title="Ohm'sches Gesetz (U = R·I)",
        subject="Physik", klasse=3, kompetenzbereich="Elektrizität und Magnetismus",
        recipe="ohm", prompt_template="{gegeben} {frage}",
        serves=[Serves(competence_id="PHY.US.3.ELE.01", relation="exercises")],
        dimensions=["W"], cognitive_level="apply", kind="open_response", est_minutes=5,
        context_frame="Diese Aufgaben verknüpfen Spannung, Stromstärke und Widerstand "
                      "über das Ohm'sche Gesetz — die Einheiten müssen zusammenpassen."),
    ParametricTask(
        id="phy-us-hebel", title="Hebelgesetz (F₁·a₁ = F₂·a₂)",
        subject="Physik", klasse=3, kompetenzbereich="Mechanik", recipe="lever",
        prompt_template="{gegeben} {frage}",
        serves=[Serves(competence_id="PHY.US.3.MEC.03", relation="exercises")],
        dimensions=["E"], cognitive_level="apply", kind="open_response", est_minutes=6,
        context_frame="Diese Aufgaben wenden das Hebelgesetz an: im Gleichgewicht sind "
                      "die Drehmomente auf beiden Seiten gleich groß."),
    ParametricTask(
        id="phy-us-arbeit-leistung", title="Elektrische Arbeit und Lageenergie",
        subject="Physik", klasse=3, kompetenzbereich="Energie", recipe="energy_power",
        prompt_template="{gegeben} {frage}",
        serves=[Serves(competence_id="PHY.US.3.ENE.01", relation="exercises")],
        dimensions=["W"], cognitive_level="apply", kind="open_response", est_minutes=6,
        context_frame="Diese Aufgaben berechnen Energie aus Leistung und Zeit (W = P·t) "
                      "bzw. die Lageenergie (E = m·g·h) — mit passenden Einheiten."),

    # --- Physik (Oberstufe) — the same dimensionally-verified engine, anchored to the
    # semesterised Oberstufe Lehrstoff (Thermodynamik/Teilchenmodell, Elektrizitätslehre,
    # elektrische Energie). Density lives here (kein eigener Dichte-Deskriptor in der US). -
    ParametricTask(
        id="phy-os-dichte", title="Dichte (ρ = m/V)",
        subject="Physik", klasse=5, kompetenzbereich="Thermodynamik", recipe="density",
        prompt_template="{gegeben} {frage}",
        serves=[Serves(competence_id="PHY.OS.5.THE.01", relation="exercises")],
        dimensions=["W"], cognitive_level="apply", kind="open_response", est_minutes=5,
        context_frame="Diese Aufgaben verknüpfen Masse, Volumen und Dichte — die Dichte "
                      "ist eine Stoffeigenschaft, die auf einen Stoff schließen lässt."),
    ParametricTask(
        id="phy-os-ersatzwiderstand", title="Ersatzwiderstand (Reihe/parallel)",
        subject="Physik", klasse=6, kompetenzbereich="Elektrizitätslehre",
        recipe="resistors", prompt_template="{gegeben} {frage}",
        serves=[Serves(competence_id="PHY.OS.6.ELE.01", relation="exercises")],
        dimensions=["W"], cognitive_level="apply", kind="open_response", est_minutes=6,
        context_frame="Diese Aufgaben berechnen den Ersatzwiderstand: in Reihe addieren "
                      "sich die Widerstände, parallel die Kehrwerte."),
    ParametricTask(
        id="phy-os-arbeit-leistung", title="Elektrische Arbeit und Energie",
        subject="Physik", klasse=6, kompetenzbereich="Elektrische Energie",
        recipe="energy_power", prompt_template="{gegeben} {frage}",
        serves=[Serves(competence_id="PHY.OS.6.ELE2.01", relation="exercises")],
        dimensions=["W"], cognitive_level="apply", kind="open_response", est_minutes=6,
        context_frame="Diese Aufgaben berechnen die elektrische Arbeit (W = P·t) und die "
                      "Lageenergie (E = m·g·h) — Energie in J bzw. kWh."),

    # --- Misconception-MC templates (roadmap A3) — multiple_choice with correct-by-
    # construction distractors: each wrong option is COMPUTED by applying a documented
    # misconception to the SAME drawn numbers (pipeline/misconceive), and the teacher guide
    # names which error each distractor probes ("B prüft: Vorzeichenfehler"). The kind is
    # multiple_choice (a core kind — no subject-model change); the options ARE the response
    # surface (no write-space, per _SELF_CONTAINED_PAYLOADS). -----------------------------
    ParametricTask(
        id="mat-prozent-mc", title="Prozentrechnung (Multiple Choice)",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="percentage_mc", prompt_template="Wie viel sind {pct} % von {base}?",
        context_frame="Bei Multiple-Choice-Aufgaben lohnt sich Nachrechnen: die falschen "
                      "Antworten sind typische Rechenfehler, keine Zufallszahlen.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="multiple_choice", est_minutes=3),
    ParametricTask(
        id="mat-lineare-gleichung-mc",
        title="Lineare Gleichungen lösen (Multiple Choice)",
        subject="Mathematik", klasse=2, kompetenzbereich="2: Variablen und Funktionen",
        recipe="linear_equation_mc",
        prompt_template="Löse die Gleichung nach $x$ auf: ${eq}$. Welche Lösung ist richtig?",
        context_frame="Die falschen Antworten entstehen durch typische Umformungsfehler — "
                      "wer die Probe macht, erkennt sie.",
        serves=[Serves(competence_id="MAT.US.2.VAR.02", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="multiple_choice", est_minutes=4),
    ParametricTask(
        id="phy-us-ohm-mc", title="Ohm'sches Gesetz (Multiple Choice)",
        subject="Physik", klasse=3, kompetenzbereich="Elektrizität und Magnetismus",
        recipe="ohm_mc", prompt_template="{aufgabe}",
        context_frame="Die falschen Antworten sind typische Fehler — etwa das Multiplizieren "
                      "statt Dividierens, wenn die Formel nicht umgestellt wird.",
        serves=[Serves(competence_id="PHY.US.3.ELE.01", relation="exercises")],
        dimensions=["W"], cognitive_level="apply", kind="multiple_choice", est_minutes=4),
    ParametricTask(
        id="phy-os-ersatzwiderstand-mc",
        title="Ersatzwiderstand parallel (Multiple Choice)",
        subject="Physik", klasse=6, kompetenzbereich="Elektrizitätslehre",
        recipe="resistors_mc", prompt_template="{aufgabe}",
        context_frame="Der häufigste Fehler bei der Parallelschaltung: die Widerstände wie "
                      "in einer Reihenschaltung einfach addieren — genau das ist ein Distraktor.",
        serves=[Serves(competence_id="PHY.OS.6.ELE.01", relation="exercises")],
        dimensions=["W"], cognitive_level="apply", kind="multiple_choice", est_minutes=5),
]


# --- Matura-Nachfrage-Pack (FA + WS) — appended via extend() so the list literal above
#     is untouched (parallel work on this file merges cleanly). Anchored to real Oberstufe
#     MAT competences (lehrplan/oberstufe/MAT.json), Klasse 6. Non-"mat-os-" ids so the
#     locked test_oberstufe exact-set assertions stay green. Recipes: pipeline/parametrize.py.
PARAM_TEMPLATES.extend([
    ParametricTask(
        id="mat-fa-exponentialmodell", title="Exponentielles Wachstum und Abnahme",
        subject="Mathematik", klasse=6, kompetenzbereich="Reelle Funktionen",
        content_area="Funktionale Abhängigkeiten", recipe="exponential_model",
        prompt_template="{aufgabe}",
        serves=[Serves(competence_id="MAT.OS.6.REE.10", relation="exercises")],
        dimensions=["FO"], cognitive_level="apply", kind="calculation", est_minutes=7),
    ParametricTask(
        id="mat-ws-boxplot", title="Boxplot und Fünf-Punkte-Zusammenfassung",
        subject="Mathematik", klasse=6,
        kompetenzbereich="Beschreibende Statistik; Wahrscheinlichkeit",
        content_area="Wahrscheinlichkeit und Statistik", recipe="boxplot_from_data",
        prompt_template="Bestimme für die folgende Datenliste die Fünf-Punkte-Zusammenfassung "
                        "(Minimum, unteres Quartil Q₁, Median, oberes Quartil Q₃, Maximum) "
                        "sowie Spannweite und Interquartilsabstand: {daten}.",
        serves=[Serves(competence_id="MAT.OS.6.BES.01", relation="exercises")],
        dimensions=["FO"], cognitive_level="apply", kind="calculation", est_minutes=7),
    ParametricTask(
        id="mat-ws-baumdiagramm", title="Baumdiagramm: zweistufiger Zufallsversuch",
        subject="Mathematik", klasse=6,
        kompetenzbereich="Beschreibende Statistik; Wahrscheinlichkeit",
        content_area="Wahrscheinlichkeit und Statistik", recipe="probability_tree",
        prompt_template="{aufgabe}",
        serves=[Serves(competence_id="MAT.OS.6.BES.04", relation="exercises")],
        dimensions=["FO"], cognitive_level="apply", kind="calculation", est_minutes=7),
])


# --- Finanzführerschein-Pack (GWB) — appended via extend() (append-only). The recipes live
#     in pipeline/finanz.py (registered into the shared registry); pipeline/finanz.build_worksheet
#     wraps them into anchor-honest sheets (Lohnzettel → ÜT 13; Inflation → GWB.US.3.ENT.09;
#     Handytarife → GWB.US.3.ENT.04) with the didactic simplification stated ON the sheet.
PARAM_TEMPLATES.extend([
    ParametricTask(
        id="fin-lohnzettel", title="Vom Brutto zum Netto (Lohnzettel)",
        subject="Geographie und wirtschaftliche Bildung", klasse=3,
        # The sheet is ÜT-13-anchored via pipeline/finanz.build_worksheet (serves=[] → no
        # competence claim). The KB is only the label for the generic variant_worksheet path;
        # build_worksheet ignores it and re-anchors to ÜT 13.
        kompetenzbereich="Entwicklungen am Wirtschaftsstandort Österreich",
        recipe="lohnzettel",
        prompt_template="Eine angestellte Person verdient {brutto} brutto im Monat. Berechne "
                        "Schritt für Schritt den Nettolohn: zuerst die Sozialversicherung, dann "
                        "die Steuerbemessungsgrundlage, die Lohnsteuer (Tarif 2026) und zuletzt "
                        "das Netto.",
        prompt_simple="Jemand verdient {brutto} brutto im Monat. Wie viel bleibt davon netto "
                      "übrig? Rechne in vier Schritten. Zuerst ziehst du die "
                      "Sozialversicherung (SV) ab. Das ist der Betrag, von dem die Steuer "
                      "berechnet wird. Dann rechnest du die Lohnsteuer aus (Tarif 2026). "
                      "Am Ende bleibt das Netto.",
        glossary=[
            Gloss(term="brutto",
                  explanation="der ganze Lohn, bevor etwas abgezogen wird"),
            Gloss(term="netto",
                  explanation="das Geld, das am Ende übrig bleibt und ausgezahlt wird"),
            Gloss(term="Sozialversicherung",
                  explanation="ein fester Anteil vom Lohn für Kranken-, Pensions- und "
                              "Arbeitslosenversicherung"),
            Gloss(term="Lohnsteuer",
                  explanation="die Steuer, die vom Lohn an den Staat gezahlt wird"),
        ],
        serves=[],  # ÜT-anchored → kein Kompetenzanspruch über `serves`
        dimensions=["OK"], cognitive_level="apply", kind="open_response", est_minutes=8),
    ParametricTask(
        id="fin-inflation", title="Inflation und Kaufkraft (VPI)",
        subject="Geographie und wirtschaftliche Bildung", klasse=3,
        kompetenzbereich="Entwicklungen am Wirtschaftsstandort Österreich",
        recipe="inflation_vpi", prompt_template="{aufgabe}",
        serves=[Serves(competence_id="GWB.US.3.ENT.09", relation="exercises")],
        dimensions=["OK"], cognitive_level="apply", kind="open_response", est_minutes=6),
    ParametricTask(
        id="fin-handyvertrag", title="Handytarife vergleichen",
        subject="Geographie und wirtschaftliche Bildung", klasse=3,
        kompetenzbereich="Entwicklungen am Wirtschaftsstandort Österreich",
        recipe="handyvertrag_vergleich",
        prompt_template="Folgende Handytarife stehen zur Wahl: {tarife} Vergleiche die Tarife "
                        "über eine Vertragsdauer von 24 Monaten. Welcher ist am günstigsten? "
                        "Begründe deine Entscheidung.",
        prompt_simple="Es gibt diese Handytarife: {tarife} Ein Vertrag läuft 24 Monate lang. "
                      "Rechne für jeden Tarif aus, was er in dieser Zeit ganz kostet. Welcher "
                      "Tarif ist am billigsten? Schreibe auf, warum du das denkst.",
        glossary=[
            Gloss(term="Grundgebühr",
                  explanation="der feste Betrag, den man jeden Monat für den Tarif zahlt"),
            Gloss(term="Aktivierungskosten",
                  explanation="einmalige Kosten am Anfang, wenn man den Vertrag abschließt"),
            Gloss(term="Vertragsdauer",
                  explanation="die Zeit, für die man den Vertrag abschließt"),
        ],
        serves=[Serves(competence_id="GWB.US.3.ENT.04", relation="exercises")],
        dimensions=["UK"], cognitive_level="evaluate", kind="decision_scenario", est_minutes=7),
])


# --- Fehlersuche — appended via extend() (append-only). The recipes live in
#     pipeline/fehlersuche.py (registered into the shared registry): a complete worked solution
#     with exactly ONE planted, catalogued Fehlermuster (computed + propagated honestly). The
#     flawed chain is the student-facing object of study (TaskBlock.flawed_solution); the correct
#     chain (solution_steps), the located step + Fehlermuster name (answer_key) stay teacher-only.
#     kind = open_response (core; the student names + corrects the error on the lines);
#     cognitive_level = analyze (Fehleranalyse is genuine AFB-II/III work). Anchored to the same
#     verbatim MAT.US competences the arithmetic-drill twins use. Design: Documents/fehlersuche-design.md
PARAM_TEMPLATES.extend([
    ParametricTask(
        id="mat-fehlersuche-lineare-gleichung",
        title="Fehlersuche: lineare Gleichung",
        subject="Mathematik", klasse=2, kompetenzbereich="2: Variablen und Funktionen",
        recipe="fehlersuche_linear_equation",
        prompt_template="Beim Lösen der Gleichung ${eq}$ ist in der Musterlösung genau ein "
                        "Schritt falsch. Finde den falschen Schritt, gib seine Nummer an und "
                        "schreibe die richtige Rechnung auf.",
        context_frame="Eine Rechnung auf Fehler zu prüfen schult den Blick fürs eigene "
                      "Umformen — man muss jeden Schritt wirklich verstehen.",
        serves=[Serves(competence_id="MAT.US.2.VAR.02", relation="exercises")],
        dimensions=["OPE"], cognitive_level="analyze", kind="open_response", est_minutes=5,
        response=LinesResponse(n=3)),
    ParametricTask(
        id="mat-fehlersuche-bruch-addition",
        title="Fehlersuche: Brüche addieren",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="fehlersuche_fraction_add",
        prompt_template="In der Musterlösung zur Aufgabe ${f1} + {f2}$ steckt genau ein "
                        "Fehler. Finde den falschen Schritt, gib seine Nummer an und rechne "
                        "richtig weiter.",
        context_frame="Fehler in einer vorgelegten Rechnung zu finden schärft das Gespür "
                      "für die Rechenregeln — hier für das Addieren von Brüchen.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.03", relation="exercises")],
        dimensions=["OPE"], cognitive_level="analyze", kind="open_response", est_minutes=5,
        response=LinesResponse(n=3)),
    ParametricTask(
        id="mat-fehlersuche-prozent",
        title="Fehlersuche: Prozentrechnung",
        subject="Mathematik", klasse=2, kompetenzbereich="1: Zahlen und Maße",
        recipe="fehlersuche_percentage",
        prompt_template="Bei der Berechnung von {pct} % von {base} ist in der Musterlösung "
                        "genau ein Schritt falsch. Finde den falschen Schritt, gib seine "
                        "Nummer an und korrigiere die Rechnung.",
        context_frame="Beim Prüfen einer fremden Rechnung erkennt man typische "
                      "Stolperstellen — und vermeidet sie in der eigenen.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["OPE"], cognitive_level="analyze", kind="open_response", est_minutes=5,
        response=LinesResponse(n=3)),
])


def find_template(template_id: str) -> ParametricTask | None:
    return next((t for t in PARAM_TEMPLATES if t.id == template_id), None)


def variant_worksheet(template: ParametricTask, n: int = 6, *, today: date | None = None,
                      seed0: int = 1, ramp: bool = True,
                      mixer_profile: ParametricMixerProfile | None = None):
    """Build an assemble-ready WorksheetContent of N variants. Returns (content, resolution).

    Genre-honest Übungsreihe framing (the blackboard test): the sheet LABELS itself as a
    variant series — subtitle, a purpose intro block (Automatisieren / Schularbeit-
    Vorbereitung / Gruppe A/B), and a teacher throughline naming the value (difficulty
    ramp + per-variant Rechenweg) and stating what it is NOT (a didactic ladder
    worksheet). `ramp=True` (default) requests ascending difficulty bands; the
    "aufsteigend" claim is only made when the recipe actually delivered a spread —
    recipes without the knob produce an honest, unramped series."""
    from ..grounding import lehrplan_store as ls
    from ..pipeline.resolve import resolve_kompetenzbereich

    stufe = ls.stufe_for_klasse(template.klasse)  # Klasse fixes the stage (1–4 / 5–8)
    res = resolve_kompetenzbereich(template.subject, template.klasse,
                                   template.kompetenzbereich, today=today)
    # each variant may carry a figure (Pythagoras triangle, circle, Baumdiagramm …); collect
    # them onto the worksheet so they render + pass the media-policy gate (role="figure", code)
    mixer_lint = None
    if mixer_profile is None:
        from ..pipeline.parametrize import make_variants_with_assets
        blocks, assets = make_variants_with_assets(template, n, seed0=seed0, ramp=ramp)
        actual_n = n
    else:
        from ..pipeline.mixer import make_mixed_variants
        blocks, assets, mixer_lint, actual_n = make_mixed_variants(
            template, n, mixer_profile, seed0=seed0, ramp=ramp,
        )
    title = template.title or template.id
    if mixer_profile is not None:
        from ..pipeline.mixer import projected_title
        title = projected_title(title, mixer_profile)
    # honest labelling: claim "aufsteigend" only if the delivered bands actually spread
    stamped = [b.difficulty for b in blocks if b.difficulty is not None]
    ramped = len(set(stamped)) > 1
    subtitle = f"Übungsreihe — {actual_n} Varianten" + (", aufsteigend" if ramped else "")

    zweck = ("Diese Übungsreihe dient dem Automatisieren und der Vorbereitung auf die "
             "Schularbeit: jede Aufgabe ist eine eigene Variante derselben "
             "Aufgabenstellung mit eigenem Zahlensatz — damit auch als Gruppe A/B "
             "einsetzbar.")
    if ramped:
        zweck += (" Die Varianten sind aufsteigend geordnet: von leicht bis "
                  "anspruchsvoll.")
    intro: list = [InfoBlock(id="uebung.zweck", kind="callout", callout_role="note",
                             content=zweck)]
    # An MC master's framing talks about distractors; the open projection removes it along
    # with the options instead of leaving contradictory student-facing prose behind.
    open_projection = bool(
        mixer_profile and mixer_profile.offenheit
        and mixer_profile.offenheit.value == "offen"
    )
    if template.context_frame and not open_projection:
        intro.append(InfoBlock(id="uebung.rahmen", kind="prose",
                               content=template.context_frame))

    throughline = (
        f"Übungsreihe, kein didaktisch aufgebautes Arbeitsblatt: {'aufsteigende' if ramped else 'gleichwertige'} "
        f"Varianten derselben Aufgabenstellung"
        + (" (leicht → anspruchsvoll)" if ramped else "")
        + ", jede mit vollständigem Rechenweg in dieser Begleitung. Wert: "
        + ("die Schwierigkeitsrampe und " if ramped else "")
        + "der geprüfte Lösungsweg zu jedem eigenen Zahlensatz — einsetzbar zum "
          "Automatisieren, zur Schularbeit-Vorbereitung, im Stationenbetrieb oder als "
          "Gruppe A/B."
    )
    meta = WorksheetMeta(
        title=f"Übungsreihe: {title}", subtitle=subtitle, subject=template.subject,
        stufe=stufe, klasse=template.klasse,
        kernfrage=f"Übung: {title}", fassung=res.fassung,
        lehrplan_label=f"{template.subject} · {template.klasse}. Kl. · {template.kompetenzbereich}")
    # Textlast (P3): at the `einfach` endpoint SELECT the curated glossary onto the worksheet
    # (rendered as a student-facing Wortschatz-Kasten); `voll`/None carry no glossary.
    glossary = (list(template.glossary)
                if mixer_profile is not None and mixer_profile.textlast == Textlast.EINFACH
                else [])
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(template.subject, stufe),
        intro=intro,
        sections=[Baustein(id="uebung", title=title,
                           teacher_overview=TeacherOverview(throughline=throughline),
                           blocks=blocks)],
        assets=assets, mixer_profile=mixer_profile, mixer_lint=mixer_lint,
        glossary=glossary)
    return content, res
