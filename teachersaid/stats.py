"""Master-library coverage statistics — now block-level.

The library unit is the block, so coverage is tracked per subject as: catalog
competences vs. competences covered by an *approved* block, how many task/info
blocks exist, their spread across cognitive level and scope (richness), and what
is still empty. This is the populate-and-track view behind the Statistik tab.
"""

from __future__ import annotations

from .grounding import lehrplan_store as ls
from .pipeline.difficulty import effective_difficulty
from .store.blockstore import BlockStore
from .store.repository import ReviewStore

# Track 1 #1 (offline-first program): a Kompetenzbereich cell is campaign-ready
# ("gruen") when it has at least this many approved task blocks AND all three
# Anforderungsbänder (leicht/mittel/anspruchsvoll) are present — the floor compose
# needs to span easy→stretch inside one envelope.
GREEN_MIN_TASKS = 4


def compute_stats(block_store: BlockStore | None = None,
                  review_store: ReviewStore | None = None) -> dict:
    bs = block_store or BlockStore()
    rs = review_store or ReviewStore()

    # Both stages, keyed (stufe, code) — the Oberstufe is a second catalog (lehrplan/oberstufe/).
    rows: dict[tuple[str, str], dict] = {}
    for stufe in ("Unterstufe", "Oberstufe"):
        for s in ls._meta(stufe).get("subjects", []):
            if s.get("type") != "pflichtgegenstand":
                continue
            rows[(stufe, s["code"])] = {
                "code": s["code"], "name": s["name"], "stufe": stufe,
                "klassen": s.get("klassen", []),
                "total_competences": s.get("n_competences", 0),
                "_covered": set(), "task_blocks": 0, "info_blocks": 0, "in_review": 0,
                "by_level": {}, "by_scope": {},
            }

    for lb in bs.list():
        # route each block to its stage by Klasse (1–4 US, 5–8 OS); the subject code is
        # resolved against that stage's alias table (Oberstufe-only subjects live only there).
        stufe = ls.stufe_for_klasse(getattr(lb, "klasse", None))
        row = rows.get((stufe, ls._code_for(lb.subject, stufe) or ""))
        if row is None:  # fall back to the other stage (e.g. a block without a Klasse)
            other = "Oberstufe" if stufe == "Unterstufe" else "Unterstufe"
            row = rows.get((other, ls._code_for(lb.subject, other) or ""))
        if row is None:
            continue
        if lb.status == "in_review":
            row["in_review"] += 1
        if lb.status != "approved":
            continue
        if lb.role == "task":
            row["task_blocks"] += 1
            if lb.cognitive_level:
                row["by_level"][lb.cognitive_level] = row["by_level"].get(lb.cognitive_level, 0) + 1
            for cid in lb.competences:
                row["_covered"].add(cid)
        else:
            row["info_blocks"] += 1
        row["by_scope"][lb.scope] = row["by_scope"].get(lb.scope, 0) + 1

    out = []
    for r in rows.values():
        covered, total = len(r["_covered"]), r["total_competences"]
        out.append({
            "code": r["code"], "name": r["name"], "stufe": r["stufe"], "klassen": r["klassen"],
            "total_competences": total,
            "covered_competences": covered,
            "coverage_pct": round(100 * covered / total) if total else 0,
            "task_blocks": r["task_blocks"], "info_blocks": r["info_blocks"],
            "in_review": r["in_review"],
            "by_level": r["by_level"], "by_scope": r["by_scope"],
            "empty": r["task_blocks"] == 0 and r["info_blocks"] == 0,
        })
    # group by stage (Unterstufe first), then by activity within each stage
    out.sort(key=lambda x: (0 if x["stufe"] == "Unterstufe" else 1,
                            -(x["task_blocks"] + x["info_blocks"]), -x["in_review"], x["name"]))

    totals = {
        "subjects": len(out),
        "subjects_started": sum(1 for r in out if r["task_blocks"] or r["info_blocks"]),
        "total_competences": sum(r["total_competences"] for r in out),
        "covered_competences": sum(r["covered_competences"] for r in out),
        "task_blocks": sum(r["task_blocks"] for r in out),
        "info_blocks": sum(r["info_blocks"] for r in out),
        "in_review": sum(r["in_review"] for r in out),
        "worksheets": len(rs.library()),
    }
    totals["coverage_pct"] = (
        round(100 * totals["covered_competences"] / totals["total_competences"])
        if totals["total_competences"] else 0
    )
    totals["by_stufe"] = {
        st: {
            "subjects": sum(1 for r in out if r["stufe"] == st),
            "started": sum(1 for r in out if r["stufe"] == st and (r["task_blocks"] or r["info_blocks"])),
            "covered_competences": sum(r["covered_competences"] for r in out if r["stufe"] == st),
            "total_competences": sum(r["total_competences"] for r in out if r["stufe"] == st),
            "task_blocks": sum(r["task_blocks"] for r in out if r["stufe"] == st),
            "in_review": sum(r["in_review"] for r in out if r["stufe"] == st),
        } for st in ("Unterstufe", "Oberstufe")
    }
    return {"subjects": out, "totals": totals}


