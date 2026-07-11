"""Hand-authored Physik 'Mondphasen und der Lauf des Himmels' (2. Kl.).

The competence-anchored companion to the Sternenhimmel Horizont flagship: where the
star chart is teacher-choice enrichment (Horizont), THIS sheet lands squarely on a
verbatim Lehrplan competence —

  PHY.US.2.SEH.04 (Kompetenzbereich „Sehen und Hören", Dimension E):
  „die Entstehung von Tag und Nacht, Jahreszeiten und Mondphasen durch
   Bewegungsabläufe und Beleuchtungsverhältnisse in unserem Sonnensystem
   szenisch oder mit Modellen darstellen."

The through-line is the one idea that dissolves every naïve moon misconception at
once: **the Moon never changes shape — we always see the same sunlit half-sphere,
just from different angles.** From there day/night (Erdrotation) and the seasons
(Achsneigung, NOT distance — the Earth is actually *closest* to the Sun in January!)
fall out of the same Sonne–Erde–Mond geometry. Every phase figure is COMPUTED by the
`matplotlib:moon_phase` recipe (`pipeline/astro`) with the illuminated fraction given
exactly and the terminator drawn correctly; the task figures are MASKED (show_label
False → "?") so "welche Mondphase ist das?" never prints its own answer.

The sheet exercises SEH.04 (t1–t4) and reaches once into SEH.03 (Lichtausbreitung —
the Moon shines by *reflected* sunlight, t5). SEH.01/02/05 (Sehbedingungen, sicherer
Umgang mit Licht/Schall, Farbe) are left to sibling Bausteine — `derive_nachweis`
surfaces them as honest gaps, exactly as the Physik hero leaves STR.01 uncovered.
"""
from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..schema.assets import Asset
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.worksheet import Baustein, BundleRequest, WorksheetContent, WorksheetMeta

SUBJECT = "Physik"
KLASSE = 2
KOMPETENZBEREICH = "Sehen und Hören"


def build_request() -> BundleRequest:
    return BundleRequest(subject=SUBJECT, klasse=KLASSE, topic_raw="Mondphasen",
                         envelope="doppelstunde")


def _moon(aid: str, frac: float, waxing: bool, title: str, *, show_label: bool) -> Asset:
    return Asset(
        id=aid, role="figure", generator="matplotlib:moon_phase",
        spec={"illuminated_fraction": frac, "waxing": waxing, "title": title,
              "show_label": show_label},
    )


def build_assets() -> list[Asset]:
    # one labelled example (introduces „zunehmend = rechts beleuchtet") + the masked task
    # figures. All COMPUTED (illuminated fraction given exactly; terminator drawn correctly).
    return [
        _moon("mp-beispiel", 0.62, True, "Beispiel", show_label=True),
        _moon("mp-t1", 0.24, True, "Der Mond am Abend", show_label=False),
        _moon("mp-a", 0.16, True, "A", show_label=False),
        _moon("mp-b", 1.0, True, "B", show_label=False),
        _moon("mp-c", 0.5, False, "C", show_label=False),
    ]


def _intro() -> list:
    return [
        InfoBlock(
            id="mp.i1", kind="prose",
            content=(
                "Der Mond scheint jede Woche anders auszusehen – mal eine schmale "
                "Sichel, mal rund, mal eine Hälfte. Trotzdem verändert der Mond seine "
                "Form nie. Wir sehen immer dieselbe Kugel – nur unterschiedlich viel "
                "von ihrer beleuchteten Hälfte."
            ),
        ),
        InfoBlock(
            id="mp.i2", kind="key_fact",
            content=(
                "Der Mond leuchtet nicht selbst. Die Sonne beleuchtet immer genau die "
                "eine Hälfte des Mondes – so wie sie auch immer eine Hälfte der Erde "
                "beleuchtet. Wie viel von dieser hellen Hälfte wir von der Erde aus "
                "sehen, hängt davon ab, wo der Mond gerade auf seiner Bahn steht. Das "
                "ergibt die Mondphasen."
            ),
        ),
        InfoBlock(
            id="mp.i3", kind="figure", asset_refs=["mp-beispiel"],
            content=(
                "Ein zunehmender Mond: Auf der Nordhalbkugel ist der Mond rechts "
                "beleuchtet, wenn er zunimmt (die helle Fläche wird von Abend zu Abend "
                "größer). Nimmt er ab, ist die linke Seite hell."
            ),
            watch_outs=[
                "Zunehmend = rechts beleuchtet gilt für die Nordhalbkugel (also auch "
                "für Österreich); auf der Südhalbkugel ist es umgekehrt. Am besten nicht "
                "als Merkspruch, sondern physikalisch begründen: die helle Seite zeigt "
                "immer zur Sonne.",
            ],
        ),
    ]


