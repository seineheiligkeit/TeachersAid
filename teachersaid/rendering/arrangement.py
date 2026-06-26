"""Teacher orchestration projection for a Lernarrangement (schema v0.5) — PURE.

The teacher's run-guide: the case, the phase timeline, the roles overview, the
shared product + rubric, the debrief, the **competence anchors** (the oral/social/
enactive band the worksheets can't reach), and the derived arrangement Nachweis.
Imports only schema + the rendering base — never pipeline. The role student/teacher
sheets are NOT produced here; they reuse `render_student_sheet`/`render_teacher_guide`
in the pipeline bundle (`renderArrangement = orchestration + roles.map(studentSheet)`).
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate

from ..schema.arrangement import Lernarrangement
from ..schema.enums import Role
from . import reportlab_base as rb
from ._document import _content_width, nachweis_story
from .blocks_to_flowables import block_flowables, should_render

_FORMAT_LABEL = {
    "simulation_game": "Planspiel", "role_debate": "Rollendebatte", "mystery": "Mystery",
    "jigsaw": "Gruppenpuzzle", "stations": "Stationenbetrieb",
}
_GROUPING_LABEL = {
    "individual": "Einzelarbeit", "role_group": "Gruppen-/Fraktionsarbeit",
    "home_group": "Stammgruppe", "plenary": "Plenum",
}
_SERVED_BY_LABEL = {
    "interaction": "Interaktion / Debatte", "debrief": "Reflexion (Debrief)",
    "shared_product": "Gemeinsames Produkt",
}


def _served_by_label(served_by: str, role_labels: dict[str, str]) -> str:
    if served_by.startswith("role:"):
        rid = served_by[5:]
        return f"Rolle: {role_labels.get(rid, rid)}"
    return _SERVED_BY_LABEL.get(served_by, served_by)


def render_teacher_orchestration(
    arr: Lernarrangement, out_path, assets: dict[str, Path] | None = None
) -> Path:
    assets = assets or {}
    S = rb.styles()
    width = _content_width()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    m = arr.meta
    role_labels = {r.id: r.label for r in arr.roles}

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=rb.PAGE_MARGIN, rightMargin=rb.PAGE_MARGIN,
        topMargin=rb.PAGE_MARGIN, bottomMargin=rb.PAGE_MARGIN,
        title=m.title + " — Lehrkraft-Begleitung (Lernarrangement)",
    )
    story = [rb.para(m.title + " — Lehrkraft-Begleitung (Lernarrangement)", S["title"])]
    if m.subtitle:
        story.append(rb.para(m.subtitle, S["subtitle"]))
    story.append(rb.para(m.lehrplan_label, S["subtitle"]))
    fmt = _FORMAT_LABEL.get(m.format, m.format)
    story.append(rb.para(
        f"Format: {fmt} · Dauer gesamt: {arr.total_minutes()} min · {len(arr.roles)} Rollen",
        S["meta"]))
    if m.kernfrage:
        story.append(rb.raw_para("Kernfrage: " + rb.richtext_markup(m.kernfrage), S["kernfrage"]))
    f = m.fassung
    story.append(rb.para(
        f"{f.bgbl} · DokNr {f.doknr} · gültig {f.valid_from}–{f.valid_to}", S["meta"]))
    story.append(rb.spacer(3))

    # 1. the shared briefing
    if arr.common_material:
        story.append(rb.para("Der Fall — gemeinsames Briefing", S["heading"]))
        for b in arr.common_material:
            if should_render(b, "teacher"):
                story += block_flowables(b, "teacher", S, width, assets)

    # 2. the phase timeline
    if arr.phases:
        story.append(rb.para("Ablauf", S["heading"]))
        rows = [["#", "Phase", "Sozialform", "Min", "Was passiert"]]
        for i, ph in enumerate(arr.phases, 1):
            rows.append([str(i), ph.label, _GROUPING_LABEL.get(ph.grouping, ph.grouping),
                         str(ph.minutes), rb.richtext_markup(ph.what_happens)])
        cw = [w * width for w in (0.04, 0.20, 0.18, 0.06, 0.52)]
        # the "Was passiert" column carries markup → pre-build that cell as raw_para
        data = [rows[0]] + [
            [r[0], r[1], r[2], r[3], rb.raw_para(r[4], S["body"])] for r in rows[1:]
        ]
        story.append(rb.wrapped_table(data, cw))

    # 3. roles overview (each role's sheet is a separate student worksheet)
    if arr.roles:
        story.append(rb.para("Rollen / Fraktionen", S["heading"]))
        story.append(rb.para("Jede Rolle erhält ihr eigenes Arbeitsblatt (Schüler-Projektion).",
                             S["meta"]))
        rows = [["Rolle", "Anteil", "Schwerpunkt-Kompetenzen (Arbeitsblatt)"]]
        for role in arr.roles:
            served = sorted({s.competence_id for b in role.material.iter_blocks()
                             if b.role == Role.TASK for s in b.serves})
            rows.append([role.label, str(role.share), ", ".join(served) or "—"])
        cw = [w * width for w in (0.30, 0.12, 0.58)]
        story.append(rb.wrapped_table(rows, cw))

    # 4. the shared product + rubric
    if arr.shared_product:
        story.append(rb.para("Gemeinsames Produkt", S["heading"]))
        story.append(rb.raw_para(rb.richtext_markup(arr.shared_product.description), S["body"]))
        if arr.shared_product.rubric:
            rows = [["Kriterium", "Stufen (niedrig → hoch)"]]
            for rc in arr.shared_product.rubric:
                rows.append([rc.criterion, "  →  ".join(rc.levels)])
            cw = [w * width for w in (0.32, 0.68)]
            story.append(rb.wrapped_table(rows, cw))

    # 5. debrief
    if arr.debrief:
        story.append(rb.para("Debrief / Reflexion", S["heading"]))
        for b in arr.debrief:
            if should_render(b, "teacher"):
                story += block_flowables(b, "teacher", S, width, assets)

    # 6. the competence anchors — the oral/social/enactive band a worksheet can't reach
    if arr.competence_anchors:
        story.append(rb.para("Kompetenz-Verankerung (über die Interaktion)", S["heading"]))
        story.append(rb.para(
            "Diese Kompetenzen werden durch das Arrangement selbst erreicht — nicht durch "
            "ein einzelnes Arbeitsblatt.", S["meta"]))
        rows = [["Kompetenz", "Dimension", "verankert über"]]
        for a in arr.competence_anchors:
            rows.append([a.competence_id, a.dimension,
                         _served_by_label(a.served_by, role_labels)])
        cw = [w * width for w in (0.38, 0.18, 0.44)]
        story.append(rb.wrapped_table(rows, cw))

    # 7. derived arrangement Nachweis + Tiefenprofil
    story.append(PageBreak())
    story += nachweis_story(arr.nachweis, arr.depth_profile, S, width, page_break=False)

    doc.build(story)
    return out_path
