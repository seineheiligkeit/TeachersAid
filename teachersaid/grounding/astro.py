"""Astronomy grounding — the curated bright-star catalog + constellation asterisms.

The astronomy analogue of `grounding/chemistry.py` (IUPAC atomic weights) and
`grounding/data` (cited datasets). The **facts** here are bright-star positions,
magnitudes and proper names; discipline is identical — *select, never author*: a
star's ``(RA, Dec, magnitude)`` is an astronomical FACT (a measurement, not
copyrightable expression — `invariants.md` §3/§6: *facts are free; copyright
protects expression, not facts*), curated in-repo and READ by `pipeline/astro.py`.
The chart is then correct **by construction** — every star position is computed
from this catalog by plain spherical astronomy, nothing is hand-placed.

Licence gate (researched honestly, recorded verbatim in `CATALOG_SOURCE.note`):

  * The **HYG database** (astronexus) is distributed under **CC BY-SA 4.0**. The
    ShareAlike clause would encumber every worksheet that embeds it → **REFUSED**
    (the same verdict the project reached for the GFN footprint dataset). We do not
    use HYG.
  * Star positions, magnitudes and traditional proper names are **astronomical
    facts**, not copyrightable expression (the celestial twin of "a date"). This
    table curates ~90 of the brightest stars from the public **Yale Bright Star
    Catalogue** (Hoffleit & Warren 1991, *BSC5*), distributed by CDS/Strasbourg as
    VizieR catalogue **V/50**; the numeric values are typed in-repo like the IUPAC
    masses in `chemistry.py`. No licence is *asserted over the facts*; the
    reference compilation is cited so every value is independently verifiable.
    Positions are J2000.0 (the ~0.3° of precession to 2026 is far below a naked-eye
    finder chart's needs and is documented in `pipeline/astro.py`).
  * The constellation **lines** (asterisms) are a curated **cultural** layer — the
    classic connect-the-dots figures (the Großer Wagen, Orion's belt-and-body, the
    Sommerdreieck …). They are *curated judgment*, SME-gated (`ASTERISM_SOURCE`),
    not lifted from any one copyrighted figure set.

Deliberately rejected seam — **ISS / satellite passes.** A live overhead pass needs
current TLE orbital elements (updated every few days) fetched from the network; that
is not offline-stable and not a durable corpus fact, so it is left out **by
decision**, not oversight. (See `pipeline/astro.py` for the same note beside the
ephemeris code.)
"""
from __future__ import annotations

from dataclasses import dataclass

from ..schema.datasets import SourceRef

# --- provenance -------------------------------------------------------------
CATALOG_SOURCE = SourceRef(
    publisher="Yale University Observatory / CDS Strasbourg",
    title="Yale Bright Star Catalogue, 5th Revised Ed. (Hoffleit & Warren 1991), "
          "VizieR catalogue V/50",
    url="https://cdsarc.cds.unistra.fr/viz-bin/cat/V/50",
    licence=None,   # the individual star FACTS are not copyrightable; no licence asserted
    redistributable=True,   # facts (positions/magnitudes) are free to state; not a licensed dataset
    attribution="Sternörter (J2000.0) und scheinbare Helligkeiten nach dem "
                "Yale Bright Star Catalogue (Hoffleit & Warren 1991)",
    stand="J2000.0",
)

ASTERISM_SOURCE = SourceRef(
    publisher="TeachersAid (kuratierte Fachjudgment-Ebene)",
    title="Klassische Sternbildlinien (Asterismen) — kuratiert",
    licence="curated judgment, SME-gated",
    redistributable=True,
    attribution="Sternbildlinien: klassische Asterismen, kuratiert (SME-geprüft)",
)


# --- the star record --------------------------------------------------------
@dataclass(frozen=True)
class Star:
    """One catalogued bright star. `ra_h` is right ascension in decimal HOURS,
    `dec_deg` declination in decimal DEGREES (both J2000.0); `mag` is the apparent
    visual magnitude (smaller = brighter). `bayer` is the Bayer/Flamsteed
    designation, `const` the 3-letter IAU constellation abbreviation."""
    name: str
    bayer: str
    const: str
    ra_h: float
    dec_deg: float
    mag: float

    @property
    def ra_deg(self) -> float:
        return self.ra_h * 15.0


