"""Sachverhalt breadth ingest — the content-layer twin of `test_ingest.py`.

A subagent authors a `Sachverhalt` JSON (structured SOURCED facts + a Darstellung over them);
`tools/ingest_sachverhalte.py` normalises the recurring agent slips, validates through the real
schema, runs the FACTS gate + the entity-lint, and derives/verifies the worksheet. These lock the
load-bearing pieces offline: the normalizer absorbs slips, the facts gate fires without a
`role="facts"` source, and the entity-lint catches a planted year — so a bad module is rejected,
never silently staged.
"""

from __future__ import annotations

import json

from teachersaid.library.sachverhalte import SACHVERHALTE
from tools.ingest_sachverhalte import _check, _normalize, _repair_text


def _write(tmp_path, name, data) -> "object":
    p = tmp_path / f"{name}.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def _flagship_dict(idx=0) -> dict:
    """A guaranteed-valid Sachverhalt as a JSON-shaped dict (round-trips through the ingest)."""
    return SACHVERHALTE[idx].model_dump(mode="json")


# --- the normalizer absorbs the recurring agent slips ------------------------

def test_normalizer_drops_stray_keys_and_fixes_klasse_range():
    out = _normalize({"id": "x", "klasse_range": 3, "bogus_top_key": 1,
                      "notes_to_self": "remove me"})
    assert "bogus_top_key" not in out and "notes_to_self" not in out  # extra=forbid would reject
    assert out["klasse_range"] == [3, 3]                              # single grade → a 1-grade range


def test_normalizer_defaults_source_role_and_causal_kind():
    out = _normalize({
        "id": "x",
        "sources": [{"title": "Q", "url": "u", "licence": "CC-BY-SA-4.0"}],   # role omitted
        "causes": [{"cause": "a", "effect": "b", "kind": "consequence"}],     # off-enum kind
    })
    assert out["sources"][0]["role"] == "facts"     # a source defaults to the mandatory facts role
    assert out["causes"][0]["kind"] == "folge"      # off-enum causal kind → a valid default


def test_normalizer_strips_authored_provenance_and_defaults_grounded_by():
    out = _normalize({"id": "x", "darstellung": [
        {"heading": "H", "body": "B", "provenance": {"expression_origin": "quoted"}}]})
    d = out["darstellung"][0]
    assert "provenance" not in d        # the derivation attaches it — authoring it would double up
    assert d["grounded_by"] == []       # defaulted so the field is always present


def test_repair_text_balances_the_german_quote_slip():
    # „…" with a straight closing quote breaks the JSON string; the repair closes it as „…“
    raw = '{"body": "Er nannte es „Restauration"."}'
    fixed = _repair_text(raw)
    assert json.loads(fixed)["body"] == "Er nannte es „Restauration“."


# --- the gate chain: clean passes, facts gate + entity-lint reject -----------

def test_check_clean_flagship_passes(tmp_path):
    for i in range(len(SACHVERHALTE)):
        p = _write(tmp_path, f"flag{i}", _flagship_dict(i))
        sv, problems = _check(p)
        assert sv is not None and problems == [], (SACHVERHALTE[i].id, problems)


def test_check_facts_gate_fires_without_a_facts_source(tmp_path):
    d = _flagship_dict(0)
    for s in d["sources"]:               # demote every source off the mandatory facts role
        s["role"] = "expression"
    sv, problems = _check(_write(tmp_path, "no_facts", d))
    assert sv is not None                          # schema-valid …
    assert any("facts gate" in p for p in problems)  # … but the facts gate rejects it


def test_check_entity_lint_catches_a_planted_year(tmp_path):
    d = _flagship_dict(0)                 # the timeline flagship (Wiener Kongress)
    # plant a year in the Darstellung that is NOT an event in the fact-set → hard entity-lint fail
    d["darstellung"][0]["body"] += " Erst 1851 änderte sich daran etwas."
    sv, problems = _check(_write(tmp_path, "bad_year", d))
    assert any("entity-lint" in p and "1851" in p for p in problems), problems
