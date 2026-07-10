"""Puzzle data models (A5 — the Rätsel engine).

A `Puzzle` is the pure, renderer-independent record of a built puzzle: the grid/tiles + the
DERIVED solution. `pipeline/puzzles.py` constructs these (answers computed, never authored);
the wrapper turns one into a `TaskBlock`, and `matplotlib:puzzle_grid` draws its
`grid_spec()`. Two projections of one object: `grid_spec(solved=False)` (the student's empty
grid) and `grid_spec(solved=True)` (the teacher's filled grid) — so the answer key cannot
drift from the puzzle, exactly like a worksheet's projections.

The models are deliberately plain (lists + dicts): a puzzle grid has no invariants a Pydantic
type would guard that the builder does not already guarantee by construction.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ============================================================================
# Kreuzworträtsel
# ============================================================================
class CrosswordPuzzle(_Base):
    puzzle_type: Literal["crossword"] = "crossword"
    title: str = "Kreuzworträtsel"
    nrows: int
    ncols: int
    # the full solution letter grid (None = a blocked/empty cell)
    solution: list[list[str | None]]
    # numbered clue slots; each: {number,row,col,answer,clue,length}
    across: list[dict] = Field(default_factory=list)
    down: list[dict] = Field(default_factory=list)

    def _numbers(self) -> dict[tuple[int, int], int]:
        return {(e["row"], e["col"]): e["number"] for e in (self.across + self.down)}

    def grid_spec(self, *, solved: bool) -> dict:
        """The `matplotlib:puzzle_grid` spec. `cells` is a row-major grid of dicts:
        {fill: bool, letter?: str, number?: int}. A non-fill cell is a blocked square."""
        numbers = self._numbers()
        cells = []
        for r in range(self.nrows):
            row = []
            for c in range(self.ncols):
                ch = self.solution[r][c]
                if ch is None:
                    row.append({"fill": False})
                else:
                    cell = {"fill": True}
                    if (r, c) in numbers:
                        cell["number"] = numbers[(r, c)]
                    if solved:
                        cell["letter"] = ch
                    row.append(cell)
            cells.append(row)
        return {"puzzle_type": "crossword", "title": self.title,
                "nrows": self.nrows, "ncols": self.ncols, "cells": cells, "solved": solved}

    def solution_text(self) -> str:
        """The teacher answer key: numbered answers by direction."""
        def fmt(entries, label):
            if not entries:
                return ""
            body = "; ".join(f"{e['number']}. {e['answer']}" for e in entries)
            return f"{label}: {body}"
        parts = [p for p in (fmt(self.across, "Waagrecht"), fmt(self.down, "Senkrecht")) if p]
        return " · ".join(parts)


# ============================================================================
# Suchsel
# ============================================================================
class PlacedWord(_Base):
    word: str
    row: int
    col: int
    drow: int
    dcol: int

    def cells(self) -> list[tuple[int, int]]:
        return [(self.row + self.drow * i, self.col + self.dcol * i)
                for i in range(len(self.word))]


class Suchsel(_Base):
    puzzle_type: Literal["suchsel"] = "suchsel"
    title: str = "Suchsel"
    size: int
    grid: list[list[str]]                 # every cell filled (letters)
    words: list[PlacedWord] = Field(default_factory=list)

    def grid_spec(self, *, solved: bool) -> dict:
        """`cells` is a row-major grid of {letter, mark?} — `mark` True (only when solved)
        highlights a cell that belongs to a found word."""
        marked: set[tuple[int, int]] = set()
        if solved:
            for w in self.words:
                marked |= set(w.cells())
        cells = [[{"letter": self.grid[r][c], "mark": (r, c) in marked}
                  for c in range(self.size)] for r in range(self.size)]
        return {"puzzle_type": "suchsel", "title": self.title, "size": self.size,
                "cells": cells, "words": [w.word for w in self.words], "solved": solved}

    def solution_text(self) -> str:
        return "Gesuchte Wörter: " + ", ".join(w.word for w in self.words)


# ============================================================================
# Domino / Trimino
# ============================================================================
class DominoChain(_Base):
    puzzle_type: Literal["domino"] = "domino"
    title: str = "Domino"
    tiles: list[dict]                     # printed (scrambled) order; each {left,right}
    solution: list[dict]                  # the correct closed loop order
    pairs: list[dict] = Field(default_factory=list)   # {question,answer} the loop encodes

    def grid_spec(self, *, solved: bool) -> dict:
        tiles = self.solution if solved else self.tiles
        return {"puzzle_type": "domino", "title": self.title,
                "tiles": [{"left": t["left"], "right": t["right"]} for t in tiles],
                "solved": solved}

    def solution_text(self) -> str:
        chain = " → ".join(f"[{t['left']} | {t['right']}]" for t in self.solution)
        return "Geschlossene Kette: " + chain + " → (zurück zum Anfang)"


# ============================================================================
# Rechenmauer
# ============================================================================
class Rechenmauer(_Base):
    puzzle_type: Literal["rechenmauer"] = "rechenmauer"
    title: str = "Rechenmauer"
    rows: list[list[int]]                 # rows[0] = base … rows[-1] = apex (full solution)
    given: list[list[int | None]]         # None = a masked (blank) brick
    masked: list[list[int]] = Field(default_factory=list)   # [[row,col], …]

    def grid_spec(self, *, solved: bool) -> dict:
        """`rows` top-to-bottom for drawing (apex first). Each brick: {value?} — value
        present when shown (given, or all when solved)."""
        draw = []
        for i in range(len(self.rows) - 1, -1, -1):        # apex row first
            row = []
            for j in range(len(self.rows[i])):
                shown = solved or self.given[i][j] is not None
                row.append({"value": self.rows[i][j] if shown else None})
            draw.append(row)
        return {"puzzle_type": "rechenmauer", "title": self.title, "rows": draw,
                "solved": solved}

    def solution_text(self) -> str:
        """Base row → apex, as the worked path is unambiguous from the base."""
        base = " · ".join(str(v) for v in self.rows[0])
        apex = self.rows[-1][0]
        return f"Basis: {base} → Spitze: {apex}"


Puzzle = CrosswordPuzzle | Suchsel | DominoChain | Rechenmauer
