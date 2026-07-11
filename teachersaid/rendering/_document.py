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

# display labels for the derived Anforderungsband (schema keys are "1"/"2"/"3");
# local on purpose — rendering imports only schema, never pipeline.
_DIFF_LABEL = {"1": "leicht", "2": "mittel", "3": "anspruchsvoll"}


def _content_width() -> float:
    return A4[0] - 2 * rb.PAGE_MARGIN


def nachweis_story(nachweis, depth_profile, S, width, *, page_break: bool = True):
    """Render a derived Nachweis + DepthProfile. Shared by the worksheet teacher
    projection and the Lernarrangement run-guide (both carry the same DERIVED types)."""
    out = ([PageBreak()] if page_break else []) + [rb.para("Nachweis (abgeleitet)", S["heading"])]
    n = nachweis
    if n is None:
        out.append(rb.para("— nicht berechnet —", S["body"]))
        return out
    out.append(rb.para(n.statement, S["body"]))
    mode_label = {
        "competence": "Lehrplan-Kompetenzen",
        "uet": "Übergreifendes Thema (ÜT)",
        "horizont": "Horizont — freiwillige Vertiefung",
    }.get(str(n.anchor_mode), n.anchor_label)
    out.append(rb.para(f"Verankerungsmodus: {mode_label}", S["label"]))
    if str(n.anchor_mode) == "uet":
        out.append(rb.para(f"Verbatim Hook: {n.anchor_label}", S["key_fact"]))
    if n.competence_coverage:
        rows = [["Kompetenz", "geübt durch", "Status"]]
        for c in n.competence_coverage:
            status = (
                "✓ abgedeckt" if c.covered else
                "↗ Voraussetzung" if c.prerequisite_by else
                "✗ LÜCKE"
            )
            rows.append([
                c.competence_id,
                ", ".join(c.exercised_by) or "—",
                status,
            ])
        out.append(rb.grid_table(rows, width))
    if n.gaps and str(n.anchor_mode) == "competence":
        out.append(rb.spacer(2))
        out.append(rb.para("Abgedeckte Lücken (Geschwister-Baustein nötig):", S["label"]))
        for g in n.gaps:
            out.append(rb.para("✗ " + g, S["watch"]))
    if n.uebergreifende_themen and str(n.anchor_mode) == "competence":
        out.append(rb.para(
            "Übergreifende Themen: " + ", ".join(map(str, n.uebergreifende_themen)),
            S["meta"],
        ))

    dp = depth_profile
    if dp is not None:
        out.append(rb.spacer(3))
        out.append(rb.para("Tiefenprofil (abgeleitet)", S["heading"]))
        levels = " · ".join(f"{k}: {v}" for k, v in dp.by_level.items())
        dims = " · ".join(f"{k}: {v}" for k, v in dp.by_dimension.items())
        out.append(rb.para(f"Niveaus — {levels}", S["body"]))
        out.append(rb.para(f"Dimensionen — {dims}", S["body"]))
        if dp.by_difficulty:
            bands = " · ".join(f"{_DIFF_LABEL.get(k, k)}: {v}"
                               for k, v in sorted(dp.by_difficulty.items()))
            out.append(rb.para(f"Anforderungsbänder — {bands}", S["body"]))
        out.append(rb.para(
            f"Zeit gesamt: {dp.minutes_total} min · "
            f"materialunabhängig: {dp.minutes_resource_independent} min",
            S["body"],
        ))
    return out


def _teacher_overview_story(ov, S):
    """The section's teacher 'rough guide': Roter Faden + talking points + extensions
    (+ logistics). Teacher projection only — never reaches the student sheet."""
    out = []
    if ov.throughline:
        out.append(rb.para("Roter Faden: " + ov.throughline, S["teacher"]))
    if ov.talking_points:
        out.append(rb.para("Gesprächsanker:", S["label"]))
        out += [rb.para("• " + tp, S["teacher"]) for tp in ov.talking_points]
    if ov.extensions:
        out.append(rb.para("Erweiterung / Vertiefung:", S["label"]))
        out += [rb.para("• " + ex, S["teacher"]) for ex in ov.extensions]
    if ov.differentiation:
        out.append(rb.para("Differenzierung: " + ov.differentiation, S["teacher"]))
    if ov.timing_notes:
        out.append(rb.para("Timing: " + ov.timing_notes, S["meta"]))
    return out


