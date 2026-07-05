"""The circuit-schematic recipe (Netzliste → Schaltbild).

Locks the correct-by-construction guarantee: the Ersatzwiderstand of known nets is exact
(series 2+3 = 5 Ω, parallel 6‖3 = 2 Ω, a hand-computed nested net); Kirchhoff holds EXACTLY
(sympy Rationals) — ΣI of parallel branches = the node current, ΣU of series elements = the node
voltage; labels are maskable and the asked element is `focus`; the schematic renders; degenerate
netlists are rejected. Offline.
"""
from __future__ import annotations

import sympy as sp

from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.circuits import (circuit_construction, equivalent_resistance,
                                           solve_network)
from teachersaid.pipeline.scene import Label, Polyline, Scene
from teachersaid.schema.assets import Asset


def _R(ohm, label="R"):
    return {"type": "resistor", "ohm": ohm, "label": label}


SERIES = {"type": "series", "children": [_R(2, "R₁"), _R(3, "R₂")]}
PARALLEL = {"type": "parallel", "children": [_R(6, "R₁"), _R(3, "R₂")]}
# nested mixed: R₁(100) in series with [ R₂(200) ∥ R₃(200) ] = 100 + 100 = 200 Ω
MIXED = {"type": "series", "children": [
    _R(100, "R₁"),
    {"type": "parallel", "children": [_R(200, "R₂"), _R(200, "R₃")]}]}
# doubly nested: [ (R₁+R₂) ∥ R₃ ] where R₁=R₂=100, R₃=150 → 200 ∥ 150 = 600/7 Ω
NESTED = {"type": "parallel", "children": [
    {"type": "series", "children": [_R(100, "R₁"), _R(100, "R₂")]},
    _R(150, "R₃")]}


def test_equivalent_resistance_known_nets():
    assert equivalent_resistance(SERIES) == 5.0            # 2 + 3
    assert equivalent_resistance(PARALLEL) == 2.0          # 6‖3 = 18/9
    assert equivalent_resistance(MIXED) == 200.0           # 100 + (200‖200)
    assert abs(equivalent_resistance(NESTED) - 600 / 7) < 1e-9    # 200‖150


def test_kirchhoff_holds_exactly():
    """The defining property, exact (sympy Rationals): ΣU of a series node = its node voltage,
    ΣI of a parallel node = its node current; the whole circuit obeys U = R·I."""
    sol = solve_network(MIXED, 12)
    # exact totals
    assert sol["R_total_exact"] == sp.Integer(200)
    assert sol["I_total_exact"] == sp.Rational(12, 200)
    elems = {e["node"]["label"]: e for e in sol["elements"]}
    # series (Maschenregel): U(R₁) + U(parallel block) = U_source. The parallel block voltage is
    # shared by R₂ and R₃, so U(R₁) + U(R₂) = 12 on the R₁→R₂ path.
    assert elems["R₁"]["U"] + elems["R₂"]["U"] == sp.Integer(12)
    # parallel (Knotenregel): I(R₂) + I(R₃) = I_total (they carry the whole current together)
    assert elems["R₂"]["I"] + elems["R₃"]["I"] == sol["I_total_exact"]
    # Ohm on every element: U == R·I, exactly
    for e in sol["elements"]:
        assert e["U"] == e["R"] * e["I"]


def test_series_current_is_shared_parallel_voltage_is_shared():
    ser = solve_network(SERIES, 10)                        # same current everywhere
    Is = {e["node"]["label"]: e["I"] for e in ser["elements"]}
    assert Is["R₁"] == Is["R₂"] == ser["I_total_exact"]
    par = solve_network(PARALLEL, 12)                      # same voltage everywhere
    Us = {e["node"]["label"]: e["U"] for e in par["elements"]}
    assert Us["R₁"] == Us["R₂"] == sp.Integer(12)


def test_nested_net_hand_computed():
    """(R₁+R₂) ∥ R₃ with 100,100,150 at 14 V: R = 600/7 Ω, I_total = 14·7/600 = 49/300 A;
    the (R₁+R₂) branch sees 14 V so carries 14/200 = 7/100 A, R₃ carries 14/150 A; they sum."""
    sol = solve_network(NESTED, 14)
    assert sol["R_total_exact"] == sp.Rational(600, 7)
    elems = {e["node"]["label"]: e for e in sol["elements"]}
    assert elems["R₁"]["I"] == elems["R₂"]["I"] == sp.Rational(14, 200)   # series branch current
    assert elems["R₃"]["I"] == sp.Rational(14, 150)
    assert (elems["R₁"]["I"] + elems["R₃"]["I"]) == sol["I_total_exact"]  # Knotenregel


def test_lamp_is_electrically_a_resistor():
    net = {"type": "series", "children": [{"type": "lamp", "ohm": 40, "label": "L₁"}, _R(20, "R₁")]}
    assert equivalent_resistance(net) == 60.0


def _labels(scene: Scene) -> list[str]:
    return [L.text for L in scene.layers if isinstance(L, Label)]


