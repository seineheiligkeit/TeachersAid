"""Derive a worksheet from a curated Sachverhalt (the content / exposition layer).

The content analogue of `pipeline/text_tasks.build_worksheet`: a `Sachverhalt` → a
`WorksheetContent` with three projections, then the usual assemble/verify/render path.

1. **Darstellung learn-text** — each `DarstellungSection` → an `InfoBlock` (prose), with a
   grounded `BlockProvenance` (`expression_origin="original"`, the module's `role="facts"`
   sources) attached automatically, so the prose-provenance gate passes by construction.
   `bedeutung`/`gegenwartsbezug` → closing `key_fact` blocks.
2. **DERIVED figures** — `timeline` → `matplotlib:timeline`; `causes` → `matplotlib:cause_effect`
   (the Wirkungsgefüge); `process` → `matplotlib:process_flow` (Phase 2 — a Bio process/cycle, the
   undated sibling of the timeline). Correct-by-construction: built straight from the structured facts.
3. **Sachkompetenz tasks** — the load-bearing correctness property: each task's `answer_key`
   is **computed from the fact-set**, never authored — chronology = the events sorted by `at`;
   `cause_effect_match` / `concept_match` = the pairing straight from `causes` / `concepts`.
   The prompt shows a *deterministically-reordered* list (stable sort by label, no RNG), so it
   is a real task whose key cannot drift. Two open tasks (content_comprehension from
   `bedeutung`, structure_overview from `actors`) and an optional high-band Urteils-task (from
   `urteilsfrage`) round out a real Anforderungs-spread.
"""

from __future__ import annotations

from datetime import date

from ..schema.assets import Asset
from ..schema.blocks import InfoBlock, MatchingPayload, OrderingPayload, Serves, TaskBlock
from ..schema.enums import CORE_TASK_KINDS, Mark
from ..schema.provenance import BlockProvenance
from ..schema.response import BoxResponse, LinesResponse
from ..schema.richtext import InlineRun, plain_text, to_runs
from ..schema.sachverhalt import Sachverhalt
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta


def _p(rt) -> str:
    """plain_text that tolerates empty RichText (an empty InlineRun fails validation)."""
    return plain_text(rt) if rt else ""


def _event_key(ev):
    """Sort key for a timeline event — numeric `at` first (chronological), strings after."""
    try:
        return (0, float(ev.at), "")
    except (TypeError, ValueError):
        return (1, 0.0, str(ev.at))


def _sorted_events(sv: Sachverhalt):
    return sorted(sv.timeline, key=_event_key)


def _heading(heading: str, body) -> list[InlineRun]:
    """A bold lead-in heading followed by the section body (a grounded projection)."""
    return [InlineRun(text=f"{heading} — ", mark=Mark.BOLD), *to_runs(body)]


