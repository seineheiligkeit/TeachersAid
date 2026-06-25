"""Hand-authored Physik 'Strahlung und Radioaktivität' (4. Kl.) content object.

This is the MINT hero, authored at the content-object level so the LLM-free slice
(M3) can render student/teacher/homework projections and reproduce the schema §8
DepthProfile exactly:

    by_level:    understand 1, apply 1, analyze 2, evaluate 2, create 1
    by_dimension (primary): W 2, S 4, E 1
    minutes_total 78 · minutes_resource_independent 56

deriveNachweis flags PHY.US.4.STR.01 ("… Quellen bewerten") as UNCOVERED — the
sheet exercises STR.02/03/04 but deliberately leaves STR.01's S-component to a
sibling Baustein, exactly as in the design.
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
        subject="Physik",
        klasse=4,
        topic_raw="Strahlung und Radioaktivität",
        envelope="doppelstunde",
    )


def build_assets() -> list[Asset]:
    return [
        Asset(
            id="em_spectrum",
            role="figure",
            generator="matplotlib:em_spectrum",
            correctness_surface="Energie steigt streng monoton; Ionisierungsschwelle markiert.",
            misleading_in_isolation=True,  # can imply 'UV = nicht-ionisierend = harmlos'
            caption="Das elektromagnetische Spektrum, nach Energie geordnet.",
        )
    ]


def _intro() -> list:
    return [
        InfoBlock(
            id="str.i1",
            kind="prose",
            content=(
                "Strahlung umgibt uns ständig – Licht, Wärme, Funksignale, kosmische "
                "Strahlung. Aber nicht jede Strahlung ist gefährlich. Was entscheidet?"
            ),
        ),
        InfoBlock(
            id="str.i2",
            kind="figure",
            asset_refs=["em_spectrum"],
            content="Das elektromagnetische Spektrum, geordnet nach Energie.",
            watch_outs=[
                "Die Grafik kann den Eindruck erwecken, alles links der Schwelle sei "
                "harmlos. UV ist nicht-ionisierend (an der Grenze), schädigt aber Zellen "
                "— 'nicht-ionisierend' ≠ 'harmlos'.",
            ],
        ),
        InfoBlock(
            id="str.i3",
            kind="key_fact",
            content=(
                "Entscheidend ist die Energie, nicht die Durchdringung: erst ab hoher "
                "Energie kann Strahlung Atome verändern (ionisieren)."
            ),
        ),
    ]


def _tasks() -> list[TaskBlock]:
    t1 = TaskBlock(  # W · understand · STR.03
        id="str.t1",
        kind="open_response",
        prompt=(
            "Beim radioaktiven Zerfall kann man für ein einzelnes Atom nicht sagen, "
            "wann es zerfällt – für sehr viele Atome aber sehr genau, wie viele pro "
            "Sekunde zerfallen. Erkläre, warum das kein Widerspruch ist."
        ),
        response={"mode": "lines", "n": 3},
        cognitive_level="understand",
        dimensions=["W"],
        serves=[{"competence_id": "PHY.US.4.STR.03", "relation": "exercises"}],
        est_minutes=8,
        answer_key=(
            "Zerfall ist ein Zufallsprozess pro Atom; über große Zahlen mittelt sich "
            "der Zufall zu einer stabilen Rate (Halbwertszeit) — Statistik, kein Plan."
        ),
    )
    t2 = TaskBlock(  # W · create · STR.04
        id="str.t2",
        kind="create_produce",
        prompt=(
            "Entwirf eine kleine Info-Karte (5–6 Sätze) für jüngere Schüler:innen zu "
            "einer aktuellen Anwendung von Strahlung (z. B. PET im Krankenhaus, "
            "Bestrahlung von Lebensmitteln, C-14-Datierung). Erkläre Nutzen UND Grenze."
        ),
        response={"mode": "box", "min_height_mm": 55},
        cognitive_level="create",
        dimensions=["W"],
        serves=[{"competence_id": "PHY.US.4.STR.04", "relation": "exercises"}],
        est_minutes=12,
        acceptable_reasoning=(
            "Jede sachlich korrekte Anwendung mit Nutzen + einer ehrlichen Grenze/"
            "Risikoabwägung, altersgemäß formuliert."
        ),
    )
    t3 = TaskBlock(  # S · analyze · STR.02  (the penetration ≠ danger task, §8)
        id="str.t3",
        kind="open_response",
        prompt=(
            "WLAN-Signale gehen durch Wände, schaden dir aber nicht – Gammastrahlung "
            "dagegen ist gefährlich. Beide durchdringen Materie. Erkläre den Unterschied."
        ),
        response={"mode": "lines", "n": 3},
        cognitive_level="analyze",
        dimensions=["S", "W"],
        serves=[{"competence_id": "PHY.US.4.STR.02", "relation": "exercises"}],
        est_minutes=6,
        acceptable_reasoning=(
            "Funkwellen = niedrige Energie, durchdringen, verändern aber keine Atome "
            "(nicht-ionisierend); Gamma = extrem hohe Energie, ionisierend → Zellschaden. "
            "Kernpunkt: Durchdringung ≠ Gefahr."
        ),
        watch_outs=[
            "Lob die Trennung 'durchdringen' vs 'schaden' — genau hier liegt die Einsicht.",
        ],
    )
    t4 = TaskBlock(  # S · evaluate · STR.02  (statements check, §8)
        id="str.t4",
        kind="true_false_justify",
        prompt="Entscheide richtig/falsch und begründe oder korrigiere.",
        payload={
            "kind": "true_false_justify",
            "statements": [
                "UV-Strahlung ist ungefährlich, weil sie nicht ionisierend ist.",
                "Je höher die Energie, desto eher kann Strahlung Atome verändern (ionisieren).",
                "Wenn ich mit dem Handy telefoniere, werde ich radioaktiv.",
            ],
        },
        response={
            "mode": "table",
            "columns": ["Aussage", "richtig / falsch", "Begründung / Korrektur"],
            "rows": 3,
        },
        cognitive_level="evaluate",
        dimensions=["S"],
        serves=[{"competence_id": "PHY.US.4.STR.02", "relation": "exercises"}],
        est_minutes=9,
        answer_key=(
            "1 falsch (UV schädigt Zellen trotz nicht-ionisierend) · 2 richtig · "
            "3 falsch (Funkwellen, kein Kernzerfall)"
        ),
        watch_outs=[
            "Aussage 1 ist die zentrale Falle — 'nicht-ionisierend' ≠ 'harmlos'.",
        ],
    )
    t5 = TaskBlock(  # S · analyze · STR.02  (dose magnitudes)
        id="str.t5",
        kind="open_response",
        prompt=(
            "Dosen zum Vergleich: 1 Banane ≈ 0,1 µSv · Thorax-Röntgen ≈ 20 µSv · "
            "Transatlantikflug ≈ 40 µSv · natürliche Jahresdosis in Österreich ≈ "
            "2–3 mSv. Ordne 'eine Banane essen', 'einmal fliegen' und 'ein Jahr leben' "
            "nach Dosis und erkläre, warum Größenordnungen wichtiger sind als Bauchgefühl."
        ),
        response={"mode": "lines", "n": 4},
        cognitive_level="analyze",
        dimensions=["S"],
        serves=[{"competence_id": "PHY.US.4.STR.02", "relation": "exercises"}],
        est_minutes=10,
        acceptable_reasoning=(
            "Banane ≪ Flug ≪ Jahresdosis; der Punkt ist die Größenordnung (µSv vs mSv), "
            "nicht das einzelne Ereignis. Sehr kleine Dosen sind fachlich umstritten "
            "(LNT) — keine scharfe sicher/unsicher-Schwelle."
        ),
        watch_outs=[
            "Zahlen vor Einsatz prüfen (⏳). Kleine Dosen nicht als scharfe Schwelle.",
        ],
    )
    t6 = TaskBlock(  # S · evaluate · STR.02 (NOT STR.01 — keeps STR.01 a deliberate gap)
        id="str.t6",
        kind="decision_scenario",
        prompt=(
            "Eine Schlagzeile behauptet: 'Handystrahlung macht krank!'. Welche EINE "
            "Frage würdest du stellen, bevor du das glaubst – und warum entscheidet "
            "gerade diese Frage über die Glaubwürdigkeit?"
        ),
        payload={
            "kind": "decision_scenario",
            "stem": "Funk/Mikrowellen sind nicht-ionisierend; gesicherter Effekt ist Erwärmung.",
        },
        response={"mode": "lines", "n": 3},
        cognitive_level="evaluate",
        dimensions=["S"],
        serves=[{"competence_id": "PHY.US.4.STR.02", "relation": "exercises"}],
        est_minutes=11,
        acceptable_reasoning=(
            "Sinnvoll: nach Studienlage/Quelle/Dosis/Mechanismus fragen. 'nicht-ionisierend "
            "≠ harmlos, aber auch ≠ Verschwörung'. (Die echte Quellenbewertung STR.01 wird "
            "hier NICHT vertieft — gehört in einen Geschwister-Baustein.)"
        ),
        watch_outs=["Ausgewogen bleiben (⚠): weder verharmlosen noch dramatisieren."],
    )
    t7 = TaskBlock(  # E · apply · STR.02 — the ONLY equipment-dependent (gated) task
        id="str.t7",
        kind="experiment_protocol",
        prompt=(
            "Versuch (mit Zählrohr): Miss die Zählrate in verschiedenen Abständen zu "
            "einer schwachen Schulquelle. Protokolliere Abstand und Zählrate und "
            "beschreibe, wie die Rate mit dem Abstand zusammenhängt."
        ),
        response={"mode": "box", "min_height_mm": 60},
        cognitive_level="apply",
        dimensions=["E"],
        serves=[{"competence_id": "PHY.US.4.STR.02", "relation": "exercises"}],
        est_minutes=22,
        flags=ContentFlags(equipment_dependent=True),
        answer_key=(
            "Zählrate sinkt mit zunehmendem Abstand (näherungsweise Abstandsgesetz); "
            "Abstand ist eine einfache, wirksame Schutzmaßnahme."
        ),
        watch_outs=["🔬 Nur mit zugelassener Schulquelle und Sicherheitsregeln."],
    )
    return [t1, t2, t3, t4, t5, t6, t7]


def build_content() -> WorksheetContent:
    model = store.get_subject_model("Physik")
    fassung = store.get_fassung()
    meta = WorksheetMeta(
        title="Strahlung und Radioaktivität",
        subtitle="Warum Energie über Gefahr entscheidet – nicht Durchdringung",
        subject="Physik",
        stufe="Unterstufe",
        klasse=4,
        kernfrage="Was macht Strahlung gefährlich – und was nicht?",
        fassung=fassung,
        lehrplan_label="Physik · 4. Klasse · Strahlung und Radioaktivität",
    )
    section = Baustein(
        id="str.kern",
        title="Durchdringung ≠ Gefahr",
        teacher_overview={
            "throughline": "Energie entscheidet über Wirkung; Risiko ist eine Frage der Größenordnung.",
            "timing_notes": "Doppelstunde; Versuch (t7) optional/geräteabhängig.",
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
