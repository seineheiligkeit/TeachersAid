"""Hand-authored Biologie 'Immunsystem und Impfungen' (4. Kl.) content object.

A second 'great worksheet' alongside the Physik hero (demo/strahlung.py), this
time exercising the Naturwissenschaften W/E/S model for BIOLOGIE UND UMWELTBILDUNG.
The Klasse-4 Anwendungsbereich is verbatim: "Immunsystem und Impfungen, Viren,
Bakterien, Entstehung von Antibiotikaresistenzen/Mikroevolution". Biologie's
competences are cross-class (klasse=null), so resolve() matches the topic through
the Anwendungsbereiche and returns the full W/E/S competence set for the grade;
every `serves` below cites a real BIO.US.x.* id.

The through-line is the single most useful and most misunderstood idea in this
field: a pathogen is not a pathogen — viruses and bacteria are different kinds of
thing, and that difference dictates everything downstream (what the immune system
does, what a vaccine trains, why antibiotics help against the one and never the
other, and why misusing them breeds resistance by ordinary selection). It is
deliberately AI-resistance-friendly: the tasks ask students to apply a mechanism
to a fresh case, weigh a real public claim, and write for an audience — work that
collapses into nonsense if the underlying model isn't actually understood.

The sheet exercises W (WIS.01/03), E (ERK.04) and S (STA.01/02/03). It leaves the
E competences ERK.01/02/03 (observe/measure, hypothesise, plan-and-protocol)
largely to a sibling Baustein — deriveNachweis surfaces those as honest gaps, the
same way the Physik sheet leaves STR.01 uncovered by design.

Resulting schema §8 DepthProfile (reproduced exactly by the LLM-free slice):

    by_level:    understand 1, apply 2, analyze 2, evaluate 1, create 1
    by_dimension (primary): W 3, E 1, S 3
    minutes_total 84 · minutes_resource_independent 68   (t3 is equipment-gated)
"""

from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..schema.assets import Asset
from ..schema.blocks import ContentFlags, InfoBlock, TaskBlock
from ..schema.worksheet import (
    Baustein,
    BundleRequest,
    WorksheetContent,
    WorksheetMeta,
)


def build_request() -> BundleRequest:
    return BundleRequest(
        subject="Biologie",
        klasse=4,
        topic_raw="Immunsystem und Impfungen",
        envelope="doppelstunde",
    )


def build_assets() -> list[Asset]:
    # No figure is needed: the depth lives in the reasoning, not in a diagram, and
    # an over-tidy schematic of "the" immune response tends to mislead more than it
    # helps at this level. We keep the asset list empty by design.
    return []


def _intro() -> list:
    return [
        InfoBlock(
            id="imm.i1",
            kind="prose",
            content=(
                "Ständig treffen Krankheitserreger auf unseren Körper – und meistens "
                "merken wir nichts davon. Zwei sehr verschiedene Arten von Erregern "
                "sind dabei besonders wichtig: Viren und Bakterien. Sie werden oft in "
                "einen Topf geworfen, sind aber grundverschieden – und genau dieser "
                "Unterschied entscheidet, was hilft und was nicht."
            ),
        ),
        InfoBlock(
            id="imm.i2",
            kind="key_fact",
            content=(
                "Bakterien sind eigenständige Lebewesen (eigene Zelle, eigener "
                "Stoffwechsel). Viren sind keine Zellen: Sie können sich nur in einer "
                "Wirtszelle vermehren, die sie umprogrammieren. Antibiotika greifen "
                "an Strukturen bakterieller Zellen an – Viren haben diese Strukturen "
                "gar nicht. Deshalb wirken Antibiotika nie gegen Viren."
            ),
        ),
        InfoBlock(
            id="imm.i3",
            kind="prose",
            content=(
                "Das Immunsystem erkennt Erreger an ihren Oberflächen (Antigenen) und "
                "kann sich merken, wen es schon einmal bekämpft hat (Immungedächtnis). "
                "Eine Impfung nutzt genau dieses Gedächtnis: Sie zeigt dem Immunsystem "
                "harmlose Bruchstücke oder abgeschwächte Erreger, damit es übt – ohne "
                "dass man erst krank werden muss."
            ),
            watch_outs=[
                "'Immun' heißt nicht 'kann nie mehr krank werden': Der Schutz kann "
                "nachlassen, und Erreger können sich verändern. 'Geimpft' ≠ "
                "'für immer unverwundbar'.",
            ],
        ),
    ]


