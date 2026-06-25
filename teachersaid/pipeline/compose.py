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
from .plan import _ENVELOPE_MINUTES
from .resolve import resolve

# which scope (richness) suits which envelope
_SCOPE_FOR = {"einzelstunde": "compact", "doppelstunde": "standard", "block": "extended"}


def compose(subject, klasse, topic, envelope="doppelstunde", *, block_store, today: date | None = None):
    """Return (WorksheetContent, LehrplanResolution). Raises ValueError if the topic
    can't be served from the approved block library."""
    req = BundleRequest(subject=subject, klasse=klasse, topic_raw=topic, envelope=envelope)
    res = resolve(req, today=today)
    model = ls.get_subject_model(subject)
    if model is None:
        raise ValueError(f"Fach '{subject}' ist nicht im Katalog.")

    code = ls._code_for(subject)
    target_ids = {c.id for c in res.competences}
    target_kbs = set(res.matched_kompetenzbereiche)

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
            f"Keine freigegebenen Aufgaben-Bausteine für '{topic}' "
            f"({subject} {klasse}. Kl.). Erst Bausteine erzeugen/freigeben."
        )
    # readable context blocks (no figures yet — assets don't travel with blocks in v1)
    infos = [
        b for b in pool
        if b.role == "info" and b.kind != "figure"
        and (not target_kbs or b.kompetenzbereich in target_kbs or b.kompetenzbereich is None)
    ]

    # one variant per family; prefer the scope that fits the envelope; climb the ladder
    pref = _SCOPE_FOR.get(envelope, "standard")
    tasks.sort(key=lambda b: (COGNITIVE_RANK.get(b.cognitive_level, 9), 0 if b.scope == pref else 1))
    seen_family, picked = set(), []
    for b in tasks:
        if b.family and b.family in seen_family:
            continue
        if b.family:
            seen_family.add(b.family)
        picked.append(b)

    # greedy time-fit (always keep at least one)
    budget = _ENVELOPE_MINUTES.get(envelope, 100)
    chosen, spent = [], 0
    for b in picked:
        m = getattr(b.block, "est_minutes", 0) or 0
        if not chosen or spent + m <= budget:
            chosen.append(b)
            spent += m
    chosen.sort(key=lambda b: COGNITIVE_RANK.get(b.cognitive_level, 9))

    intro = [InfoBlock(
        id="cmp.intro", kind="prose",
        content=f"Arbeitsblatt zu '{topic}'. Bearbeite die Aufgaben der Reihe nach.",
    )]
    intro += [b.block for b in infos[:2]]
    section = Baustein(
        id="cmp.kern", title=topic,
        teacher_overview={
            "throughline": f"Aus {len(chosen)} freigegebenen Bausteinen zusammengestellt (~{spent} min).",
        },
        blocks=[b.block for b in chosen],
    )
    meta = WorksheetMeta(
        title=topic, subtitle="Zusammengestellt aus der Baustein-Bibliothek",
        subject=subject, stufe="Unterstufe", klasse=klasse,
        kernfrage=f"Was solltest du über '{topic}' sicher können?",
        fassung=ls.get_fassung(),
        lehrplan_label=f"{subject} · {klasse}. Klasse · {topic}",
    )
    content = WorksheetContent(meta=meta, subject_model=model, intro=intro, sections=[section])
    return content, res
