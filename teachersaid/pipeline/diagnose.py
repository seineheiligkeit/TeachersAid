"""Diagnose-Blatt — the first consumer of the prerequisite graph (Wave C1).

Before teaching competence *X*, a teacher wants to know the class actually brings the
*prerequisites*. This builds exactly that check: for every prerequisite **ancestor** of
``competence_id`` (``pipeline/prereq.ancestors``), pull ONE easy (band-1-preferred),
already-approved task from the block library that exercises it. The result is an ordinary
``WorksheetContent`` — it assembles, verifies and renders through the unchanged pipeline.

**Deterministic + honest, no LLM.** Selection is a filter over the *approved* ``BlockStore``
(the delivery loop's discipline, like ``pipeline/compose``). Where a prerequisite has no
approved task yet, that is recorded as an **honest gap note** (into the resolution + the
teacher overview) — never papered over — which is itself a signal for the demand queue.

Not built (documented seams, cf. ``prereq``): warm-up injection into a *topic* worksheet,
spiral revision, and campaign ordering all reuse the same graph.
"""

from __future__ import annotations

from datetime import date

from ..grounding import lehrplan_store as ls
from ..schema.blocks import InfoBlock
from ..schema.worksheet import (
    Baustein,
    FassungRef,
    LehrplanResolution,
    ResolvedCompetence,
    TeacherOverview,
    WorksheetContent,
    WorksheetMeta,
)
from .difficulty import DIFFICULTY_LABEL, effective_difficulty
from .prereq import ancestors, depth, prerequisites


def _klasse_of(competence_id: str) -> int:
    """The Klasse encoded in a competence id (``MAT.US.2.ZAH.04`` -> 2); 99 for the
    grade-independent Oberstufe descriptors (``…OS.x.…``), which sort last."""
    parts = competence_id.split(".")
    try:
        return int(parts[2])
    except (IndexError, ValueError):
        return 99


def _resolve_ids(
    subject: str, ids: list[str]
) -> tuple[dict[str, ResolvedCompetence], list[str]]:
    """Resolve competence ids to their verbatim ``ResolvedCompetence`` across BOTH Stufen
    (prerequisites reach back over Klassen). Returns (found_by_id, unresolved_ids)."""
    want = set(ids)
    found: dict[str, ResolvedCompetence] = {}
    for stufe in ("Unterstufe", "Oberstufe"):
        klassen = range(1, 5) if stufe == "Unterstufe" else range(5, 9)
        for k in klassen:
            for c in ls.competences_for(subject, k, stufe):
                if c.id in want and c.id not in found:
                    found[c.id] = c
    return found, [i for i in ids if i not in found]


def _pick_task(block_store, competence_id: str, used: set[str]):
    """The easiest not-yet-used approved task exercising `competence_id`, or None.
    'Easiest' = lowest effective difficulty (band-1 first — a diagnostic probes the
    basics), ties broken by the shortest task, then id (deterministic)."""
    cands = [
        lb for lb in block_store.approved()
        if lb.role == "task" and lb.id not in used and competence_id in lb.competences
    ]
    if not cands:
        return None
    return min(
        cands,
        key=lambda lb: (
            effective_difficulty(lb.block),
            getattr(lb.block, "est_minutes", 0) or 0,
            lb.id,
        ),
    )