def _tasks() -> list[TaskBlock]:
    t1 = TaskBlock(  # W · understand · WIS.01 — the core conceptual split
        id="imm.t1",
        kind="open_response",
        prompt=(
            "Jemand mit einer normalen Erkältung (durch Viren ausgelöst) verlangt vom "
            "Arzt ein Antibiotikum. Erkläre in eigenen Worten, warum das Antibiotikum "
            "hier nicht helfen kann – und beziehe dich dabei auf den Unterschied "
            "zwischen Viren und Bakterien."
        ),
        response={"mode": "lines", "n": 4},
        cognitive_level="understand",
        dimensions=["W"],
        serves=[{"competence_id": "BIO.US.x.WIS.01", "relation": "exercises"}],
        est_minutes=8,
        answer_key=(
            "Antibiotika greifen Strukturen/Stoffwechsel bakterieller Zellen an (z. B. "
            "Zellwand). Viren sind keine Zellen und besitzen diese Angriffspunkte nicht; "
            "sie vermehren sich in körpereigenen Zellen. Daher kann ein Antibiotikum den "
            "Virus nicht treffen – gegen die Erkältung hilft das eigene Immunsystem."
        ),
        watch_outs=[
            "Häufiger Denkfehler: 'Antibiotikum = starkes Medikament gegen alles'. "
            "Würdige es, wenn der Angriffspunkt (Zelle vs. keine Zelle) genannt wird.",
        ],
    )
    t2 = TaskBlock(  # W · apply · WIS.03 — apply the immune-memory MODEL to a new case
        id="imm.t2",
        kind="open_response",
        prompt=(
            "Modell 'Immungedächtnis': Beim ersten Kontakt mit einem Erreger reagiert "
            "der Körper langsam; danach merkt er sich den Erreger und reagiert beim "
            "nächsten Mal schnell und stark. Erkläre mit diesem Modell, (a) warum eine "
            "Impfung schützt, obwohl man dabei nicht richtig krank wird, und (b) nenne "
            "EINE Grenze des Modells (etwas, das es NICHT erklärt)."
        ),
        response={"mode": "lines", "n": 5},
        cognitive_level="apply",
        dimensions=["W"],
        serves=[{"competence_id": "BIO.US.x.WIS.03", "relation": "exercises"}],
        est_minutes=11,
        acceptable_reasoning=(
            "(a) Die Impfung liefert harmlose Antigene → das Immunsystem bildet "
            "Gedächtniszellen, ohne die Krankheit zu durchlaufen; bei echtem Kontakt "
            "reagiert es dann schnell. (b) Sinnvolle Grenzen: erklärt nicht, warum "
            "der Schutz nachlässt / warum manche Erreger sich so verändern, dass das "
            "Gedächtnis nicht mehr passt / sagt nichts über Nebenwirkungen oder "
            "Unterschiede zwischen Erregern. Jede begründete Grenze zählt."
        ),
        watch_outs=[
            "Teil (b) ist der eigentliche Hebel (WIS.03 verlangt Gültigkeitsgrenzen): "
            "kein Modell erklärt alles. Eine genannte, plausible Grenze genügt.",
        ],
    )
    t3 = TaskBlock(  # E · apply · ERK.04 — interpret data; the ONLY equipment-gated task
        id="imm.t3",
        kind="data_interpretation",
        prompt=(
            "Im Schullabor habt ihr (vereinfacht) den Antikörper-Spiegel im Blut nach "
            "einer Impfung über die Zeit aufgenommen. Messwerte (relative Einheiten): "
            "Tag 0 → 1 · Tag 7 → 3 · Tag 14 → 9 · Tag 28 → 8 · nach Auffrischung an "
            "Tag 60 → 30. Beschreibe den Verlauf, benenne den Effekt der Auffrischung "
            "und erkläre, was die Werte über das Immungedächtnis aussagen."
        ),
        payload={"kind": "other", "data": {"messreihe": "AK-Titer relativ"}},
        response={"mode": "box", "min_height_mm": 55},
        cognitive_level="apply",
        dimensions=["E"],
        serves=[{"competence_id": "BIO.US.x.ERK.04", "relation": "exercises"}],
        est_minutes=16,
        flags=ContentFlags(equipment_dependent=True),
        answer_key=(
            "Erstkontakt: langsamer Anstieg (Tag 7–14), dann leichtes Absinken (Tag 28). "
            "Die Auffrischung führt zu einem viel höheren, schnelleren Anstieg (30) – "
            "Beleg für das Immungedächtnis: Der Körper 'kennt' das Antigen schon und "
            "reagiert kräftiger. Größenordnungen vergleichen, nicht Einzelwerte."
        ),
        watch_outs=[
            "🔬 Geräteabhängig: ohne Labor/Datensatz als Trockenübung mit den "
            "angegebenen Werten rechenbar. Auf die Form der Kurve achten, nicht auf "
            "absolute Zahlen.",
        ],
    )
    t4 = TaskBlock(  # S · analyze · STA.01 — naturwiss. vs. nicht-naturwiss. Argument
        id="imm.t4",
        kind="true_false_justify",
        prompt=(
            "Vier Aussagen aus einer Internetdiskussion über Impfungen. Entscheide "
            "jeweils, ob die Aussage naturwissenschaftlich überprüfbar ist oder nicht, "
            "und begründe kurz (es geht NICHT darum, ob sie dir gefällt)."
        ),
        payload={
            "kind": "true_false_justify",
            "statements": [
                "In einer Studie mit 10 000 Personen erkrankten Geimpfte seltener als "
                "Ungeimpfte.",
                "Impfen ist unnatürlich und deshalb falsch.",
                "Der Impfstoff enthält den Wirkstoff X in der Menge Y pro Dosis.",
                "Wer sich impfen lässt, vertraut der Pharmaindustrie blind.",
            ],
        },
        response={
            "mode": "table",
            "columns": ["Aussage", "überprüfbar? (ja/nein)", "Begründung"],
            "rows": 4,
        },
        cognitive_level="analyze",
        dimensions=["S", "W"],
        serves=[{"competence_id": "BIO.US.x.STA.01", "relation": "exercises"}],
        est_minutes=12,
        answer_key=(
            "1 ja (empirisch prüfbar: Daten, Häufigkeiten) · 2 nein ('unnatürlich → "
            "falsch' ist ein Werturteil/Naturalistischer Fehlschluss, nicht messbar) · "
            "3 ja (Menge ist messbar) · 4 nein (Unterstellung über Motive, kein "
            "naturwissenschaftlicher Satz)."
        ),
        watch_outs=[
            "Kernkompetenz STA.01: naturwissenschaftlich ≠ richtig. Eine Aussage kann "
            "prüfbar und falsch sein – oder unüberprüfbar und sympathisch. Trennen!",
        ],
    )
    t5 = TaskBlock(  # W · analyze · WIS.01 — resistance as selection (Mikroevolution)
        id="imm.t5",
        kind="open_response",
        prompt=(
            "In einem Krankenhaus tauchen plötzlich Bakterien auf, gegen die ein "
            "bestimmtes Antibiotikum kaum noch wirkt. Erkläre Schritt für Schritt, wie "
            "so eine Antibiotikaresistenz entsteht – verwende dabei die Begriffe "
            "'zufällige Veränderung (Mutation)', 'Selektion' und 'Vermehrung'. Warum "
            "ist das ein Beispiel für Evolution im Kleinen?"
        ),
        response={"mode": "lines", "n": 6},
        cognitive_level="analyze",
        dimensions=["W"],
        serves=[{"competence_id": "BIO.US.x.WIS.01", "relation": "exercises"}],
        est_minutes=12,
        acceptable_reasoning=(
            "In einer großen Bakterienpopulation gibt es durch zufällige Mutationen "
            "vereinzelt widerstandsfähige Zellen. Das Antibiotikum tötet die "
            "empfindlichen, die resistenten überleben (Selektion) und vermehren sich – "
            "die Population wird resistent. Das ist Mikroevolution: Variation + "
            "Selektion + Vermehrung verschieben die Häufigkeiten über Generationen. "
            "Wichtig: Das Antibiotikum 'macht' die Resistenz nicht, es wählt sie aus."
        ),
        watch_outs=[
            "Verbreiteter Fehler: 'Die Bakterien gewöhnen sich an / wollen überleben'. "
            "Genau hier ansetzen: die Variation ist VOR dem Antibiotikum da, das Mittel "
            "selektiert nur. Das ist der Kern von WIS.01 (Prinzipien in Beziehung setzen).",
        ],
    )
    t6 = TaskBlock(  # S · evaluate · STA.03 — handling recommendation (Stewardship)
        id="imm.t6",
        kind="decision_scenario",
        prompt=(
            "Ein Familienmitglied sagt: 'Mir geht es nach drei Tagen schon besser, "
            "ich höre mit dem Antibiotikum jetzt auf und hebe den Rest für das nächste "
            "Mal auf.' Beurteile beide Teile dieser Entscheidung fachlich und gib eine "
            "begründete Empfehlung. Verknüpfe deine Begründung mit dem, was du über "
            "Resistenzen weißt."
        ),
        payload={
            "kind": "decision_scenario",
            "stem": (
                "Antibiotika sollen laut ärztlicher Anweisung eingenommen werden; "
                "Resistenzen entstehen durch Selektion überlebender Bakterien."
            ),
        },
        response={"mode": "lines", "n": 5},
        cognitive_level="evaluate",
        dimensions=["S"],
        serves=[{"competence_id": "BIO.US.x.STA.03", "relation": "exercises"}],
        est_minutes=11,
        acceptable_reasoning=(
            "Vorzeitiges Absetzen kann überlebende, weniger empfindliche Bakterien "
            "begünstigen → fördert Resistenzen; daher Einnahme nach ärztlicher "
            "Anweisung. Reste aufheben und selbst 'beim nächsten Mal' nehmen ist "
            "fachlich nicht haltbar (anderer Erreger? falsches Mittel? abgelaufen?). "
            "Empfehlung: nach Anweisung zu Ende nehmen, Reste fachgerecht entsorgen, "
            "im Zweifel Arzt/Apotheke fragen. (Hinweis: Die Frage der optimalen "
            "Therapiedauer ist fachlich differenziert – die Kernaussage 'nicht "
            "eigenmächtig steuern' bleibt.)"
        ),
        watch_outs=[
            "STA.03 will eine begründete Handlungsempfehlung, nicht nur 'ist schlecht'. "
            "Auf die Brücke zur Resistenz (Selektion) achten; ausgewogen bleiben.",
        ],
    )
    t7 = TaskBlock(  # S · create · STA.02 — balanced text on a bioethics/health controversy
        id="imm.t7",
        kind="create_produce",
        prompt=(
            "Eine Schülerzeitung diskutiert: 'Sollte es für bestimmte Berufe (z. B. in "
            "Krankenhäusern) eine Impfpflicht geben?' Schreibe einen kurzen, sachlichen "
            "Text (6–8 Sätze), der MINDESTENS ein Argument dafür UND ein Argument "
            "dagegen fair darstellt (z. B. Schutz besonders gefährdeter Patient:innen "
            "vs. Recht auf körperliche Selbstbestimmung) und am Ende deinen eigenen, "
            "begründeten Standpunkt nennt."
        ),
        response={"mode": "box", "min_height_mm": 65},
        cognitive_level="create",
        dimensions=["S"],
        serves=[{"competence_id": "BIO.US.x.STA.02", "relation": "exercises"}],
        est_minutes=14,
        acceptable_reasoning=(
            "Erwartet wird ein abgewogener Text: je ein fair formuliertes Argument pro "
            "(z. B. Fremdschutz, Gemeinschaftsschutz/Herdenimmunität) und contra "
            "(Selbstbestimmung, Verhältnismäßigkeit, Vertrauen), klar von der eigenen "
            "begründeten Position getrennt. Bewertet wird die Fairness der Darstellung "
            "und die Qualität der Begründung, NICHT welche Position bezogen wird."
        ),
        watch_outs=[
            "STA.02 verlangt kontroverse Gesichtspunkte: ein Text, der nur eine Seite "
            "darstellt, verfehlt die Kompetenz – auch wenn die Meinung 'richtig' ist.",
        ],
    )
    return [t1, t2, t3, t4, t5, t6, t7]


