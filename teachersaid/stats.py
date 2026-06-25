"""Master-library coverage statistics — now block-level.

The library unit is the block, so coverage is tracked per subject as: catalog
competences vs. competences covered by an *approved* block, how many task/info
blocks exist, their spread across cognitive level and scope (richness), and what
is still empty. This is the populate-and-track view behind the Statistik tab.
"""

from __future__ import annotations

from .grounding import lehrplan_store as ls
from .store.blockstore import BlockStore
from .store.repository import ReviewStore


def compute_stats(block_store: BlockStore | None = None,
                  review_store: ReviewStore | None = None) -> dict:
    bs = block_store or BlockStore()
    rs = review_store or ReviewStore()
    subjects = [s for s in ls._meta().get("subjects", []) if s.get("type") == "pflichtgegenstand"]

    rows: dict[str, dict] = {
        s["code"]: {
            "code": s["code"], "name": s["name"], "klassen": s["klassen"],
            "total_competences": s.get("n_competences", 0),
            "_covered": set(), "task_blocks": 0, "info_blocks": 0, "in_review": 0,
            "by_level": {}, "by_scope": {},
        }
        for s in subjects
    }

    for lb in bs.list():
        row = rows.get(ls._code_for(lb.subject) or "")
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
            "code": r["code"], "name": r["name"], "klassen": r["klassen"],
            "total_competences": total,
            "covered_competences": covered,
            "coverage_pct": round(100 * covered / total) if total else 0,
            "task_blocks": r["task_blocks"], "info_blocks": r["info_blocks"],
            "in_review": r["in_review"],
            "by_level": r["by_level"], "by_scope": r["by_scope"],
            "empty": r["task_blocks"] == 0 and r["info_blocks"] == 0,
        })
    out.sort(key=lambda x: (-(x["task_blocks"] + x["info_blocks"]), -x["in_review"], x["name"]))

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
    return {"subjects": out, "totals": totals}