def _s(name, bayer, const, ra_h, dec_deg, mag) -> tuple[str, Star]:
    slug = (name or bayer).lower().replace(" ", "_").replace("'", "")
    return slug, Star(name, bayer, const, ra_h, dec_deg, mag)


# The catalog, grouped by constellation for review. RA in decimal hours, Dec in
# decimal degrees, J2000.0; magnitudes are apparent V. Curated from BSC5 (see
# CATALOG_SOURCE). Extend by adding one cited row — exactly the chemistry pattern.
_ROWS: list[tuple[str, Star]] = [
    # Ursa Major — der Große Wagen (the seven Wagen stars)
    _s("Dubhe", "α UMa", "UMa", 11.0622, 61.751, 1.79),
    _s("Merak", "β UMa", "UMa", 11.0307, 56.383, 2.37),
    _s("Phecda", "γ UMa", "UMa", 11.8972, 53.695, 2.44),
    _s("Megrez", "δ UMa", "UMa", 12.2571, 57.033, 3.31),
    _s("Alioth", "ε UMa", "UMa", 12.9004, 55.960, 1.77),
    _s("Mizar", "ζ UMa", "UMa", 13.3987, 54.925, 2.23),
    _s("Alkaid", "η UMa", "UMa", 13.7923, 49.313, 1.86),
    # Ursa Minor — der Kleine Wagen
    _s("Polaris", "α UMi", "UMi", 2.5303, 89.264, 1.98),
    _s("Kochab", "β UMi", "UMi", 14.8451, 74.156, 2.08),
    _s("Pherkad", "γ UMi", "UMi", 15.3453, 71.834, 3.00),
    # Cassiopeia — das Himmels-W
    _s("Caph", "β Cas", "Cas", 0.1528, 59.150, 2.28),
    _s("Schedar", "α Cas", "Cas", 0.6751, 56.537, 2.24),
    _s("Cih", "γ Cas", "Cas", 0.9451, 60.717, 2.47),
    _s("Ruchbah", "δ Cas", "Cas", 1.4303, 60.235, 2.68),
    _s("Segin", "ε Cas", "Cas", 1.9067, 63.670, 3.35),
    # Orion
    _s("Betelgeuse", "α Ori", "Ori", 5.9195, 7.407, 0.45),
    _s("Rigel", "β Ori", "Ori", 5.2423, -8.202, 0.13),
    _s("Bellatrix", "γ Ori", "Ori", 5.4188, 6.350, 1.64),
    _s("Mintaka", "δ Ori", "Ori", 5.5334, -0.299, 2.23),
    _s("Alnilam", "ε Ori", "Ori", 5.6036, -1.202, 1.69),
    _s("Alnitak", "ζ Ori", "Ori", 5.6793, -1.943, 1.74),
    _s("Saiph", "κ Ori", "Ori", 5.7959, -9.670, 2.07),
    # Canis Major — der Große Hund
    _s("Sirius", "α CMa", "CMa", 6.7525, -16.716, -1.46),
    _s("Mirzam", "β CMa", "CMa", 6.3783, -17.956, 1.98),
    _s("Wezen", "δ CMa", "CMa", 7.1399, -26.393, 1.83),
    _s("Adhara", "ε CMa", "CMa", 6.9770, -28.972, 1.50),
    _s("Aludra", "η CMa", "CMa", 7.4016, -29.303, 2.45),
    # Canis Minor
    _s("Procyon", "α CMi", "CMi", 7.6550, 5.225, 0.34),
    _s("Gomeisa", "β CMi", "CMi", 7.4527, 8.289, 2.89),
    # Gemini — die Zwillinge
    _s("Castor", "α Gem", "Gem", 7.5767, 31.888, 1.58),
    _s("Pollux", "β Gem", "Gem", 7.7553, 28.026, 1.14),
    _s("Alhena", "γ Gem", "Gem", 6.6285, 16.399, 1.93),
    _s("Wasat", "δ Gem", "Gem", 7.3351, 21.982, 3.53),
    _s("Mebsuta", "ε Gem", "Gem", 6.7322, 25.131, 2.98),
    _s("Tejat", "μ Gem", "Gem", 6.3826, 22.514, 2.87),
    # Taurus — der Stier
    _s("Aldebaran", "α Tau", "Tau", 4.5987, 16.509, 0.85),
    _s("Elnath", "β Tau", "Tau", 5.4382, 28.607, 1.65),
    _s("Alcyone", "η Tau", "Tau", 3.7914, 24.105, 2.87),   # die Plejaden
    _s("Hyadum", "γ Tau", "Tau", 4.3298, 15.628, 3.65),
    _s("Ain", "ε Tau", "Tau", 4.4776, 19.180, 3.53),
    # Auriga — der Fuhrmann
    _s("Capella", "α Aur", "Aur", 5.2782, 45.998, 0.08),
    _s("Menkalinan", "β Aur", "Aur", 5.9921, 44.947, 1.90),
    _s("Mahasim", "θ Aur", "Aur", 5.9953, 37.213, 2.62),
    _s("Hassaleh", "ι Aur", "Aur", 4.9497, 33.166, 2.69),
    # Leo — der Löwe
    _s("Regulus", "α Leo", "Leo", 10.1395, 11.967, 1.35),
    _s("Denebola", "β Leo", "Leo", 11.8177, 14.572, 2.11),
    _s("Algieba", "γ Leo", "Leo", 10.3329, 19.842, 2.28),
    _s("Zosma", "δ Leo", "Leo", 11.2351, 20.524, 2.56),
    _s("Chertan", "θ Leo", "Leo", 11.2373, 15.430, 3.34),
    _s("Adhafera", "ζ Leo", "Leo", 10.2781, 23.417, 3.44),
    _s("Rasalas", "μ Leo", "Leo", 9.8797, 26.007, 3.88),
    _s("Algenubi", "ε Leo", "Leo", 9.7644, 23.774, 2.98),
    # Bootes — der Bärenhüter
    _s("Arcturus", "α Boo", "Boo", 14.2610, 19.182, -0.05),
    _s("Izar", "ε Boo", "Boo", 14.7498, 27.074, 2.35),
    _s("Muphrid", "η Boo", "Boo", 13.9114, 18.398, 2.68),
    _s("Seginus", "γ Boo", "Boo", 14.5346, 38.308, 3.03),
    _s("Nekkar", "β Boo", "Boo", 15.0319, 40.390, 3.49),
    _s("Rho Boo", "ρ Boo", "Boo", 14.5301, 30.371, 3.58),
    # Corona Borealis — die Nördliche Krone
    _s("Alphecca", "α CrB", "CrB", 15.5781, 26.715, 2.22),
    _s("Nusakan", "β CrB", "CrB", 15.4638, 29.106, 3.66),
    # Cygnus — der Schwan (das Kreuz des Nordens)
    _s("Deneb", "α Cyg", "Cyg", 20.6905, 45.280, 1.25),
    _s("Sadr", "γ Cyg", "Cyg", 20.3705, 40.257, 2.23),
    _s("Gienah", "ε Cyg", "Cyg", 20.7704, 33.970, 2.48),
    _s("Fawaris", "δ Cyg", "Cyg", 19.7496, 45.131, 2.87),
    _s("Albireo", "β Cyg", "Cyg", 19.5121, 27.960, 3.08),
    # Lyra — die Leier
    _s("Vega", "α Lyr", "Lyr", 18.6156, 38.784, 0.03),
    _s("Sheliak", "β Lyr", "Lyr", 18.8347, 33.363, 3.52),
    _s("Sulafat", "γ Lyr", "Lyr", 18.9824, 32.690, 3.24),
    # Aquila — der Adler
    _s("Altair", "α Aql", "Aql", 19.8464, 8.868, 0.77),
    _s("Tarazed", "γ Aql", "Aql", 19.7710, 10.613, 2.72),
    _s("Alshain", "β Aql", "Aql", 19.9219, 6.407, 3.71),
    # Andromeda + Pegasus (das Herbst-Viereck / Great Square)
    _s("Alpheratz", "α And", "And", 0.1398, 29.090, 2.06),
    _s("Mirach", "β And", "And", 1.1622, 35.621, 2.06),
    _s("Almach", "γ And", "And", 2.0650, 42.330, 2.10),
    _s("Markab", "α Peg", "Peg", 23.0793, 15.205, 2.49),
    _s("Scheat", "β Peg", "Peg", 23.0629, 28.083, 2.42),
    _s("Algenib", "γ Peg", "Peg", 0.2206, 15.184, 2.83),
    _s("Enif", "ε Peg", "Peg", 21.7364, 9.875, 2.39),
    # Perseus
    _s("Mirfak", "α Per", "Per", 3.4054, 49.861, 1.79),
    _s("Algol", "β Per", "Per", 3.1361, 40.956, 2.12),
    _s("Gorgonea", "γ Per", "Per", 3.0799, 53.506, 2.93),
    _s("Menkib", "ζ Per", "Per", 3.9021, 31.884, 2.85),
    # Triangulum + Aries — Dreieck und Widder
    _s("Mothallah", "α Tri", "Tri", 1.8846, 29.579, 3.42),
    _s("Beta Tri", "β Tri", "Tri", 2.1595, 34.987, 3.00),
    _s("Hamal", "α Ari", "Ari", 2.1195, 23.463, 2.00),
    _s("Sheratan", "β Ari", "Ari", 1.9106, 20.808, 2.64),
    # Cetus — der Walfisch
    _s("Menkar", "α Cet", "Cet", 3.0380, 4.090, 2.53),
    _s("Diphda", "β Cet", "Cet", 0.7265, -17.987, 2.04),
    # Virgo + Corvus
    _s("Spica", "α Vir", "Vir", 13.4199, -11.161, 1.04),
    _s("Vindemiatrix", "ε Vir", "Vir", 13.0362, 10.959, 2.83),
    _s("Porrima", "γ Vir", "Vir", 12.6943, -1.449, 2.74),
    _s("Gienah Crv", "γ Crv", "Crv", 12.2634, -17.542, 2.59),
    _s("Kraz", "β Crv", "Crv", 12.5724, -23.397, 2.65),
    _s("Algorab", "δ Crv", "Crv", 12.4977, -16.515, 2.95),
    _s("Alchiba", "ε Crv", "Crv", 12.1682, -22.620, 3.02),
    # Leo-neighbours / Hydra head anchor
    _s("Alphard", "α Hya", "Hya", 9.4597, -8.659, 1.98),
    # Scorpius — der Skorpion (nur der über Wien sichtbare Teil)
    _s("Antares", "α Sco", "Sco", 16.4901, -26.432, 1.06),
    _s("Dschubba", "δ Sco", "Sco", 16.0055, -22.622, 2.29),
    _s("Acrab", "β Sco", "Sco", 16.0906, -19.805, 2.62),
    _s("Pi Sco", "π Sco", "Sco", 15.9809, -26.114, 2.89),
    _s("Shaula", "λ Sco", "Sco", 17.5601, -37.104, 1.62),
    # Sagittarius — der Schütze (die „Teekanne")
    _s("Kaus Australis", "ε Sgr", "Sgr", 18.4029, -34.385, 1.85),
    _s("Nunki", "σ Sgr", "Sgr", 18.9211, -26.297, 2.05),
    _s("Kaus Media", "δ Sgr", "Sgr", 18.3499, -29.828, 2.70),
    _s("Kaus Borealis", "λ Sgr", "Sgr", 18.4661, -25.421, 2.81),
    _s("Ascella", "ζ Sgr", "Sgr", 19.0435, -29.880, 2.60),
    _s("Alnasl", "γ Sgr", "Sgr", 18.0966, -30.424, 2.98),
    # Ophiuchus + Hercules + Draco (Sommerhimmel-Höhe)
    _s("Rasalhague", "α Oph", "Oph", 17.5822, 12.560, 2.08),
    _s("Kornephoros", "β Her", "Her", 16.5036, 21.490, 2.77),
    _s("Zeta Her", "ζ Her", "Her", 16.6882, 31.603, 2.81),
    _s("Pi Her", "π Her", "Her", 17.2508, 36.809, 3.16),
    _s("Eta Her", "η Her", "Her", 16.7146, 38.922, 3.48),
    _s("Eltanin", "γ Dra", "Dra", 17.9434, 51.489, 2.23),
    _s("Rastaban", "β Dra", "Dra", 17.5074, 52.301, 2.79),
    _s("Altais", "δ Dra", "Dra", 19.2090, 67.662, 3.07),
    _s("Edasich", "ι Dra", "Dra", 15.4155, 58.966, 3.29),
    # Cepheus
    _s("Alderamin", "α Cep", "Cep", 21.3096, 62.585, 2.45),
    _s("Alfirk", "β Cep", "Cep", 21.4776, 70.561, 3.23),
    _s("Errai", "γ Cep", "Cep", 23.6558, 77.632, 3.21),
    # Piscis Austrinus
    _s("Fomalhaut", "α PsA", "PsA", 22.9608, -29.622, 1.16),
]

