"""Physics grounding — the curated physical constants the parametric engine computes from.

The physics analogue of `grounding/chemistry.py` (IUPAC atomic weights) and `data_store`
(datasets): the **facts** here are physical constants and school-typical material
densities. Discipline is identical — *select, never author*: every number carries a cited
`SourceRef`, the engine *reads* it, the LLM never invents a constant. A computed velocity,
Ersatzwiderstand, torque or energy is then **correct by construction** — and, because the
recipes compute with `sympy.physics.units`, **dimensionally verified** (a unit-category
error is structurally impossible, see `pipeline/physics.py::_assert_dimension`).

Two curated tables:
  * physical constants (`STANDARD_GRAVITY` — exact by definition) with their source;
  * `MATERIAL_DENSITIES` — school-typical densities (Wasser, Eisen, …) in kg/m³, each a
    cited value. `density_material_for` reverse-looks-up the nearest curated material for
    a computed density (the "Um welchen Stoff könnte es sich handeln?" task).
"""

from __future__ import annotations

from ..schema.datasets import SourceRef

# --- provenance --------------------------------------------------------------
# Standard gravity is a DEFINED value (CGPM 1901 / ISO 80000-3), not a measurement —
# exact, so no uncertainty. We *select* it; we never author a value.
GRAVITY_SOURCE = SourceRef(
    publisher="BIPM / CGPM",
    title="Standard acceleration of gravity gₙ (defined value, 3rd CGPM 1901; ISO 80000-3)",
    url="https://www.bipm.org/en/committees/cg/cgpm/3-1901",
    licence="public (defined constant)",
    redistributable=True,
    attribution="Normfallbeschleunigung gₙ = 9,80665 m/s² (CGPM 1901, definiert)",
    stand="1901",
)

# School-typical mass densities at ~20 °C / 1 atm, rounded to the precision a worksheet
# uses. These are standard reference values (a physics Tabellenbuch / CRC Handbook); the
# SourceRef records provenance so the values are cited, never asserted. Air is the odd one
# out (gas, strongly T/p-dependent) — the value is the dry-air standard-condition figure.
DENSITY_SOURCE = SourceRef(
    publisher="CRC Press",
    title="CRC Handbook of Chemistry and Physics — physical properties (densities of "
          "solids, liquids and gases), school-rounded",
    url="https://hbcp.chemnetbase.com/",
    licence="reference value (schulüblich gerundet)",
    redistributable=True,
    attribution="Dichtewerte: Tabellenwerte nach CRC Handbook of Chemistry and Physics "
                "(schulüblich gerundet, ~20 °C)",
    stand="2020",
)

# --- physical constants ------------------------------------------------------
# Standard gravity in m/s² — the value the energy/lever recipes carry (E_pot = m·g·h,
# Gewichtskraft F = m·g). Exact by definition.
STANDARD_GRAVITY: float = 9.80665


# --- material densities (curated truth — select, never author) ---------------
# German name → density in kg/m³. School-typical values (~20 °C). Chosen to be
# well-separated so the reverse lookup ("welcher Stoff?") is unambiguous at school
# precision. Kork/Fichtenholz/Eis/Aluminium float-or-sink favourites; the metals span the
# range up to Blei.
MATERIAL_DENSITIES: dict[str, float] = {
    "Kork": 240.0,          # ~0,24 g/cm³ — schwimmt
    "Fichtenholz": 470.0,   # ~0,47 g/cm³ — schwimmt (lufttrocken)
    "Eis": 917.0,           # ~0,92 g/cm³ — schwimmt knapp auf Wasser
    "Wasser": 1000.0,       # die Referenz: 1 g/cm³ = 1000 kg/m³ (bei 4 °C exakt)
    "Aluminium": 2700.0,    # 2,7 g/cm³
    "Eisen": 7870.0,        # 7,87 g/cm³
    "Kupfer": 8960.0,       # 8,96 g/cm³
    "Blei": 11340.0,        # 11,34 g/cm³
}

# Air separately — a gas, orders of magnitude lighter and strongly condition-dependent, so
# it does not belong in the solid/liquid reverse-lookup pool (it would swamp the tolerance
# band). Kept as a cited fact for a "Luft ist auch ein Stoff mit Dichte" context.
AIR_DENSITY: float = 1.293   # kg/m³, trockene Luft bei 0 °C, 1013 hPa (Normbedingungen)

# The unambiguous reverse-lookup pool (solids + liquids). Air excluded (see above).
_LOOKUP_MATERIALS: dict[str, float] = dict(MATERIAL_DENSITIES)


def density_material_for(rho: float, *, rel_tol: float = 0.03) -> str | None:
    """The curated material whose density matches `rho` (kg/m³) within `rel_tol`, or None.

    Used by the "Um welchen Stoff könnte es sich handeln?" variant: the recipe computes a
    density from a drawn (mass, volume) pair built FROM a curated material, so a match is
    guaranteed for those draws; the tolerance keeps the answer robust to school rounding.
    Correct by curation — the answer IS the curated material, never invented."""
    best: tuple[float, str] | None = None
    for name, d in _LOOKUP_MATERIALS.items():
        rel = abs(d - rho) / d
        if rel <= rel_tol and (best is None or rel < best[0]):
            best = (rel, name)
    return best[1] if best else None
