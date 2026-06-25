"""The three worked examples (worked-examples-three.md), hand-authored at the
content-object level to exercise the v0.4 deltas end-to-end:

* English listening — an oral `speaking_task` that must be ABSENT from the printed
  student sheet; an audio asset that is `machine_generatable=False` (sourced).
* "Geschönte Kurve" (Physik × Math) — cross-curricular `subject_models` (B5) and
  an `intentionally_flawed` truncated-axis graph (B3) the pipeline must NOT fix,
  with the honest graph teacher-only.
* Math "unfair game" — a `create`/modelling task with a `rubric` (A4) and an
  `artifact`/box response.
"""

from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..schema.assets import Asset, AssetProvenance, IntentionallyFlawed
from ..schema.blocks import ContentFlags, InfoBlock, RubricCriterion, TaskBlock
from ..schema.competence import CompetenceDimension, SubjectCompetenceModel
from ..schema.worksheet import (
    Baustein,
    SubjectCompetenceModelRef,
    WorksheetContent,
    WorksheetMeta,
)

_FASSUNG = None


def _fassung():
    global _FASSUNG
    if _FASSUNG is None:
        _FASSUNG = store.get_fassung()
    return _FASSUNG


# --- 1) English listening ----------------------------------------------------
_ENGLISH_MODEL = SubjectCompetenceModel(
    subject="Lebende Fremdsprache (Englisch)",
    stufe="Unterstufe",
    dimensions=[
        CompetenceDimension(id="hoeren", label="Hören", modality="oral"),
        CompetenceDimension(id="lesen", label="Lesen", modality="printable"),
        CompetenceDimension(id="sprechen", label="Sprechen", modality="oral"),
        CompetenceDimension(id="schreiben", label="Schreiben", modality="printable"),
    ],
    task_kind_extensions=["listening_task", "speaking_task", "text_production"],
)


def build_english() -> WorksheetContent:
    meta = WorksheetMeta(
        title="Listening: a historic speech",
        subject="Lebende Fremdsprache (Englisch)",
        stufe="Unterstufe",
        klasse=4,
        kernfrage="What makes a speech persuasive?",
        fassung=_fassung(),
        lehrplan_label="Englisch · 4. Klasse · Hören & Sprechen",
        content_language="en",
    )
    audio = Asset(
        id="speech_audio",
        role="recording",
        medium="audio",
        machine_generatable=False,  # real historic speech — never synthesise
        provenance=AssetProvenance(source="public archive recording", rights="public_domain"),
        caption="Audio is sourced, not machine-generated.",
    )
    intro = [
        InfoBlock(
            id="en.audio",
            kind="data_reference",
            asset_refs=["speech_audio"],
            content="Listen to the recording twice before answering.",
            teacher_note="Play the sourced audio (public domain); do not use TTS.",
        ),
    ]
    listen = TaskBlock(  # printable comprehension
        id="en.t1",
        kind="listening_task",
        prompt="While listening, note TWO reasons the speaker gives for their claim.",
        response={"mode": "lines", "n": 2},
        cognitive_level="understand",
        dimensions=["hoeren"],
        est_minutes=8,
        answer_key="Any two reasons actually stated in the recording.",
    )
    speak = TaskBlock(  # ORAL — must not appear on the printed student sheet
        id="en.t2",
        kind="speaking_task",
        modality="oral",
        prompt="In pairs, summarise the speech in 4–5 sentences and say whether it convinced you.",
        response={"mode": "none"},
        cognitive_level="evaluate",
        dimensions=["sprechen"],
        est_minutes=10,
        acceptable_reasoning="A coherent oral summary + a justified stance.",
        watch_outs=["Oral task — assess live; it is not part of the printed sheet."],
    )
    section = Baustein(
        id="en.s",
        title="Listen, then respond",
        teacher_overview={"throughline": "Comprehension on paper; evaluation out loud."},
        blocks=[listen, speak],
    )
    return WorksheetContent(
        meta=meta, subject_model=_ENGLISH_MODEL, intro=intro, sections=[section],
        assets=[audio],
    )


