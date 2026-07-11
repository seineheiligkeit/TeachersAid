"""Positional astronomy — pure computation + the star-chart / moon-phase recipes.

Everything here is COMPUTED (Meeus-grade spherical astronomy), never authored: a
Julian date → sidereal time → the equatorial→horizontal transform for an observer,
plus low-precision Sun and truncated-series Moon positions and the Moon's phase. The
star positions themselves are *selected* from the curated catalog (`grounding/astro`);
this module turns "which stars, seen from where and when" into a figure — the same
two-tier seam as `constructions.py` (a didactic recipe COMPUTES a `scene.Scene`; the
LLM never authors one).

Accuracy (tested against published reference instants in `tests/test_astro.py`):
  * Julian date, GMST/LST, and the alt-az transform are EXACT (to floating point) —
    Meeus Ch. 12/13. GMST is locked against Meeus *Astronomical Algorithms* 2nd ed.
    Example 12.a (1987 Apr 10, 0h UT → 13h10m46.37s).
  * The Sun is the low-precision method (Meeus Ch. 25), good to ~0.01°.
  * The Moon uses the main periodic terms of the ELP-2000 series (Meeus Ch. 47,
    Tables 47.A/47.B, truncated to the largest terms). Geocentric longitude is good
    to **~0.03°** at the reference instant and the position is well within **~1°**
    across the range that matters for a naked-eye finder chart — locked against Meeus
    Example 47.a (1992 Apr 12, 0h TD → λ=133.16°, β=−3.23°, Δ=368410 km). The small
    additive (planetary/flattening) terms and ΔT are neglected — dominated by the
    naked-eye chart's own precision, and documented rather than silently dropped.
  * The Moon's PHASE (illuminated fraction) is exact to the day: locked against Meeus
    Example 48.a (1992 Apr 12, 0h TD → k=0.6786, phase angle 69.08°).
  * J2000.0 positions are used as-is; ~0.3° of precession to 2026 is far below a
    finder chart's needs.

Deliberately rejected seam — **ISS / satellite passes.** A live overhead pass needs
current TLE orbital elements (updated every few days, fetched over the network); that
is not offline-stable and not a durable corpus fact, so it is OUT by decision. The
Sun/Moon/stars here are all closed-form from the date — no network, fully offline.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from ..grounding import astro as cat
from .scene import Arc, Canvas, CircleShape, Label, Line, PointMark, Polyline, Region, Scene

D2R = math.pi / 180.0
R2D = 180.0 / math.pi
J2000 = 2451545.0
SYNODIC_MONTH = 29.530588853   # mean synodic month (days)
AU_KM = 149597870.7


# --- time -------------------------------------------------------------------
def julian_date(dt: datetime) -> float:
    """Julian Day for a UTC calendar date/time (Meeus 7.1, Gregorian). `dt` is treated
    as UT; ΔT (UT vs. TT) is neglected — sub-arc-minute for the Sun and dominated by the
    Moon-series truncation, immaterial for a finder chart."""
    y, m = dt.year, dt.month
    day = dt.day + (dt.hour + dt.minute / 60.0 + (dt.second + dt.microsecond / 1e6) / 3600.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4                       # Gregorian calendar correction
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + b - 1524.5


def julian_centuries(jd: float) -> float:
    return (jd - J2000) / 36525.0


def gmst_deg(jd: float) -> float:
    """Greenwich Mean Sidereal Time in degrees (Meeus 12.4), for any instant."""
    t = julian_centuries(jd)
    theta = (280.46061837 + 360.98564736629 * (jd - J2000)
             + 0.000387933 * t * t - t * t * t / 38710000.0)
    return theta % 360.0


def lst_deg(jd: float, lon_deg: float) -> float:
    """Local (apparent≈mean) Sidereal Time in degrees; `lon_deg` east-positive."""
    return (gmst_deg(jd) + lon_deg) % 360.0


def obliquity_deg(jd: float) -> float:
    """Mean obliquity of the ecliptic (Meeus 22.2), degrees."""
    t = julian_centuries(jd)
    return 23.439291 - 0.0130042 * t - 1.64e-7 * t * t + 5.04e-7 * t * t * t


# --- coordinate transform ---------------------------------------------------
def equatorial_to_horizontal(
    ra_deg: float, dec_deg: float, lst_deg_: float, lat_deg: float
) -> tuple[float, float]:
    """(RA, Dec) → (altitude, azimuth) for an observer, all in degrees. Azimuth is
    measured from **North, clockwise** (N=0°, E=90°, S=180°, W=270°) — the compass
    convention the chart's N/O/S/W ring uses. Standard Meeus 13.5/13.6 (rewritten
    from Meeus' south-referenced azimuth to the north-referenced one)."""
    ha = (lst_deg_ - ra_deg) * D2R                    # local hour angle (rad)
    dec = dec_deg * D2R
    lat = lat_deg * D2R
    sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ha)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    alt = math.asin(sin_alt)
    # azimuth from North, clockwise (E positive)
    az = math.atan2(math.sin(ha), math.cos(ha) * math.sin(lat) - math.tan(dec) * math.cos(lat))
    az_north = (az * R2D + 180.0) % 360.0
    return alt * R2D, az_north