def build_worksheet(
    subject: str,
    competence_id: str,
    klasse: int,
    *,
    block_store,
    today: date | None = None,
) -> tuple[WorksheetContent, LehrplanResolution]:
    """Build a Diagnose-Blatt for `competence_id` (taught at `klasse`): one easy approved
    task per prerequisite ancestor. Returns (content, resolution) for the standard
    assemble/verify/render path. Honest gap notes ride the resolution."""
    today = today or date.today()
    stufe = ls.stufe_for_klasse(klasse)
    fassung: FassungRef = ls.get_fassung()

    anc = ancestors(competence_id)
    # foundational first: earliest Klasse, then id (a learnable diagnostic order)
    ordered = sorted(anc, key=lambda cid: (_klasse_of(cid), cid))

    # resolve the target (for the title/Kernfrage) + all ancestors (for display text)
    resolved, _unresolved_anc = _resolve_ids(subject, [competence_id, *ordered])
    target = resolved.get(competence_id)
    target_label = (target.text.rstrip(" ,.;") if target else competence_id)

    # one easy approved task per ancestor; honest gap where none is approved yet
    used: set[str] = set()
    blocks = []
    picked_meta: list[tuple[str, int]] = []  # (ancestor id, effective difficulty)
    gaps: list[str] = []
    served_ids: set[str] = set()
    seen_assets: set[str] = set()
    assets = []
    n = 0
    for aid in ordered:
        lb = _pick_task(block_store, aid, used)
        if lb is None:
            ac = resolved.get(aid)
            label = f"{aid} ({ac.text.rstrip(' ,.;')})" if ac else aid
            gaps.append(
                f"Für die Voraussetzung {label} ist noch keine freigegebene "
                "Aufgabe in der Baustein-Bibliothek — Lücke für die Wunschliste."
            )
            continue
        used.add(lb.id)
        n += 1
        # re-id so two library blocks can't collide inside this sheet; keep everything else
        new_block = lb.block.model_copy(update={"id": f"diag.t{n}"})
        blocks.append(new_block)
        picked_meta.append((aid, effective_difficulty(lb.block)))
        # every competence the task ACTUALLY serves must be resolved (verify coverage)
        served_ids.update(s.competence_id for s in new_block.serves)
        for a in lb.assets or []:
            if a.id not in seen_assets:
                seen_assets.add(a.id)
                assets.append(a)

    # resolution: every competence the chosen tasks SERVE must be resolved (verify coverage).
    served_resolved, _ = _resolve_ids(subject, sorted(served_ids))
    competences = list(served_resolved.values())
    kbs = sorted({c.kompetenzbereich for c in competences})

    notes: list[str] = [
        f"Diagnose-Blatt: Voraussetzungen für {competence_id}"
        + (f" ({target_label})" if target else "")
        + f". {len(picked_meta)} von {len(ordered)} Voraussetzungen mit einer "
        "freigegebenen Aufgabe abgedeckt."
    ]
    if not ordered:
        notes.append(
            f"Für {competence_id} sind im Voraussetzungs-Graphen keine Vorläufer "
            "hinterlegt (Wurzelkompetenz oder Graph noch nicht kuratiert)."
        )
    notes += gaps

    res = LehrplanResolution(
        fassung=fassung, subject=subject, klasse=klasse,
        matched_kompetenzbereiche=kbs, grade_check=True,
        competences=competences, notes=notes,
    )

    # --- the content object ---------------------------------------------------
    intro_text = (
        f"Dieses Diagnose-Blatt prüft die Grundlagen, die du für „{target_label}“ "
        "brauchst. Bearbeite die Aufgaben der Reihe nach — so siehst du (und deine "
        "Lehrkraft), wo du vor dem neuen Thema noch üben solltest."
    )
    intro: list[InfoBlock] = [InfoBlock(id="diag.intro", kind="prose", content=intro_text)]
    if not blocks:
        intro.append(InfoBlock(
            id="diag.leer", kind="callout", callout_role="note",
            content="Für die Voraussetzungen dieses Themas sind noch keine freigegebenen "
                    "Übungsaufgaben vorhanden. Die offenen Lücken stehen im Lehrer-Teil.",
        ))

    ov = TeacherOverview(
        throughline=f"Voraussetzungs-Check vor „{target_label}“ — {len(picked_meta)} "
                    f"von {len(ordered)} Vorläuferkompetenzen geprüft.",
        talking_points=[
            f"{aid}: {DIFFICULTY_LABEL[band]}" for aid, band in picked_meta
        ],
        extensions=(["Offene Voraussetzungen (noch keine freigegebene Aufgabe):",
                     *gaps] if gaps else []),
    )
    section = Baustein(id="diag.kern", title="Voraussetzungen prüfen",
                       teacher_overview=ov, blocks=blocks)

    meta = WorksheetMeta(
        title=f"Diagnose: Voraussetzungen für {target_label}",
        subtitle="Prüfe die Grundlagen vor dem neuen Thema",
        subject=subject, stufe=stufe, klasse=klasse,
        kernfrage=f"Bringst du die Voraussetzungen für „{target_label}“ mit?",
        fassung=fassung,
        lehrplan_label=f"{subject} · {klasse}. Klasse · Diagnose {competence_id}",
    )
    model = ls.get_subject_model(subject, stufe)
    if model is None:
        raise ValueError(f"Fach '{subject}' ist im {stufe}-Katalog nicht hinterlegt.")
    content = WorksheetContent(
        meta=meta, subject_model=model, intro=intro, sections=[section], assets=assets,
    )
    return content, res


def prerequisite_report(competence_id: str) -> dict:
    """A small structural summary of a competence's position in the graph — handy for the
    dashboard / a campaign brief (direct prerequisites, all ancestors, graph depth)."""
    return {
        "competence_id": competence_id,
        "prerequisites": prerequisites(competence_id),
        "ancestors": sorted(ancestors(competence_id)),
        "depth": depth(competence_id),
    }
