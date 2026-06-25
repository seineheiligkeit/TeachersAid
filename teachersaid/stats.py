"""Master-library coverage statistics.

Tracks how far the approved material library has populated the catalog, per subject:
how many tasks exist, how many catalog competences are covered (served by ≥1
approved worksheet), how many worksheets, and what is still empty. This is the
"are we well-informed as we populate" view behind the dashboard's Statistik tab.
"""

from __future__ import annotations

from .grounding import lehrplan_store as ls
from .schema.enums import Role
from .store.repository import ReviewStore


def compute_stats(store: ReviewStore | None = None) -> dict:
    store = store or ReviewStore()
    meta = ls._meta()
    subjects = [s for s in meta.get("subjects", []) if s.get("type") == "pflichtgegenstand"]

    by_code: dict[str, dict] = {
        s["code"]: {
            "code": s["code"], "name": s["name"], "klassen": s["klassen"],
            "total_competences": s.get("n_competences", 0),
            "_covered": set(), "worksheets": 0, "tasks": 0, "in_progress": 0,
        }
        for s in subjects
    }

    # approved library → coverage + counts
    for it in store.library():
        if not it.content:
            continue
        row = by_code.get(ls._code_for(it.request.subject) or "")
        if row is None:
            continue
        row["worksheets"] += 1
        for b in it.content.iter_blocks():
            if b.role == Role.TASK:
                row["tasks"] += 1
                for s in b.serves:
                    row["_covered"].add(s.competence_id)

    # content still in review (informational)
    for it in store.list(stage="content"):
        if it.status in ("pending", "changes_requested", "generating"):
            row = by_code.get(ls._code_for(it.request.subject) or "")
            if row is not None:
                row["in_progress"] += 1

    rows = []
    for r in by_code.values():
        covered = len(r["_covered"])
        total = r["total_competences"]
        rows.append({
            "code": r["code"], "name": r["name"], "klassen": r["klassen"],
            "total_competences": total,
            "covered_competences": covered,
            "coverage_pct": round(100 * covered / total) if total else 0,
            "worksheets": r["worksheets"], "tasks": r["tasks"],
            "in_progress": r["in_progress"],
            "empty": r["worksheets"] == 0,
        })
    rows.sort(key=lambda x: (-x["worksheets"], -x["in_progress"], x["name"]))

    totals = {
        "subjects": len(rows),
        "subjects_started": sum(1 for r in rows if r["worksheets"]),
        "total_competences": sum(r["total_competences"] for r in rows),
        "covered_competences": sum(r["covered_competences"] for r in rows),
        "worksheets": sum(r["worksheets"] for r in rows),
        "tasks": sum(r["tasks"] for r in rows),
        "in_progress": sum(r["in_progress"] for r in rows),
    }
    totals["coverage_pct"] = (
        round(100 * totals["covered_competences"] / totals["total_competences"])
        if totals["total_competences"] else 0
    )
    return {"subjects": rows, "totals": totals}