def _ecl_to_equatorial(lon_deg: float, lat_deg: float, eps_deg: float) -> tuple[float, float]:
    lon, lat, eps = lon_deg * D2R, lat_deg * D2R, eps_deg * D2R
    ra = math.atan2(math.sin(lon) * math.cos(eps) - math.tan(lat) * math.sin(eps),
                    math.cos(lon))
    dec = math.asin(math.sin(lat) * math.cos(eps) + math.cos(lat) * math.sin(eps) * math.sin(lon))
    return (ra * R2D) % 360.0, dec * R2D


# --- the Sun (Meeus Ch. 25, low precision) ----------------------------------
def sun_position(jd: float) -> tuple[float, float, float, float]:
    """Geometric/apparent Sun: returns (ra_deg, dec_deg, ecl_lon_deg, dist_km).
    Good to ~0.01° (Meeus Ch. 25)."""
    t = julian_centuries(jd)
    l0 = (280.46646 + 36000.76983 * t + 0.0003032 * t * t) % 360.0
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    e = 0.016708634 - 0.000042037 * t - 0.0000001267 * t * t
    mr = m * D2R
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mr)
         + (0.019993 - 0.000101 * t) * math.sin(2 * mr)
         + 0.000289 * math.sin(3 * mr))
    true_lon = l0 + c
    nu = m + c
    r_au = 1.000001018 * (1 - e * e) / (1 + e * math.cos(nu * D2R))
    omega = 125.04 - 1934.136 * t
    lam = true_lon - 0.00569 - 0.00478 * math.sin(omega * D2R)       # apparent longitude
    eps = obliquity_deg(jd) + 0.00256 * math.cos(omega * D2R)        # apparent obliquity
    ra, dec = _ecl_to_equatorial(lam, 0.0, eps)
    return ra, dec, lam % 360.0, r_au * AU_KM


# --- the Moon (Meeus Ch. 47, main periodic terms) ---------------------------
# (D, M, M', F, Σl[1e-6 deg], Σr[1e-3 km]) — Table 47.A, largest terms.
_MOON_LR = [
    (0, 0, 1, 0, 6288774, -20905355),
    (2, 0, -1, 0, 1274027, -3699111),
    (2, 0, 0, 0, 658314, -2955968),
    (0, 0, 2, 0, 213618, -569925),
    (0, 1, 0, 0, -185116, 48888),
    (0, 0, 0, 2, -114332, -3149),
    (2, 0, -2, 0, 58793, 246158),
    (2, -1, -1, 0, 57066, -152138),
    (2, 0, 1, 0, 53322, -170733),
    (2, -1, 0, 0, 45758, -204586),
    (0, 1, -1, 0, -40923, -129620),
    (1, 0, 0, 0, -34720, 108743),
    (0, 1, 1, 0, -30383, 104755),
    (2, 0, 0, -2, 15327, 10321),
    (0, 0, 1, 2, -12528, 0),
    (0, 0, 1, -2, 10980, 79661),
    (4, 0, -1, 0, 10675, -34782),
    (0, 0, 3, 0, 10034, -23210),
    (4, 0, -2, 0, 8548, -21636),
    (2, 1, -1, 0, -7888, 24208),
    (2, 1, 0, 0, -6766, 30824),
    (1, 0, -1, 0, -5163, -8379),
]
# (D, M, M', F, Σb[1e-6 deg]) — Table 47.B, largest latitude terms.
_MOON_B = [
    (0, 0, 0, 1, 5128122),
    (0, 0, 1, 1, 280602),
    (0, 0, 1, -1, 277693),
    (2, 0, 0, -1, 173237),
    (2, 0, -1, 1, 55413),
    (2, 0, -1, -1, 46271),
    (2, 0, 0, 1, 32573),
    (0, 0, 2, 1, 17198),
    (2, 0, 1, -1, 9266),
    (0, 0, 2, -1, 8822),
    (2, -1, 0, -1, 8216),
    (2, 0, -2, -1, 4324),
    (2, 0, 1, 1, 4200),
]


