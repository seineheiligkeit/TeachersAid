"""Realien breadth ingest — the modern-FS twin of `test_ingest_sachverhalte.py`.

A subagent authors a CONSTRUCTED Realie JSON; `tools/ingest_realien.py` normalises the recurring
agent slips, validates through the real schema, and runs the internal-consistency lint. These lock
the load-bearing pieces offline: the normalizer absorbs slips (incl. dropping a stray source so a
constructed Realie rides no rights gate), and the consistency check catches an answer the Realie
can't support — so a bad module is rejected, never silently staged. The SME vets the L2 + level.
"""

from __future__ import annotations

import json

from teachersaid.library.realie_bahnhof import BAHNHOF
from teachersaid.library.realie_cafe import CAFE
from tools.ingest_realien import _check, _normalize, _repair_text


def _write(tmp_path, name, data):
    p = tmp_path / f"{name}.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def _flagship_dict(at) -> dict:
    return at.model_dump(mode="json", exclude_defaults=True)


# --- the normalizer absorbs the recurring agent slips ------------------------

def test_normalizer_drops_stray_keys_and_defaults_origin_textsorte():
    out = _normalize({"id": "x", "bogus": 1, "note_to_self": "drop me"})
    assert "bogus" not in out and "note_to_self" not in out      # extra=forbid would reject
    assert out["origin"] == "constructed" and out["textsorte"] == "Realie"


def test_normalizer_drops_source_for_a_constructed_realie():
    out = _normalize({"id": "x", "origin": "constructed",
                      "source": {"author": "A", "title": "T", "repository": "R", "attribution": "x"}})
    assert "source" not in out                                   # constructed fiction → no rights gate


def test_normalizer_canonicalises_annotation_kind_and_serves_relation():
    out = _normalize({"id": "x", "serves": [{"competence_id": "C"}],
                      "annotations": [{"kind": "scan", "label": "q", "dimensions": "LES"}]})
    assert out["serves"][0]["relation"] == "exercises"          # a serves entry defaults the relation
    assert out["annotations"][0]["kind"] == "comprehension"     # "scan" → the canonical kind
    assert out["annotations"][0]["dimensions"] == ["LES"]       # a stray scalar dim → a list


def test_repair_text_balances_the_german_quote_slip():
    fixed = _repair_text('{"answer": "Modelltext: „Hello!"."}')
    assert json.loads(fixed)["answer"] == "Modelltext: „Hello!“."


# --- the gate chain: clean passes, the consistency lint rejects --------------

def test_check_clean_flagships_pass(tmp_path):
    for at in (BAHNHOF, CAFE):
        sv, problems = _check(_write(tmp_path, at.id, _flagship_dict(at)))
        assert sv is not None and problems == [], (at.id, problems)


def test_check_catches_an_internally_inconsistent_answer(tmp_path):
    d = _flagship_dict(CAFE)
    # a scan answer citing a price the menu can't support (and not a shown sum) → flagged
    next(a for a in d["annotations"] if a["kind"] == "comprehension")["answer"] = "£9.99."
    at, problems = _check(_write(tmp_path, "bad_price", d))
    assert at is not None                                        # schema-valid …
    assert any("9.99" in p and "consistency" in p for p in problems)   # … but inconsistent
