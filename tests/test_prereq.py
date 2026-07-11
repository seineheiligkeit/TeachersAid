"""Wave C1 — the competence prerequisite graph: lints, pure queries, the Diagnose-Blatt,
and the coverage-map leverage overlay."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.grounding import prerequisites as pre
from teachersaid.pipeline import prereq as pq
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.diagnose import build_worksheet
from teachersaid.pipeline.verify import verify
from teachersaid.schema.enums import Role
from teachersaid.store.blockstore import BlockStore

IN = date(2026, 3, 1)  # inside the Fassung window

# A small acyclic fixture:  A (root) <- B <- C ;  A <- D ;  {C, D} <- E
FIX = {"B": ["A"], "C": ["B"], "D": ["A"], "E": ["C", "D"]}


# --- deterministic lints (the structural guarantees) -------------------------
def test_lint_flags_dangling_self_and_cycle():
    valid = frozenset({"A", "B", "C"})
    # dangling: an id (or a requires) outside the catalog
    assert any("dangling" in p for p in pre._lint({"A": ["Z"]}, valid))
    assert any("dangling" in p for p in pre._lint({"ZZ": ["A"]}, valid))
    # self-edge
    assert any("self-edge" in p for p in pre._lint({"A": ["A"]}, valid))
    # cycle
    probs = pre._lint({"A": ["B"], "B": ["A"]}, valid)
    assert any("cycle" in p for p in probs)
    # a clean acyclic graph lints empty
    assert pre._lint({"B": ["A"], "C": ["B"]}, valid) == []


def test_find_cycle():
    assert pre._find_cycle(FIX) is None
    cyc = pre._find_cycle({"A": ["B"], "B": ["C"], "C": ["A"]})
    assert cyc is not None and cyc[0] == cyc[-1]  # a closed path


def test_load_raises_on_broken_catalog(monkeypatch):
    monkeypatch.setattr(pre, "load_catalog",
                        lambda code="MAT": {"edges": [{"competence_id": "MAT.US.1.ZAH.01",
                                                       "requires": ["MAT.US.1.ZAH.01"]}]})
    pre.load_edges.cache_clear()
    try:
        with pytest.raises(pre.PrerequisiteError):
            pre.load_edges("MAT")
    finally:
        pre.load_edges.cache_clear()  # drop the poisoned entry; real catalog reloads


# --- the shipped MAT catalog -------------------------------------------------
def test_shipped_mat_catalog_is_clean_and_resolves():
    assert pre.lint("MAT") == []                       # a test locks the shipped graph clean
    edges = pre.load_edges("MAT")
    valid = pre.valid_ids("MAT")
    refs = set(edges) | {r for reqs in edges.values() for r in reqs}
    assert refs, "catalog must have edges"
    assert refs <= valid, f"every edge id resolves against the Lehrplan: {refs - valid}"
    # genuinely cross-Klasse and reaching into the Oberstufe (the design intent)
    assert any(".OS." in cid for cid in edges)
    pairs = sum(len(v) for v in edges.values())
    assert pairs >= 40, f"a connected, defensible graph (got {pairs} edges)"


# --- pure queries (fixture ground truth) -------------------------------------
def test_queries_on_fixture():
    assert pq.prerequisites("E", edges=FIX) == ["C", "D"]
    assert pq.ancestors("E", edges=FIX) == {"A", "B", "C", "D"}
    assert pq.ancestors("A", edges=FIX) == set()             # a root has no prerequisites
    assert pq.dependents("A", edges=FIX) == {"B", "D"}
    assert pq.descendants("A", edges=FIX) == {"B", "C", "D", "E"}
    assert pq.depth("A", edges=FIX) == 0
    assert pq.depth("E", edges=FIX) == 3                     # E->C->B->A is the longest chain
    assert pq.downstream_impact(["A"], edges=FIX) == 4
    assert pq.downstream_impact(["B", "D"], edges=FIX) == 2  # {C,E} ∪ {E}, minus the cell itself
    assert pq.blocking_gaps({("x",): ["A"], ("y",): ["E"]}, edges=FIX) == {("x",): 4, ("y",): 0}


def test_queries_on_shipped_graph():
    # Bruchrechnung → Prozentrechnung: an authored, catalog-anchored chain
    anc = pq.ancestors("MAT.US.2.ZAH.04")
    assert "MAT.US.2.ZAH.03" in anc and "MAT.US.1.ZAH.01" in anc
    # a US competence is an ancestor of an OS one (the graph spans Stufen)
    assert "MAT.US.3.VAR.04" in pq.ancestors("MAT.OS.6.REE.03")
    assert pq.depth("MAT.OS.6.REE.03") >= 4                  # sits atop a deep tower
    assert pq.depth("MAT.US.1.ZAH.01") == 0                  # a root
    # a subject without a catalog degrades to an empty graph (no error)
    assert pq.ancestors("PHY.US.4.STR.01") == set()


# --- the Diagnose-Blatt (the first consumer) ---------------------------------
def _seeded(tmp_path, monkeypatch) -> BlockStore:
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.library.diagnose import seed_diagnose_blocks
    bs = BlockStore(tmp_path / "blocks")
    seed_diagnose_blocks(bs)
    return bs


def test_diagnose_fully_covered_node(tmp_path, monkeypatch):
    """Prozentrechnung (MAT.US.2.ZAH.04): every prerequisite ancestor has a seeded band-1
    check, so the sheet is task-complete, verify-clean, and every task serves a resolved
    competence."""
    bs = _seeded(tmp_path, monkeypatch)
    content, res = build_worksheet("Mathematik", "MAT.US.2.ZAH.04", 2, block_store=bs, today=IN)
    tasks = [b for b in content.iter_blocks() if b.role == Role.TASK]
    assert len(tasks) == len(pq.ancestors("MAT.US.2.ZAH.04")) == 5
    assemble(content, res)
    report = verify(content, res)
    assert report.problems == [], report.problems
    valid = {c.id for c in res.competences}
    assert all(any(s.competence_id in valid for s in t.serves) for t in tasks)
    # no gap lines when everything is covered (only the summary note)
    assert not any("Lücke für die Wunschliste" in n for n in res.notes)


def test_diagnose_reports_honest_gaps(tmp_path, monkeypatch):
    """Wachstum/Zinsrechnung (MAT.US.3.VAR.04): some prerequisites have no approved task —
    those become honest gap notes, and the sheet still assembles + verifies clean."""
    bs = _seeded(tmp_path, monkeypatch)
    content, res = build_worksheet("Mathematik", "MAT.US.3.VAR.04", 3, block_store=bs, today=IN)
    tasks = [b for b in content.iter_blocks() if b.role == Role.TASK]
    assert tasks, "the covered prerequisites still yield tasks"
    gaps = [n for n in res.notes if "Lücke für die Wunschliste" in n]
    assert gaps, "uncovered prerequisites are surfaced as honest gaps"
    # the uncovered ancestors are named in the gaps, not silently dropped
    assert any("MAT.US.3.VAR.02" in g for g in gaps)
    assemble(content, res)
    assert verify(content, res).problems == []


def test_diagnose_via_orchestrator(tmp_path, monkeypatch):
    """The normal orch staging path produces a Gate-2 content item with rendered artifacts."""
    bs = _seeded(tmp_path, monkeypatch)
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.repository import ReviewStore
    rs = ReviewStore(tmp_path / "store")
    item = orch.compose_diagnose_worksheet(rs, bs, "Mathematik", "MAT.US.2.ZAH.04", 2, today=IN)
    assert item.stage == "content" and item.source == "diagnose"
    assert item.error is None, item.error
    assert item.content and item.artifacts and item.artifacts.student_pdf
    assert item.content.nachweis is not None


# --- the coverage-map leverage overlay ---------------------------------------
def test_coverage_map_blocks_dependents(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.stats import campaign_gaps, coverage_map
    bs = BlockStore(tmp_path / "blocks")            # empty is fine — the overlay is graph-only
    cov = coverage_map(bs)
    mat = next(s for s in cov["subjects"] if s["code"] == "MAT" and s["stufe"] == "Unterstufe")
    # the foundational Kl.1 "Zahlen und Maße" cell gates a large downstream subtree
    zah1 = next(c for c in mat["cells"]
                if c["klasse"] == 1 and c["kompetenzbereich"].startswith("1:"))
    assert zah1["blocks_dependents"] > 10
    # a subject without a curated graph scores 0 everywhere
    phy = next(s for s in cov["subjects"] if s["code"] == "PHY")
    assert all(c["blocks_dependents"] == 0 for c in phy["cells"])
    # the gap export carries the leverage so the planner can rank by it
    gaps = campaign_gaps(bs, subject="MAT", stufe="Unterstufe")
    assert gaps and all("blocks_dependents" in g for g in gaps)
    assert max(g["blocks_dependents"] for g in gaps) > 10