def moon_position(jd: float) -> tuple[float, float, float, float, float]:
    """Truncated ELP-2000 Moon (Meeus Ch. 47). Returns
    (ra_deg, dec_deg, ecl_lon_deg, ecl_lat_deg, dist_km). ~1° accuracy (documented)."""
    t = julian_centuries(jd)
    lp = 218.3164477 + 481267.88123421 * t - 0.0015786 * t**2 + t**3 / 538841 - t**4 / 65194000
    d = 297.8501921 + 445267.1114034 * t - 0.0018819 * t**2 + t**3 / 545868 - t**4 / 113065000
    m = 357.5291092 + 35999.0502909 * t - 0.0001536 * t**2 + t**3 / 24490000
    mp = 134.9633964 + 477198.8675055 * t + 0.0087414 * t**2 + t**3 / 69699 - t**4 / 14712000
    f = 93.2720950 + 483202.0175233 * t - 0.0036539 * t**2 - t**3 / 3526000 + t**4 / 863310000
    e = 1 - 0.002516 * t - 0.0000074 * t * t                         # eccentricity factor

    # longitude (sin) + distance (cos) share table 47.A; latitude (sin) is 47.B. Terms
    # carrying the Sun's anomaly M are scaled by E (or E² for 2M) — Meeus p. 338.
    sum_l = sum_r = 0.0
    for dd, mm, mmp, ff, cl, cr in _MOON_LR:
        arg = (dd * d + mm * m + mmp * mp + ff * f) * D2R
        factor = e ** abs(mm)
        sum_l += cl * factor * math.sin(arg)
        sum_r += cr * factor * math.cos(arg)
    sum_b = 0.0
    for dd, mm, mmp, ff, cb in _MOON_B:
        arg = (dd * d + mm * m + mmp * mp + ff * f) * D2R
        sum_b += cb * (e ** abs(mm)) * math.sin(arg)

    lam = (lp + sum_l / 1e6) % 360.0
    beta = sum_b / 1e6
    dist = 385000.56 + sum_r / 1000.0
    ra, dec = _ecl_to_equatorial(lam, beta, obliquity_deg(jd))
    return ra, dec, lam, beta, dist


@dataclass(frozen=True)
class MoonPhase:
    illuminated_fraction: float   # k, 0 (new) … 1 (full)
    phase_angle_deg: float        # i, Sun–Moon–Earth angle
    elongation_deg: float         # Moon − Sun ecliptic longitude, 0…360
    waxing: bool                  # True while the lit fraction grows (evening sky)
    age_days: float               # days since the last new moon (mean)
    name_de: str                  # German phase name


_PHASE_NAMES = [
    (10, "Neumond"),
    (85, "zunehmende Sichel"),
    (95, "erstes Viertel (zunehmender Halbmond)"),
    (170, "zunehmender Mond"),
    (190, "Vollmond"),
    (265, "abnehmender Mond"),
    (275, "letztes Viertel (abnehmender Halbmond)"),
    (350, "abnehmende Sichel"),
    (360, "Neumond"),
]


def _phase_name(elong_deg: float) -> str:
    for hi, name in _PHASE_NAMES:
        if elong_deg < hi:
            return name
    return "Neumond"


def moon_phase(jd: float) -> MoonPhase:
    """The Moon's phase (Meeus Ch. 48). Illuminated fraction k is exact to the day;
    waxing/waning from the Sun→Moon ecliptic elongation."""
    sra, sdec, slon, sdist = sun_position(jd)
    mra, mdec, mlon, mlat, mdist = moon_position(jd)
    sra_r, sdec_r, mra_r, mdec_r = (x * D2R for x in (sra, sdec, mra, mdec))
    cos_psi = (math.sin(sdec_r) * math.sin(mdec_r)
               + math.cos(sdec_r) * math.cos(mdec_r) * math.cos(sra_r - mra_r))
    cos_psi = max(-1.0, min(1.0, cos_psi))
    psi = math.acos(cos_psi)                                         # geocentric elongation
    i = math.atan2(sdist * math.sin(psi), mdist - sdist * math.cos(psi))  # phase angle
    k = (1 + math.cos(i)) / 2.0
    elong = (mlon - slon) % 360.0                                   # 0…360, grows while waxing
    waxing = elong < 180.0
    return MoonPhase(
        illuminated_fraction=k, phase_angle_deg=i * R2D, elongation_deg=elong,
        waxing=waxing, age_days=elong / 360.0 * SYNODIC_MONTH, name_de=_phase_name(elong),
    )


