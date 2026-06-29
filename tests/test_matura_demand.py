"""Pure-function tests for the Matura demand-map aggregator (tools/matura_demand.py)."""
from __future__ import annotations

from tools import matura_demand as md


def test_norm_tokens_expands_optional_prefix_and_strips_annotations():
    assert md._norm_tokens("(be)nennen") == {"benennen", "nennen"}
    assert md._norm_tokens("(über)prüfen") == {"überprüfen", "prüfen"}
    assert md._norm_tokens("trennen (Wortbildung)") == {"trennen"}
    assert md._norm_tokens("analysieren / untersuchen") == {"analysieren", "untersuchen"}


def test_validate_deutsch_operators_all_in_catalog():
    from collections import Counter
    seen = Counter({"(be)nennen": 5, "deuten / interpretieren": 3, "wiedergeben": 9})
    v = md._validate(seen, "DEU")
    assert not v["not_in_catalog"]
    assert set(v["in_catalog"]) == {"(be)nennen", "deuten / interpretieren", "wiedergeben"}


def test_validate_routes_amt_to_mat_catalog():
    v = md._validate(__import__("collections").Counter({"ankreuzen": 3}), "AMT")
    assert v["catalog_code"] == "MAT"
    assert "ankreuzen" in v["in_catalog"]


def test_digest_groups_by_subject_kind():
    records = [
        {"subject_kind": "deutsch", "deutsch": {"aufgaben": [
            {"textsorte": "Kommentar", "wortanzahl": "270 – 330",
             "schreibhandlungen": ["Argumentation"],
             "arbeitsauftraege": [{"text": "Nehmen Sie Stellung.",
                                   "operator": "kommentieren / Stellung nehmen"}]}]}},
        {"subject_kind": "latein", "latein": {
            "uebersetzung": {"operator": "übersetzen", "points": 36, "source": "Ovid, Heroides"},
            "interpretation": {"points": 24, "source": "Ovid, Heroides"},
            "arbeitsaufgaben": [{"nr": 1, "operator": "finden", "points": 2}]}},
        {"subject_kind": "language", "language": {
            "skill": "Lesen", "cefr": "B2", "n_tasks": 4, "formats": ["matching"]}},
    ]
    d = md.digest(records)
    assert d["DEU"]["textsorten"] == {"Kommentar": 1}
    assert d["LAT"]["ut_points"] == {36: 1} and d["LAT"]["it_points"] == {24: 1}
    assert "finden" in d["LAT"]["operators"]["not_in_catalog"]
    assert d["FS"]["skill_x_cefr"] == {"Lesen/B2": 1}