STARS: dict[str, Star] = dict(_ROWS)


# --- constellation names (German) -------------------------------------------
CONSTELLATIONS: dict[str, str] = {
    "UMa": "Großer Wagen",
    "UMi": "Kleiner Wagen",
    "Cas": "Kassiopeia",
    "Ori": "Orion",
    "CMa": "Großer Hund",
    "CMi": "Kleiner Hund",
    "Gem": "Zwillinge",
    "Tau": "Stier",
    "Aur": "Fuhrmann",
    "Leo": "Löwe",
    "Boo": "Bärenhüter",
    "CrB": "Nördliche Krone",
    "Cyg": "Schwan",
    "Lyr": "Leier",
    "Aql": "Adler",
    "And": "Andromeda",
    "Peg": "Pegasus",
    "Per": "Perseus",
    "Tri": "Dreieck",
    "Ari": "Widder",
    "Cet": "Walfisch",
    "Vir": "Jungfrau",
    "Crv": "Rabe",
    "Hya": "Wasserschlange",
    "Sco": "Skorpion",
    "Sgr": "Schütze",
    "Oph": "Schlangenträger",
    "Her": "Herkules",
    "Dra": "Drache",
    "Cep": "Kepheus",
    "PsA": "Südlicher Fisch",
}


# --- asterisms (the curated cultural line layer) ----------------------------
# Each entry: constellation abbr -> list of (star_id, star_id) segments. Every id
# MUST resolve in STARS (locked by tests/test_astro.py::test_catalog_integrity).
ASTERISMS: dict[str, list[tuple[str, str]]] = {
    # der Große Wagen: der Kasten + die Deichsel
    "UMa": [("dubhe", "merak"), ("merak", "phecda"), ("phecda", "megrez"),
            ("megrez", "dubhe"), ("megrez", "alioth"), ("alioth", "mizar"),
            ("mizar", "alkaid")],
    # der Kleine Wagen: Polaris an der Deichselspitze bis zum Kasten
    "UMi": [("polaris", "kochab"), ("kochab", "pherkad")],
    # Kassiopeia: das W  ε–δ–γ–α–β
    "Cas": [("segin", "ruchbah"), ("ruchbah", "cih"), ("cih", "schedar"),
            ("schedar", "caph")],
    # Orion: Schultern, Gürtel, Beine
    "Ori": [("betelgeuse", "bellatrix"), ("bellatrix", "mintaka"),
            ("mintaka", "alnilam"), ("alnilam", "alnitak"),
            ("alnitak", "betelgeuse"), ("mintaka", "rigel"),
            ("alnitak", "saiph"), ("rigel", "saiph")],
    # der Große Hund
    "CMa": [("mirzam", "sirius"), ("sirius", "wezen"), ("wezen", "adhara"),
            ("adhara", "aludra"), ("aludra", "wezen")],
    # die Zwillinge: zwei Strichmännchen (Castor- und Pollux-Reihe)
    "Gem": [("castor", "pollux"), ("castor", "mebsuta"), ("mebsuta", "tejat"),
            ("pollux", "wasat"), ("wasat", "alhena")],
    # der Stier: das V des Kopfes + die Hörner
    "Tau": [("aldebaran", "ain"), ("aldebaran", "hyadum"), ("ain", "elnath")],
    # der Fuhrmann: das Fünfeck (schließt über Elnath des Stiers)
    "Aur": [("capella", "menkalinan"), ("menkalinan", "mahasim"),
            ("mahasim", "elnath"), ("elnath", "hassaleh"), ("hassaleh", "capella")],
    # der Löwe: die Sichel + das Hinterteil-Dreieck
    "Leo": [("regulus", "algieba"), ("algieba", "adhafera"),
            ("adhafera", "rasalas"), ("rasalas", "algenubi"),
            ("regulus", "chertan"), ("chertan", "zosma"),
            ("zosma", "denebola"), ("denebola", "chertan"),
            ("zosma", "algieba")],
    # der Bärenhüter: der Drachen
    "Boo": [("arcturus", "muphrid"), ("arcturus", "izar"), ("izar", "seginus"),
            ("seginus", "rho_boo"), ("rho_boo", "arcturus"), ("izar", "nekkar")],
    # die Nördliche Krone
    "CrB": [("alphecca", "nusakan")],
    # der Schwan: das Kreuz des Nordens
    "Cyg": [("deneb", "sadr"), ("sadr", "albireo"), ("fawaris", "sadr"),
            ("sadr", "gienah")],
    # die Leier
    "Lyr": [("vega", "sheliak"), ("sheliak", "sulafat"), ("sulafat", "vega")],
    # der Adler
    "Aql": [("tarazed", "altair"), ("altair", "alshain")],
    # Andromeda-Kette (ans Herbstviereck angehängt)
    "And": [("alpheratz", "mirach"), ("mirach", "almach")],
    # das Herbst-Viereck (Pegasus + Alpheratz)
    "Peg": [("markab", "scheat"), ("scheat", "alpheratz"),
            ("alpheratz", "algenib"), ("algenib", "markab"),
            ("markab", "enif")],
    # Perseus
    "Per": [("mirfak", "algol"), ("mirfak", "gorgonea"), ("mirfak", "menkib")],
    # der Widder
    "Ari": [("hamal", "sheratan")],
    # das Dreieck
    "Tri": [("mothallah", "beta_tri")],
    # der Rabe (das kleine Viereck)
    "Crv": [("alchiba", "gienah_crv"), ("gienah_crv", "algorab"),
            ("algorab", "kraz"), ("kraz", "alchiba")],
    # der Skorpion (Kopf-Reihe + Herz Antares Richtung Stachel)
    "Sco": [("acrab", "dschubba"), ("dschubba", "pi_sco"), ("pi_sco", "antares"),
            ("antares", "shaula")],
    # der Schütze — die Teekanne
    "Sgr": [("kaus_australis", "kaus_media"), ("kaus_media", "kaus_borealis"),
            ("kaus_borealis", "nunki"), ("nunki", "ascella"),
            ("ascella", "kaus_australis"), ("kaus_media", "alnasl"),
            ("kaus_borealis", "nunki")],
    # der Drache (das Kopf-Viereck Richtung Deichsel)
    "Dra": [("eltanin", "rastaban"), ("rastaban", "altais"), ("altais", "edasich")],
    # der Herkules — der „Keystone"
    "Her": [("zeta_her", "kornephoros"), ("zeta_her", "eta_her"),
            ("eta_her", "pi_her"), ("pi_her", "zeta_her")],
    # Kepheus (das „Haus")
    "Cep": [("alderamin", "alfirk"), ("alfirk", "errai"), ("errai", "alderamin")],
}


# --- accessors --------------------------------------------------------------
def all_stars() -> list[Star]:
    """Every catalogued star (unordered view of the catalog)."""
    return list(STARS.values())


def get_star(star_id: str) -> Star:
    """Look up a star by its catalog id (raises KeyError on an unknown id)."""
    return STARS[star_id]


def bright_stars(mag_limit: float) -> dict[str, Star]:
    """The stars at or brighter than `mag_limit` (smaller magnitude = brighter)."""
    return {sid: s for sid, s in STARS.items() if s.mag <= mag_limit}


def constellation_name(abbr: str) -> str:
    """The German constellation name for an IAU abbreviation (falls back to abbr)."""
    return CONSTELLATIONS.get(abbr, abbr)


def asterism_edges(abbr: str) -> list[tuple[Star, Star]]:
    """The (Star, Star) segments of a constellation's curated asterism."""
    return [(STARS[a], STARS[b]) for a, b in ASTERISMS.get(abbr, [])]


# Vienna — the default observing site (Stephansdom, rounded), for the chart recipe.
WIEN_LAT = 48.21
WIEN_LON = 16.37
