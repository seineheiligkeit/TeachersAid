"""Choose the pedagogically-appropriate chart REPRESENTATION for a data intent.

The generator declares WHAT the data is (the `intent`) and the data; this pure mapping
picks the chart family and assembles its recipe spec — so a trend becomes a line, a
relationship a scatter, a distribution a histogram, a scale a number line, a category
comparison a bar. The representation choice is correct-by-construction here, not the
LLM's guess ("everything is a bar"). Pure (no rendering): the recipes in
`pipeline/assets.py` render whatever generator this returns.
"""
from __future__ import annotations

import math

INTENTS = ("trend", "comparison", "relationship", "composition", "distribution", "scale")


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, [], "")}


def choose_representation(intent: str, data: dict) -> tuple[str, dict]:
    """Map (intent, data) → (generator_id, spec) for a code-generated figure."""
    d = dict(data or {})
    title = d.get("title")
    xl = d.get("xlabel") or d.get("x_label")
    yl = d.get("ylabel") or d.get("y_label")
    cats, vals, pts = d.get("categories"), d.get("values"), d.get("points")

    if intent == "trend":                      # change over time / ordered progression → line
        spec = {"title": title, "xlabel": xl, "ylabel": yl, "log": d.get("log")}
        if d.get("series"):
            spec["series"] = d["series"]
        else:
            spec["categories"], spec["values"] = cats, vals
        return "matplotlib:line", _clean(spec)

    if intent == "relationship":               # two numeric variables → scatter (+ optional fit)
        return "matplotlib:scatter", _clean(
            {"points": pts, "xlabel": xl, "ylabel": yl, "title": title, "fit": d.get("fit") or None})

    if intent == "distribution":               # spread of one variable → histogram
        return "matplotlib:histogram", _clean(
            {"values": vals, "bins": d.get("bins"), "xlabel": xl, "ylabel": yl, "title": title})

    if intent == "scale":                      # a position on a scale (e.g. pH) → number line
        marks = d.get("marks")
        if not marks and cats and vals:
            marks = [{"at": float(v), "label": str(c)} for c, v in zip(cats, vals)]
        nums = [m["at"] for m in (marks or [])] or [float(v) for v in (vals or [])]
        lo = d.get("min", math.floor(min(nums)) if nums else 0)
        hi = d.get("max", math.ceil(max(nums)) if nums else 10)
        return "matplotlib:number_line", _clean({"min": lo, "max": hi, "marks": marks})

    # comparison / composition (and any unknown intent) → bar
    return "matplotlib:bar_chart", _clean(
        {"categories": cats, "values": vals, "title": title, "xlabel": xl, "ylabel": yl,
         "log": d.get("log")})
