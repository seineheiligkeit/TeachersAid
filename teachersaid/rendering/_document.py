"""Shared PDF builder for all projections. Pure over WorksheetContent + a map of
already-rendered asset images (asset_id → png path). Imports only schema + base.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, SimpleDocTemplate

from ..schema.worksheet import WorksheetContent
from . import reportlab_base as rb
from .blocks_to_flowables import block_flowables, should_render

_TITLE_SUFFIX = {
    "student": "",
    "teacher": " — Lehrkraft-Begleitung",
    "homework": " — Hausübung",
}


def _content_width() -> float:
    return A4[0] - 2 * rb.PAGE_MARGIN


def _nachweis_story(content: WorksheetContent, S, width):
    out = [PageBreak(), rb.para("Nachweis (abgeleitet)", S["heading"])]
    n = content.nachweis
    if n is None:
        out.append(rb.para("— nicht berechnet —", S["body"]))
        return out
    out.append(rb.para(n.statement, S["body"]))
    rows = [["Kompetenz", "geübt durch", "Status"]]
    for c in n.competence_coverage:
        rows.append([
            c.competence_id,
            ", ".join(c.exercised_by) or "—",
            "✓ abgedeckt" if c.covered else "✗ LÜCKE",
        ])
    out.append(rb.grid_table(rows, width))
    if n.gaps:
        out.append(rb.spacer(2))
        out.append(rb.para("Abgedeckte Lücken (Geschwister-Baustein nötig):", S["label"]))
        for g in n.gaps:
            out.append(rb.para("✗ " + g, S["watch"]))
    if n.uebergreifende_themen:
        out.append(rb.para(
            "Übergreifende Themen: " + ", ".join(map(str, n.uebergreifende_themen)),
            S["meta"],
        ))

    dp = content.depth_profile
    if dp is not None:
        out.append(rb.spacer(3))
        out.append(rb.para("Tiefenprofil (abgeleitet)", S["heading"]))
        levels = " · ".join(f"{k}: {v}" for k, v in dp.by_level.items())
        dims = " · ".join(f"{k}: {v}" for k, v in dp.by_dimension.items())
        out.append(rb.para(f"Niveaus — {levels}", S["body"]))
        out.append(rb.para(f"Dimensionen — {dims}", S["body"]))
        out.append(rb.para(
            f"Zeit gesamt: {dp.minutes_total} min · "
            f"materialunabhängig: {dp.minutes_resource_independent} min",
            S["body"],
        ))
    return out


def build_pdf(
    content: WorksheetContent,
    projection: str,
    out_path: str | Path,
    assets: dict[str, Path] | None = None,
) -> Path:
    assets = assets or {}
    S = rb.styles()
    width = _content_width()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=rb.PAGE_MARGIN, rightMargin=rb.PAGE_MARGIN,
        topMargin=rb.PAGE_MARGIN, bottomMargin=rb.PAGE_MARGIN,
        title=content.meta.title + _TITLE_SUFFIX.get(projection, ""),
    )
    story = []
    story.append(rb.para(content.meta.title + _TITLE_SUFFIX.get(projection, ""), S["title"]))
    story.append(rb.para(content.meta.lehrplan_label, S["subtitle"]))
    if content.meta.kernfrage:
        story.append(rb.raw_para("Kernfrage: " + rb.richtext_markup(content.meta.kernfrage),
                                 S["kernfrage"]))
    f = content.meta.fassung
    story.append(rb.para(f"{f.bgbl} · DokNr {f.doknr} · gültig {f.valid_from}–{f.valid_to}",
                         S["meta"]))
    story.append(rb.spacer(3))

    task_no = 0
    for b in content.intro:
        if should_render(b, projection):
            story += block_flowables(b, projection, S, width, assets)

    for section in content.sections:
        story.append(rb.para(section.title, S["heading"]))
        if projection == "teacher":
            tl = section.teacher_overview.get("throughline")
            if tl:
                story.append(rb.para("Roter Faden: " + str(tl), S["teacher"]))
        for b in section.blocks:
            if not should_render(b, projection):
                continue
            if b.role == "task":
                task_no += 1
                story += block_flowables(b, projection, S, width, assets, number=task_no)
            else:
                story += block_flowables(b, projection, S, width, assets)

    if projection == "teacher":
        story += _nachweis_story(content, S, width)

    doc.build(story)
    return out_path
