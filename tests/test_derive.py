"""M3 verification: derived depth/coverage match schema §8 + structural no-drift."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.demo import strahlung
from teachersaid.pipeline.assemble import assemble, validate_against_model
from teachersaid.pipeline.resolve import resolve

IN_WINDOW = date(2026, 3, 1)


@pytest.fixture
def assembled():
    content = strahlung.build_content()
    res = resolve(strahlung.build_request(), today=IN_WINDOW)
    return assemble(content, res), res


def test_model_validation_clean():
    content = strahlung.build_content()
    assert validate_against_model(content) == []


def test_depth_profile_matches_schema_section8(assembled):
    content, _ = assembled
    dp = content.depth_profile
    assert dp.by_level == {
        "understand": 1, "apply": 1, "analyze": 2, "evaluate": 2, "create": 1
    }
    assert dp.by_dimension == {"W": 2, "S": 4, "E": 1}
    assert dp.minutes_total == 78
    assert dp.minutes_resource_independent == 56


def test_nachweis_flags_str01_gap(assembled):
    content, _ = assembled
    n = content.nachweis
    covered = {c.competence_id for c in n.competence_coverage if c.covered}
    assert covered == {"PHY.US.4.STR.02", "PHY.US.4.STR.03", "PHY.US.4.STR.04"}
    # STR.01 (Quellen bewerten) is the deliberate, auto-surfaced gap.
    assert any(g.startswith("PHY.US.4.STR.01") for g in n.gaps)
    # ÜT 11 (Umweltbildung, from covered STR.02) aggregated; ÜT 6 (STR.01) not,
    # because STR.01 is uncovered.
    assert 11 in n.uebergreifende_themen
    assert 6 not in n.uebergreifende_themen


def test_no_drift_teacher_keys_are_same_objects(assembled):
    """The teacher guide and student sheet are projections of ONE content object,
    so the answer keys belong to the very same task blocks the student sees."""
    content, _ = assembled
    tasks = [b for b in content.iter_blocks() if b.role == "task"]
    # The objects a renderer would read are these exact blocks; there is no second
    # copy of task/answer data anywhere.
    t4 = next(b for b in tasks if b.id == "str.t4")
    assert "UV schädigt Zellen" in t4.answer_key
    assert t4.payload.statements[0].startswith("UV-Strahlung")
    # answer key references the same payload it grades
    assert len(t4.payload.statements) == t4.response.rows
