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


def test_shipped_phy_catalog_is_clean_and_resolves():
    assert pre.lint("PHY") == []                        # the shipped graph lints clean
    edges = pre.load_edges("PHY")
    valid = pre.valid_ids("PHY")
    refs = set(edges) | {r for reqs in edges.values() for r in reqs}
    assert refs, "catalog must have edges"
    assert refs <= valid, f"every edge id resolves against the Lehrplan: {refs - valid}"
    # cross-Klasse and reaching into the Oberstufe (mirrors the MAT precedent)
    assert any(".OS." in cid for cid in edges)
    pairs = sum(len(v) for v in edges.values())
    assert pairs >= 25, f"a connected, defensible graph (got {pairs} edges)"


def test_shipped_che_catalog_is_clean_and_resolves():
    assert pre.lint("CHE") == []                        # the shipped graph lints clean
    edges = pre.load_edges("CHE")
    valid = pre.valid_ids("CHE")
    refs = set(edges) | {r for reqs in edges.values() for r in reqs}
    assert refs, "catalog must have edges"
    assert refs <= valid, f"every edge id resolves against the Lehrplan: {refs - valid}"
    pairs = sum(len(v) for v in edges.values())
    assert pairs >= 25, f"a connected, defensible graph (got {pairs} edges)"
    # Chemie US is single-Klasse + process-only, so the whole graph lives in the
    # Oberstufe (7. -> 8. Klasse across semesters) — see the catalog description.
    assert all(".OS." in cid for cid in edges), "CHE graph is Oberstufe-only"
    assert all(".OS." in r for reqs in edges.values() for r in reqs)


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
    assert pq.ancestors("DEU.US.1.LES.01") == set()


def test_queries_on_phy_graph():
    # the Energie strand integrates BOTH mechanics and electricity (a cross-KB node)
    assert pq.ancestors("PHY.US.3.ENE.01") == {"PHY.US.3.MEC.01", "PHY.US.3.ELE.01"}
    # a deep 4. Klasse chain: Klimaschutz builds on the energy/heat tower
    assert {"PHY.US.4.WET.02", "PHY.US.3.ENE.01", "PHY.US.3.ELE.01"} <= pq.ancestors(
        "PHY.US.4.WET.05")
    assert pq.depth("PHY.US.4.WET.05") >= 4
    # a US Kompetenz is an ancestor of an OS one (the graph spans Stufen, like MAT)
    assert "PHY.US.3.ELE.01" in pq.ancestors("PHY.OS.6.ELE.01")
    # the Optik (2. Kl) -> Strahlung (4. Kl) -> Kernphysik (OS) thread reaches the light model
    assert "PHY.US.2.OPT.04" in pq.ancestors("PHY.OS.8.KER.01")
    assert pq.depth("PHY.US.3.MEC.01") == 0                  # a root
    # SEH.01 (Sender-Empfaenger-Modell) is a high-leverage foundational node
    assert pq.downstream_impact(["PHY.US.2.SEH.01"]) > 5


def test_queries_on_che_graph():
    # the Oberstufe content tower: Stoff-Teilchen -> Bindung -> Struktur -> organisch -> Biochemie
    anc = pq.ancestors("CHE.OS.8.CHE.01")                    # Lebensvorgaenge
    assert {"CHE.OS.7.MOD.01", "CHE.OS.7.MOD.04", "CHE.OS.8.STR2.01"} <= anc
    assert pq.depth("CHE.OS.8.CHE.01") >= 6                  # sits atop a deep tower
    # the Stoff-Teilchen-Konzept (MOD.01) is the root that gates essentially the whole graph
    assert pq.depth("CHE.OS.7.MOD.01") == 0
    assert pq.downstream_impact(["CHE.OS.7.MOD.01"]) > 20
    # a blocking_gaps sanity case: the root cell far outranks a leaf cell
    bg = pq.blocking_gaps({("root",): ["CHE.OS.7.MOD.01"], ("leaf",): ["CHE.OS.8.CHE.07"]})
    assert bg[("root",)] > bg[("leaf",)] == 0


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
    # PHY carries a US cross-Klasse graph, so its foundational US cells gate dependents
    phy = next(s for s in cov["subjects"]
               if s["code"] == "PHY" and s["stufe"] == "Unterstufe")
    assert max(c["blocks_dependents"] for c in phy["cells"]) > 0
    # CHE's graph is Oberstufe-only (US is single-Klasse, process-only): OS gates, US does not
    che_os = next(s for s in cov["subjects"]
                  if s["code"] == "CHE" and s["stufe"] == "Oberstufe")
    che_us = next(s for s in cov["subjects"]
                  if s["code"] == "CHE" and s["stufe"] == "Unterstufe")
    assert max(c["blocks_dependents"] for c in che_os["cells"]) > 0
    assert all(c["blocks_dependents"] == 0 for c in che_us["cells"])
    # a subject without any curated graph scores 0 everywhere
    deu = next(s for s in cov["subjects"] if s["code"] == "DEU")
    assert all(c["blocks_dependents"] == 0 for c in deu["cells"])
    # the gap export carries the leverage so the planner can rank by it
    gaps = campaign_gaps(bs, subject="MAT", stufe="Unterstufe")
    assert gaps and all("blocks_dependents" in g for g in gaps)
    assert max(g["blocks_dependents"] for g in gaps) > 10
