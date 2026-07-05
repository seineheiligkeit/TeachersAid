"""Specimen sheet for the Rätsel engine (A5) — every puzzle type, student + solved, from REAL
curated content (chemistry truth tables · a registered Sachverhalt's Concepts · a MAT draw).

Renders each puzzle grid through the real `build_asset` seam (so what you see is exactly what a
worksheet gets). LOOK at the PNGs and tune the drawers (cell size, number placement, clue-number
legibility, domino wrapping) until they read like a printed Austrian schoolbook.

    python -m tools.puzzles_specimen [OUTDIR]     # default: runs/specimens/puzzles
"""
from __future__ import annotations

import sys
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import chemistry as chem
from teachersaid.library.sachverhalt_blutkreislauf import build_sachverhalt as build_bk
from teachersaid.pipeline import puzzles as pz
from teachersaid.pipeline.assets import build_asset


def _crossword_from_chemistry() -> pz.Puzzle:
    """A Trennverfahren crossword: the separation method is the ANSWER, the mixture the clue
    (curated truth from grounding/chemistry.SEPARATION_METHODS — select, never author). We take
    the one-word method name as the grid answer."""
    entries = []
    for mixture, method in chem.SEPARATION_METHODS:
        answer = method.split(" ")[0].split("/")[0].strip("()")   # the head word, e.g. "Filtrieren"
        clue = f"Trennung von: {mixture}"
        entries.append((answer, clue))
    return pz.build_crossword(entries, seed=11, title="Trennverfahren (Chemie)")


def _suchsel_from_chemistry() -> pz.Puzzle:
    """A Suchsel of acid/base/neutral substances (curated ACID_BASE truth)."""
    words = [name for name, _ in chem.ACID_BASE][:8]
    return pz.build_suchsel(words, seed=4, klasse=3, title="Säuren, Basen, Neutrales")


def _domino_from_sachverhalt() -> pz.Puzzle:
    """A Struktur→Funktion domino from a registered Sachverhalt's structures (Blutkreislauf
    actors). The structure name is the question, its (distinct, verbatim) role is the answer —
    curated, never authored; the drawer wraps the longer answer half."""
    sv = build_bk()
    pairs = [(a.name, str(a.role)) for a in sv.actors]
    return pz.build_domino(pairs, seed=2, title="Struktur & Funktion: Der Blutkreislauf")


def _rechenmauer_mat() -> pz.Puzzle:
    """A MAT Rechenmauer (2. Kl. range), unique-solution masked."""
    return pz.build_rechenmauer(seed=5, klasse=2, levels=4, title="Rechenmauer")


BUILDERS = {
    "crossword_chemie": _crossword_from_chemistry,
    "suchsel_chemie": _suchsel_from_chemistry,
    "domino_blutkreislauf": _domino_from_sachverhalt,
    "rechenmauer_mat": _rechenmauer_mat,
}


def render(outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, build in BUILDERS.items():
        puzzle = build()
        pt = pz.puzzle_task(puzzle, block_id=name, subject="X")
        for asset in pt.assets:                     # empty (…-grid) + solved (…-grid-solved)
            paths.append(build_asset(asset, outdir=outdir))
    return paths


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNS_DIR / "specimens" / "puzzles"
    for p in render(out):
        print(p)
