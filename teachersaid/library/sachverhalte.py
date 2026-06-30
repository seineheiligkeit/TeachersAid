"""The curated Sachverhalt registry — the content-layer flagships staged for review.

Mirrors `library/texts.py::ANNOTATED_TEXTS`: a flat list the seed path
(`orchestrator.seed_sachverhalte`) ingests through the facts/entity-lint gate. Add a
Sachverhalt = add its module + one line here.
"""

from __future__ import annotations

from . import sachverhalt_blutkreislauf as _blutkreislauf
from . import sachverhalt_wiener_kongress as _wiener_kongress

SACHVERHALTE = [
    _wiener_kongress.build_sachverhalt(),   # GPB (History) — the dated-timeline flagship
    _blutkreislauf.build_sachverhalt(),     # Biologie — the process/cycle flagship (Phase 2)
]
