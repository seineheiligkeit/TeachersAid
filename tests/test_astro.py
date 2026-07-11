"""The Sternkarten-Engine — positional astronomy + the star-chart / moon-phase recipes.

Accuracy is locked against PUBLISHED reference instants from Jean Meeus, *Astronomical
Algorithms* (2nd ed., Willmann-Bell 1998) — the standard the physicist SME will check
against. Catalog integrity, the answer-masking invariant, chart rendering (no colliding
labels) and moon-phase orientation are locked too.
"""
from __future__ import annotations

import math
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from teachersaid.grounding import astro as cat
from teachersaid.pipeline import astro as ap
from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline.figtext import overlap_pairs
from teachersaid.pipeline.scene import Region, render_scene, scene_to_png


# --- time + sidereal time ---------------------------------------------------
def test_julian_date_standard_epoch():
    # J2000.0 = 2000 January 1.5 TT = JD 2451545.0 (Meeus §7).
    assert ap.julian_date(datetime(2000, 1, 1, 12, 0)) == 2451545.0
    # Meeus Example 7.a: 1957 October 4.81 (Sputnik 1) = JD 2436116.31.
    assert abs(ap.julian_date(datetime(1957, 10, 4, 19, 26, 24)) - 2436116.31) < 1e-2


def test_gmst_meeus_example_12a():
    # Meeus Example 12.a: 1987 April 10, 0h UT → GMST = 13h10m46.3668s = 197.693195°.
    jd = ap.julian_date(datetime(1987, 4, 10, 0, 0))
    assert jd == 2446895.5
    assert abs(ap.gmst_deg(jd) - 197.693195) < 1e-4


# --- the alt-az transform ---------------------------------------------------
def test_altaz_zenith_is_overhead():
    # A star with Dec = observer latitude, on the meridian (LST = RA), sits at the zenith.
    alt, az = ap.equatorial_to_horizontal(100.0, 48.21, lst_deg_=100.0, lat_deg=48.21)
    assert abs(alt - 90.0) < 1e-6


def test_altaz_meeus_example_13b():
    # Meeus Example 13.b: apparent (α,δ)=(347.3193°, −6.7198°), Washington
    # (lat 38.9213°, lon −77.0655°), apparent Greenwich sidereal time 8h34m56.853s.
    # Result: altitude h = 15.1249°, azimuth A = 68.0337° WEST of south → 248.0337° from N.
    gst_deg = 15.0 * (8 + 34 / 60 + 56.853 / 3600)
    lst = (gst_deg - 77.0655) % 360.0
    alt, az = ap.equatorial_to_horizontal(347.3193, -6.7198, lst, 38.9213)
    assert abs(alt - 15.1249) < 1e-3
    assert abs(az - 248.0337) < 1e-3


# --- the Sun ----------------------------------------------------------------
def test_sun_solstices_and_equinox():
    # The Sun's declination reaches ±the obliquity (~23.44°) at the solstices and ~0 at
    # the equinoxes — a physics invariant independent of any single reference table.
    dec_jun = ap.sun_position(ap.julian_date(datetime(2001, 6, 21, 12)))[1]
    dec_dec = ap.sun_position(ap.julian_date(datetime(2001, 12, 21, 12)))[1]
    dec_mar = ap.sun_position(ap.julian_date(datetime(2001, 3, 20, 12)))[1]
    assert 23.2 < dec_jun < 23.6
    assert -23.6 < dec_dec < -23.2
    assert abs(dec_mar) < 0.6


def test_sun_meeus_example_25b():
    # Meeus Example 25.b: 1992 October 13, 0h TD → apparent longitude ≈ 199.9073°,
    # declination ≈ −7.785°. Low-precision method, good to ~0.01°.
    ra, dec, lon, dist = ap.sun_position(ap.julian_date(datetime(1992, 10, 13, 0, 0)))
    assert abs(lon - 199.9073) < 0.02
    assert abs(dec - (-7.785)) < 0.02


