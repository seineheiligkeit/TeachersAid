"""Pure queries over the curated competence prerequisite graph (Wave C1).

One graph (``grounding/prerequisites/<CODE>.json``, loaded + lint-guaranteed acyclic
there), many pure queries here. The graph is directed: an edge ``X -> Y`` means "Y is a
prerequisite of X". So *ancestors* are the things you must already be able to do, and
*descendants* are the things that depend on you.

Every query takes a competence id and infers its subject catalog from the id prefix
(``MAT.US.2.ZAH.04`` -> ``MAT``), so the same functions serve any future subject graph.
An optional ``edges`` map (``id -> [direct prerequisite ids]``) can be injected for
testing against a fixture graph without touching the shipped catalog.

**Consumers built on this graph:**
* ``pipeline/diagnose.py`` — a Diagnose-Blatt: one easy task per prerequisite *ancestor*.
* ``stats.coverage_map`` — a ``blocks_dependents`` overlay (``downstream_impact``), so the
  campaign planner ranks a gap by how many dependents it blocks (a blocking cell > a leaf).

**Un-built seams (documented per the C1 brief — deliberately NOT built here):**
* *warm-up injection* — ``compose`` could prepend one ancestor task ("Bevor wir starten…")
  keyed off ``prerequisites()``.
* *spiral revision* — resurface ``descendants()`` of a mastered competence at later Klassen.
* *campaign ordering* — order a campaign by ``depth()`` so prerequisites are filled before
  dependents (``blocking_gaps`` already ranks the leverage).
* *difficulty feature* — ``depth()`` is the graph-depth signal Wave C4 can fold in.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..grounding import prerequisites as _catalog


def _code(competence_id: str) -> str:
    """The subject catalog code carried in a competence id (``MAT.US.2.ZAH.04`` -> ``MAT``)."""
    return competence_id.split(".", 1)[0]


def _edges_for(competence_id: str, edges: dict[str, list[str]] | None) -> dict[str, list[str]]:
    return edges if edges is not None else _catalog.load_edges(_code(competence_id))


def _reverse(edges: dict[str, list[str]]) -> dict[str, list[str]]:
    """Reverse adjacency: prerequisite id -> [ids that directly require it]."""
    rev: dict[str, list[str]] = {}
    for cid, reqs in edges.items():
        for r in reqs:
            rev.setdefault(r, []).append(cid)
    return rev


def _closure(start: str, adj: dict[str, list[str]]) -> set[str]:
    """Transitive closure of `start` over adjacency `adj`, excluding `start` itself."""
    seen: set[str] = set()
    stack = list(adj.get(start, []))
    while stack:
        n = stack.pop()
        if n in seen or n == start:
            continue
        seen.add(n)
        stack.extend(adj.get(n, []))
    return seen


def prerequisites(competence_id: str, *, edges: dict[str, list[str]] | None = None) -> list[str]:
    """The DIRECT prerequisites of a competence (order as curated)."""
    return list(_edges_for(competence_id, edges).get(competence_id, []))


def ancestors(competence_id: str, *, edges: dict[str, list[str]] | None = None) -> set[str]:
    """All TRANSITIVE prerequisites of a competence (everything it ultimately builds on)."""
    return _closure(competence_id, _edges_for(competence_id, edges))


def dependents(competence_id: str, *, edges: dict[str, list[str]] | None = None) -> set[str]:
    """The DIRECT dependents — competences that list this one as a prerequisite."""
    return set(_reverse(_edges_for(competence_id, edges)).get(competence_id, []))


def descendants(competence_id: str, *, edges: dict[str, list[str]] | None = None) -> set[str]:
    """All TRANSITIVE dependents — everything downstream that ultimately builds on this."""
    return _closure(competence_id, _reverse(_edges_for(competence_id, edges)))


def depth(competence_id: str, *, edges: dict[str, list[str]] | None = None) -> int:
    """Graph depth = the length of the LONGEST prerequisite chain below a competence
    (a root with no prerequisites is 0). The future difficulty signal (Wave C4): a
    competence that sits atop a deep prerequisite tower is structurally more demanding."""
    e = _edges_for(competence_id, edges)
    memo: dict[str, int] = {}

    def d(node: str, on_path: frozenset[str]) -> int:
        if node in memo:
            return memo[node]
        best = 0
        for p in e.get(node, []):
            if p in on_path:  # defensive: the shipped graph is acyclic, fixtures may not be
                continue
            best = max(best, 1 + d(p, on_path | {node}))
        memo[node] = best
        return best

    return d(competence_id, frozenset())


def downstream_impact(
    competence_ids: Iterable[str], *, edges: dict[str, list[str]] | None = None
) -> int:
    """How many DISTINCT competences transitively depend on this set — the graph leverage
    of a coverage cell. An empty cell with high downstream_impact blocks many dependents
    and matters more than a leaf (empty cell with impact 0). Cell-internal ids don't count
    themselves."""
    ids = list(competence_ids)
    if not ids:
        return 0
    e = edges if edges is not None else _catalog.load_edges(_code(ids[0]))
    rev = _reverse(e)
    hit: set[str] = set()
    own = set(ids)
    for cid in ids:
        hit |= _closure(cid, rev)
    return len(hit - own)


def blocking_gaps(
    cell_ids: dict[tuple, list[str]], *, edges: dict[str, list[str]] | None = None
) -> dict[tuple, int]:
    """Per coverage cell, its ``downstream_impact`` — the number of downstream dependents it
    blocks. Keyed exactly like ``cell_ids`` (whatever tuple the caller uses). ``stats`` feeds
    this its ``(stufe, code, klasse, kompetenzbereich) -> [competence ids]`` map and stamps
    the result onto each cell as ``blocks_dependents`` so the Kampagnen-Planer can rank gaps
    by downstream impact. Cells whose subject has no curated graph score 0."""
    out: dict[tuple, int] = {}
    for key, ids in cell_ids.items():
        out[key] = downstream_impact(ids, edges=edges)
    return out
