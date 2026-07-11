"""Assemble / derive / verify for a Lernarrangement (schema v0.5) — DETERMINISTIC.

Reuses the worksheet pipeline entirely: each role's material is assembled/verified
as a normal worksheet, then the arrangement-level Nachweis is the **union of the
role Nachweise plus the competence_anchors** — the latter are how the oral / social
/ enactive competences (reached by the interaction, debrief, or shared product, not
by any printable sheet) enter coverage. depth_profile is the aggregate over all
role tasks. As with a worksheet, these DERIVED fields are never authored by hand.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..schema.arrangement import GROUPINGS, SERVED_BY, Lernarrangement
from ..schema.derived import CompetenceCoverage, DepthProfile, Nachweis
from ..schema.enums import CoverageRelation, Role
from ..schema.worksheet import LehrplanResolution
from .assemble import assemble
from .verify import VerifyReport, verify


def _aggregate_depth(arr: Lernarrangement) -> DepthProfile:
    by_level: dict[str, int] = defaultdict(int)
    by_dimension: dict[str, int] = defaultdict(int)
    minutes_total = minutes_ri = 0
    for role in arr.roles:
        dp = role.material.depth_profile
        if dp is None:
            continue
        for k, v in dp.by_level.items():
            by_level[k] += v
        for k, v in dp.by_dimension.items():
            by_dimension[k] += v
        minutes_total += dp.minutes_total
        minutes_ri += dp.minutes_resource_independent
    return DepthProfile(
        by_level=dict(by_level), by_dimension=dict(by_dimension),
        minutes_total=minutes_total, minutes_resource_independent=minutes_ri,
    )


def derive_arrangement_nachweis(
    arr: Lernarrangement, resolution: LehrplanResolution
) -> Nachweis:
    """⋃ of the roles' exercised competences + the arrangement-level anchors.
    A competence covered ONLY by an anchor is the v0.5 payoff: the worksheet
    couldn't reach it, the arrangement does."""
    exercised: dict[str, list[str]] = defaultdict(list)
    for role in arr.roles:
        for b in role.material.iter_blocks():
            if b.role != Role.TASK:
                continue
            for s in b.serves:
                if s.relation == CoverageRelation.EXERCISES:
                    exercised[s.competence_id].append(f"{role.id}:{b.id}")

    anchored: dict[str, list[str]] = defaultdict(list)
    for a in arr.competence_anchors:
        anchored[a.competence_id].append(a.served_by)

    universe = {c.id: c for c in resolution.competences}
    for cid in list(exercised) + list(anchored):
        universe.setdefault(cid, None)

    coverage: list[CompetenceCoverage] = []
    gaps: list[str] = []
    uet: set[int] = set()
    konzepte: set[str] = set()
    anchor_only = 0
    for cid, comp in universe.items():
        ex = exercised.get(cid, [])
        an = anchored.get(cid, [])
        covered = bool(ex) or bool(an)
        coverage.append(CompetenceCoverage(
            competence_id=cid,
            exercised_by=ex + [f"anchor:{s}" for s in an],
            covered=covered,
        ))
        if covered and not ex and an:
            anchor_only += 1
        if comp is not None:
            konzepte.add(comp.kompetenzbereich)
            if covered:
                uet.update(comp.uebergreifende_themen)
        if not covered:
            gaps.append(f"{cid} — {comp.text if comp is not None else cid}")

    n_cov = sum(1 for c in coverage if c.covered)
    statement = (
        f"Dieses Lernarrangement adressiert {n_cov} von {len(coverage)} verbatim "
        f"Kompetenzen des Lehrplans (davon {anchor_only} über Interaktion, Debrief "
        f"oder gemeinsames Produkt verankert — nicht über ein einzelnes Arbeitsblatt), "
        f"gebunden an {resolution.fassung.bgbl} (DokNr {resolution.fassung.doknr})."
    )
    return Nachweis(
        fassung=resolution.fassung.model_dump(),
        statement=statement,
        competence_coverage=coverage,
        gaps=gaps,
        zentrale_konzepte=sorted(konzepte),
        uebergreifende_themen=sorted(uet),
    )


def assemble_arrangement(
    arr: Lernarrangement, resolution: LehrplanResolution,
    *, role_resolutions: dict[str, LehrplanResolution] | None = None,
) -> Lernarrangement:
    """Assemble each role's material (its own Nachweis/DepthProfile), then fill the
    arrangement-level DERIVED fields.

    `role_resolutions` maps a role id → the resolution to assemble THAT role against.
    A single-subject arrangement (GWB hero) needs none — every role shares `resolution`.
    A **fächerübergreifendes** bundle (Wave C3) does: each role is a different subject, so
    its material must be assembled against its OWN subject-grade resolution (else the
    per-role Nachweis lists other subjects' competences as gaps). The arrangement-level
    Nachweis is always derived against `resolution` (the shared, e.g. ÜT, universe)."""
    rr = role_resolutions or {}
    for role in arr.roles:
        assemble(role.material, rr.get(role.id, resolution))
    arr.depth_profile = _aggregate_depth(arr)
    arr.nachweis = derive_arrangement_nachweis(arr, resolution)
    return arr