# --- the Moon ---------------------------------------------------------------
def test_moon_position_meeus_example_47a():
    # Meeus Example 47.a: 1992 April 12, 0h TD (JDE 2448724.5) →
    # geocentric ecliptic λ = 133.162655°, β = −3.229126°, Δ = 368409.7 km.
    # Truncated ELP series → λ within ~0.03°, distance within a few tens of km.
    jd = ap.julian_date(datetime(1992, 4, 12, 0, 0))
    assert jd == 2448724.5
    ra, dec, lon, lat, dist = ap.moon_position(jd)
    assert abs(lon - 133.162655) < 0.1
    assert abs(lat - (-3.229126)) < 0.1
    assert abs(dist - 368409.7) < 200.0
    # apparent equatorial position (Meeus gives α ≈ 134.688°, δ ≈ +13.768°; nutation
    # ~0.004° is neglected → well within a degree, the documented Moon accuracy).
    assert abs(ra - 134.688) < 0.5
    assert abs(dec - 13.768) < 0.5


def test_moon_phase_meeus_example_48a():
    # Meeus Example 48.a: 1992 April 12, 0h TD → phase angle i = 69.0756°,
    # illuminated fraction k = 0.6786.
    ph = ap.moon_phase(ap.julian_date(datetime(1992, 4, 12, 0, 0)))
    assert abs(ph.illuminated_fraction - 0.6786) < 0.005
    assert abs(ph.phase_angle_deg - 69.0756) < 0.5


def test_moon_phase_known_full_and_new_moons():
    # Well-documented syzygies (times in UTC). Full → k≈1, New → k≈0.
    full = ap.moon_phase(ap.julian_date(datetime(2000, 1, 21, 4, 41)))   # 2000 total eclipse
    new = ap.moon_phase(ap.julian_date(datetime(2000, 1, 6, 18, 14)))
    full25 = ap.moon_phase(ap.julian_date(datetime(2025, 1, 13, 22, 27)))  # 2025 „Wolf Moon"
    assert full.illuminated_fraction > 0.99
    assert new.illuminated_fraction < 0.02
    assert full25.illuminated_fraction > 0.99
    # a few days after new → waxing; a few days after full → waning
    assert ap.moon_phase(ap.julian_date(datetime(2000, 1, 10, 20))).waxing is True
    assert ap.moon_phase(ap.julian_date(datetime(2000, 1, 25, 20))).waxing is False


# --- catalog integrity ------------------------------------------------------
def test_catalog_coordinates_in_range_and_ids_unique():
    assert len(cat.STARS) >= 90
    for sid, s in cat.STARS.items():
        assert 0.0 <= s.ra_deg < 360.0, (sid, s.ra_deg)
        assert -90.0 <= s.dec_deg <= 90.0, (sid, s.dec_deg)
        assert math.isfinite(s.mag)
    # the slug ids are the catalog keys and must be unique (dict would collapse dupes)
    assert len(cat._ROWS) == len(cat.STARS)


def test_every_asterism_vertex_resolves_and_is_named():
    for abbr, edges in cat.ASTERISMS.items():
        assert abbr in cat.CONSTELLATIONS, abbr
        for a, b in edges:
            assert a in cat.STARS, (abbr, a)
            assert b in cat.STARS, (abbr, b)
    # the classic Big Dipper is present and complete (7 Wagen stars, 6 segments)
    uma = {v for e in cat.ASTERISMS["UMa"] for v in e}
    assert {"dubhe", "merak", "phecda", "megrez", "alioth", "mizar", "alkaid"} <= uma


def test_recognisable_positions_over_vienna_winter():
    # A physical sanity check on the whole chain (catalog → LST → alt-az): on a mid-January
    # evening over Vienna, Orion is UP in the south and the Big Dipper is UP in the NE.
    jd, _, lst, lat, lon = ap.resolve_instant({"date": "2026-01-15", "time": "21:00"})

    def altaz(sid):
        s = cat.STARS[sid]
        return ap.equatorial_to_horizontal(s.ra_deg, s.dec_deg, lst, lat)

    bet_alt, bet_az = altaz("betelgeuse")
    assert bet_alt > 20 and 120 < bet_az < 210          # Orion up, roughly south
    dub_alt, dub_az = altaz("dubhe")
    assert dub_alt > 0 and (dub_az < 90 or dub_az > 300)  # Big Dipper up, north-east/north


# --- the masking invariant --------------------------------------------------
def _label_texts(scene):
    from teachersaid.pipeline.scene import Label
    return [L.text for L in scene.layers if isinstance(L, Label)]