def _tasks() -> list[TaskBlock]:
    t1 = TaskBlock(  # E · understand · SEH.04 — read the geometry off one phase
        id="mp.t1", kind="open_response",
        prompt=(
            "Sieh dir das Mondbild an. (a) Auf welcher Seite ist der Mond beleuchtet? "
            "(b) In welche Richtung steht also die Sonne von diesem Mond aus gesehen? "
            "(c) Nimmt der Mond zu oder ab? Begründe kurz."
        ),
        asset_refs=["mp-t1"],
        response={"mode": "lines", "n": 4},
        cognitive_level="understand", dimensions=["E"],
        serves=[{"competence_id": "PHY.US.2.SEH.04", "relation": "exercises"}],
        est_minutes=8,
        answer_key=(
            "(a) Rechts. (b) Die beleuchtete Seite zeigt immer zur Sonne – die Sonne "
            "steht also rechts (nach Sonnenuntergang im Westen). (c) Zunehmend: auf der "
            "Nordhalbkugel ist ein rechts beleuchteter Mond ein zunehmender Mond."
        ),
        watch_outs=[
            "Kernidee (SEH.04): die helle Seite zeigt zur Sonne – daraus lässt sich die "
            "Sonnenrichtung ABLESEN. „Rechts hell → zunehmend“ nur auf der Nordhalbkugel.",
        ],
    )
    t2 = TaskBlock(  # E · apply · SEH.04 — the core „mit Modellen darstellen"
        id="mp.t2", kind="open_response",
        prompt=(
            "Die drei Mondbilder A, B und C zeigen verschiedene Phasen. (1) Bringe sie "
            "in die richtige Reihenfolge von kurz nach Neumond bis kurz vor dem nächsten "
            "Neumond. (2) Schreibe zu jedem Bild den Namen der Phase. (3) Gib an, ob der "
            "Mond dabei zu- oder abnimmt."
        ),
        asset_refs=["mp-a", "mp-b", "mp-c"],
        response={"mode": "table",
                  "columns": ["Reihenfolge (1–3)", "Bild (A/B/C)", "Name der Phase",
                              "zu-/abnehmend"],
                  "rows": 3},
        cognitive_level="apply", dimensions=["E"],
        serves=[{"competence_id": "PHY.US.2.SEH.04", "relation": "exercises"}],
        est_minutes=12,
        answer_key=(
            "Reihenfolge A → B → C. "
            "A: zunehmende Sichel (schmal, rechts hell) – zunehmend. "
            "B: Vollmond (ganz hell) – der Wendepunkt. "
            "C: letztes Viertel (linke Hälfte hell) – abnehmend. "
            "Begründung der Reihenfolge: nach Neumond wird die helle (rechte) Fläche "
            "größer bis zum Vollmond, danach wird sie von rechts her wieder kleiner – "
            "jetzt ist die linke Seite hell."
        ),
        watch_outs=[
            "Das ist der Kern von SEH.04 („mit Modellen darstellen“): nicht auswendig, "
            "sondern an der hellen Seite ablesen. Verwechslung erstes/letztes Viertel: "
            "rechts hell = zunehmend (erstes Viertel), links hell = abnehmend (letztes).",
        ],
    )
    t3 = TaskBlock(  # E · apply · SEH.04 — day/night with a lamp-and-ball model
        id="mp.t3", kind="open_response",
        prompt=(
            "Modell für Tag und Nacht: eine Lampe ist die Sonne, ein Ball (oder Globus) "
            "die Erde. (a) Erkläre mit diesem Modell, warum es auf der Erde gleichzeitig "
            "Tag und Nacht gibt. (b) Ein Kind sagt: „Nachts ist die Sonne weg – sie "
            "fährt fort.“ Was stimmt daran physikalisch nicht?"
        ),
        response={"mode": "lines", "n": 5},
        cognitive_level="apply", dimensions=["E"],
        serves=[{"competence_id": "PHY.US.2.SEH.04", "relation": "exercises"}],
        est_minutes=10,
        answer_key=(
            "(a) Die Lampe beleuchtet immer nur eine Hälfte des Balls: dort ist Tag, auf "
            "der abgewandten Hälfte Nacht. Weil sich die Erde einmal am Tag um sich "
            "selbst dreht, wandert jeder Ort abwechselnd in die helle und die dunkle "
            "Hälfte. (b) Die Sonne fährt nicht weg – die ERDE dreht sich weg. Für uns "
            "sieht es nur so aus, als ob die Sonne auf- und untergeht."
        ),
        watch_outs=[
            "Häufige Alltagsvorstellung: „die Sonne geht weg / kreist um die Erde“. Am "
            "Modell festmachen: es dreht sich die Erde, nicht die Sonne (SEH.04, "
            "Bewegungsabläufe).",
        ],
    )
    t4 = TaskBlock(  # E · analyze · SEH.04 — seasons: the tilt, not the distance
        id="mp.t4", kind="multiple_choice",
        prompt=(
            "Warum ist es bei uns im Sommer wärmer als im Winter? Kreuze die richtige "
            "Erklärung an und begründe sie in einem Satz. Tipp zum Nachdenken: Auf der "
            "Nordhalbkugel ist die Erde der Sonne im Jänner (Winter!) sogar am nächsten."
        ),
        payload={
            "kind": "multiple_choice",
            "options": [
                "Weil die Erde im Sommer näher an der Sonne ist als im Winter.",
                "Weil die Erdachse geneigt ist: im Sommer steht die Sonne höher am "
                "Himmel und scheint länger – die Wärme verteilt sich auf weniger Fläche.",
                "Weil die Sonne im Sommer heißer brennt als im Winter.",
            ],
            "select": "one",
        },
        response={"mode": "lines", "n": 3},
        cognitive_level="analyze", dimensions=["E"],
        serves=[{"competence_id": "PHY.US.2.SEH.04", "relation": "exercises"}],
        est_minutes=10,
        answer_key=(
            "Richtig ist die zweite Aussage. Begründung: Die geneigte Erdachse sorgt "
            "dafür, dass die Sonne im Sommer höher steht (die Strahlen treffen steiler "
            "auf und verteilen sich auf eine kleinere Fläche) und länger scheint. Der "
            "Abstand Erde–Sonne ist NICHT der Grund – sonst müssten Nord- und "
            "Südhalbkugel gleichzeitig Sommer haben, und die Erde ist im Jänner am "
            "nächsten."
        ),
        watch_outs=[
            "Die verbreitetste Fehlvorstellung überhaupt (Aussage 1). Der Jänner-"
            "Näheste-Punkt (Perihel) ist der Konter: der Abstand kann es nicht sein. "
            "Kern: Achsneigung → Sonnenhöhe + Tageslänge (SEH.04, Jahreszeiten).",
        ],
    )
    t5 = TaskBlock(  # W · evaluate · SEH.03 — the Moon shines by reflected light
        id="mp.t5", kind="open_response",
        prompt=(
            "Behauptung: „Der Mond leuchtet selbst, so wie eine Lampe.“ Stimmt das? "
            "Begründe mit dem, was du über Licht und über die Mondphasen weißt – und "
            "erkläre, warum es gerade die Phasen sind, die die Behauptung widerlegen."
        ),
        response={"mode": "lines", "n": 5},
        cognitive_level="evaluate", dimensions=["W"],
        serves=[{"competence_id": "PHY.US.2.SEH.03", "relation": "exercises"}],
        est_minutes=8,
        acceptable_reasoning=(
            "Nein. Der Mond leuchtet nicht selbst, er wirft Sonnenlicht zurück (wir "
            "sehen ihn wie alle nicht-selbstleuchtenden Körper durch reflektiertes "
            "Licht). Gerade die Phasen sind der Beweis: Würde der Mond selbst leuchten, "
            "sähen wir immer die ganze runde Scheibe. Weil aber die Sonne nur eine "
            "Hälfte beleuchtet und wir je nach Stellung mehr oder weniger davon sehen, "
            "wechseln die Phasen."
        ),
        watch_outs=[
            "Brücke zu SEH.03 (Lichtausbreitung/Reflexion): wir sehen den Mond durch "
            "REFLEKTIERTES Sonnenlicht. Das Phasen-Argument ist der eigentliche Hebel – "
            "Selbstleuchten würde eine immer gleich runde Scheibe bedeuten.",
        ],
    )
    return [t1, t2, t3, t4, t5]


