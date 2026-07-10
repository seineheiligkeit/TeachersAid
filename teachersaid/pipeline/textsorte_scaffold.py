"""Derive a Textsorten-scaffold worksheet from the curated genre grounding.

The German genre analogue of `pipeline/sachverhalt.build_worksheet` (and the `text_tasks`
twin): a target **Textsorte** (Kommentar, Zusammenfassung, Interpretation, …) from
`grounding/textsorten.py` → a `WorksheetContent` that *teaches and scaffolds* the genre,
then the usual assemble/verify/render path.

**Matura-backward design** (see `Documents/matura-deutsch-coverage.md`): the SRDP demands
students *produce* a Textsorte by performing operator-driven Arbeitsaufträge, and it assumes
the genre is already mastered. We invert it — build the genre richly and earlier:

1. **Learn-text** (InfoBlocks) — what the Textsorte is, its leitende Schreibhandlungen, its
   Aufbau and its Sprachregister. Authored *expression over the frozen curated fields*
   (definition · struktur · schreibhandlungen · sprachregister) — the fourth
   correct-by-construction mechanism (invariants.md §3), never inventing genre facts.
2. **Low-band matching** — match each Bauteil to its Funktion (self-contained payload = its
   own response surface); the answer is the curated struktur pairing.
3. **Mid-band guided plan** — a Schreibplan-Raster (`table_fill`): one row per Bauteil with
   its Funktion as a Leitfrage and a blank column for the student's Stichworte.
4. **Capstone Arbeitsauftrag** — the Matura-shaped, operator-headed writing task
   ("Verfasse einen Kommentar … Umfang: 270–330 Wörter", `BoxResponse`). Its **rubric is
   DERIVED from the curated Schreibhandlungen + Struktur** (the Erwartungshorizont comes from
   the grounding, not invented at task time).

`serves` anchors to real `lehrplan/DEU.json` Schreiben-competences (honest 3./4. Klasse).
"""

from __future__ import annotations

from datetime import date

from ..grounding import textsorten as tsg
from ..schema.blocks import (
    InfoBlock,
    MatchingPayload,
    RubricCriterion,
    Serves,
    TableFillPayload,
    TaskBlock,
)
from ..schema.enums import Mark
from ..schema.response import BoxResponse, NoneResponse
from ..schema.richtext import InlineRun
from ..schema.worksheet import (
    Baustein,
    TeacherOverview,
    WorksheetContent,
    WorksheetMeta,
)

SUBJECT = "Deutsch"

# The three-level Bewertungsraster the SRDP-Korrekturheft uses (nicht/teilweise/erreicht).
STANDARD_LEVELS = ["nicht erreicht", "teilweise erreicht", "erreicht"]

# The Schreiben-competence a capstone "produce the Textsorte" task most directly builds
# toward, per grade — honest anchoring to the genre's dominant Schreibhandlung
# (DEU.US.3/4.SCH.02 = informieren/argumentieren; SCH.01 = pragmatische/kreative
# Schreibprozesse aus Vorlagen). Validated against the resolution; falls back to the
# grade's first Schreiben-competence if a mapping is absent for the requested grade.
_CAPSTONE_COMPETENCE: dict[str, dict[int, str]] = {
    "zusammenfassung": {3: "DEU.US.3.SCH.02", 4: "DEU.US.4.SCH.01"},
    "kommentar": {3: "DEU.US.3.SCH.02", 4: "DEU.US.4.SCH.02"},
    "leserbrief": {3: "DEU.US.3.SCH.02", 4: "DEU.US.4.SCH.02"},
    "eroerterung": {4: "DEU.US.4.SCH.02"},
    "meinungsrede": {3: "DEU.US.3.SCH.02", 4: "DEU.US.4.SCH.02"},
    "textanalyse": {4: "DEU.US.4.SCH.01"},
    "textinterpretation": {4: "DEU.US.4.SCH.01"},
}

# The 1–2 leitende Schreibhandlungen the Korrekturheft scores "im Sinne der Textsorte"
# (the rubric foregrounds these; all are ⊆ the Textsorte's grounded schreibhandlungen).
_LEIT_SCHREIBHANDLUNGEN: dict[str, tuple[str, ...]] = {
    "zusammenfassung": ("rekapitulation", "deskription"),
    "kommentar": ("argumentation", "rekapitulation"),
    "leserbrief": ("argumentation", "rekapitulation"),
    "eroerterung": ("argumentation", "evaluation"),
    "meinungsrede": ("argumentation",),
    "textanalyse": ("deskription", "explikation"),
    "textinterpretation": ("explikation", "argumentation"),
}

