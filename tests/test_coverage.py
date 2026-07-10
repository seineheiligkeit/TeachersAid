"""Track 1 #1 — the coverage planner: per-(Stufe·subject·Klasse·KB) cells with
Anforderungsband spread and a campaign status, plus the exportable gap list."""

from __future__ import annotations

from teachersaid.library import seed_blocks
from teachersaid.stats import GREEN_MIN_TASKS, campaign_gaps, coverage_map
from teachersaid.store.blockstore import BlockStore


def _seeded(tmp_path) -> BlockStore:
    bs = BlockStore(tmp_path / "blocks")
    seed_blocks(bs)                      # the curated examples' blocks, approved
    return bs


def test_coverage_map_cells_and_status(tmp_path):
    cov = coverage_map(_seeded(tmp_path))
    phy = next(s for s in cov["subjects"] if s["code"] == "PHY")
    cell = next(c for c in phy["cells"]
                if c["klasse"] == 4 and "Strahlung" in c["kompetenzbereich"])
    assert cell["task_blocks"] >= 1
    expected = ("gruen" if cell["task_blocks"] >= GREEN_MIN_TASKS and not cell["missing_bands"]
                else "teil")
    assert cell["status"] == expected
    # statuses partition the cells, per subject and in the totals
    for s in cov["subjects"]:
        assert s["gruen"] + s["teil"] + s["leer"] == s["cells_total"]
    t = cov["totals"]
    assert t["cells"] == sum(s["cells_total"] for s in cov["subjects"])
    assert t["gruen"] + t["teil"] + t["leer"] == t["cells"]
    # both stages present (the Oberstufe catalog is part of the corpus target)
    assert {s["stufe"] for s in cov["subjects"]} == {"Unterstufe", "Oberstufe"}


def test_campaign_gaps_carry_brief_anchors(tmp_path):
    bs = _seeded(tmp_path)
    gaps = campaign_gaps(bs, stufe="Unterstufe", subject="PHY")
    assert gaps and all(g["status"] in ("teil", "leer") for g in gaps)
    g0 = gaps[0]
    # a gap row is a campaign brief anchor: KB + Klasse + verbatim competence ids
    assert g0["kompetenzbereich"] and g0["klasse"] in (1, 2, 3, 4)
    assert g0["competences"] and all(cid.startswith("PHY.") for cid in g0["competences"])
    assert isinstance(g0["missing_bands"], list)
