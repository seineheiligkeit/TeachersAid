"""Parametric figure emission — a recipe emits a per-instance figure onto its variant.

The seam: `Instance.figure` (a code-gen asset request) → `instantiate` assigns a UNIQUE
per-variant asset id and wires it onto the block's `asset_refs` → `variant_worksheet`
collects them onto the worksheet. Locked here:

* the figure is COMPUTED from the sampled values and MASKS the asked unknown — the numeric
  answer value never appears anywhere in the figure spec ("c = ?"), so a figure can't leak
  the answer (the core invariant);
* asset ids are unique across variants (else the PNGs overwrite one another);
* the figures pass the media-policy gate (role="figure", code-gen backend) and verify clean;
* a Pythagoras / circle / Baumdiagramm worksheet assembles, verifies AND renders — the PNGs
  actually build and embed in the student/teacher PDFs;
* the Boxplot decision is LOCKED: no solution figure is emitted (a task figure renders on the
  student sheet too — there is no teacher-only asset channel — so it would leak the summary).
"""

from __future__ import annotations

import re
from datetime import date

import fitz

from teachersaid.library.templates import find_template, variant_worksheet
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.media_policy import check_content
from teachersaid.pipeline.parametrize import _RECIPES, make_variants_with_assets
from teachersaid.pipeline.verify import verify
from teachersaid.rendering.student_sheet import render_student_sheet
from teachersaid.rendering.teacher_guide import render_teacher_guide

PNG = b"\x89PNG\r\n\x1a\n"
IN_WINDOW = date(2026, 3, 1)


def _flat(rt) -> str:
    return rt if isinstance(rt, str) else "".join(getattr(r, "text", "") for r in rt)


def _pairs(tid: str, n: int):
    """(block, its figure asset) for each variant, correlated by asset_ref."""
    blocks, assets = make_variants_with_assets(find_template(tid), n, seed0=1)
    by_id = {a.id: a for a in assets}
    return [(b, by_id[b.asset_refs[0]]) for b in blocks if b.asset_refs], assets


# --- the seam: unique ids, wired onto the block ------------------------------
def test_figure_ids_unique_across_variants_and_wired():
    for tid in ("mat-pythagoras", "mat-kreis", "mat-ws-baumdiagramm"):
        pairs, assets = _pairs(tid, 6)
        assert len(pairs) == 6                              # every variant emits a figure
        assert len({a.id for a in assets}) == 6            # UNIQUE per variant (no PNG overwrite)
        for blk, asset in pairs:
            assert blk.asset_refs == [asset.id]            # wired onto the block by id
            assert asset.role == "figure"                  # → media-policy must_be_code lane
            assert (asset.generator or "").startswith("matplotlib:")   # code-gen backend


# --- the core invariant: the figure masks the asked unknown, never leaks ------
def test_pythagoras_figure_masks_the_asked_side():
    pairs, _ = _pairs("mat-pythagoras", 8)
    for blk, asset in pairs:
        assert asset.generator == "matplotlib:right_triangle"
        spec = asset.spec
        labels = [spec["label_a"], spec["label_b"], spec["label_c"]]
        assert sum(str(v).strip().endswith("?") for v in labels) == 1   # exactly one masked "?"
        # the numeric answer value never appears on the VISIBLE figure text (labels + title):
        # the asked side reads "x = ?", the other two show the givens (≠ the answer)
        ans = int(re.search(r"= (\d+) cm", _flat(blk.answer_key)).group(1))
        shown = " ".join([*labels, str(spec.get("title", ""))])
        assert not re.search(rf"\b{ans}\b", shown), (ans, shown)
        # the drawing lengths are normed onto the hypotenuse (∈ (0,1)) — proportions, not the
        # integer answer, so even the geometry coordinates can't hand a leg's value over
        assert 0 < spec["a"] < 1 and 0 < spec["b"] < 1 and spec["a"] != ans and spec["b"] != ans


def test_kreis_figure_shows_only_the_given_radius():
    pairs, _ = _pairs("mat-kreis", 5)
    for blk, asset in pairs:
        assert asset.generator == "matplotlib:circle"
        assert set(asset.spec) <= {"radius", "label_r", "title"}       # only the given radius
        # the computed circumference/area (the unknowns) are not drawn → cannot leak
        for approx in re.findall(r"≈ ([\d,]+)", _flat(blk.answer_key)):
            assert approx not in str(asset.spec)


