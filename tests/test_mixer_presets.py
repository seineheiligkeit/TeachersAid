"""Lesson-purpose presets: curated fader bundles over the ONE typed Mischpult profile.

A preset is a lesson PURPOSE (Wiederholung vor der Schularbeit · Vertiefungsstunde ·
Vertretungsstunde · Hausübung), not a student level.  These tests lock: every preset validates
as a `ParametricMixerProfile` (round-trip through the one currency), references only real faders
and only their ACTIVE endpoints (so a preset can never cause a spurious capability failure), and
— intersected with a template's DISCOVERED capabilities exactly as the dashboard does — always
composes on every registered template (a preset never bypasses capability discovery).  The
drift-test style mirrors `tests/test_mixer_capabilities.py`.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from teachersaid.library.templates import PARAM_TEMPLATES
from teachersaid.pipeline.mixer import (
    DISCOVERY_N,
    adjusted_variant_count,
    discover_capabilities,
    make_mixed_variants,
)
from teachersaid.schema.mixer import (
    LESSON_PRESETS,
    ParametricMixerProfile,
    lesson_presets_payload,
)
from teachersaid.store.repository import ReviewStore

# The ACTIVE (sheet-changing) endpoint of each OPTIONAL fader.  A preset may ONLY ever set these
# — never the base endpoint (ueben/anschaulich/geschlossen/ohne/voll), which would add a
# capability requirement for a no-op change and risk a spurious hard-fail on a template that
# merely lacks that fader.  (Umfang is universal — any of its three values is safe.)
_ACTIVE_ENDPOINT: dict[str, str] = {
    "tiefe": "strategien_vergleichen",
    "abstraktion": "formal",
    "offenheit": "offen",
    "geruest": "gestuetzt",
    "textlast": "einfach",
}
_PRESET_IDS = ["wiederholung", "vertiefung", "vertretung", "hausuebung"]


def test_the_four_lesson_purposes_are_present():
    assert [p.id for p in LESSON_PRESETS] == _PRESET_IDS
    for p in LESSON_PRESETS:
        assert p.name and p.description          # German display surfaces present


def test_every_preset_bundle_validates_through_the_typed_profile():
    """The bundle round-trips through the ONE profile currency — no second schema."""
    for p in LESSON_PRESETS:
        assert isinstance(p.profile, ParametricMixerProfile)
        assert ParametricMixerProfile.model_validate(p.profile.model_dump()) == p.profile


def test_presets_reference_only_real_faders_and_active_endpoints():
    """Drift lock (mirrors the capabilities drift test): every fader a preset sets is a real
    field on the typed profile, Umfang is always present, and every OPTIONAL fader it sets is the
    ACTIVE endpoint (so applying a preset never demands a capability just to no-op a fader)."""
    fields = set(ParametricMixerProfile.model_fields)
    for p in LESSON_PRESETS:
        faders = p.set_faders()
        assert "umfang" in faders                # Umfang is universal, always present
        assert set(faders) <= fields             # only real profile faders — nothing invented
        for fader, value in faders.items():
            if fader == "umfang":
                assert value in ("kompakt", "standard", "erweitert")
            else:
                assert value == _ACTIVE_ENDPOINT[fader], (p.id, fader, value)


def test_presets_compose_when_capabilities_are_discovered_at_the_build_count():
    """The crux — a preset never bypasses discovery.  For EVERY registered template, the preset
    intersected with the template's DISCOVERED capabilities (the client-side rule: keep Umfang +
    the supported optional faders) builds variants without a hard-fail and the Regler-Lint passes,
    as long as discovery and the build agree on the count.  Umfang scales the build count, so the
    honest self-consistent guarantee probes discovery at the SAME `eff_n` the build uses."""
    for task in PARAM_TEMPLATES:
        for preset in LESSON_PRESETS:
            eff_n = adjusted_variant_count(DISCOVERY_N, preset.profile.umfang)
            caps = {c.fader: c for c in discover_capabilities(task, n=eff_n).capabilities}
            supported = {f: v for f, v in preset.set_faders().items()
                         if f == "umfang" or caps[f].supported}
            _, _, report, _ = make_mixed_variants(
                task, DISCOVERY_N, ParametricMixerProfile(**supported))
            assert report.passed, (task.id, preset.id)


def test_dashboard_flow_is_honest_never_silently_wrong():
    """The dashboard discovers at DISCOVERY_N but Umfang scales the build count, so a
    SOME-quantifier capability (Gerüst/Abstraktion) shown at n=6 can vanish at a kompakt-reduced
    count on a rare late-seed template (measured: 3 Hausübung × Oberstufe-Maths cells).  When it
    does, the build must fail as an honest mixer ValueError — surfaced to the teacher via
    `item.error`, NEVER a crash or a silent wrong sheet — the same pre-existing Umfang×n property
    as manually pairing kompakt with that fader.  This locks that the residual edge stays honest
    (a clean rejection), without pinning brittle template ids."""
    for task in PARAM_TEMPLATES:
        caps = {c.fader: c for c in discover_capabilities(task).capabilities}   # dashboard: n=6
        for preset in LESSON_PRESETS:
            supported = {f: v for f, v in preset.set_faders().items()
                         if f == "umfang" or caps[f].supported}
            profile = ParametricMixerProfile(**supported)
            try:
                _, _, report, _ = make_mixed_variants(task, DISCOVERY_N, profile)
            except ValueError:
                continue                    # an honest, surfaced capability rejection — acceptable
            assert report.passed, (task.id, preset.id)


def test_each_preset_can_shape_some_template():
    """Sanity: each purpose actually moves SOME template (it is not dead copy).  A preset shapes a
    template when it sets a non-standard Umfang or any supported optional fader."""
    shaped = {p.id: False for p in LESSON_PRESETS}
    for task in PARAM_TEMPLATES:
        caps = {c.fader: c for c in discover_capabilities(task).capabilities}
        for preset in LESSON_PRESETS:
            faders = preset.set_faders()
            if faders.get("umfang") != "standard" or any(
                    caps[f].supported for f in faders if f != "umfang"):
                shaped[preset.id] = True
    assert all(shaped.values()), shaped


# --- the API surface (mirrors test_mixer_capabilities) -----------------------------------

def _client(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    from teachersaid.api import app as appmod

    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    appmod.STORE = ReviewStore(tmp_path / "store")
    return TestClient(appmod.app)


def test_presets_endpoint_returns_the_served_table(tmp_path, monkeypatch):
    """The endpoint is a thin wrapper over the served table (no second source of truth)."""
    client = _client(tmp_path, monkeypatch)
    body = client.get("/api/mixer/presets").json()
    assert body == {"presets": lesson_presets_payload()}
    presets = {p["id"]: p for p in body["presets"]}
    assert list(presets) == _PRESET_IDS
    # the PARTIAL bundle shape the dashboard applies to the selects
    assert presets["vertretung"]["faders"] == {
        "umfang": "standard", "geruest": "gestuetzt", "textlast": "einfach"}
    assert presets["hausuebung"]["faders"] == {"umfang": "kompakt", "geruest": "gestuetzt"}
    assert presets["wiederholung"]["faders"] == {"umfang": "erweitert", "offenheit": "offen"}
    for p in body["presets"]:
        assert p["name"] and p["description"]    # German surfaces present on every preset
