"""P4 Tiefenregler: capability discovery + the drift lock against the mixer.

The load-bearing test is `test_discovery_matches_mixer_accept_reject_for_every_template`:
it iterates the WHOLE template registry × every fader and asserts that what
`discover_capabilities` reports as supported is EXACTLY what `make_mixed_variants` will
actually accept.  Discovery derives capability from lightweight structural checks; the mixer
derives it from its real rejection code.  Two independent paths — if either drifts, this test
turns red, which is the point (single source of truth for the accept/reject decision).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from teachersaid.library.templates import PARAM_TEMPLATES
from teachersaid.pipeline.mixer import DISCOVERY_N, discover_capabilities, make_mixed_variants
from teachersaid.schema.mixer import (
    Abstraktion,
    Geruest,
    Offenheit,
    ParametricMixerProfile,
    Textlast,
    Tiefe,
    Umfang,
)
from teachersaid.store.repository import ReviewStore

# both endpoints of every optional fader — the design says even the LOW endpoint requires the
# capability (the mixer probes the high endpoint from the low one), so a supported fader must
# accept BOTH endpoints and an unsupported one must reject BOTH.
_ENDPOINTS: dict[str, list] = {
    "tiefe": [Tiefe.UEBEN, Tiefe.STRATEGIEN_VERGLEICHEN],
    "abstraktion": [Abstraktion.ANSCHAULICH, Abstraktion.FORMAL],
    "offenheit": [Offenheit.GESCHLOSSEN, Offenheit.OFFEN],
    "geruest": [Geruest.OHNE, Geruest.GESTUETZT],
    "textlast": [Textlast.VOLL, Textlast.EINFACH],
}
_OPTIONAL_FADERS = tuple(_ENDPOINTS)


def _mixer_accepts(task, fader, endpoint) -> bool:
    """Ground truth: does the mixer accept a single-fader profile at this endpoint?"""
    try:
        make_mixed_variants(task, DISCOVERY_N, ParametricMixerProfile(**{fader: endpoint}))
        return True
    except ValueError:
        return False


def test_discovery_matches_mixer_accept_reject_for_every_template():
    """The drift lock: discovery.supported == the mixer's real accept/reject, registry-wide."""
    for task in PARAM_TEMPLATES:
        caps = {c.fader: c for c in discover_capabilities(task).capabilities}
        for fader, (low, high) in _ENDPOINTS.items():
            supported = caps[fader].supported
            low_ok = _mixer_accepts(task, fader, low)
            high_ok = _mixer_accepts(task, fader, high)
            # both endpoints agree with each other AND with discovery — no drift, no half-fader
            assert low_ok == high_ok == supported, (
                f"{task.id}/{fader}: discovery={supported}, mixer low={low_ok} high={high_ok}"
            )


def test_umfang_is_universal_and_always_accepted():
    """Umfang is the one always-on fader: never optional, always accepted at both endpoints."""
    for task in PARAM_TEMPLATES:
        umfang = next(c for c in discover_capabilities(task).capabilities
                      if c.fader == "umfang")
        assert umfang.supported and not umfang.optional
        assert umfang.default == Umfang.STANDARD.value
        assert [o.value for o in umfang.options] == ["kompakt", "standard", "erweitert"]
        assert _mixer_accepts(task, "umfang", Umfang.KOMPAKT)
        assert _mixer_accepts(task, "umfang", Umfang.ERWEITERT)


def test_capability_shape_is_consistent():
    """Every optional fader carries two labelled endpoints, a None default, and a reason iff
    unsupported (a supported fader never carries a decorative 'warum nicht')."""
    for task in PARAM_TEMPLATES:
        caps = discover_capabilities(task).capabilities
        assert [c.fader for c in caps] == [
            "umfang", "tiefe", "abstraktion", "offenheit", "geruest", "textlast"]
        for cap in caps:
            assert cap.label                                  # a German control label
            assert all(o.value and o.label for o in cap.options)
            if cap.fader in _OPTIONAL_FADERS:
                assert cap.optional and cap.default is None
                assert len(cap.options) == 2
                # reason present exactly when unsupported
                assert (cap.reason is None) == cap.supported
            else:                                             # umfang
                assert not cap.optional and cap.reason is None


def test_expected_capability_matrix():
    """A human-readable pin on which faders each family supports (guards silent regressions in
    the corpus of templates + recipes). Counts, not ids, so adding a template doesn't churn."""
    supported = {f: 0 for f in _OPTIONAL_FADERS}
    for task in PARAM_TEMPLATES:
        for cap in discover_capabilities(task).capabilities:
            if cap.fader in supported and cap.supported:
                supported[cap.fader] += 1
    # tiefe: the solution_paths recipes (percentage, percentage_rate, linear_system_2)
    assert supported["tiefe"] == 3
    # abstraktion: the student-figure recipes (pythagoras, kreis, quader, probability_tree)
    assert supported["abstraktion"] == 4
    # offenheit: the misconception-MC templates (percent-mc, linear-mc, ohm-mc, ersatz-mc)
    assert supported["offenheit"] == 4
    # textlast: the authored twins (tiefenregler-design §7: fin-lohnzettel/-handyvertrag +
    # mat-pythagoras/-kreis/-kennzahlen/-rechteck)
    assert supported["textlast"] == 6
    # geruest: broad (Formulierungshilfen apply to many kinds); a healthy majority
    assert supported["geruest"] >= 30


# --- the API surface ---------------------------------------------------------------------

def _client(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    from teachersaid.api import app as appmod

    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    appmod.STORE = ReviewStore(tmp_path / "store")
    return TestClient(appmod.app)


def test_capabilities_endpoint_returns_discovery(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    body = client.get("/api/templates/mat-prozent/capabilities").json()
    assert body["template_id"] == "mat-prozent"
    caps = {c["fader"]: c for c in body["capabilities"]}
    assert caps["umfang"]["supported"] and not caps["umfang"]["optional"]
    assert caps["tiefe"]["supported"] and caps["tiefe"]["reason"] is None
    # a rich template without a figure/MC/twin: honest German reasons on the unsupported faders
    assert not caps["abstraktion"]["supported"] and caps["abstraktion"]["reason"]
    assert not caps["textlast"]["supported"] and caps["textlast"]["reason"]


def test_capabilities_endpoint_matches_the_pure_function(tmp_path, monkeypatch):
    """The endpoint is a thin wrapper over discover_capabilities (no second source of truth)."""
    client = _client(tmp_path, monkeypatch)
    for tid in ("fin-lohnzettel", "phy-us-ohm-mc", "mat-pythagoras"):
        from teachersaid.library.templates import find_template
        expected = discover_capabilities(find_template(tid)).model_dump()
        assert client.get(f"/api/templates/{tid}/capabilities").json() == expected


def test_capabilities_endpoint_unknown_template_is_404(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    assert client.get("/api/templates/nope/capabilities").status_code == 404