def verify_arrangement(
    arr: Lernarrangement, resolution: LehrplanResolution,
    *, role_resolutions: dict[str, LehrplanResolution] | None = None,
) -> VerifyReport:
    """Every role's material verifies as a worksheet (kinds/dims/coverage/media);
    plus arrangement-level rules: roles exist, phases are well-formed, and every
    anchor references a resolved competence + a valid served_by.

    `role_resolutions` (see `assemble_arrangement`) lets a cross-subject bundle verify
    each role against its own subject-grade resolution; the anchors are checked against
    `resolution` (the shared universe the anchors must live in)."""
    problems: list[str] = []
    warnings: list[str] = []
    rr = role_resolutions or {}

    if not arr.roles:
        problems.append("arrangement has no roles")

    for role in arr.roles:
        rep = verify(role.material, rr.get(role.id, resolution))
        problems += [f"role '{role.id}': {p}" for p in rep.problems]
        warnings += [f"role '{role.id}': {w}" for w in rep.warnings]

    for ph in arr.phases:
        if ph.grouping not in GROUPINGS:
            problems.append(f"phase '{ph.id}': invalid grouping '{ph.grouping}'")
        if ph.minutes <= 0:
            warnings.append(f"phase '{ph.id}': non-positive minutes")

    valid_ids = {c.id for c in resolution.competences}
    role_ids = {r.id for r in arr.roles}
    if not arr.competence_anchors:
        warnings.append("no competence_anchors — an arrangement with no oral/social "
                        "anchor is just stapled worksheets")
    for a in arr.competence_anchors:
        if valid_ids and a.competence_id not in valid_ids:
            problems.append(f"anchor: unknown competence '{a.competence_id}'")
        ok = a.served_by in SERVED_BY or (
            a.served_by.startswith("role:") and a.served_by[5:] in role_ids)
        if not ok:
            problems.append(f"anchor '{a.competence_id}': invalid served_by '{a.served_by}'")

    return VerifyReport(ok=not problems, problems=problems, warnings=warnings)


def render_arrangement(arr: Lernarrangement, out_dir, assets: dict | None = None) -> dict:
    """Render the full bundle (the v0.5 contract): the teacher run-guide +, per role,
    a student handout AND a teacher copy (with answers, for running the room). The
    role sheets reuse the worksheet renderers untouched, so the no-drift guarantee
    carries over. This lives in the pipeline (not rendering/) because it builds asset
    images — the renderers themselves stay pure over schema."""
    from ..rendering.arrangement import render_teacher_orchestration
    from ..rendering.student_sheet import render_student_sheet
    from ..rendering.teacher_guide import render_teacher_guide
    from .assets import build_asset

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_assets: dict = dict(assets or {})
    roles_out = []
    for role in arr.roles:
        radir = out_dir / f"role_{role.id}_assets"
        rassets = {a.id: build_asset(a, outdir=radir)
                   for a in role.material.assets if a.generator}
        all_assets.update(rassets)
        student = render_student_sheet(role.material, out_dir / f"role_{role.id}_student.pdf", rassets)
        teacher = render_teacher_guide(role.material, out_dir / f"role_{role.id}_teacher.pdf", rassets)
        roles_out.append({"id": role.id, "label": role.label,
                          "student": str(student), "teacher": str(teacher)})
    orch = render_teacher_orchestration(arr, out_dir / "orchestration.pdf", all_assets)
    return {"orchestration": str(orch), "roles": roles_out}


def stage_arrangement(store, arr: Lernarrangement, *, arr_id: str | None = None,
                      source: str = "ai", today=None,
                      resolution: LehrplanResolution | None = None,
                      role_resolutions: dict[str, LehrplanResolution] | None = None):
    """Assemble → verify → render an arrangement and stage it as an ArrangementRecord
    for HITL review (the v0.5 analogue of orch.ingest_generated for worksheets).
    `arr_id` gives a stable id for idempotent seeding; otherwise the store assigns one.

    Single-subject arrangements resolve from `arr.meta.subject` automatically. A
    fächerübergreifendes bundle (Wave C3) passes a precomputed cross-subject `resolution`
    (its `arr.meta.subject` is an ÜT label, not a catalog subject) plus `role_resolutions`."""
    from .. import config
    from ..store.arrangementstore import ArrangementArtifacts, ArrangementRecord
    from .resolve import resolve_grade

    res = resolution or resolve_grade(arr.meta.subject, arr.meta.klasse, today=today)
    assemble_arrangement(arr, res, role_resolutions=role_resolutions)
    report = verify_arrangement(arr, res, role_resolutions=role_resolutions)
    rid = arr_id or store.next_id()
    bundle = render_arrangement(arr, config.RUNS_DIR / "arrangements" / rid)
    rec = ArrangementRecord(
        id=rid, arrangement=arr, title=arr.meta.title, source=source,
        verify_problems=report.problems,
        artifacts=ArrangementArtifacts(orchestration=bundle["orchestration"], roles=bundle["roles"]),
    )
    return store.upsert(rec)


def ingest_arrangement(store, subject: str, klasse: int, *, title: str, kernfrage: str,
                       format: str, body, arr_id: str | None = None, source: str = "ai",
                       today=None):
    """Up-convert a generated arrangement body → a `Lernarrangement` → stage it for
    review (the v0.5 analogue of `orch.ingest_generated`). `body` is a GenArrangementBody
    or its dict. Meta/subject_model/fassung come from the catalog, not the model."""
    from ..grounding import lehrplan_store as ls
    from ..schema.arrangement import ArrangementMeta
    from ..schema.generation_views import GenArrangementBody, arrangement_body_to_canonical

    model = ls.get_subject_model(subject)
    meta = ArrangementMeta(
        title=title, subject=subject, stufe="Unterstufe", klasse=klasse,
        kernfrage=kernfrage, fassung=ls.get_fassung(), format=format,
        lehrplan_label=f"{subject} · {klasse}. Kl.",
    )
    gb = body if isinstance(body, GenArrangementBody) else GenArrangementBody.model_validate(body)
    arr = arrangement_body_to_canonical(gb, meta=meta, subject_model=model)
    return stage_arrangement(store, arr, arr_id=arr_id, source=source, today=today)
