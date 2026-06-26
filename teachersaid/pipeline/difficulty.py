"""Difficulty as an honest, bounded estimate (Phase 3d).

Difficulty is **not measured** — we deliberately collect no student-response data, so
there is no psychometric calibration here. A task may carry an author/SME `difficulty`
(1 leicht · 2 mittel · 3 anspruchsvoll); when it doesn't, we fall back to the
**Anforderungsbereich** of its `cognitive_level` (the Lehrplan's own ladder):
Reproduktion → 1, Transfer → 2, Reflexion/Problemlösung → 3. So every task has an
*effective* difficulty, and an author/SME estimate simply overrides the default.

Used by: derive (DepthProfile.by_difficulty), verify (a flat-spectrum warning), and
compose (difficulty-calibrated selection — span the bands, don't crowd out the stretch).
"""
from __future__ import annotations

from ..schema.enums import COGNITIVE_RANK

# cognitive rank (0..5) → Anforderungsbereich difficulty band (1..3)
_RANK_TO_BAND = {0: 1, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3}
DIFFICULTY_LABEL = {1: "leicht (Reproduktion)", 2: "mittel (Transfer)",
                    3: "anspruchsvoll (Reflexion)"}


def effective_difficulty(task) -> int:
    """The task's difficulty 1–3: the explicit author/SME estimate if set, else the
    Anforderungsbereich of its cognitive_level."""
    d = getattr(task, "difficulty", None)
    if d in (1, 2, 3):
        return d
    rank = COGNITIVE_RANK.get(getattr(task, "cognitive_level", ""), 1)
    return _RANK_TO_BAND.get(rank, 2)