# --- date/time plumbing for the recipes -------------------------------------
_MONTHS_DE = ["", "Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli",
              "August", "September", "Oktober", "November", "Dezember"]


def _parse_date(spec) -> tuple[int, int, int]:
    d = spec.get("date")
    if isinstance(d, str):
        y, m, day = (int(x) for x in d.split("-"))
        return y, m, day
    if isinstance(d, (list, tuple)) and len(d) == 3:
        return int(d[0]), int(d[1]), int(d[2])
    if isinstance(d, dict):
        return int(d["year"]), int(d["month"]), int(d["day"])
    return 2026, 1, 15                                              # a clear winter evening default


def _parse_time(spec) -> tuple[int, int]:
    tm = spec.get("time", "21:00")
    if isinstance(tm, str):
        hh, mm = (int(x) for x in tm.split(":")[:2])
        return hh, mm
    if isinstance(tm, (list, tuple)):
        return int(tm[0]), int(tm[1])
    return 21, 0


def resolve_instant(spec: dict) -> tuple[float, datetime, float, float, float]:
    """Read a chart/phase spec → (jd, local_datetime, lst_deg, lat, lon). Local civil
    time minus `utc_offset` hours (default +1, Mitteleuropäische Zeit) gives UT. A
    direct `jd` short-circuits the calendar path (used by tests)."""
    lat = float(spec.get("lat", cat.WIEN_LAT))
    lon = float(spec.get("lon", cat.WIEN_LON))
    if spec.get("jd") is not None:
        jd = float(spec["jd"])
        return jd, datetime(2000, 1, 1), lst_deg(jd, lon), lat, lon
    y, mo, da = _parse_date(spec)
    hh, mm = _parse_time(spec)
    offset = float(spec.get("utc_offset", 1.0))                     # MEZ default
    local = datetime(y, mo, da, hh, mm)
    utc = local - timedelta(hours=offset)
    jd = julian_date(utc)
    return jd, local, lst_deg(jd, lon), lat, lon


def _german_datetime(dt: datetime) -> str:
    return f"{dt.day}. {_MONTHS_DE[dt.month]} {dt.year}, {dt.hour:02d}:{dt.minute:02d} Uhr"


def _title_when(dt: datetime) -> str:
    """A compact date/time for the chart title (Austrian month, no year — the task's
    "…, 15. Jänner, 21:00" form)."""
    return f"{dt.day}. {_MONTHS_DE[dt.month]}, {dt.hour:02d}:{dt.minute:02d}"


def _name_from_fraction(k: float, waxing: bool) -> str:
    """German phase name from an illuminated fraction + waxing flag (for the direct-
    fraction path, where there is no date to compute the elongation from). k relates to
    the Sun–Moon elongation by k = (1 − cos e)/2, so e = arccos(1 − 2k)."""
    e = math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * k))))
    return _phase_name(e if waxing else (360.0 - e))


# --- projection -------------------------------------------------------------
def _project(alt_deg: float, az_deg: float) -> tuple[float, float]:
    """Azimuthal-equidistant sky projection: zenith at the centre, horizon at radius 1
    (r = (90−alt)/90). Oriented for a chart held OVERHEAD, facing the map: North up,
    East to the LEFT, South down, West to the right — the standard all-sky planisphere."""
    r = (90.0 - alt_deg) / 90.0
    a = az_deg * D2R
    return -r * math.sin(a), r * math.cos(a)


def _mag_size(mag: float, mag_limit: float) -> float:
    """Marker size (matplotlib points) from apparent magnitude — brighter = bigger."""
    return max(2.0, min(12.0, 3.0 + 2.1 * (mag_limit - mag)))


