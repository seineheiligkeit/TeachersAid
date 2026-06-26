"""The MediaPolicy library-entry gate (Phase 4 #3).

content-bearing visuals must be correct (code-gen or vetted-sourced); decorative
must be content-free. The gate runs inside verify(), so it covers every entry path.
"""

from __future__ import annotations

from teachersaid.library import EXAMPLES
from teachersaid.pipeline.media_policy import (
    check_asset,
    check_content,
    classify_source,
)
from teachersaid.schema.assets import Asset, AssetProvenance, IntentionallyFlawed


def test_classify_source():
    assert classify_source(Asset(id="x", role="figure", generator="matplotlib:bar_chart")) == "code"
    assert classify_source(Asset(id="x", role="icon", generator="diffusion:sdxl")) == "diffusion"
    assert classify_source(Asset(id="x", role="photo",
        provenance=AssetProvenance(source="s", rights="licensed"))) == "sourced"
    assert classify_source(Asset(id="x", role="figure")) == "none"


def test_content_figure_must_be_code_generated():
    assert not check_asset(Asset(id="f", role="figure", generator="matplotlib:bar_chart"))[0]
    # a content figure with no code generator is blocked…
    problems, _ = check_asset(Asset(id="f", role="figure"))
    assert problems and "code-generated" in problems[0]
    # …and so is a figure from diffusion (content must be correct-by-construction)
    assert check_asset(Asset(id="f", role="figure", generator="diffusion:sdxl"))[0]


def test_sourced_audio_needs_vetted_rights():
    ok = Asset(id="r", role="recording", medium="audio",
               provenance=AssetProvenance(source="public archive", rights="public_domain"))
    assert not check_asset(ok)[0]
    assert check_asset(Asset(id="r", role="recording", medium="audio",
        provenance=AssetProvenance(source="x", rights="unverified")))[0]
    # a content-sourced role with no provenance at all is blocked
    assert check_asset(Asset(id="r", role="recording", medium="audio"))[0]


def test_decorative_must_be_content_free():
    # a content-free decorative asset from diffusion is admissible (the source is fine)
    assert not check_asset(Asset(id="d", role="icon", generator="diffusion:sdxl"))[0]
    # but a decorative asset that claims content is blocked (diffusion slop-as-content)
    assert check_asset(Asset(id="d", role="mascot", generator="diffusion:sdxl",
        correctness_surface="the real EM spectrum"))[0]
    assert check_asset(Asset(id="d", role="decoration", generator="diffusion:sdxl",
        intentionally_flawed=IntentionallyFlawed(what="wrong on purpose")))[0]


def test_uncovered_role_warns_only_when_unvetted():
    p, w = check_asset(Asset(id="m", role="meme", generator="diffusion:sdxl"))
    assert not p and w  # unknown role + unvetted source → triage warning, not a block
    p, w = check_asset(Asset(id="m", role="meme",
        provenance=AssetProvenance(source="s", rights="licensed")))
    assert not p and not w  # already vetted → fine


def test_curated_examples_pass_their_own_gate():
    for ex in EXAMPLES:
        problems, _ = check_content(ex.build())
        assert not problems, (ex.key, problems)


def test_verify_blocks_a_policy_violating_asset():
    """The gate runs inside verify(), so a mis-sourced content asset blocks the
    worksheet exactly like any verify problem."""
    from datetime import date

    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.resolve import resolve
    from teachersaid.pipeline.verify import verify
    from teachersaid.schema.worksheet import BundleRequest

    ex = EXAMPLES[0]
    content = ex.build()
    res = resolve(BundleRequest(subject=ex.subject, klasse=ex.klasse, topic_raw=ex.topic),
                  today=date(2026, 3, 1))
    assemble(content, res)
    assert verify(content, res).problems == []  # clean to start
    # a content figure with no code generator must make verify fail
    content.assets.append(Asset(id="rogue", role="figure"))
    assert any("rogue" in p for p in verify(content, res).problems)
