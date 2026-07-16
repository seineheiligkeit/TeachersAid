"""Gap-directed targeting for the breadth-campaign briefs (`tools/breadth_prompt.py`).

The selection policy and the injected `## Ziel-Lücken` section are pure functions over
`stats.campaign_gaps(...)` output, so they test without file I/O; two integration tests
(a seeded BlockStore + a redirected RUNS_DIR) lock the `--gaps` wiring and the honest
uniform/skip behaviour."""

from __future__ import annotations

import json

import tools.breadth_prompt as bp
from teachersaid.library import seed_blocks
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.repository import ReviewStore


def _gap(code, klasse, kb, status, *, dep=0, missing=None, comps=()):
    """A synthetic campaign_gaps row (the fields select/render read)."""
    return {"code": code, "klasse": klasse, "kompetenzbereich": kb, "status": status,
            "blocks_dependents": dep, "missing_bands": list(missing or []),
            "competences": list(comps)}


# --- selection policy (pure) -------------------------------------------------
def test_select_gap_targets_worst_first_and_distribution():
    gaps = [
        _gap("PHY", 2, "B", "teil", dep=9, missing=[3]),   # teil sorts AFTER any leer, despite dep
        _gap("PHY", 4, "A", "leer", dep=1),
        _gap("PHY", 1, "C", "leer", dep=5),                # higher leverage → first among leer
    ]
    # n == number of leer cells: both leer picked, teil left out; leverage orders C before A
    t2 = bp.select_gap_targets(gaps, 2)
    assert [c["kompetenzbereich"] for c in t2] == ["C", "A"]
    assert all(c["status"] == "leer" for c in t2)
    assert [c["n_kernfragen"] for c in t2] == [1, 1]
    assert sum(c["n_kernfragen"] for c in t2) == 2

    # more Kernfragen than gap cells → spread over min(n, len(gaps)); worst cell takes the extra
    t5 = bp.select_gap_targets(gaps, 5)
    assert len(t5) == 3
    assert [c["n_kernfragen"] for c in t5] == [2, 2, 1]
    assert sum(c["n_kernfragen"] for c in t5) == 5
    # the teil cell is only reached once every leer cell is covered (worst-first)
    assert t5[-1]["kompetenzbereich"] == "B" and t5[-1]["status"] == "teil"

    # fewer Kernfragen than gaps → exactly n cells, one each
    t1 = bp.select_gap_targets(gaps, 1)
    assert len(t1) == 1 and t1[0]["kompetenzbereich"] == "C" and t1[0]["n_kernfragen"] == 1


def test_select_gap_targets_no_gap_skip():
    # a subject with nothing open (or n<=0) yields no targets → the caller skips it
    assert bp.select_gap_targets([], 2) == []
    assert bp.select_gap_targets([_gap("PHY", 1, "A", "leer")], 0) == []


# --- the injected section (pure) ---------------------------------------------
def test_render_gap_section_carries_verbatim_competence_ids():
    targets = bp.select_gap_targets([
        _gap("PHY", 1, "Elektrizität", "leer", dep=2,
             comps=["PHY.US.1.EL.01", "PHY.US.1.EL.02"]),
        _gap("PHY", 3, "Wärme", "teil", missing=[2, 3], comps=["PHY.US.3.WA.01"]),
    ], 2)
    sec = bp.render_gap_section(targets)
    assert sec.startswith("\n## Ziel-Lücken")
    assert "VERBINDLICH" in sec and "Verbindlich" in sec
    # every verbatim competence id of every target cell is present as an anchor
    for cid in ("PHY.US.1.EL.01", "PHY.US.1.EL.02", "PHY.US.3.WA.01"):
        assert cid in sec
    # the per-cell distribution is stated, and the teil cell names its still-missing bands
    assert "Kernfrage(n)" in sec
    assert "noch fehlende Bänder: mittel, anspruchsvoll" in sec
    # an empty target set never yields a section (uniform stays byte-identical)
    assert bp.render_gap_section([]) == ""


# --- wiring: build() in both modes (seeded store, redirected RUNS_DIR) -------
_PHY_US = [("PHY", "Physik", "kb", False, None)]


def _build(tmp_path, monkeypatch, *, gaps, gen_dir):
    monkeypatch.setattr(bp, "RUNS_DIR", tmp_path)
    bs = BlockStore(tmp_path / "blocks")
    seed_blocks(bs)                                   # curated blocks, approved
    rs = ReviewStore(tmp_path / "review")             # empty corpus
    bp.build("Unterstufe", _PHY_US, 2, gen_dir, gaps=gaps, review_store=rs, block_store=bs)
    brief = (tmp_path / "ingest" / f"prompt_PHY.md").read_text("utf-8")
    manifest = json.loads((tmp_path / "ingest" / "manifest.json").read_text("utf-8"))
    return brief, next(m for m in manifest if m["code"] == "PHY")


def test_build_gap_mode_injects_targeted_section_and_manifest(tmp_path, monkeypatch):
    brief, entry = _build(tmp_path, monkeypatch, gaps=True, gen_dir="gen_test_gaps")
    # the brief carries the gap section with real PHY competence anchors
    assert "## Ziel-Lücken" in brief
    assert "PHY." in brief.split("## Ziel-Lücken", 1)[1].split("## Kompetenzen", 1)[0]
    # the manifest records the mode + the chosen cells (so campaign_status/operator see the aim)
    assert entry["targeting"] == "gaps"
    assert entry["targets"] and all(t["competences"] for t in entry["targets"])
    assert sum(t["n_kernfragen"] for t in entry["targets"]) == 2


def test_build_uniform_mode_has_no_gap_section(tmp_path, monkeypatch):
    brief, entry = _build(tmp_path, monkeypatch, gaps=False, gen_dir="gen_test_uniform")
    assert "Ziel-Lücken" not in brief
    assert entry["targeting"] == "uniform" and "targets" not in entry