def test_labels_are_maskable_and_asked_element_is_focus():
    shown = circuit_construction(MIXED, 12, show_value=True)
    masked = circuit_construction(MIXED, 12, show_value=False, ask="R₂")
    assert any("R₁ = 100 Ω" == t for t in _labels(shown))
    assert any(t.startswith("U =") and "V" in t and "?" not in t for t in _labels(shown))
    assert "R₂ = ?" in _labels(masked) and "U = ?" in _labels(masked)
    # the asked resistor is drawn in the focus role (its rectangle Polyline)
    focus_rects = [L for L in masked.layers if isinstance(L, Polyline) and L.role == "focus"]
    assert focus_rects, "asked element R₂ should carry the focus role"


def test_gegeben_gesucht_selective_mask():
    """The canonical task shape: gegeben U, I, R₁, R₃ — berechne R₂ (und Rers als
    Zwischenschritt). `mask` hides EXACTLY the listed tokens; every given stays visible."""
    sc = circuit_construction(MIXED, 12, ask="R₂", mask=["R₂", "Rers"])
    labels = _labels(sc)
    masked = [t for t in labels if "?" in t]
    assert "R₂ = ?" in masked
    assert any("Rₑᵣₛ = ?" in t for t in masked)
    assert len(masked) == 2                                    # EXACTLY the masked ones read "?"
    # the givens render with their computed values
    assert "R₁ = 100 Ω" in labels and "R₃ = 200 Ω" in labels
    assert "U = 12 V" in labels and "I = 0,06 A" in labels
    # ask (focus) worked alongside mask — orthogonal concerns
    assert any(L.role == "focus" for L in sc.layers if isinstance(L, Polyline))


def test_mask_can_target_the_totals():
    """"U"/"I"/"Rers" are maskable tokens too (e.g. the task 'berechne U' from R and I)."""
    labels = _labels(circuit_construction(MIXED, 12, mask=["U", "I", "Rers"]))
    assert "U = ?" in labels and "I = ?" in labels
    assert any("Rₑᵣₛ = ?" in t for t in labels)
    assert "R₁ = 100 Ω" in labels and "R₂ = 200 Ω" in labels   # elements stay visible


def test_show_value_false_masks_all_backcompat():
    """Without `mask`, show_value=False keeps its original mask-ALL meaning (the stored spec
    contract stays backward-compatible)."""
    labels = _labels(circuit_construction(MIXED, 12, show_value=False))
    for t in ("R₁ = ?", "R₂ = ?", "R₃ = ?", "U = ?", "I = ?"):
        assert t in labels
    assert any("Rₑᵣₛ = ?" in t for t in labels)
    assert not any("Ω" in t and "?" not in t for t in labels)  # no value leaks anywhere


def test_mask_wins_over_show_value_and_accepts_a_bare_string():
    """An explicit `mask` overrides show_value entirely (mask exactly those; the rest shows);
    a bare string is tolerated as a one-element list (hand-written JSON robustness)."""
    labels = _labels(circuit_construction(MIXED, 12, show_value=False, mask=["I"]))
    assert "I = ?" in labels
    assert "R₁ = 100 Ω" in labels and "U = 12 V" in labels     # mask wins: the rest shows
    labels2 = _labels(circuit_construction(MIXED, 12, mask="R₂"))
    assert "R₂ = ?" in labels2 and "R₁ = 100 Ω" in labels2


def test_mask_spec_key_flows_through_build_asset(tmp_path):
    """The wrapper's stored contract: spec["mask"] reaches the scene (render smoke via the
    generator id, plus the scene-level check above)."""
    a = Asset(id="c_mask", role="figure", generator="matplotlib:circuit",
              spec={"net": MIXED, "volt": 12, "ask": "R₂", "mask": ["R₂", "Rers"]})
    p = build_asset(a, outdir=tmp_path)
    assert p.exists() and p.stat().st_size > 1500


def test_schematic_renders_through_build_asset(tmp_path):
    PNG = b"\x89PNG\r\n\x1a\n"
    for name, net in {"series": SERIES, "parallel": PARALLEL, "mixed": MIXED,
                      "nested": NESTED}.items():
        a = Asset(id=f"c_{name}", role="figure", generator="matplotlib:circuit",
                  spec={"net": net, "volt": 12})
        p = build_asset(a, outdir=tmp_path)
        assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1500


def test_recipe_in_generation_vocabulary():
    assert "matplotlib:circuit" in GENERATION_RECIPES


def test_degenerate_nets_rejected():
    bad_nets = [
        {"type": "series", "children": []},                       # empty
        {"type": "series", "children": [_R(0, "R₁")]},            # non-positive resistance
        {"type": "resistor", "ohm": -5, "label": "R₁"},           # negative resistance
        {"type": "parallel", "children": [{"type": "series", "children": []}]},  # empty subtree
        {"type": "frobnicate", "children": [_R(10)]},             # unknown node type
    ]
    for net in bad_nets:
        try:
            solve_network(net, 12)
            assert False, f"expected ValueError for {net}"
        except ValueError:
            pass
    # a valid net at non-positive voltage is also rejected
    try:
        solve_network(SERIES, 0)
        assert False, "expected ValueError for zero voltage"
    except ValueError:
        pass


def test_determinism():
    a = circuit_construction(MIXED, 12)
    b = circuit_construction(MIXED, 12)
    assert _labels(a) == _labels(b) and len(a.layers) == len(b.layers)
