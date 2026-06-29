"""Aggregate extracted Matura exams (runs/matura/json/) into a per-subject DEMAND MAP.

Deterministic, no-LLM: reads the JSON the extractor produced, groups by subject, and computes
the demand signals that drive the engine-extension priority — for Deutsch the Textsorten /
Schreibhandlungen / operator frequencies, for Latein the operator + ÜT/IT point split, for
the modern languages the skill × CEFR coverage and item formats, for Math/AMT the operator ×
Anforderungsbereich mix. Operators are validated against the authoritative catalogs in
``teachersaid.grounding.operators`` (the same *select, never author* tie the calibration uses).

    python tools/matura_demand.py                 # summary for every subject in runs/matura/json
    python tools/matura_demand.py --json out.json # machine-readable digest
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter

from teachersaid.grounding import operators as ops


def _load(json_dir: str) -> list[dict]:
    records: list[dict] = []
    for path in sorted(glob.glob(os.path.join(json_dir, "*.json"))):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        records.extend(data if isinstance(data, list) else [data])
    return records


import re

# AMT shares the Mathematik operator list (the catalog's own source: "SRP Mathematik und die
# SRDP Angewandte Mathematik") but operators.SUBJECT_OPERATORS only wires "MAT" today — so we
# validate AMT against MAT here. (Wiring AMT→MATHEMATIK in operators.py is a clean follow-up.)
_VALIDATION_CODE = {"AMT": "MAT"}


def _norm_tokens(form: str) -> set[str]:
    """Normalise an operator label into comparable tokens: split slash-synonyms, expand a
    leading optional prefix ("(be)nennen" → benennen·nennen), and drop our own annotations
    ("trennen (Wortbildung)" → trennen)."""
    s = re.sub(r"\s*\((?:wortbildung|auswahl)\)", "", (form or "").lower())
    out: set[str] = set()
    for part in s.split("/"):
        p = part.strip()
        m = re.match(r"^\(([^)]+)\)(.+)$", p)
        if m:
            out |= {(m.group(1) + m.group(2)).strip(), m.group(2).strip()}
        elif p:
            out.add(p)
    return out


def _validate(op_counter: Counter, code: str) -> dict:
    """Split observed operators into catalogued vs uncatalogued (demand-map honesty)."""
    cat_code = _VALIDATION_CODE.get(code, code)
    catalog: set[str] = set()
    for op in (ops.operator_set(cat_code) if hasattr(ops, "operator_set") else []) or []:
        catalog |= _norm_tokens(getattr(op, "forms", ""))
    known, unknown = {}, {}
    for op, n in op_counter.items():
        (known if (_norm_tokens(op) & catalog) else unknown)[op] = n
    return {"in_catalog": known, "not_in_catalog": unknown, "catalog_code": cat_code,
            "catalog_size": len(catalog)}


def digest(records: list[dict]) -> dict:
    by_kind: dict[str, list[dict]] = {}
    for r in records:
        by_kind.setdefault(r.get("subject_kind", "math"), []).append(r)
    out: dict = {}

    # --- Deutsch -----------------------------------------------------------------
    if "deutsch" in by_kind:
        ts, sh, opc = Counter(), Counter(), Counter()
        n_auf = 0
        for r in by_kind["deutsch"]:
            for a in r.get("deutsch", {}).get("aufgaben", []):
                n_auf += 1
                if a.get("textsorte"):
                    ts[a["textsorte"]] += 1
                for s in a.get("schreibhandlungen", []):
                    sh[s] += 1
                for w in a.get("arbeitsauftraege", []):
                    if w.get("operator"):
                        opc[w["operator"]] += 1
        out["DEU"] = {"exams": len(by_kind["deutsch"]), "aufgaben": n_auf,
                      "textsorten": dict(ts.most_common()),
                      "schreibhandlungen": dict(sh.most_common()),
                      "operators": _validate(opc, "DEU")}

    # --- Latein ------------------------------------------------------------------
    if "latein" in by_kind:
        opc, sources = Counter(), Counter()
        ut_pts, it_pts = Counter(), Counter()
        for r in by_kind["latein"]:
            lat = r.get("latein", {})
            if (lat.get("uebersetzung") or {}).get("points"):
                ut_pts[lat["uebersetzung"]["points"]] += 1
            if (lat.get("interpretation") or {}).get("points"):
                it_pts[lat["interpretation"]["points"]] += 1
            for key in ("uebersetzung", "interpretation"):
                src = (lat.get(key) or {}).get("source")
                if src:
                    sources[src] += 1
            for a in lat.get("arbeitsaufgaben", []):
                if a.get("operator"):
                    opc[a["operator"]] += 1
        out["LAT"] = {"exams": len(by_kind["latein"]),
                      "ut_points": dict(ut_pts), "it_points": dict(it_pts),
                      "sources": dict(sources.most_common()),
                      "operators": _validate(opc, "LAT")}

    # --- Modern languages --------------------------------------------------------
    if "language" in by_kind:
        skill_cefr = Counter()
        fmts = Counter()
        for r in by_kind["language"]:
            lang = r.get("language", {})
            skill_cefr[(lang.get("skill"), lang.get("cefr"))] += 1
            for f in lang.get("formats", []):
                fmts[f] += 1
        out["FS"] = {"booklets": len(by_kind["language"]),
                     "skill_x_cefr": {f"{s}/{c}": n for (s, c), n in skill_cefr.most_common()},
                     "formats": dict(fmts.most_common())}

    # --- Math / Angewandte Mathematik -------------------------------------------
    if "math" in by_kind:
        opc, t1, t2 = Counter(), Counter(), Counter()
        gk = 0
        subj = "MAT"
        for r in by_kind["math"]:
            subj = (r.get("meta") or {}).get("subject", subj)
            for t in r.get("tasks", []):
                op = t.get("operator")
                if op:
                    opc[op] += 1
                    (t1 if t.get("teil") == 1 else t2)[op] += 1
                if t.get("grundkompetenz"):
                    gk += 1
        out[subj] = {"exams": len(by_kind["math"]), "gk_tagged": gk,
                     "operators_teil1": dict(t1.most_common()),
                     "operators_teil2": dict(t2.most_common()),
                     "operators": _validate(opc, subj)}
    return out


def _print(d: dict) -> None:
    for code, info in d.items():
        print(f"\n=== {code} ===")
        for k, v in info.items():
            if isinstance(v, dict) and k == "operators":
                print(f"  catalog forms: {v['catalog_size']}")
                print(f"  in-catalog:     {v['in_catalog']}")
                if v["not_in_catalog"]:
                    print(f"  NOT-in-catalog: {v['not_in_catalog']}")
            else:
                print(f"  {k}: {v}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Aggregate Matura exams into a demand map.")
    ap.add_argument("--dir", default=os.path.join("runs", "matura", "json"))
    ap.add_argument("--json", help="write the digest as JSON here")
    args = ap.parse_args(argv)

    records = _load(args.dir)
    d = digest(records)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=2)
        print(f"wrote {args.json}", file=sys.stderr)
    _print(d)
    print(f"\n{len(records)} exam record(s) across {len(d)} subject(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