def test_probability_tree_scaffold_hides_the_asked_result():
    pairs, _ = _pairs("mat-ws-baumdiagramm", 6)
    for blk, asset in pairs:
        assert asset.generator == "matplotlib:tree_diagram"
        branches = asset.spec["branches"]
        assert all("p" in br for br in branches)                       # 1st stage: labelled
        assert all("p" not in c for br in branches for c in br["children"])   # 2nd: unlabelled
        # every asked quantity (path product · sum of paths · conditional) needs the hidden
        # 2nd stage, so the answer fraction is never written on the tree
        assert blk.answer_key[0].text not in [br["p"] for br in branches]


# --- media-policy + verify are clean with the figures on the sheet ------------
def test_figure_worksheets_media_policy_and_verify_clean():
    for tid in ("mat-pythagoras", "mat-kreis", "mat-ws-baumdiagramm"):
        content, res = variant_worksheet(find_template(tid), 4, today=IN_WINDOW)
        assert content.assets and all(a.role == "figure" for a in content.assets)
        problems, _ = check_content(content)                # the asset library-entry gate
        assert not problems, (tid, problems)
        content = assemble(content, res)
        report = verify(content, res)
        assert not report.problems, (tid, report.problems)  # code-gen figures → verify-clean


# --- the full product path: assemble → build the PNGs → render ----------------
def test_pythagoras_worksheet_renders_with_figure_pngs(tmp_path):
    content, res = variant_worksheet(find_template("mat-pythagoras"), 3, today=IN_WINDOW)
    content = assemble(content, res)
    assets = {a.id: build_asset(a, outdir=tmp_path / "assets") for a in content.assets}
    assert len(assets) == 3
    for p in assets.values():
        assert p.exists() and p.read_bytes()[:8] == PNG    # a real PNG was built
    for render in (render_student_sheet, render_teacher_guide):
        out = render(content, tmp_path / f"{render.__name__}.pdf", assets)
        assert out.exists() and out.stat().st_size > 1000
    # the figures actually embed in the student PDF (an image XObject on the page)
    doc = fitz.open(tmp_path / "render_student_sheet.pdf")
    assert sum(len(page.get_images()) for page in doc) >= 3


def test_probability_tree_worksheet_renders_with_trees(tmp_path):
    content, res = variant_worksheet(find_template("mat-ws-baumdiagramm"), 3, today=IN_WINDOW)
    content = assemble(content, res)
    assets = {a.id: build_asset(a, outdir=tmp_path / "assets") for a in content.assets}
    assert len(assets) == 3 and all(p.read_bytes()[:8] == PNG for p in assets.values())
    out = render_student_sheet(content, tmp_path / "tree_student.pdf", assets)
    assert sum(len(page.get_images()) for page in fitz.open(out)) >= 3


# --- the Boxplot decision: NO figure (it would leak the five-number summary) ---
def test_boxplot_recipe_emits_no_figure():
    """Investigated + locked: assets render to students too, so a solution boxplot would
    hand over Q1/Median/Q3/Min/Max. The recipe therefore emits no figure."""
    seen = 0
    for seed in range(20):
        try:
            inst = _RECIPES["boxplot_from_data"](__import__("random").Random(seed))
        except Exception:
            continue                                        # Unsuitable draw → skip
        seen += 1
        assert inst.figure is None                          # deliberately no figure
    assert seen >= 3
    # and no figure asset reaches a boxplot worksheet
    blocks, assets = make_variants_with_assets(find_template("mat-ws-boxplot"), 5, seed0=1)
    assert assets == [] and all(not b.asset_refs for b in blocks)


def test_task_figures_render_on_the_student_sheet(tmp_path):
    """The load-bearing reason the boxplot figure is withheld: a task's `asset_refs` are
    embedded on EVERY projection (no teacher-only asset channel), so any solution figure
    would reach the student. Proven here with the Pythagoras figure."""
    content, res = variant_worksheet(find_template("mat-pythagoras"), 1, today=IN_WINDOW)
    content = assemble(content, res)
    assets = {a.id: build_asset(a, outdir=tmp_path / "a") for a in content.assets}
    out = render_student_sheet(content, tmp_path / "student.pdf", assets)
    assert any(page.get_images() for page in fitz.open(out))