# --- Track 1 #1 — the coverage planner (offline-first program) -----------------

def coverage_map(block_store: BlockStore | None = None) -> dict:
    """The campaign planner behind Statistik: one cell per (Stufe · subject · Klasse ·
    Kompetenzbereich), each with its approved task blocks split by Anforderungsband,
    scope variety, info blocks, and a status —

        "gruen" — ≥ GREEN_MIN_TASKS approved task blocks AND all 3 bands present
        "teil"  — at least one approved task block
        "leer"  — nothing approved yet

    Under the offline-first pivot this is the corpus progress bar: the catalog is a
    closed, parsed set, so "covered" is a computation, and a campaign's job is to
    turn cells green. Deterministic; a block is routed to cells by the competences
    it serves (preferring the cells of its own Klasse for cross-class competences).
    """
    bs = block_store or BlockStore()

    # 1) the catalog's cells: (stufe, code) → {(klasse, kb) → set(competence ids)}
    subjects_meta: list[tuple[tuple[str, str], dict]] = []
    cells: dict[tuple[str, str], dict[tuple[int, str], set[str]]] = {}
    for stufe in ("Unterstufe", "Oberstufe"):
        for s in ls._meta(stufe).get("subjects", []):
            if s.get("type") != "pflichtgegenstand":
                continue
            key = (stufe, s["code"])
            subjects_meta.append((key, s))
            per = cells.setdefault(key, {})
            for klasse in s.get("klassen", []):
                for c in ls.competences_for(s["code"], klasse, stufe):
                    per.setdefault((klasse, c.kompetenzbereich), set()).add(c.id)

    comp_cells: dict[str, list[tuple]] = {}
    for key, per in cells.items():
        for cell_key, ids in per.items():
            for cid in ids:
                comp_cells.setdefault(cid, []).append((key, cell_key))

    # 2) route approved blocks into cells
    stat: dict[tuple, dict] = {}

    def _cell(k):
        return stat.setdefault(k, {"tasks": set(), "bands": {1: 0, 2: 0, 3: 0},
                                   "scopes": set(), "infos": 0})

    for lb in bs.list():
        if lb.status != "approved":
            continue
        if lb.role == "task":
            targets: set[tuple] = set()
            for cid in lb.competences:
                locs = comp_cells.get(cid) or []
                pref = [loc for loc in locs if loc[1][0] == lb.klasse] or locs
                targets.update(pref)
            band = effective_difficulty(lb.block)
            for t in targets:
                cs = _cell(t)
                if lb.id not in cs["tasks"]:
                    cs["tasks"].add(lb.id)
                    cs["bands"][band] += 1
                    cs["scopes"].add(lb.scope)
        elif lb.kompetenzbereich:
            stufe = ls.stufe_for_klasse(lb.klasse)
            code = ls._code_for(lb.subject, stufe)
            k = ((stufe, code or ""), (lb.klasse, lb.kompetenzbereich))
            if k[0] in cells and k[1] in cells[k[0]]:
                _cell(k)["infos"] += 1

    # 3) assemble
    out_subjects = []
    for key, s in subjects_meta:
        rows, g, t, e = [], 0, 0, 0
        for (klasse, kb), ids in sorted(cells[key].items(), key=lambda x: (x[0][0], x[0][1])):
            cs = stat.get((key, (klasse, kb)))
            n = len(cs["tasks"]) if cs else 0
            bands = cs["bands"] if cs else {1: 0, 2: 0, 3: 0}
            missing = [b for b in (1, 2, 3) if not bands.get(b)]
            status = ("gruen" if n >= GREEN_MIN_TASKS and not missing
                      else "teil" if n else "leer")
            g, t, e = g + (status == "gruen"), t + (status == "teil"), e + (status == "leer")
            rows.append({
                "klasse": klasse, "kompetenzbereich": kb, "n_competences": len(ids),
                "task_blocks": n, "bands": {str(k): v for k, v in bands.items()},
                "missing_bands": missing,
                "scopes": sorted(cs["scopes"]) if cs else [],
                "info_blocks": cs["infos"] if cs else 0, "status": status,
            })
        out_subjects.append({
            "code": s["code"], "name": s["name"], "stufe": key[0],
            "cells": rows, "gruen": g, "teil": t, "leer": e,
            "cells_total": len(rows),
            "ready_pct": round(100 * g / len(rows)) if rows else 0,
        })
    out_subjects.sort(key=lambda x: (0 if x["stufe"] == "Unterstufe" else 1,
                                     -x["ready_pct"], x["name"]))
    totals = {
        "cells": sum(x["cells_total"] for x in out_subjects),
        "gruen": sum(x["gruen"] for x in out_subjects),
        "teil": sum(x["teil"] for x in out_subjects),
        "leer": sum(x["leer"] for x in out_subjects),
    }
    totals["ready_pct"] = round(100 * totals["gruen"] / totals["cells"]) if totals["cells"] else 0
    return {"subjects": out_subjects, "totals": totals, "green_min_tasks": GREEN_MIN_TASKS}


