"""Curated competence *prerequisite* edges — a didactic-judgment grounding layer.

**The pattern.** A prerequisite edge says "to work on competence X a student should
already be able to Y" (Bruchrechnung → Prozentrechnung → Zinsrechnung). Unlike the
Lehrplan competences (verbatim facts) these edges are **not in the source** — they are
a **curated didactic-judgment layer** (the same status as the empirical operator
definitions): *authored-then-SME-vetted*, provenance recorded as ``didactic judgment,
SME-gated`` in each catalog's header, staged for review. So the honest discipline is
split cleanly:

* **deterministic lints GUARANTEE the structure** — no cycles, no dangling ids, no
  self-edges (run at load; a test locks the shipped catalog clean), and
* **the SME vets the didactics** (is *this* the right prerequisite?).

**One catalog per subject.** ``<CODE>.json`` (e.g. ``MAT.json``) holds a header +
``edges: [{competence_id, requires: [competence_id...], note?}]``. Every id is validated
against that subject's Lehrplan catalog — **both Stufen** (edges are cross-Klasse *within
a subject* and legitimately reach Unterstufe → Oberstufe where the texts chain). This is
grounding only — the graph is loaded here; the pure queries live in ``pipeline/prereq.py``.

Add a subject = add ``<CODE>.json`` (start with MAT — the cleanest structure — then
PHY/CHE). Correct an edge = edit the JSON, no engine change.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DIR = Path(__file__).resolve().parent  # this package's folder (holds the <CODE>.json catalogs)


class PrerequisiteError(ValueError):
    """A prerequisite catalog violates a deterministic structural guarantee
    (cycle / dangling id / self-edge). Raised at load — never shipped."""


@lru_cache(maxsize=8)
def valid_ids(code: str = "MAT") -> frozenset[str]:
    """Every catalog competence id for a subject, across BOTH Stufen — the id universe
    an edge may reference (edges are cross-Klasse within a subject, US → OS included)."""
    from ..lehrplan_store import _subject  # parent package (grounding); local import avoids cycle

    ids: set[str] = set()
    for stufe in ("Unterstufe", "Oberstufe"):
        data = _subject(code, stufe)
        if data:
            ids.update(c["id"] for c in data.get("competences", []))
    return frozenset(ids)


@lru_cache(maxsize=8)
def load_catalog(code: str = "MAT") -> dict | None:
    """The raw catalog dict for a subject, or None when no catalog is curated yet
    (so a subject without a prerequisite graph degrades gracefully to no edges)."""
    p = _DIR / f"{code}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _edge_map(catalog: dict) -> dict[str, list[str]]:
    """competence_id -> its direct prerequisite ids (later entries merge, order kept)."""
    out: dict[str, list[str]] = {}
    for e in catalog.get("edges", []):
        cid = e["competence_id"]
        reqs = out.setdefault(cid, [])
        for r in e.get("requires", []):
            if r not in reqs:
                reqs.append(r)
    return out


def _find_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    """Return a cycle as an id path (first found) or None. DFS over the requires-graph;
    a back-edge to a node on the current stack is a cycle."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        colour[node] = GREY
        stack.append(node)
        for nxt in edges.get(node, []):
            c = colour.get(nxt, WHITE)
            if c == GREY:  # back-edge → cycle from nxt … node → nxt
                return stack[stack.index(nxt):] + [nxt]
            if c == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        colour[node] = BLACK
        return None

    for n in edges:
        if colour.get(n, WHITE) == WHITE:
            found = visit(n)
            if found:
                return found
    return None


def _lint(edges: dict[str, list[str]], valid: frozenset[str]) -> list[str]:
    """The deterministic structural guarantees: dangling ids, self-edges, cycles.
    Returns a (possibly empty) list of problems — never raises."""
    problems: list[str] = []
    for cid, reqs in edges.items():
        if cid not in valid:
            problems.append(f"dangling competence_id '{cid}' (not in the Lehrplan catalog)")
        for r in reqs:
            if r not in valid:
                problems.append(f"edge {cid} → requires dangling id '{r}'")
            if r == cid:
                problems.append(f"self-edge: {cid} requires itself")
    cycle = _find_cycle(edges)
    if cycle:
        problems.append("cycle detected: " + " → ".join(cycle))
    return problems


def lint(code: str = "MAT") -> list[str]:
    """Lint a shipped catalog and return its problems (empty = clean). A missing catalog
    is vacuously clean. Used by the test that locks the shipped graph and by the loader."""
    catalog = load_catalog(code)
    if catalog is None:
        return []
    return _lint(_edge_map(catalog), valid_ids(code))


@lru_cache(maxsize=8)
def load_edges(code: str = "MAT") -> dict[str, list[str]]:
    """The lint-validated edge map ``competence_id -> [direct prerequisite ids]`` for a
    subject. Runs the deterministic lints at load and RAISES ``PrerequisiteError`` on any
    structural violation — a broken catalog never reaches a query. A subject without a
    curated catalog yields ``{}`` (no edges, no error)."""
    catalog = load_catalog(code)
    if catalog is None:
        return {}
    edges = _edge_map(catalog)
    problems = _lint(edges, valid_ids(code))
    if problems:
        raise PrerequisiteError(f"prerequisites/{code}.json: " + "; ".join(problems))
    return edges


def available() -> list[str]:
    """Subject codes with a curated prerequisite catalog."""
    return sorted(p.stem for p in _DIR.glob("*.json"))
