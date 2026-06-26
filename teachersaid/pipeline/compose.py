"""Compose a worksheet from approved library blocks (Phase 2, deliberately dumb).

Given a subject / Klasse / topic / time envelope, select approved `LibraryBlock`s
that serve the topic's competences, fit them to the time budget while climbing the
cognitive ladder, pull in a couple of readable info blocks for context, and add a
light generated framing (Kernfrage + intro). The result is a `WorksheetContent` →
the existing assemble(+derive) / verify / render stages, unchanged.

No optimizer, no LLM (offline): framing is a simple template; selection is a filter
+ greedy time-fit. Difficulty calibration is still deferred. See
`Documents/block-library-design.md` §4.
"""

from __future__ import annotations

import re
from datetime import date

from ..grounding import lehrplan_store as ls
from ..schema.blocks import InfoBlock
from ..schema.enums import COGNITIVE_RANK
from ..schema.worksheet import (
    Baustein,
    BundleRequest,
    WorksheetContent,
    WorksheetMeta,
)
from .difficulty import effective_difficulty
from .plan import _ENVELOPE_MINUTES
from .resolve import resolve, resolve_kompetenzbereich

# which scope (richness) suits which envelope
_SCOPE_FOR = {"einzelstunde": "compact", "doppelstunde": "standard", "block": "extended"}

# --- angle-aware selection (Phase 3b) ----------------------------------------
# Competences fix WHICH blocks are eligible; the requested topic/Kernfrage is the
# ANGLE that picks among them. Deterministic term overlap (no LLM) — content words
# of the angle vs. the block's own text — so two Kernfragen on one Kompetenzbereich
# compose different sheets. Empty/echoes-the-KB angle ⇒ no preference (back-compat).
_ANGLE_STOP = frozenset((
    "eine einen einem eines oder aber wenn dann auch noch schon sehr mehr viel viele alle "
    "beide durch sowie sowohl anhand mithilfe zwischen welche welcher welches dieser diese "
    "dieses jeder jede jedes kann können soll sollen sollte muss müssen wird werden sind "
    "waren haben hatte nicht über unter gegen ohne beim vom zum zur aus bei für von das der die "
    "arbeitsblatt aufgabe aufgaben thema themen beispiel beispiele erkläre erklären beschreibe "
    "beschreiben nenne begründe begründen beurteile vergleiche ordne schreibe fülle deine "
    "schüler schülerinnen klasse"
).split())


def _angle_terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zäöüß]+", (text or "").lower())
            if len(w) >= 4 and w not in _ANGLE_STOP}


def _block_text(lb) -> str:
    raw = getattr(lb.block, "prompt", None) or getattr(lb.block, "content", None) or ""
    if isinstance(raw, list):
        raw = "".join(getattr(r, "text", "") for r in raw)
    return str(raw)