def test_star_chart_masks_names_by_default():
    # Default = a task figure: no star names, no constellation names printed.
    sc = ap.star_chart_scene({"date": "2026-01-15", "time": "21:00"})
    texts = _label_texts(sc)
    assert "Orion" not in texts and "Großer Wagen" not in texts
    assert "Betelgeuse" not in texts and "Sirius" not in texts
    # only the compass ring is labelled
    assert {"N", "O", "S", "W"} <= set(texts)


def test_star_chart_riddle_hides_the_highlighted_name():
    # „Welches Sternbild ist das?" — a highlighted constellation must NOT print its name.
    sc = ap.star_chart_scene({"date": "2026-01-15", "time": "21:00", "highlight": "UMa"})
    assert "Großer Wagen" not in _label_texts(sc)


def test_star_chart_labels_reveal_names_when_asked():
    # The teacher/solution chart CAN show the names.
    sc = ap.star_chart_scene({"date": "2026-01-15", "time": "21:00",
                              "show_constellation_labels": True})
    assert "Orion" in _label_texts(sc)


def test_moon_phase_masks_name_for_a_task():
    masked = ap.moon_phase_scene({"illuminated_fraction": 0.5, "waxing": True,
                                  "show_label": False})
    assert "?" in _label_texts(masked)
    assert not any("Viertel" in t for t in _label_texts(masked))
    shown = ap.moon_phase_scene({"illuminated_fraction": 0.5, "waxing": True})
    assert any("Viertel" in t for t in _label_texts(shown))


# --- rendering + layout -----------------------------------------------------
def _render_pairs(scene):
    with plt.rc_context(fs.house_rc()):
        fig, ax = plt.subplots(figsize=scene.canvas.figsize)
        render_scene(scene, ax)
        pairs = overlap_pairs(fig)
        plt.close(fig)
    return pairs


def test_star_chart_default_has_no_overlapping_labels():
    # The default (masked) task chart's labels (the N/O/S/W ring, the source line) must
    # not collide — the figure-side layout lint.
    sc = ap.star_chart_scene({"date": "2026-01-15", "time": "21:00"})
    assert _render_pairs(sc) == []


def test_recipes_render_pngs(tmp_path):
    star = scene_to_png(ap.star_chart_scene({"date": "2026-07-15", "time": "23:00",
                                             "show_constellation_labels": True}),
                        tmp_path / "sky.png")
    moon = scene_to_png(ap.moon_phase_scene({"date": "2026-01-15", "time": "21:00"}),
                        tmp_path / "moon.png")
    assert star.exists() and star.stat().st_size > 5000
    assert moon.exists() and moon.stat().st_size > 3000


def test_moon_phase_orientation_north_hemisphere():
    # WAXING → lit on the RIGHT (illuminated region centroid x > 0); WANING → left.
    def lit_centroid_x(waxing):
        sc = ap.moon_phase_scene({"illuminated_fraction": 0.3, "waxing": waxing})
        region = next(L for L in sc.layers if isinstance(L, Region))
        return sum(p[0] for p in region.points) / len(region.points)

    assert lit_centroid_x(True) > 0.0
    assert lit_centroid_x(False) < 0.0


# --- recipe registration ----------------------------------------------------
def test_recipes_registered_in_the_generation_library():
    from teachersaid.pipeline.assets import GENERATION_RECIPES, _GENERATORS, build_asset
    from teachersaid.schema.assets import Asset

    for gid in ("matplotlib:star_chart", "matplotlib:moon_phase"):
        assert gid in GENERATION_RECIPES
        assert gid in _GENERATORS
    # they actually build through the ordinary asset path
    p = build_asset(Asset(id="t-moon", role="figure", generator="matplotlib:moon_phase",
                          spec={"illuminated_fraction": 0.4, "waxing": True}))
    assert p.exists()


# --- the deliberately rejected seam -----------------------------------------
def test_iss_passes_are_a_documented_rejected_seam():
    # ISS/satellite passes need live TLE data (not offline-stable) — recorded as OUT by
    # decision in BOTH module docstrings, not silently forgotten.
    assert "ISS" in ap.__doc__ and "TLE" in ap.__doc__
    assert "ISS" in cat.__doc__