def build_worksheet(sv: Sachverhalt, *, klasse: int | None = None,
                    today: date | None = None):
    """A Sachverhalt → (WorksheetContent, LehrplanResolution), assemble-ready."""
    from ..grounding import lehrplan_store as ls
    from .resolve import resolve_grade

    kl = klasse or sv.default_klasse()
    res = resolve_grade(sv.subject, kl, today=today)
    res_by_id = {c.id: c for c in res.competences}
    comp_ids = sv.competences or [c.id for c in res.competences]
    subject_model = ls.get_subject_model(sv.subject)
    _allowed = set(CORE_TASK_KINDS) | set(subject_model.task_kind_extensions)
    # the judgment task uses the subject's best available kind (GPB has position_argument; a
    # science Sachverhalt falls back to the core open_response for a Standpunkt/Bewertung).
    urteil_kind = "position_argument" if "position_argument" in _allowed else "open_response"

    def pick(i: int) -> str | None:
        return comp_ids[i % len(comp_ids)] if comp_ids else None

    def dims_for(cid: str | None, *, urteil: bool = False) -> list[str]:
        """A task's dimensions: the served competence's own dims if the catalog carries
        them, else the module's Sach-/Urteils-dimension hint (GPB.US competences resolve
        with empty dims, so the hint is the real source there)."""
        c = res_by_id.get(cid or "")
        if c and c.dimensions:
            return list(c.dimensions)
        hint = (sv.urteil_dimension or sv.sach_dimension) if urteil else sv.sach_dimension
        return [hint] if hint else []

    facts_sources = sv.facts_sources()
    grounded = (BlockProvenance(expression_origin="original", sources=facts_sources)
                if facts_sources else None)

    blocks: list = []
    tasks: list[TaskBlock] = []
    assets: list[Asset] = []

    # 1) the Darstellung learn-text (grounded provenance attached by construction)
    for i, sec in enumerate(sv.darstellung, 1):
        blocks.append(InfoBlock(
            id=f"sv.d{i}", kind="prose", content=_heading(sec.heading, sec.body),
            provenance=sec.provenance or grounded))
    if sv.bedeutung:
        blocks.append(InfoBlock(id="sv.bedeutung", kind="key_fact",
                                content=_heading("Bedeutung", sv.bedeutung),
                                provenance=grounded))
    if sv.gegenwartsbezug:
        blocks.append(InfoBlock(id="sv.gegenwart", kind="key_fact",
                                content=_heading("Gegenwartsbezug", sv.gegenwartsbezug),
                                provenance=grounded))

    # 2) DERIVED figures (correct-by-construction, straight from the structured facts)
    if len(sv.timeline) >= 2:
        events = [{"at": e.at, "label": e.label} for e in _sorted_events(sv)]
        assets.append(Asset(
            id="sv-timeline", role="figure", generator="matplotlib:timeline",
            spec={"events": events, "title": f"Zeitleiste: {sv.topic}"},
            caption=f"Zeitleiste: {sv.topic}"))
        blocks.append(InfoBlock(id="sv.fig-timeline", kind="figure",
                                asset_refs=["sv-timeline"],
                                content=f"Zeitleiste zu „{sv.topic}“."))
    if len(sv.causes) >= 1:
        links = [{"cause": c.cause, "effect": c.effect, "kind": c.kind} for c in sv.causes]
        assets.append(Asset(
            id="sv-wirkung", role="figure", generator="matplotlib:cause_effect",
            spec={"links": links, "title": f"Wirkungsgefüge: {sv.topic}"},
            caption=f"Wirkungsgefüge: {sv.topic}"))
        blocks.append(InfoBlock(id="sv.fig-wirkung", kind="figure",
                                asset_refs=["sv-wirkung"],
                                content="Ursachen und Folgen im Überblick."))
    if len(sv.process) >= 2:
        steps = [{"name": st.name, "text": _p(st.text)} for st in sv.process]
        assets.append(Asset(
            id="sv-process", role="figure", generator="matplotlib:process_flow",
            spec={"steps": steps, "cyclic": sv.process_cyclic,
                  "title": sv.process_name or sv.topic},
            caption=sv.process_name or f"Ablauf: {sv.topic}"))
        blocks.append(InfoBlock(id="sv.fig-process", kind="figure",
                                asset_refs=["sv-process"],
                                content=f"{sv.process_name or 'Der Ablauf'} im Überblick."))

    # 3) Sachkompetenz tasks — answer_key COMPUTED from the fact-set (select, never author)
    n = 0

    if len(sv.timeline) >= 2:                              # chronology (deterministic)
        ordered = _sorted_events(sv)
        shown = sorted(ordered, key=lambda e: str(e.label).casefold())
        n += 1
        cid = pick(n - 1)
        tasks.append(TaskBlock(
            id=f"sv.t{n}", kind="ordering",
            prompt="Bringe die Ereignisse in die richtige zeitliche Reihenfolge.",
            payload=OrderingPayload(items=[e.label for e in shown]),
            response=LinesResponse(n=len(shown)),
            cognitive_level="remember", dimensions=dims_for(cid),
            serves=[Serves(competence_id=cid, relation="builds_prerequisite")] if cid else [],
            est_minutes=5,
            answer_key=" → ".join(f"{e.label} ({e.at})" for e in ordered)))
    elif len(sv.process) >= 2:                            # process-ordering (deterministic)
        ordered_p = sv.process                            # the authored order IS the sequence
        shown_p = sorted(ordered_p, key=lambda st: str(st.name).casefold())
        n += 1
        cid = pick(n - 1)
        tasks.append(TaskBlock(
            id=f"sv.t{n}", kind="ordering",
            prompt=f"Bringe die Schritte von „{sv.process_name or sv.topic}“ in die richtige "
                   f"Reihenfolge.",
            payload=OrderingPayload(items=[st.name for st in shown_p]),
            response=LinesResponse(n=len(shown_p)),
            cognitive_level="remember", dimensions=dims_for(cid),
            serves=[Serves(competence_id=cid, relation="builds_prerequisite")] if cid else [],
            est_minutes=5,
            answer_key=" → ".join(st.name for st in ordered_p)
                       + (" → (zurück zum Anfang)" if sv.process_cyclic else "")))

    if len(sv.causes) >= 2:                                # cause→effect match (deterministic)
        shown_eff = sorted(sv.causes, key=lambda c: str(c.effect).casefold())
        n += 1
        cid = pick(n - 1)
        tasks.append(TaskBlock(
            id=f"sv.t{n}", kind="cause_effect_match",
            prompt="Ordne jeder Ursache die passende Folge zu.",
            payload=MatchingPayload(left=[c.cause for c in sv.causes],
                                    right=[c.effect for c in shown_eff]),
            response=LinesResponse(n=len(sv.causes)),
            cognitive_level="analyze", dimensions=dims_for(cid),
            serves=[Serves(competence_id=cid, relation="exercises")] if cid else [],
            est_minutes=8,
            answer_key="; ".join(f"{c.cause} → {c.effect}" for c in sv.causes)))

    if len(sv.concepts) >= 2:                              # Begriff-Zuordnung (deterministic)
        defs = {c.term: _p(c.definition) for c in sv.concepts}
        shown_def = sorted(sv.concepts, key=lambda c: defs[c.term].casefold())
        n += 1
        cid = pick(n - 1)
        tasks.append(TaskBlock(
            id=f"sv.t{n}", kind="concept_match",
            prompt="Ordne jedem Begriff die richtige Erklärung zu.",
            payload=MatchingPayload(left=[c.term for c in sv.concepts],
                                    right=[defs[c.term] for c in shown_def]),
            response=LinesResponse(n=len(sv.concepts)),
            cognitive_level="understand", dimensions=dims_for(cid),
            serves=[Serves(competence_id=cid, relation="exercises")] if cid else [],
            est_minutes=7,
            answer_key="; ".join(f"{c.term}: {defs[c.term]}" for c in sv.concepts)))

    if sv.bedeutung:                                       # content comprehension (open)
        n += 1
        cid = pick(n - 1)
        tasks.append(TaskBlock(
            id=f"sv.t{n}", kind="content_comprehension",
            prompt=f"Erkläre in eigenen Worten, warum „{sv.topic}“ wichtig war.",
            response=BoxResponse(min_height_mm=45),
            cognitive_level="understand", dimensions=dims_for(cid),
            serves=[Serves(competence_id=cid, relation="exercises")] if cid else [],
            est_minutes=8, answer_key=sv.bedeutung,
            acceptable_reasoning=("Akzeptiere jede Antwort, die die im Lerntext genannte "
                                  "Bedeutung sinngemäß wiedergibt.")))

    if sv.actors:                                          # structure overview (open)
        n += 1
        cid = pick(n - 1)
        roles = "; ".join(f"{a.name}: {_p(a.role)}" for a in sv.actors)
        tasks.append(TaskBlock(
            id=f"sv.t{n}", kind="structure_overview",
            prompt=f"Nenne die wichtigsten {sv.actor_label} und beschreibe kurz ihre Rolle "
                   f"bzw. Funktion.",
            response=BoxResponse(min_height_mm=45),
            cognitive_level="understand", dimensions=dims_for(cid),
            serves=[Serves(competence_id=cid, relation="exercises")] if cid else [],
            est_minutes=7, answer_key=roles))

    if sv.urteilsfrage:                                    # the high-band Urteils-task
        n += 1
        cid = sv.urteil_competence or pick(n - 1)
        tasks.append(TaskBlock(
            id=f"sv.t{n}", kind=urteil_kind, prompt=sv.urteilsfrage,
            response=BoxResponse(min_height_mm=60),
            cognitive_level="evaluate", dimensions=dims_for(cid, urteil=True),
            serves=[Serves(competence_id=cid, relation="exercises")] if cid else [],
            est_minutes=12,
            acceptable_reasoning=("Ein begründetes Urteil in beide Richtungen ist gültig — "
                                  "bewertet wird die Begründung, nicht die Position.")))

    intro = ("Lies zuerst den Darstellungstext: Er fasst zusammen, worum es geht und warum es "
             "wichtig ist. Die Abbildungen ordnen die wichtigsten Zusammenhänge. Bearbeite "
             "danach die Aufgaben.")
    meta = WorksheetMeta(
        title=sv.topic, subject=sv.subject, stufe=ls.stufe_for_klasse(kl), klasse=kl,
        kernfrage=sv.leitfrage or f"Worum geht es bei „{sv.topic}“?",
        fassung=res.fassung,
        lehrplan_label=f"{sv.subject} · {kl}. Kl. · {sv.topic}")
    content = WorksheetContent(
        meta=meta, subject_model=subject_model,
        intro=[InfoBlock(id="sv.intro", kind="callout", callout_role="note", content=intro)],
        sections=[Baustein(id="sv.kern", title=sv.topic, blocks=blocks + tasks)],
        assets=assets)
    return content, res