# --- 2) Geschönte Kurve (Physik × Math) -------------------------------------
_CROSS_MODEL = SubjectCompetenceModel(
    subject="Physik × Mathematik",
    stufe="Unterstufe",
    dimensions=[
        CompetenceDimension(id="S", label="Standpunkte bewerten (Physik)"),
        CompetenceDimension(id="darstellen", label="Darstellen und Interpretieren (Math)"),
        CompetenceDimension(id="begruenden", label="Vermuten und Begründen (Math)"),
    ],
    task_kind_extensions=["source_critique", "data_interpretation"],
)


def build_geschoente_kurve() -> WorksheetContent:
    meta = WorksheetMeta(
        title="Die geschönte Kurve",
        subject="Physik × Mathematik",
        stufe="Unterstufe",
        klasse=4,
        kernfrage="Wann täuscht eine Grafik – obwohl die Zahlen stimmen?",
        fassung=_fassung(),
        lehrplan_label="Physik × Mathematik · 4. Klasse · Daten kritisch lesen",
        subject_models=[  # B5: cite BOTH subjects' models, primary first
            SubjectCompetenceModelRef(ref="Physik"),
            SubjectCompetenceModelRef(ref="Mathematik"),
        ],
    )
    flawed = Asset(
        id="trick_graph",
        role="figure",
        generator="matplotlib:truncated_axis",
        intentionally_flawed=IntentionallyFlawed(
            what="y-Achse abgeschnitten (startet bei 100,5) — übertreibt den Anstieg. "
            "Muss falsch bleiben: die Aufgabe ist, die Manipulation zu erkennen."
        ),
        caption="Eine echte, aber manipulativ skalierte Grafik.",
    )
    honest = Asset(
        id="honest_graph",
        role="figure",
        generator="matplotlib:honest_axis",
        correctness_surface="Nullbasierte Achse — zeigt den tatsächlich kleinen Effekt.",
        caption="Dieselben Daten, ehrliche Achse (nur Lehrkraft).",
    )
    intro = [
        InfoBlock(
            id="gk.fig",
            kind="figure",
            asset_refs=["trick_graph"],
            content="Studiere die Grafik. Wirkt der Anstieg dramatisch?",
        ),
        InfoBlock(  # teacher-only honest comparison (oral modality → dropped for students)
            id="gk.honest",
            kind="figure",
            modality="oral",
            asset_refs=["honest_graph"],
            content="Vergleichsgrafik mit ehrlicher Achse.",
            teacher_note="Erst nach der Schülerkritik zeigen.",
        ),
    ]
    critique = TaskBlock(
        id="gk.t1",
        kind="source_critique",
        prompt="Die Zahlen in der Grafik stimmen. Trotzdem täuscht sie. Erkläre, wodurch.",
        response={"mode": "lines", "n": 3},
        cognitive_level="analyze",
        dimensions=["darstellen", "S"],
        serves=[
            {"competence_id": "PHY.US.4.STR.02", "relation": "exercises"},
            {"competence_id": "MA.US.4.DATEN.x", "relation": "exercises"},
        ],
        est_minutes=8,
        acceptable_reasoning=(
            "Die y-Achse ist abgeschnitten; ein winziger Unterschied sieht riesig aus. "
            "Mathematisch: relative Änderung ist klein."
        ),
        watch_outs=[
            "Zentrale Falle: 'die Grafik ist manipulativ' ≠ 'das Thema ist falsch'. "
            "SuS dürfen nicht als Klimaskeptiker hinausgehen.",
        ],
    )
    redraw = TaskBlock(
        id="gk.t2",
        kind="data_interpretation",
        prompt="Skizziere, wie eine ehrliche Version derselben Grafik aussehen müsste.",
        response={"mode": "drawing", "guide": "Achse bei 0 beginnen"},
        cognitive_level="evaluate",
        dimensions=["begruenden"],
        serves=[{"competence_id": "MA.US.4.DATEN.x", "relation": "exercises"}],
        est_minutes=7,
    )
    section = Baustein(
        id="gk.s",
        title="Wahre Zahlen, falscher Eindruck",
        teacher_overview={"throughline": "Darstellung kann täuschen, ohne zu lügen."},
        blocks=[critique, redraw],
    )
    return WorksheetContent(
        meta=meta, subject_model=_CROSS_MODEL, intro=intro, sections=[section],
        assets=[flawed, honest],
    )