def build_content() -> WorksheetContent:
    model = store.get_subject_model("Biologie")
    fassung = store.get_fassung()
    meta = WorksheetMeta(
        title="Immunsystem und Impfungen",
        subtitle="Viren, Bakterien, Antibiotikaresistenzen – warum der Unterschied alles ändert",
        subject="Biologie",
        stufe="Unterstufe",
        klasse=4,
        kernfrage="Was hilft gegen einen Erreger – und warum hilft es manchmal gerade nicht?",
        fassung=fassung,
        lehrplan_label="Biologie und Umweltbildung · 4. Klasse · Immunsystem und Impfungen",
    )
    section = Baustein(
        id="imm.kern",
        title="Viren ≠ Bakterien",
        teacher_overview={
            "throughline": (
                "Erregertyp entscheidet über Wirkung; Resistenz ist gewöhnliche "
                "Selektion, kein 'Gewöhnen'."
            ),
            "talking_points": [
                "Warum hilft ein Antibiotikum bei einer (viralen) Erkältung nicht? Am "
                "Unterschied Virus/Bakterium festmachen, nicht auswendig lernen lassen.",
                "Resistenz: Bakterien 'gewöhnen sich' NICHT an — die zufällig "
                "resistenten überleben und vermehren sich. Diese Fehlvorstellung gezielt "
                "ansprechen.",
                "Impfung trainiert das Gedächtnis ohne die Krankheit; die Auffrischung "
                "hebt den Antikörperspiegel (Anschluss an die Datenaufgabe t3).",
            ],
            "extensions": [
                "Antibiotikaresistenz als Gesundheitsthema (ÜT): warum unnötige "
                "Einnahme auch der Allgemeinheit schadet.",
                "Datenaufgabe t3 vertiefen: eine zweite Auffrischung modellieren und das "
                "Absinken des Antikörperspiegels zwischen den Impfungen deuten.",
            ],
            "timing_notes": (
                "Doppelstunde; Datenaufgabe (t3) geräteabhängig, als Trockenübung mit "
                "den angegebenen Werten möglich."
            ),
            "differentiation": (
                "Leistungsstarke: t5 (Mikroevolution) und t7 (Standpunkt) vertiefen; "
                "Basis: t1/t2 sichern den Viren-Bakterien-Unterschied zuerst ab."
            ),
        },
        blocks=_tasks(),
    )
    return WorksheetContent(
        meta=meta,
        subject_model=model,
        intro=_intro(),
        sections=[section],
        assets=build_assets(),
    )