# A scorable rubric phrase per Schreibhandlung (grounded in its `ziel`; keeps the criterion
# short and gradeable, unlike the full katalog definition).
_SH_KRITERIUM: dict[str, str] = {
    "deskription": "Sachverhalte werden genau und geordnet dargestellt",
    "narration": "der Verlauf wird anschaulich und schlüssig geschildert",
    "explikation": "Zusammenhänge werden nachvollziehbar erklärt",
    "argumentation": "die Position wird mit stichhaltigen Argumenten und Belegen gestützt",
    "rekapitulation": "der Ausgangstext bzw. der Anlass wird sachlich in eigenen Worten "
                      "wiedergegeben",
    "evaluation": "der Sachverhalt wird begründet bewertet, die Maßstäbe werden offengelegt",
}

# An operator (a Textsorte's typical_operators form) → the imperative Arbeitsauftrag it heads.
# The operator is the curated fact; the imperative wording is authored (allowed).
_OPERATOR_AUFTRAG: dict[str, str] = {
    "zusammenfassen": "Fasse die Kernaussagen des Ausgangstextes zusammen.",
    "wiedergeben": "Gib den Inhalt bzw. den Anlass sachlich in eigenen Worten wieder.",
    "beschreiben": "Beschreibe die wesentlichen Merkmale genau.",
    "analysieren / untersuchen": "Untersuche Inhalt, Aufbau und sprachliche Gestaltung und "
                                 "belege am Text.",
    "erschließen": "Erschließe, was der Text nicht ausdrücklich sagt.",
    "erklären": "Erkläre die wichtigsten Zusammenhänge nachvollziehbar.",
    "erläutern": "Erläutere die zentralen Aspekte anhand von Beispielen.",
    "deuten / interpretieren": "Entwickle eine schlüssige, am Text belegte Deutung.",
    "begründen / Gründe angeben": "Begründe deine Position mit nachvollziehbaren Argumenten.",
    "kommentieren / Stellung nehmen": "Nimm klar und begründet Stellung.",
    "appellieren": "Schließe mit einem Appell an deine Leserinnen und Leser.",
    "diskutieren / erörtern / sich auseinandersetzen mit": "Wäge Pro- und Kontra-Argumente ab.",
    "beurteilen": "Fälle am Ende ein begründetes eigenes Urteil.",
}

# A concrete Schreibanlass per Textsorte (a pretext/Impuls — expression, not a load-bearing
# fact; overridable via the `impuls` argument). The compression/analysis genres reference the
# Textbeilage the teacher supplies; the argumentative genres carry a neutral debate Impuls.
_DEFAULT_IMPULS: dict[str, str] = {
    "zusammenfassung": "Fasse den im Unterricht gelesenen Sachtext (die Textbeilage) zusammen.",
    "kommentar": "An vielen Schulen wird über ein Handyverbot diskutiert. Nimm dazu Stellung.",
    "leserbrief": "Reagiere auf einen Zeitungsartikel, der ein Handyverbot an Schulen fordert.",
    "eroerterung": "„Sollen Schülerinnen und Schüler mehr Mitbestimmung in der Schule haben?“",
    "meinungsrede": "Halte vor deiner Klasse eine Rede zur Frage, ob es an eurer Schule mehr "
                    "Grünflächen geben soll.",
    "textanalyse": "Analysiere den im Unterricht gelesenen Sachtext (die Textbeilage).",
    "textinterpretation": "Interpretiere das im Unterricht gelesene Gedicht (die Textbeilage).",
}


def _lead(heading: str, body: str) -> list[InlineRun]:
    """A bold lead-in heading followed by the body (a projection over curated fields)."""
    return [InlineRun(text=f"{heading} — ", mark=Mark.BOLD), InlineRun(text=body)]


def _register_kurz(sprachregister: str) -> str:
    """The first clause of the register note (before the first ';') — the headline rule."""
    return sprachregister.split(";", 1)[0].strip()


def _capstone_competence(textsorte_id: str, kl: int, sch_ids: list[str]) -> str | None:
    """The Schreiben-competence the capstone serves: the curated mapping if it resolves for
    this grade, else the grade's first Schreiben-competence (honest fallback)."""
    want = _CAPSTONE_COMPETENCE.get(textsorte_id, {}).get(kl)
    if want and want in sch_ids:
        return want
    return sch_ids[0] if sch_ids else None