def campaign_gaps(block_store: BlockStore | None = None, *, coverage: dict | None = None,
                  stufe: str | None = None, subject: str | None = None) -> list[dict]:
    """The exportable gap list — every non-green cell, with the competence ids a
    campaign brief needs (`tools/breadth_prompt.py` consumes exactly these anchors)."""
    cov = coverage or coverage_map(block_store)
    bs_cells = cells_with_ids()
    gaps: list[dict] = []
    for s in cov["subjects"]:
        if stufe and s["stufe"] != stufe:
            continue
        if subject and subject not in (s["code"], s["name"]):
            continue
        for c in s["cells"]:
            if c["status"] == "gruen":
                continue
            gaps.append({
                "subject": s["name"], "code": s["code"], "stufe": s["stufe"],
                "klasse": c["klasse"], "kompetenzbereich": c["kompetenzbereich"],
                "status": c["status"], "task_blocks": c["task_blocks"],
                "missing_bands": c["missing_bands"], "n_competences": c["n_competences"],
                "competences": bs_cells.get((s["stufe"], s["code"], c["klasse"],
                                             c["kompetenzbereich"]), []),
            })
    gaps.sort(key=lambda x: (0 if x["stufe"] == "Unterstufe" else 1,
                             x["code"], x["klasse"], x["kompetenzbereich"]))
    return gaps


def cells_with_ids() -> dict[tuple, list[str]]:
    """(stufe, code, klasse, kb) → sorted competence ids (the brief anchors); kept out
    of coverage_map's response so the dashboard payload stays light."""
    out: dict[tuple, list[str]] = {}
    for stufe in ("Unterstufe", "Oberstufe"):
        for s in ls._meta(stufe).get("subjects", []):
            if s.get("type") != "pflichtgegenstand":
                continue
            per: dict[tuple, set[str]] = {}
            for klasse in s.get("klassen", []):
                for c in ls.competences_for(s["code"], klasse, stufe):
                    per.setdefault((klasse, c.kompetenzbereich), set()).add(c.id)
            for (klasse, kb), ids in per.items():
                out[(stufe, s["code"], klasse, kb)] = sorted(ids)
    return out