def build_content() -> WorksheetContent:
    model = store.get_subject_model(SUBJECT, "Unterstufe")
    fassung = store.get_fassung()
    meta = WorksheetMeta(
        title="Mondphasen und der Lauf des Himmels",
        subtitle="Warum der Mond sein Gesicht wechselt – und die Erde Tag, Nacht und "
                 "Jahreszeiten macht",
        subject=SUBJECT, stufe="Unterstufe", klasse=KLASSE,
        kernfrage="Der Mond verändert nie seine Form – warum sieht er dann jede Woche "
                  "anders aus?",
        fassung=fassung,
        lehrplan_label="Physik · 2. Klasse · Sehen und Hören (Mondphasen, Tag/Nacht, "
                       "Jahreszeiten)",
    )
    section = Baustein(
        id="mp.kern",
        title="Sonne, Erde, Mond – ein Modell erklärt den Himmel",
        teacher_overview={
            "throughline": (
                "Der Mond ändert nie seine Form; wir sehen nur verschieden viel seiner "
                "immer gleich beleuchteten Hälfte. Dieselbe Sonne-Erde-Mond-Geometrie "
                "erklärt Phasen, Tag/Nacht und Jahreszeiten."
            ),
            "talking_points": [
                "Zuerst die Kernidee sichern (i2): der Mond leuchtet nicht selbst, die "
                "Sonne beleuchtet immer eine Hälfte. Erst dann Phasen benennen.",
                "„Rechts hell = zunehmend“ nicht auswendig lernen lassen – an der "
                "Sonnenrichtung ablesen (t1).",
                "Jahreszeiten (t4): den Abstand-Irrtum gezielt mit dem Jänner-Perihel "
                "kontern. Achsneigung → Sonnenhöhe + Tageslänge.",
                "Am besten enaktiv: Taschenlampe + Styroporkugel im abgedunkelten Raum – "
                "die Phasen entstehen live (SEH.04 „szenisch/mit Modellen darstellen“).",
            ],
            "extensions": [
                "Warum sehen wir bei Neumond den Mond gar nicht? (Die beleuchtete Seite "
                "zeigt von uns weg – nicht, weil die Erde den Schatten wirft.)",
                "Finsternisse abgrenzen: eine Mondfinsternis ist NICHT dasselbe wie "
                "Neumond – der Erdschatten fällt nur selten genau auf den Mond.",
                "Anschluss an die Sternkarte (Horizont-Blatt „Sternenhimmel über Wien“): "
                "wo steht der Mond heute Abend?",
            ],
            "differentiation": (
                "Basis: t1–t3 mit dem Lampe-Ball-Modell handgreiflich sichern. "
                "Weiterführend: t4 (Jahreszeiten) und t5 (Selbstleuchten-Widerlegung "
                "über die Phasen) verlangen echtes Durchdenken des Modells."
            ),
            "timing_notes": (
                "Doppelstunde; das Verdunkeln des Raums für das Lampe-Kugel-Modell lohnt "
                "sich – t2 fällt danach fast von selbst."
            ),
        },
        blocks=_tasks(),
    )
    return WorksheetContent(
        meta=meta, subject_model=model, intro=_intro(), sections=[section],
        assets=build_assets(),
    )
