"""SRDP Operatoren grounding table (the Matura-orientation vocabulary)."""
from __future__ import annotations

from teachersaid.grounding import operators as ops
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.llm.prompts import build_system
from teachersaid.pipeline.difficulty import _RANK_TO_BAND
from teachersaid.schema.enums import CognitiveLevel


def test_tables_well_formed():
    for table in (ops.DEFAULT, ops.DEUTSCH):
        assert set(table) == {1, 2, 3}
        for band in (1, 2, 3):
            assert table[band], f"AFB {band} empty"
            assert all(isinstance(o, ops.Operator) and o.forms for o in table[band])


def test_one_ladder_with_difficulty():
    """Operators and difficulty must band the cognitive ladder identically — one ladder,
    two surfaces (locks the invariant the docstring promises)."""
    assert ops._RANK_TO_AFB == _RANK_TO_BAND


def test_level_maps_to_band():
    assert ops.afb_for_level(CognitiveLevel.REMEMBER) == 1
    assert ops.afb_for_level(CognitiveLevel.APPLY) == 2
    assert ops.afb_for_level(CognitiveLevel.CREATE) == 3
    # unknown level falls back exactly as difficulty.py does (rank default 1 → band 1)
    assert ops.afb_for_level("nonsense") == 1


def test_deutsch_is_authoritative():
    assert ops.is_authoritative("Deutsch")
    assert not ops.is_authoritative("Physik")
    assert ops.operator_set("Physik") is ops.DEFAULT
    assert ops.operator_set("Deutsch") is ops.DEUTSCH
    # the Deutsch catalog carries the official definitions (not just bare verbs)
    erfoertern = [o for o in ops.DEUTSCH[3] if "erörtern" in o.forms]
    assert erfoertern and erfoertern[0].definition


def test_brief_is_subject_specific():
    de = ops.format_operators_brief("Deutsch")
    for band in (1, 2, 3):
        assert ops.AFB_LABEL[band] in de
    assert "erörtern" in de and "Deutsch" in de
    # a subject without a catalog gets the generic palette, flagged as such
    phy = ops.format_operators_brief("Physik")
    assert "berechnen" in phy and "pending" in phy


def test_injected_into_generation_prompt():
    de_system = build_system(ls.get_subject_model("Deutsch"))
    assert "Operatoren" in de_system and "Anforderungsbereich" in de_system
    assert "erörtern" in de_system  # the authoritative Deutsch verb made it in
    # a non-curated subject still gets a (generic) operator palette
    phy_system = build_system(ls.get_subject_model("Physik"))
    assert "Operatoren" in phy_system and "berechnen" in phy_system