# --- the star-chart recipe (a COMPUTED scene) -------------------------------
def star_chart_scene(spec: dict) -> Scene:
    """Compute the visible sky as a `scene.Scene`. spec (all optional):
      date "YYYY-MM-DD" · time "HH:MM" · utc_offset (h, default +1) · lat/lon (default Wien) ·
      mag_limit (default 4.5) · title ·
      show_star_labels (bool) · show_constellation_labels (bool) — both MASKED off by default,
      so a "Welches Sternbild ist das?" task never prints the answer ·
      highlight (constellation abbr to draw in focus) · show_moon (default True).
    Stars below the horizon are dropped; an asterism segment is drawn only when BOTH of
    its stars are up. Marker size ← magnitude; asterism lines carry the figstyle
    family (hue+dash) so the chart survives a B/W photocopy."""
    jd, local, lst, lat, lon = resolve_instant(spec)
    mag_limit = float(spec.get("mag_limit", 4.5))
    show_star_labels = bool(spec.get("show_star_labels", False))
    show_const_labels = bool(spec.get("show_constellation_labels", False))
    highlight = spec.get("highlight")
    show_moon = bool(spec.get("show_moon", True))

    sc = Scene(canvas=Canvas(figsize=(6.6, 7.0), aspect="equal", frame="off",
                             xlim=(-1.32, 1.32), ylim=(-1.42, 1.44)))

    # the horizon ring + a faint sky disk (kept very light so it photocopies clean)
    sc.add(CircleShape((0.0, 0.0), 1.0, role="ink", width=1.6, z=2))
    # cardinal directions just outside the ring (the compass the azimuth ring encodes)
    for label, az in (("N", 0.0), ("O", 90.0), ("S", 180.0), ("W", 270.0)):
        a = az * D2R
        sc.add(Label((-1.16 * math.sin(a), 1.16 * math.cos(a)), label, role="ink",
                     size=13.0, bold=True, halo=False))

    # project every catalogued star that is above the horizon
    up: dict[str, tuple[float, float]] = {}
    for sid, star in cat.bright_stars(mag_limit).items():
        alt, az = equatorial_to_horizontal(star.ra_deg, star.dec_deg, lst, lat)
        if alt < 0:
            continue
        x, y = _project(alt, az)
        up[sid] = (x, y)

    # asterism lines (only where both endpoints are up); one figstyle family per
    # constellation → a paired hue+dash, redundant so it reads in B/W too.
    for ci, (abbr, edges) in enumerate(sorted(cat.ASTERISMS.items())):
        is_hl = (abbr == highlight)
        for a, b in edges:
            if a in up and b in up:
                if is_hl:
                    sc.add(Line(up[a], up[b], role="focus", width=2.4, alpha=0.95, z=4))
                else:
                    sc.add(Line(up[a], up[b], family=ci, width=1.0, alpha=0.75, z=3))

    # the stars themselves (dark dots on white — print-first); size ← brightness
    for sid, (x, y) in up.items():
        star = cat.STARS[sid]
        role = "focus" if (highlight and star.const == highlight) else "ink"
        lab = star.name if (show_star_labels and star.mag <= min(mag_limit, 1.6)) else None
        sc.add(PointMark((x, y), label=lab, role=role, size=_mag_size(star.mag, mag_limit),
                         label_offset=(0.05, 0.045), bold=False, leader=False, z=6))

    # constellation names at the mean of their up-stars (maskable — off by default)
    if show_const_labels:
        for abbr in cat.ASTERISMS:
            pts = [up[s] for s in {v for e in cat.ASTERISMS[abbr] for v in e} if s in up]
            if len(pts) >= 2:
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                role = "focus" if abbr == highlight else "muted"
                sc.add(Label((cx, cy - 0.055), cat.constellation_name(abbr), role=role,
                             size=8.0, bold=(abbr == highlight), halo=True, z=7))

    # the Moon, if it is up (a computed extra — a nice "where is it tonight")
    if show_moon and spec.get("jd") is None:
        mra, mdec, *_ = moon_position(jd)
        malt, maz = equatorial_to_horizontal(mra, mdec, lst, lat)
        if malt >= 0:
            mx, my = _project(malt, maz)
            sc.add(CircleShape((mx, my), 0.035, role="focus", width=1.4, fill=True,
                               alpha=0.85, z=6))
            sc.add(Label((mx, my + 0.075), "Mond", role="focus", size=7.5, halo=True, z=7))

    # title + honest source line (the catalogue provenance rides on the figure)
    ort = "Wien" if (abs(lat - cat.WIEN_LAT) < 0.5 and abs(lon - cat.WIEN_LON) < 0.5) else \
        f"{abs(lat):.1f}° {'N' if lat >= 0 else 'S'}, {abs(lon):.1f}° {'O' if lon >= 0 else 'W'}"
    default_title = f"Sternenhimmel über {ort}"
    if spec.get("jd") is None:
        default_title += f", {_title_when(local)}"
    sc.canvas.title = str(spec.get("title", default_title))
    sc.add(Label((0.0, -1.36), cat.CATALOG_SOURCE.attribution, role="muted",
                 size=6.0, halo=False, z=5))
    return sc


