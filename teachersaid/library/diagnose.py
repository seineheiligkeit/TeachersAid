"""Curated band-1 Mathematik 'Grundfertigkeiten' blocks — the diagnostic stock.

A Diagnose-Blatt (``pipeline/diagnose.py``) pulls ONE easy approved task per prerequisite
ancestor of a topic. For that to show real checks offline, the approved block library needs
band-1 tasks on the foundational Unterstufe competences. This is that seed: small, curated,
correct-by-curation checks (difficulty pinned to 1 = *leicht*), SME-gated like every block —
``seed_diagnose_blocks`` stages them (approved for the demo). They double as the prerequisite
warm-up stock for future consumers (spiral revision, warm-up injection).

These are a *seed*, not part of the default ``seed_blocks`` corpus, so they don't perturb the
coverage statistics of the main library — a caller opts in explicitly.
"""

from __future__ import annotations

from .block import LibraryBlock
from ..schema.blocks import Serves, TaskBlock
from ..schema.response import LinesResponse

_KB = {
    "ZAH": "1: Zahlen und Maße",
    "VAR": "2: Variablen und Funktionen",
    "FIG": "3: Figuren und Körper",
    "DAT": "4: Daten und Zufall",
}


def _blk(bid, comp, klasse, kb_code, kind, prompt, answer, *, level, dim, mins=3, lines=2):
    """One curated band-1 (difficulty=1) Mathematik check, as an approved-ready LibraryBlock."""
    task = TaskBlock(
        id=bid, kind=kind, prompt=prompt, response=LinesResponse(n=lines),
        cognitive_level=level, difficulty=1, dimensions=[dim],
        serves=[Serves(competence_id=comp, relation="exercises")],
        est_minutes=mins, answer_key=answer,
    )
    return LibraryBlock(
        id=f"diag-seed.{bid}", block=task, role="task", kind=kind,
        subject="Mathematik", klasse=klasse, kompetenzbereich=_KB[kb_code],
        competences=[comp], cognitive_level=level, dimensions=[dim],
        scope="compact", provenance="authored", source="ai",
    )


# The foundational checks — one per key Unterstufe prerequisite competence. Together they
# fully cover the Bruchrechnung → Prozentrechnung → Wachstum/Zinsrechnung ancestor chain,
# plus a little geometry and term work for other Diagnose-Blätter.
GRUNDFERTIGKEITEN: list[LibraryBlock] = [
    _blk("zahlvergleich", "MAT.US.1.ZAH.01", 1, "ZAH", "open_response",
         "Setze das richtige Zeichen ein (< , > , =):  3/4 ___ 0,7.",
         "3/4 > 0,7  (denn 3/4 = 0,75 und 0,75 > 0,70).",
         level="understand", dim="DAR", mins=2, lines=1),
    _blk("grundrechnen", "MAT.US.1.ZAH.02", 1, "ZAH", "calculation",
         "Berechne im Kopf und beachte die Vorrangregeln:  6 · 7 − 12 : 4.",
         "39  (6·7 = 42, 12:4 = 3, 42 − 3 = 39).",
         level="apply", dim="OPE", mins=2, lines=1),
    _blk("term-aufstellen", "MAT.US.1.VAR.01", 1, "VAR", "modelling_task",
         "Schreibe als Term: „Multipliziere eine Zahl x mit 3 und addiere dann 5.“",
         "3 · x + 5.",
         level="understand", dim="MOD", mins=2, lines=1),
    _blk("rechter-winkel", "MAT.US.1.FIG.01", 1, "FIG", "open_response",
         "Wie viele Grad hat ein rechter Winkel? Und wie nennt man einen Winkel, "
         "der kleiner als ein rechter Winkel ist?",
         "Ein rechter Winkel hat 90°. Ein kleinerer Winkel heißt spitzer Winkel.",
         level="remember", dim="OPE", mins=2, lines=1),
    _blk("rechteck-umfang", "MAT.US.1.FIG.02", 1, "FIG", "calculation",
         "Ein Rechteck ist 6 cm lang und 4 cm breit. Berechne Umfang und Flächeninhalt.",
         "U = 2 · (6 + 4) = 20 cm;  A = 6 · 4 = 24 cm².",
         level="apply", dim="OPE", mins=3, lines=2),
    _blk("teiler", "MAT.US.2.ZAH.01", 2, "ZAH", "open_response",
         "Nenne alle Teiler von 12.",
         "1, 2, 3, 4, 6, 12.",
         level="understand", dim="OPE", mins=2, lines=1),
    _blk("ganze-zahlen", "MAT.US.2.ZAH.02", 2, "ZAH", "open_response",
         "Ordne der Größe nach, die kleinste Zahl zuerst:  -3, 2, -5, 0.",
         "-5 < -3 < 0 < 2.",
         level="understand", dim="DAR", mins=2, lines=1),
    _blk("bruchrechnen", "MAT.US.2.ZAH.03", 2, "ZAH", "calculation",
         "Berechne und kürze so weit wie möglich:  1/2 + 1/4.",
         "1/2 + 1/4 = 2/4 + 1/4 = 3/4.",
         level="apply", dim="OPE", mins=3, lines=2),
    _blk("prozent", "MAT.US.2.ZAH.04", 2, "ZAH", "calculation",
         "Wie viel sind 20 % von 150 €?",
         "20 % von 150 € = 0,20 · 150 € = 30 €.",
         level="apply", dim="OPE", mins=3, lines=2),
]


def seed_diagnose_blocks(block_store=None, *, status: str = "approved") -> list[LibraryBlock]:
    """Stage the curated band-1 Grundfertigkeiten into the block library (approved by default,
    so the Diagnose-Blatt demo has real checks to pull). Idempotent: ``upsert`` preserves the
    status of blocks that already exist."""
    from ..store.blockstore import BlockStore

    store = block_store or BlockStore()
    out = []
    for lb in GRUNDFERTIGKEITEN:
        lb.status = status
        out.append(store.upsert(lb))
    return out
