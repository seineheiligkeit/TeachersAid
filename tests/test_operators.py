"""SRDP Operatoren grounding table (the Matura-orientation vocabulary)."""
from __future__ import annotations

from teachersaid.grounding import operators as ops
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.llm.prompts import build_system
from teachersaid.pipeline.difficulty import _RANK_TO_BAND
from teachersaid.schema.enums import CognitiveLevel


def test_table_well_formed():
    assert set(ops.OPERATORS) == {1, 2, 3}
    for band in (1, 2, 3):
        assert ops.OPERATORS[band], f"AFB {band} has no operators"
        assert all(isinstance(v, str) and v for v in ops.OPERATORS[band])


def test_one_ladder_with_difficulty():
    """Operators and difficulty must band the cognitive ladder identically — one ladder,
    two surfaces (locks the invariant the docstring promises)."""
    assert ops._RANK_TO_AFB == _RANK_TO_BAND


def test_level_maps_to_band():
    assert ops.afb_for_level(CognitiveLevel.REMEMBER) == 1
    assert ops.afb_for_level(CognitiveLevel.APPLY) == 2
    assert ops.afb_for_level(CognitiveLevel.CREATE) == 3
    # unknown level falls back exactly as difficulty.py does (rank default 1 → band 1),
    # never raises
    assert ops.afb_for_level("nonsense") == 1
    assert ops.operators_for_level(CognitiveLevel.EVALUATE) == ops.OPERATORS[3]


def test_brief_lists_every_band():
    brief = ops.format_operators_brief()
    for band in (1, 2, 3):
        assert ops.AFB_LABEL[band] in brief
    # a representative operator from each band surfaces
    assert "beschreiben" in brief and "berechnen" in brief and "beurteilen" in brief


def test_injected_into_generation_prompt():
    model = ls.get_subject_model("Physik")
    system = build_system(model)
    assert "Operatoren" in system
    assert "Anforderungsbereich" in system
    assert "beurteilen" in system  # an AFB III verb made it into the brief
