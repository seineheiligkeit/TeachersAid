"""SRDP Operatoren grounding table (the Matura-orientation vocabulary)."""
from __future__ import annotations

from teachersaid.grounding import operators as ops
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.llm.prompts import build_system
from teachersaid.pipeline.difficulty import _RANK_TO_BAND
from teachersaid.schema.enums import CognitiveLevel


def test_catalogs_well_formed():
    for cat in (ops.DEUTSCH, ops.NATURWISSENSCHAFTEN, ops.MATHEMATIK, ops.GEOGRAPHIE,
                ops.DEFAULT):
        assert cat and all(isinstance(o, ops.Operator) and o.forms for o in cat)
        for o in cat:
            assert all(b in (1, 2, 3) for b in o.afb)
            assert all(w in ("W", "E", "S") for w in o.wes)


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


def test_subject_routing():
    assert ops.is_authoritative("Deutsch") and ops.is_authoritative("Physik")
    assert ops.is_authoritative("GWB")
    assert not ops.is_authoritative("Bewegung und Sport")
    # BIO/PHY/CHE share the Naturwissenschaften catalog
    assert ops.operator_set("Physik") is ops.NATURWISSENSCHAFTEN
    assert ops.operator_set("Chemie") is ops.NATURWISSENSCHAFTEN
    assert ops.operator_set("Mathematik") is ops.MATHEMATIK
    assert ops.operator_set("GWB") is ops.GEOGRAPHIE
    assert ops.operator_set("Bewegung und Sport") is ops.DEFAULT  # uncurated → fallback


def test_routing_is_code_based_not_name_based():
    """The GWB demo passes the long display name, sciences the short name — both must
    route via canonical code (model.subject is the caller's string, not a code)."""
    assert ops.operator_set("Geographie und wirtschaftliche Bildung") is ops.GEOGRAPHIE
    assert ops.is_authoritative("Geographie und wirtschaftliche Bildung")


def test_banded_vs_flat():
    assert ops.is_banded(ops.DEUTSCH) and ops.is_banded(ops.NATURWISSENSCHAFTEN)
    assert ops.is_banded(ops.GEOGRAPHIE)
    assert not ops.is_banded(ops.MATHEMATIK)  # the official math list carries no AFB band


def test_science_grid_read_faithfully():
    """A few cells read from the AECC-Bio grid (afb=Rp/Tr/Rf cols, wes=W/E/S rows)."""
    by_form = {o.forms: o for o in ops.NATURWISSENSCHAFTEN}
    assert by_form["definieren"].afb == (1,) and by_form["definieren"].wes == ("W",)
    assert by_form["erörtern"].afb == (3,) and by_form["erörtern"].wes == ("S",)
    assert by_form["beschreiben"].afb == (1, 2)        # W×Rp+Tr
    assert by_form["vergleichen"].wes == ("W", "E", "S")  # marked across all three rows


def test_operators_for_level():
    # banded: an operator surfaces at a level whose band it carries
    de_apply = [o.forms for o in ops.operators_for_level(CognitiveLevel.APPLY, "Deutsch")]
    assert "analysieren / untersuchen" in de_apply  # AFB 2
    # flat (math): the whole list regardless of level (source has no band)
    assert ops.operators_for_level(CognitiveLevel.REMEMBER, "Mathematik") is ops.MATHEMATIK


def test_math_format_to_kind():
    from teachersaid.schema.enums import CORE_TASK_KINDS
    mat_ext = set(ls.get_subject_model("Mathematik").task_kind_extensions)
    allowed = CORE_TASK_KINDS | mat_ext
    # every mapped kind is a legal Math kind (core or MAT extension)
    assert set(ops.FORMAT_TO_KIND.values()) <= allowed
    assert "construction" in mat_ext  # the k → construction target exists
    assert ops.kinds_for_answer_format("mc") == ["multiple_choice"]
    assert ops.kinds_for_answer_format("ho/o") == ["open_response"]  # both → one, deduped
    assert ops.kinds_for_answer_format("k/ho") == ["construction", "open_response"]
    # every Math operator's answer format resolves to at least one suggested kind
    for o in ops.MATHEMATIK:
        assert ops.kinds_for_answer_format(o.answer_format)
    assert "→multiple_choice" in ops.format_operators_brief("Mathematik")


def test_brief_shapes_per_subject():
    de = ops.format_operators_brief("Deutsch")
    assert "erörtern" in de and all(ops.AFB_LABEL[b] in de for b in (1, 2, 3))
    mat = ops.format_operators_brief("Mathematik")
    assert "not AFB-banded" in mat and "umformen" in mat and "Konstruktion" in mat
    phy = ops.format_operators_brief("Physik")
    assert "interpretieren" in phy and "Physik" in phy
    sport = ops.format_operators_brief("Sport")
    assert "pending" in sport


def test_injected_into_generation_prompt():
    de_system = build_system(ls.get_subject_model("Deutsch"))
    assert "Operatoren" in de_system and "erörtern" in de_system
    mat_system = build_system(ls.get_subject_model("Mathematik"))
    assert "Operatoren" in mat_system and "umformen" in mat_system