def build_pdf(
    content: WorksheetContent,
    projection: str,
    out_path: str | Path,
    assets: dict[str, Path] | None = None,
) -> Path:
    assets = assets or {}
    # figure_id → "Quelle: …" line, from each asset's resolved data_source (filled by
    # assemble). Kept on the content object so this stays a pure projection.
    citations = {a.id: a.data_source.citation()
                 for a in content.assets if a.data_source}
    S = rb.styles()
    width = _content_width()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from . import inline_math
    inline_math.configure(out_path.parent / "math")   # inline LaTeX runs → PNGs here

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=rb.PAGE_MARGIN, rightMargin=rb.PAGE_MARGIN,
        topMargin=rb.PAGE_MARGIN, bottomMargin=rb.PAGE_MARGIN,
        title=content.meta.title + _TITLE_SUFFIX.get(projection, ""),
    )
    story = []
    rendered_title = content.meta.title + _TITLE_SUFFIX.get(projection, "")
    theme_path = assets.get(content.theme_asset) if content.theme_asset else None
    story.append(rb.title_with_vignette(rendered_title, S["title"], width, theme_path)
                 if theme_path else rb.para(rendered_title, S["title"]))
    if content.meta.subtitle:                     # genre label (e.g. "Übungsreihe — …")
        story.append(rb.para(content.meta.subtitle, S["subtitle"]))
    story.append(rb.para(content.meta.lehrplan_label, S["subtitle"]))
    if content.meta.kernfrage:
        story.append(rb.raw_para("Kernfrage: " + rb.richtext_markup(content.meta.kernfrage),
                                 S["kernfrage"]))
    # The Fassung stamp is regulatory provenance for the teacher's copy — students
    # (and the homework that goes home) don't need it.
    if projection == "teacher":
        f = content.meta.fassung
        story.append(rb.para(f"{f.bgbl} · DokNr {f.doknr} · gültig {f.valid_from}–{f.valid_to}",
                             S["meta"]))
        if content.mixer_profile is not None:
            profile = content.mixer_profile
            settings = [f"Umfang: {profile.umfang.value}"]
            depth_labels = {
                "ueben": "üben",
                "strategien_vergleichen": "Strategien vergleichen",
            }
            settings += ([f"Tiefe: {depth_labels[profile.tiefe.value]}"]
                         if profile.tiefe else [])
            settings += ([f"Abstraktion: {profile.abstraktion.value}"]
                         if profile.abstraktion else [])
            settings += [f"Offenheit: {profile.offenheit.value}"] if profile.offenheit else []
            lint = content.mixer_lint
            lint_stamp = ("bestanden" if lint and lint.passed else "nicht bestanden")
            story.append(rb.para(
                "Mischpult-Profil · " + " · ".join(settings)
                + f" · Regler-Lint: {lint_stamp}",
                S["meta"],
            ))
    story.append(rb.spacer(3))

    task_no = 0
    for b in content.intro:
        if should_render(b, projection):
            story += block_flowables(b, projection, S, width, assets, citations=citations)

    for section in content.sections:
        story.append(rb.para(section.title, S["heading"]))
        if projection == "teacher":
            story += _teacher_overview_story(section.teacher_overview, S)
        for b in section.blocks:
            if not should_render(b, projection):
                continue
            if b.role == "task":
                task_no += 1
                story += block_flowables(b, projection, S, width, assets,
                                         number=task_no, citations=citations)
            else:
                story += block_flowables(b, projection, S, width, assets, citations=citations)

    if projection == "teacher":
        story += nachweis_story(content.nachweis, content.depth_profile, S, width)

    doc.build(story)
    return out_path