# --- the moon-phase recipe (a COMPUTED scene) -------------------------------
_MOON_DARK = "#39434d"    # the night side (dark slate)
_MOON_LIT = "#f3d774"     # the sunlit side (warm cream-gold)


def moon_phase_scene(spec: dict) -> Scene:
    """A correctly-shaped Moon disk. spec (all optional):
      date "YYYY-MM-DD" (+utc_offset) → phase COMPUTED; OR illuminated_fraction (0..1) +
      waxing (bool) given directly. title · show_label (bool; False → "?" so a
      "Welche Mondphase?" task doesn't leak) · phase_name (override the label).
    Northern-hemisphere orientation: a WAXING moon is lit on the RIGHT, a WANING moon on
    the left. The terminator is the exact projected half-ellipse for the illuminated
    fraction (k=½ → straight, k→0 → thin right/left crescent, k→1 → full)."""
    if spec.get("illuminated_fraction") is not None:
        k = float(spec["illuminated_fraction"])
        waxing = bool(spec.get("waxing", True))
        name = spec.get("phase_name") or _name_from_fraction(k, waxing)
    else:
        jd, local, *_ = resolve_instant(spec)
        ph = moon_phase(jd)
        k, waxing, name = ph.illuminated_fraction, ph.waxing, spec.get("phase_name") or ph.name_de
    k = max(0.0, min(1.0, k))

    sc = Scene(canvas=Canvas(figsize=(3.7, 3.9), aspect="equal", frame="off",
                             xlim=(-1.4, 1.4), ylim=(-1.66, 1.5)))
    # the Moon body (the NIGHT side, dark) with the sunlit part in warm cream. Literal
    # hues (not the semantic ramp): a moon is neither "data" nor "structure" — the two
    # colours ARE the fact being taught (Sonnenlicht vs. Schatten). Cf. constructions._RECEDED.
    sc.add(CircleShape((0.0, 0.0), 1.0, role=_MOON_DARK, width=0.0, fill=True, alpha=1.0, z=1))

    # the illuminated region: up the terminator x=(1-2k)·w(y), down the lit limb x=±w(y)
    n = 90
    ys = [-1.0 + 2.0 * i / n for i in range(n + 1)]
    sign = 1.0 if waxing else -1.0                                  # +1 lit-right, -1 lit-left
    if 0.004 < k < 0.996:
        term = [(sign * (1 - 2 * k) * math.sqrt(max(0.0, 1 - y * y)), y) for y in ys]
        limb = [(sign * math.sqrt(max(0.0, 1 - y * y)), y) for y in reversed(ys)]
        sc.add(Region(term + limb, role=_MOON_LIT, alpha=1.0, z=2))
    elif k >= 0.996:                                                # full moon — whole disk lit
        sc.add(CircleShape((0.0, 0.0), 1.0, role=_MOON_LIT, width=0.0, fill=True, z=2))
    # a crisp limb outline on top, so the disk edge always reads (even at new moon)
    sc.add(CircleShape((0.0, 0.0), 1.0, role="ink", width=1.4,
                       dash=(0, (2, 2)) if k <= 0.004 else "solid", z=3))

    sc.canvas.title = str(spec.get("title", "Mondphase"))
    if bool(spec.get("show_label", True)):
        sc.add(Label((0.0, -1.30), name, role="ink", size=8.5, bold=True, halo=False, z=4))
        sc.add(Label((0.0, -1.52), f"{round(k * 100)} % beleuchtet", role="muted",
                     size=7.5, halo=False, z=4))
    else:
        sc.add(Label((0.0, -1.34), "?", role="ink", size=15.0, bold=True, halo=False, z=4))
    return sc


def scene_png(scene: Scene, path: Path, *, dpi: int = 165) -> Path:
    """Convenience wrapper (the recipes in `assets.py` call `scene_to_png` directly)."""
    from .scene import scene_to_png
    return scene_to_png(scene, path, dpi=dpi)
