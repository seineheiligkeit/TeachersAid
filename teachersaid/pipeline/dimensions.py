"""The dimensional guard — base-SI dimension reduction + the assertion.

Extracted into its own module so it is a shared primitive with no import cycle (this file
imports ONLY sympy). Two engines build on it, in opposite directions:

  * `pipeline/physics.py` uses `_assert_dimension` to PROVE a computed answer's unit right
    before formatting (a unit-category error cannot survive);
  * `pipeline/einheiten.py` INVERTS the same check — a candidate formula is a valid distractor
    exactly when `_base_dims(candidate) != _base_dims(target)`.

One source of truth for "do these two quantities carry the same physical dimension?".
`physics.py` re-exports `DimensionError`/`_assert_dimension` for callers that still reference
them as `physics.<name>`.
"""

from __future__ import annotations

from sympy.physics.units import Dimension
from sympy.physics.units.systems.si import SI

_DIMSYS = SI.get_dimension_system()


class DimensionError(AssertionError):
    """A computed quantity does not carry the expected physical dimension. Raised by
    `_assert_dimension` — a structural guarantee that a unit-category error cannot pass."""


def _base_dims(expr) -> dict:
    """Reduce a units expression to its base-SI dimension exponents (a canonical dict),
    so `R·I` and `volt` compare EQUAL despite different surface forms."""
    return _DIMSYS.get_dimensional_dependencies(Dimension(SI.get_dimensional_expr(expr)))


def _assert_dimension(qty, expected_unit) -> None:
    """Assert `qty` has the same physical dimension as `expected_unit`, else raise
    `DimensionError`. Called before formatting a computed answer (physics.py) and to prove a
    candidate formula dimensionally wrong (einheiten.py)."""
    if _base_dims(qty) != _base_dims(expected_unit):
        raise DimensionError(
            f"dimension mismatch: {SI.get_dimensional_expr(qty)} "
            f"is not {SI.get_dimensional_expr(expected_unit)}")