def compose(
    subject, klasse, topic, envelope="doppelstunde",
    *, kompetenzbereich: str | None = None, block_store, today: date | None = None,
):
    """Return (WorksheetContent, LehrplanResolution).

    Targets competences either by an explicit `kompetenzbereich` (deterministic, the
    robust path — the block library is competence-anchored) or, when none is given, by
    matching the free-text `topic` against the catalog (works when the title echoes a
    KB name or an Anwendungsbereich). `topic` is always the worksheet's display title.
    Raises ValueError if nothing resolves or no approved blocks serve the target."""
    if kompetenzbereich:
        res = resolve_kompetenzbereich(subject, klasse, kompetenzbereich, today=today)
    else:
        req = BundleRequest(subject=subject, klasse=klasse, topic_raw=topic, envelope=envelope)
        res = resolve(req, today=today)
    model = ls.get_subject_model(subject)
    if model is None:
        raise ValueError(f"Fach '{subject}' ist nicht im Katalog.")

    display = (topic or "").strip() or kompetenzbereich or "Arbeitsblatt"
    code = ls._code_for(subject)
    target_ids = {c.id for c in res.competences}
    target_kbs = set(res.matched_kompetenzbereiche)
    if not target_ids and not target_kbs:
        raise ValueError(
            f"'{display}' ließ sich keinem Kompetenzbereich von {subject} "
            f"{klasse}. Kl. zuordnen — bitte einen Kompetenzbereich wählen."
        )

    pool = [
        b for b in block_store.approved()
        if ls._code_for(b.subject) == code and b.modality == "printable"
    ]

    def task_matches(b) -> bool:
        return bool(set(b.competences) & target_ids) or (
            b.kompetenzbereich is not None and b.kompetenzbereich in target_kbs
        )

    tasks = [b for b in pool if b.role == "task" and task_matches(b)]
    if not tasks:
        raise ValueError(
            f"Keine freigegebenen Aufgaben-Bausteine für '{display}' "
            f"({subject} {klasse}. Kl.). Erst Bausteine erzeugen/freigeben."
        )
    # context blocks incl. figures — their assets now travel with the block (Phase 3c)
    infos = [
        b for b in pool
        if b.role == "info"
        and (not target_kbs or b.kompetenzbereich in target_kbs or b.kompetenzbereich is None)
    ]

    # angle (Phase 3b): the requested topic minus the KB's own words is the angle;
    # prefer blocks whose text overlaps it. Empty angle ⇒ rel 0 everywhere ⇒ the old
    # cognitive-ladder ordering, unchanged.
    angle = _angle_terms(topic) - _angle_terms(kompetenzbereich or "")
    rel = {b.id: (len(angle & _angle_terms(_block_text(b))) if angle else 0) for b in pool}

    # one variant per family; prefer on-angle blocks, then climb the ladder, then scope
    pref = _SCOPE_FOR.get(envelope, "standard")
    tasks.sort(key=lambda b: (0 if rel[b.id] else 1, -rel[b.id],
                              COGNITIVE_RANK.get(b.cognitive_level, 9),
                              0 if b.scope == pref else 1))
    seen_family, picked = set(), []
    for b in tasks:
        if b.family and b.family in seen_family:
            continue
        if b.family:
            seen_family.add(b.family)
        picked.append(b)

    # difficulty-calibrated time-fit (Phase 3d): seed the top-priority block of each
    # Anforderungsband (1/2/3) that fits — so a tight budget spans easy→stretch rather
    # than greedily filling from the easy end — then fill the rest by priority.
    budget = _ENVELOPE_MINUTES.get(envelope, 100)
    chosen, spent, chosen_ids = [], 0, set()
    for band in (1, 2, 3):
        cand = next((b for b in picked if b.id not in chosen_ids
                     and effective_difficulty(b.block) == band), None)
        if cand:
            m = getattr(cand.block, "est_minutes", 0) or 0
            if not chosen or spent + m <= budget:
                chosen.append(cand); chosen_ids.add(cand.id); spent += m
    for b in picked:
        if b.id in chosen_ids:
            continue
        m = getattr(b.block, "est_minutes", 0) or 0
        if spent + m <= budget:
            chosen.append(b); chosen_ids.add(b.id); spent += m
    chosen.sort(key=lambda b: COGNITIVE_RANK.get(b.cognitive_level, 9))

    # up to 2 readable infos + up to 1 figure as context (so a figure's asset travels);
    # prefer the on-angle ones
    infos.sort(key=lambda b: -rel[b.id])
    readable = [b for b in infos if b.kind != "figure"][:2]
    figures = [b for b in infos if b.kind == "figure"][:1]
    used_infos = readable + figures
    intro = [InfoBlock(
        id="cmp.intro", kind="prose",
        content=f"Arbeitsblatt zu '{display}'. Bearbeite die Aufgaben der Reihe nach.",
    )]
    intro += [b.block for b in used_infos]
    on_angle = sum(1 for b in chosen if rel[b.id])
    focus = f" · auf „{display}“ ausgerichtet ({on_angle}/{len(chosen)} angle-relevant)" if angle else ""
    section = Baustein(
        id="cmp.kern", title=display,
        teacher_overview={
            "throughline": f"Aus {len(chosen)} freigegebenen Bausteinen zusammengestellt "
                           f"(~{spent} min){focus}.",
        },
        blocks=[b.block for b in chosen],
    )
    # the chosen blocks' assets travel with them (figures/data), deduped by id (Phase 3c)
    seen_a, assets = set(), []
    for lb in chosen + used_infos:
        for a in (lb.assets or []):
            if a.id not in seen_a:
                seen_a.add(a.id)
                assets.append(a)
    meta = WorksheetMeta(
        title=display, subtitle="Zusammengestellt aus der Baustein-Bibliothek",
        subject=subject, stufe="Unterstufe", klasse=klasse,
        kernfrage=f"Was solltest du über '{display}' sicher können?",
        fassung=ls.get_fassung(),
        lehrplan_label=f"{subject} · {klasse}. Klasse · {display}",
    )
    content = WorksheetContent(
        meta=meta, subject_model=model, intro=intro, sections=[section], assets=assets,
    )
    return content, res