# --- 3) Math "unfair game" ---------------------------------------------------
def build_math_unfair_game() -> WorksheetContent:
    math = store.get_subject_model("Mathematik")
    meta = WorksheetMeta(
        title="Das unfaire Spiel",
        subject="Mathematik",
        stufe="Unterstufe",
        klasse=4,
        kernfrage="Wann ist ein Glücksspiel fair?",
        fassung=_fassung(),
        lehrplan_label="Mathematik · 4. Klasse · Daten und Zufall",
    )
    design = TaskBlock(
        id="ug.t1",
        kind="modelling_task",
        prompt=(
            "Erfinde ein einfaches Würfel- oder Münzspiel für zwei Personen, das auf "
            "den ersten Blick fair wirkt, in Wahrheit aber eine Person bevorzugt. "
            "Beschreibe die Regeln und begründe mit Wahrscheinlichkeiten, warum es unfair ist."
        ),
        response={"mode": "artifact", "produces": "Spielregeln + Begründung"},
        cognitive_level="create",
        dimensions=["MOD", "BEG"],  # catalog dimension codes (Modellieren / Begründen)
        content_area="Daten und Zufall",
        serves=[{"competence_id": "MAT.US.4.DAT.02", "relation": "exercises"}],
        est_minutes=20,
        rubric=[
            RubricCriterion(
                criterion="Regeln klar",
                levels=["unklar", "teilweise klar", "klar & vollständig"],
            ),
            RubricCriterion(
                criterion="Begründung mit Wahrscheinlichkeit",
                levels=["fehlt", "ansatzweise", "korrekt quantifiziert"],
            ),
        ],
        flags=ContentFlags(),
        acceptable_reasoning="Jedes Spiel mit korrekt berechneter ungleicher Gewinnchance.",
    )
    section = Baustein(
        id="ug.s",
        title="Fairness messen",
        teacher_overview={
            "throughline": "Fairness ist eine Frage der Wahrscheinlichkeit.",
            "talking_points": [
                "Fair heißt gleiche Gewinnchance, nicht 'gleiche Regeln' — symmetrische "
                "Regeln können trotzdem unfair sein.",
                "Wahrscheinlichkeit quantifizieren statt 'gefühlt fair': günstige/mögliche "
                "Fälle abzählen (Laplace) oder das Spiel simulieren.",
                "Auf lange Sicht denken: Wer gewinnt über viele Spiele häufiger? "
                "Häufigkeit statt Einzelausgang.",
            ],
            "extensions": [
                "Spiele tauschen und gegenseitig die Unfairness aufdecken und "
                "quantifizieren lassen (Peer-Review der Wahrscheinlichkeiten).",
                "Simulation: das Spiel viele Male würfeln und die relative Häufigkeit mit "
                "der berechneten Wahrscheinlichkeit vergleichen (Gesetz der großen Zahlen).",
            ],
            "differentiation": (
                "Basis: ein vorgegebenes einfaches Spiel analysieren (z. B. Summe zweier "
                "Würfel gerade/ungerade). Leistungsstarke: ein eigenes Spiel mit "
                "nicht-offensichtlicher Unfairness entwerfen und begründen."
            ),
        },
        blocks=[design],
    )
    return WorksheetContent(
        meta=meta, subject_model=math, intro=[], sections=[section], assets=[]
    )


ALL = {
    "english": build_english,
    "geschoente_kurve": build_geschoente_kurve,
    "math_unfair_game": build_math_unfair_game,
}
