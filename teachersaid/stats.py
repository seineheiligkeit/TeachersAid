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
