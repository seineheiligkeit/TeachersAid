"""M4 verification: plan → generate (fake LLM) → assemble → verify, all offline."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.generate import generate_body
from teachersaid.pipeline.plan import plan
from teachersaid.pipeline.resolve import resolve
from teachersaid.pipeline.verify import verify
from teachersaid.schema.generation_views import GenWorksheetBody
from teachersaid.schema.worksheet import BundleRequest, WorksheetContent

IN_WINDOW = date(2026, 3, 1)


class FakeGenerator:
    """Returns a canned body realising the four STR competences, climbing the
    ladder so the depth target (≥2 at analyze+) is met."""

    def __init__(self):
        self.calls = 0

    def parse(self, system, user, schema):
        self.calls += 1
        assert schema is GenWorksheetBody
        # sanity: the prompt carries the rules + the verbatim competences
        assert "AHS" in system and "PHY.US.4.STR.02" in user
        levels = ["understand", "apply", "analyze", "evaluate"]
        dims = ["W", "E", "W", "W"]
        body = {
            "intro": [
                {"role": "info", "id": "i1", "kind": "prose",
                 "content": "Strahlung ist überall — aber nicht jede ist gefährlich."}
            ],
            "sections": [],
        }
        for i, cid in enumerate(
            ["PHY.US.4.STR.01", "PHY.US.4.STR.02", "PHY.US.4.STR.03", "PHY.US.4.STR.04"]
        ):
            body["sections"].append(
                {
                    "id": f"s{i+1}",
                    "title": cid,
                    "throughline": "Energie entscheidet.",
                    "blocks": [
                        {
                            "role": "task",
                            "id": f"t{i+1}",
                            "kind": "open_response",
                            "prompt": f"Aufgabe zu {cid}: erkläre und begründe.",
                            "response": {"mode": "lines", "n": 3},
                            "cognitive_level": levels[i],
                            "dimensions": [dims[i]],
                            "serves": [{"competence_id": cid, "relation": "exercises"}],
                            "est_minutes": 12,
                        }
                    ],
                }
            )
        return GenWorksheetBody.model_validate(body)


def test_plan_is_deterministic_idea_artifact():
    res = resolve(
        BundleRequest(subject="Physik", klasse=4, topic_raw="Strahlung und Radioaktivität"),
        today=IN_WINDOW,
    )
    p = plan(res, "doppelstunde")
    assert p.competence_ids == [
        "PHY.US.4.STR.01", "PHY.US.4.STR.02", "PHY.US.4.STR.03", "PHY.US.4.STR.04"
    ]
    assert p.minutes_budget == 100
    assert p.depth_target.min_at_or_above == {"level": "analyze", "count": 2}
    assert len(p.section_specs) == 4
    assert p.threads  # creative seeds present for idea-stage review


def test_generate_assemble_verify_offline():
    res = resolve(
        BundleRequest(subject="Physik", klasse=4, topic_raw="Strahlung und Radioaktivität"),
        today=IN_WINDOW,
    )
    p = plan(res, "doppelstunde")
    fake = FakeGenerator()
    content = generate_body(p, res, generator=fake)
    assert fake.calls == 1
    assert isinstance(content, WorksheetContent)
    assert content.nachweis is None  # not yet derived

    assemble(content, res)
    # derived now present; all 4 competences exercised -> no gaps
    assert content.nachweis is not None
    assert content.nachweis.gaps == []
    assert content.depth_profile.by_level.get("analyze", 0) >= 1

    report = verify(content, res, plan=p)
    assert report.ok is True
    assert report.problems == []


def test_verify_catches_bad_dimension():
    res = resolve(
        BundleRequest(subject="Physik", klasse=4, topic_raw="Strahlung und Radioaktivität"),
        today=IN_WINDOW,
    )
    p = plan(res, "doppelstunde")
    content = generate_body(p, res, generator=FakeGenerator())
    # corrupt a dimension to something not in the Physik model
    content.sections[0].blocks[0].dimensions = ["BOGUS"]
    report = verify(content, res, plan=p)
    assert report.ok is False
    assert any("BOGUS" in pr for pr in report.problems)


def test_anthropic_generator_clear_error_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from teachersaid.llm.client import AnthropicGenerator

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        AnthropicGenerator().parse("sys", "user", GenWorksheetBody)