def build_worksheet(
    textsorte_id: str, klasse: int, *, impuls: str | None = None,
    today: date | None = None,
):
    """A target Textsorte + grade → (WorksheetContent, LehrplanResolution), assemble-ready.

    `textsorte_id` is a `grounding.textsorten` id or display name; `klasse` is the Unterstufe
    grade (3 or 4 are the honest homes). `impuls` overrides the default Schreibanlass.
    """
    from ..grounding import lehrplan_store as ls
    from .resolve import resolve_grade

    ts = tsg.get_textsorte(textsorte_id)
    if ts is None:
        raise KeyError(f"unknown Textsorte '{textsorte_id}'")

    res = resolve_grade(SUBJECT, klasse, today=today)
    sch_ids = [c.id for c in res.competences if ".SCH." in c.id]
    cap_id = _capstone_competence(ts.id, klasse, sch_ids)
    serves_cap = [Serves(competence_id=cap_id, relation="exercises")] if cap_id else []
    serves_pre = ([Serves(competence_id=cap_id, relation="builds_prerequisite")]
                  if cap_id else [])
    subject_model = ls.get_subject_model(SUBJECT)

    bauteile = [teil for teil, _ in ts.struktur]
    funktionen = [funk for _, funk in ts.struktur]
    bauteile_txt = ", ".join(bauteile)
    lo, hi = ts.umfang[0]                       # the shortest band — the accessible entry
    reg_kurz = _register_kurz(ts.sprachregister)
    leit = [s for s in _LEIT_SCHREIBHANDLUNGEN.get(ts.id, ts.schreibhandlungen[:2])
            if s in tsg.SCHREIBHANDLUNGEN]
    leit_namen = ", ".join(tsg.SCHREIBHANDLUNGEN[s].name for s in leit)
    impuls_txt = impuls or _DEFAULT_IMPULS.get(ts.id,
                 f"Verfasse {ts.artikel} {ts.name} zu einem im Unterricht vereinbarten Thema.")

    # --- 1) learn-text: what the Textsorte is + its Aufbau (authored over curated fields).
    # Uses the SIMPLE `schueler_definition` wording (grade-readable — the Wiener-
    # Sachtextformel lint checks it) in short sentences; the source-faithful SRDP
    # `definition` + the full register notes stay in the teacher layer (talking points). ---
    i1 = InfoBlock(
        id="tx.i1", kind="prose",
        content=_lead(
            f"Was ist {ts.artikel} {ts.name}?",
            f"{ts.schueler_definition or ts.definition} Wichtig dabei: {leit_namen}. "
            f"Üblicher Umfang: {lo}–{hi} Wörter."))
    i2 = InfoBlock(
        id="tx.i2", kind="key_fact",
        content=_lead(f"So ist {ts.artikel} {ts.name} aufgebaut",
                      " → ".join(bauteile) + "."))

    # --- 2) low band: match each Bauteil to its Funktion (self-contained → own surface) ---
    t1 = TaskBlock(
        id="tx.t1", kind="matching",
        prompt="Ordne jedem Bauteil die passende Aufgabe zu.",
        payload=MatchingPayload(left=list(bauteile), right=list(funktionen)),
        response=NoneResponse(),
        cognitive_level="understand", dimensions=["SCH"], serves=serves_pre, est_minutes=6,
        answer_key="; ".join(f"{teil}: {funk}" for teil, funk in ts.struktur))

    # --- 3) mid band: a Schreibplan-Raster (Funktion as the Leitfrage, blank for notes) ---
    t2 = TaskBlock(
        id="tx.t2", kind="table_fill",
        prompt=f"Plane {ts.artikel} {ts.name} zu deinem Thema: Notiere zu jedem Bauteil deine "
               f"Stichworte.",
        payload=TableFillPayload(
            columns=["Bauteil", "Das gehört hinein", "Deine Stichworte"],
            rows=[[teil, funk, None] for teil, funk in ts.struktur]),
        response=NoneResponse(),
        cognitive_level="apply", dimensions=["SCH"], serves=serves_pre, est_minutes=10,
        answer_key="Individuelle Planung; jedes Bauteil ist mit passenden Stichworten gefüllt.",
        acceptable_reasoning="Akzeptiere jede Planung, die zu jedem Bauteil sinnvolle, zum "
                             "Thema passende Stichworte enthält.")

    # --- 4) capstone: the Matura-shaped, operator-headed Arbeitsauftrag ---
    auftraege = [_OPERATOR_AUFTRAG.get(op, f"Beachte den Operator „{op}“.")
                 for op in ts.typical_operators]
    auftrag_txt = " ".join(f"({i}) {a}" for i, a in enumerate(auftraege, 1))
    capstone_min = 30 if lo <= 350 else 40
    t3 = TaskBlock(
        id="tx.t3", kind="text_production",
        # Deliberately Matura-FORMAT wording (operator heads, SRDP task language) — this
        # register IS the genre being taught, so the readability lint's advisory on this
        # one block is expected (the learn-text i1 must be grade-readable; this may not be).
        prompt=(f"Verfasse {ts.artikel} {ts.name}. Schreibauftrag: {impuls_txt} "
                f"Arbeitsaufträge: {auftrag_txt} Halte den Aufbau ein: {bauteile_txt}. "
                f"Achte auf die Sprache: {reg_kurz}. Umfang: {lo}–{hi} Wörter."),
        response=BoxResponse(min_height_mm=120),
        cognitive_level="create", dimensions=["SCH"], serves=serves_cap, est_minutes=capstone_min,
        acceptable_reasoning=(
            f"Ein gelungener Text erfüllt die leitenden Schreibhandlungen ({leit_namen}), hält "
            f"den Aufbau ({bauteile_txt}) ein und bleibt im Umfang ({lo}–{hi} Wörter) und im "
            f"geforderten Register. Bewertet wird nach den Kriterien, nicht eine bestimmte "
            f"Meinung."),
        rubric=_derive_rubric(ts, leit, bauteile_txt, reg_kurz, lo, hi),
        watch_outs=[
            f"Die Textsorte selbst ist das Lernziel: Achte darauf, dass alle Bauteile "
            f"({bauteile_txt}) vorkommen — nicht nur auf den Inhalt.",
        ])

    # --- teacher overview (authored guide, teacher-only) ---
    overview = TeacherOverview(
        throughline=(
            f"Die Matura verlangt, {ts.artikel} {ts.name} zu PRODUZIEREN, setzt die Textsorte "
            f"aber als bekannt voraus. Hier wird sie Schritt für Schritt aufgebaut: verstehen "
            f"(Bauteile), planen (Raster), verfassen (Schreibauftrag)."),
        talking_points=[
            f"Zuerst die Bauteile am Modell zeigen ({bauteile_txt}), dann in t1 selbst "
            f"zuordnen lassen.",
            f"Sprachregister bewusst machen: {reg_kurz}.",
            f"Der Schreibauftrag (t3) ist Matura-förmig und operatorgeleitet — die Operatoren "
            f"({', '.join(ts.typical_operators)}) markieren, was zu tun ist.",
        ],
        extensions=[
            "Einen Modelltext gemeinsam an den Kriterien messen (Peer-Feedback).",
            f"Denselben Anlass in einer verwandten Textsorte "
            f"({', '.join(tsg.get_textsorte(v).name for v in ts.verwandt) or 'z. B. Kommentar'}) "
            f"verfassen und vergleichen.",
        ],
        differentiation=(
            "Basis: t1–t2 (Bauteile erkennen und planen). Vertiefung: t3 (eigenständig "
            "verfassen); Gegenargumente und der volle Umfang als Zusatzanforderung."),
        timing_notes=(
            "Doppelstunde. t3 kann als Hausübung fertiggestellt werden — auf einem Extrablatt "
            "weiterschreiben."))

    intro = InfoBlock(
        id="tx.intro", kind="callout", callout_role="note",
        content=(f"In dieser Stunde lernst du, {ts.artikel} {ts.name} zu schreiben: Du "
                 f"erkennst zuerst die Bauteile, planst dann deinen Text und verfasst ihn "
                 f"zum Schluss selbst."))

    meta = WorksheetMeta(
        title=f"{ts.name} schreiben",
        subtitle=f"Die Textsorte {ts.name} verstehen, planen und verfassen",
        subject=SUBJECT, stufe=ls.stufe_for_klasse(klasse), klasse=klasse,
        kernfrage=f"Wie schreibe ich {ts.artikel} {ts.name}?",
        fassung=res.fassung,
        lehrplan_label=f"Deutsch · {klasse}. Klasse · Textsorte {ts.name}")
    content = WorksheetContent(
        meta=meta, subject_model=subject_model, intro=[intro],
        sections=[Baustein(id="tx.kern", title=f"{ts.name} schreiben",
                           teacher_overview=overview, blocks=[i1, i2, t1, t2, t3])])
    return content, res


def _derive_rubric(ts, leit, bauteile_txt: str, reg_kurz: str, lo: int, hi: int):
    """The capstone's rubric — DERIVED from the curated Struktur + Schreibhandlungen (the
    Erwartungshorizont from the grounding, not invented at task time)."""
    rubric = [RubricCriterion(
        criterion=f"Aufbau: alle Bauteile vorhanden und sinnvoll angeordnet ({bauteile_txt})",
        levels=list(STANDARD_LEVELS))]
    for sh in leit:
        s = tsg.SCHREIBHANDLUNGEN[sh]
        rubric.append(RubricCriterion(
            criterion=f"{s.name}: {_SH_KRITERIUM.get(sh, s.ziel)}",
            levels=list(STANDARD_LEVELS)))
    rubric.append(RubricCriterion(
        criterion=f"Sprache und Umfang: {reg_kurz}; {lo}–{hi} Wörter eingehalten",
        levels=list(STANDARD_LEVELS)))
    return rubric
