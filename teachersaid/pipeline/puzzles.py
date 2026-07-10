"""The Rätsel engine (roadmap A5) — zero-LLM puzzles with DERIVED answers.

A puzzle is *correct by construction*: it is BUILT from curated clue/answer pairs (or a
seeded numeric draw), and the solution is COMPUTED, never authored. Four types, one
discipline (a seeded `random.Random` → deterministic per seed; answers derived):

* **Kreuzworträtsel** — backtracking placement of (clue, answer) pairs into a crossing
  grid; a layout below a minimal crossing count is rejected and re-searched. The grid is a
  figure asset; the numbered waagrecht/senkrecht clue lists render as the prompt.
* **Suchsel** (word search) — answers placed (→ ↓ ↘, and ← ↑ ↖ for older Klassen); the
  rest filled with seeded random letters; then VERIFIED that no target word appears twice
  by accident (refill until clean — the correct-by-construction touch).
* **Domino / Trimino chains** — from curated matching pairs, a CLOSED chain: each tile's
  right half = a question, the NEXT tile's left half = its answer. The loop closes **iff
  every match is correct** — self-checking by graph construction. The printed order is a
  deterministic shuffle; the derived answer is the correct sequence.
* **Rechenmauern** (number pyramids) — a seeded base row, each brick = the sum of the two
  below (derived); a subset of cells is masked such that the solution stays UNIQUE (checked
  honestly by constraint propagation, not assumed). Klasse-appropriate value ranges.

Each builder returns a **schema `Puzzle`** (the pure data model, `schema/puzzle.py`); the
wrapper `puzzle_task` turns one into a `TaskBlock` (+ the grid figure `Asset`s, empty for
the student, solved for the teacher). The block's `kind` is the new CORE kind `"puzzle"`
(cross-subject, additive); the grid is the response surface, so no generic write-space.

**Umlaut convention** (`UMLAUT_MODE`): Ä/Ö/Ü stay SINGLE letters (one grid cell each) —
Unterstufe-friendly and standard Austrian school practice; ß → SS. Flip the module-level
constant to `"ae"` to spell them out (Ä→AE …) in one place, should the SME prefer it.

**Age scaling** — Suchsel reverses only from `klasse >= REVERSE_FROM_KLASSE`; the crossword
grid and Rechenmauer value ranges widen with Klasse (`rechenmauer_range`).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from ..schema.assets import Asset
from ..schema.blocks import Serves, TaskBlock
from ..schema.puzzle import (
    CrosswordPuzzle, DominoChain, PlacedWord, Puzzle, Rechenmauer, Suchsel,
)
from ..schema.response import NoneResponse
from ..schema.richtext import RichText


# --- umlaut convention (SME-flippable in ONE place) --------------------------
# "keep": Ä/Ö/Ü occupy a single grid cell each (Austrian school practice, Unterstufe-
# friendly). "ae": expand to AE/OE/UE (some German puzzle traditions). ß → SS either way
# (there is no single-cell capital ß in a school grid).
UMLAUT_MODE = "keep"

_UMLAUT_EXPAND = {"Ä": "AE", "Ö": "OE", "Ü": "UE", "ß": "SS"}


def normalize_answer(word: str) -> str:
    """A clue answer → the uppercase letter sequence that goes in the grid, under the
    umlaut convention. Spaces/hyphens are dropped (a grid has no spaces); ß always → SS."""
    s = (word or "").strip().upper().replace("ß", "SS")
    if UMLAUT_MODE == "ae":
        for k, v in _UMLAUT_EXPAND.items():
            s = s.replace(k, v)
    # strip everything that is not a puzzle letter (keep A–Z + the kept umlauts)
    keep = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if UMLAUT_MODE == "keep":
        keep |= {"Ä", "Ö", "Ü"}
    return "".join(ch for ch in s if ch in keep)


# --- age scaling knobs -------------------------------------------------------
REVERSE_FROM_KLASSE = 3          # Suchsel: allow reversed (←/↑/↖) placements from 3. Kl.


def rechenmauer_range(klasse: int) -> tuple[int, int]:
    """Klasse-appropriate base-brick range for a Rechenmauer (age scaling). Younger
    grades get small numbers whose pyramid stays in a comfortable head-arithmetic range."""
    if klasse <= 1:
        return (1, 9)
    if klasse <= 2:
        return (1, 15)
    if klasse <= 4:
        return (1, 25)
    return (1, 40)


# ============================================================================
# 1) KREUZWORTRÄTSEL — backtracking crossing-grid placement
# ============================================================================
@dataclass
class _Placement:
    word: str            # the gridded letters
    clue: str            # the natural-language clue
    row: int
    col: int
    horizontal: bool

    def cells(self) -> list[tuple[int, int]]:
        return [(self.row, self.col + i) if self.horizontal
                else (self.row + i, self.col) for i in range(len(self.word))]


class _CrosswordBuilder:
    """Greedy-with-backtracking placement that MAXIMISES crossings. The first word is
    placed horizontally at the origin; each subsequent word is placed so that at least one
    of its letters crosses an already-placed letter, and the placement is legal (no illegal
    adjacency, no overlap of differing letters). More crossings = a denser, better grid, so
    candidate positions are scored by crossing count."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.placements: list[_Placement] = []
        self.grid: dict[tuple[int, int], str] = {}

    # -- legality -------------------------------------------------------------
    def _fits(self, word: str, row: int, col: int, horizontal: bool) -> int | None:
        """Return the crossing count if `word` fits legally at (row,col), else None.
        Legal = every cell is empty or already carries the SAME letter, at least one is a
        crossing, and no *parallel* neighbour touches a non-crossing cell (which would make
        two words run side by side and read as garbage)."""
        crossings = 0
        for i, ch in enumerate(word):
            r = row + (0 if horizontal else i)
            c = col + (i if horizontal else 0)
            cur = self.grid.get((r, c))
            if cur is not None:
                if cur != ch:
                    return None
                crossings += 1
            else:
                # the perpendicular neighbours must be empty (no accidental side-by-side word)
                if horizontal:
                    if (r - 1, c) in self.grid or (r + 1, c) in self.grid:
                        return None
                else:
                    if (r, c - 1) in self.grid or (r, c + 1) in self.grid:
                        return None
        # the cells immediately before/after the word must be empty (word boundaries)
        before = (row, col - 1) if horizontal else (row - 1, col)
        after = ((row, col + len(word)) if horizontal else (row + len(word), col))
        if before in self.grid or after in self.grid:
            return None
        return crossings

    def _candidates(self, word: str) -> list[tuple[int, int, int, bool]]:
        """All legal (crossings, row, col, horizontal) for `word` that cross an existing
        letter — sorted best-first (most crossings). The first word (empty grid) places at
        the origin horizontally."""
        if not self.grid:
            return [(0, 0, 0, True)]
        out: list[tuple[int, int, int, bool]] = []
        for i, ch in enumerate(word):
            for (r, c), gch in self.grid.items():
                if gch != ch:
                    continue
                # try the word horizontally so its i-th letter lands on (r,c)
                cr = self._fits(word, r, c - i, True)
                if cr:
                    out.append((cr, r, c - i, True))
                cr = self._fits(word, r - i, c, False)
                if cr:
                    out.append((cr, r - i, c, False))
        out.sort(key=lambda t: -t[0])
        return out

    def _place(self, word: str, clue: str, row: int, col: int, horizontal: bool) -> None:
        p = _Placement(word=word, clue=clue, row=row, col=col, horizontal=horizontal)
        self.placements.append(p)
        for (r, c), ch in zip(p.cells(), word):
            self.grid[(r, c)] = ch

    def _unplace(self, p: _Placement, before: dict[tuple[int, int], str]) -> None:
        self.placements.pop()
        self.grid = before

    def build(self, entries: list[tuple[str, str]]) -> bool:
        """Place every (word, clue) so all cross the growing skeleton. Backtracks when a
        word has no legal crossing placement given the current grid. Returns True on
        success (all placed)."""
        # place the longest word first (a good spine), then descend by length
        order = sorted(entries, key=lambda e: -len(e[0]))
        return self._recurse(order, 0)

    def _recurse(self, order: list[tuple[str, str]], idx: int) -> bool:
        if idx >= len(order):
            return True
        word, clue = order[idx]
        for _crossings, row, col, horizontal in self._candidates(word):
            snapshot = dict(self.grid)
            self._place(word, clue, row, col, horizontal)
            if self._recurse(order, idx + 1):
                return True
            self._unplace(self.placements[-1], snapshot)
        return False


class UnplaceableError(ValueError):
    """A clue set could not be laid into a connected crossing grid (no common letters, or
    the words simply don't interlock). The caller must curate a better set — we never ship a
    disconnected or degenerate grid."""


def build_crossword(entries: list[tuple[str, str]], *, seed: int = 1,
                    title: str = "Kreuzworträtsel",
                    min_crossings: int | None = None) -> CrosswordPuzzle:
    """A crossword from curated (clue, answer) pairs. Deterministic per seed. Rejects a
    layout with fewer than `min_crossings` crossings (default: one per word beyond the
    first — i.e. a fully connected skeleton) and re-tries from a reshuffled order; raises
    `UnplaceableError` if no connected grid exists.

    The returned puzzle is normalised to a 0-based grid with numbered slots and
    waagrecht/senkrecht clue lists; `solution` carries the full letter grid."""
    norm = [(normalize_answer(a), c) for a, c in entries]
    norm = [(w, c) for w, c in norm if len(w) >= 2]
    if len(norm) < 2:
        raise UnplaceableError("need at least two answers of length ≥ 2")
    if len({w for w, _ in norm}) != len(norm):
        raise UnplaceableError("duplicate answers in the clue set")
    need = min_crossings if min_crossings is not None else (len(norm) - 1)

    rng = random.Random(seed)
    best: _CrosswordBuilder | None = None
    for attempt in range(60):
        b = _CrosswordBuilder(random.Random(rng.random()))
        shuffled = list(norm)
        if attempt:                                   # attempt 0 keeps the length order
            rng.shuffle(shuffled)
        if b.build(shuffled) and len(b.placements) == len(norm):
            crossings = _count_crossings(b)
            if crossings >= need:
                best = b
                break
            if best is None or crossings > _count_crossings(best):
                best = b
    if best is None or len(best.placements) != len(norm):
        raise UnplaceableError(
            f"could not lay {len(norm)} answers into a connected crossing grid")
    return _to_crossword_puzzle(best, title=title)


def _count_crossings(b: _CrosswordBuilder) -> int:
    """A cell shared by two words is one crossing."""
    from collections import Counter
    cnt: Counter = Counter()
    for p in b.placements:
        for cell in p.cells():
            cnt[cell] += 1
    return sum(1 for v in cnt.values() if v >= 2)


def _to_crossword_puzzle(b: _CrosswordBuilder, *, title: str) -> CrosswordPuzzle:
    rmin = min(r for r, _ in b.grid)
    cmin = min(c for _, c in b.grid)
    rmax = max(r for r, _ in b.grid)
    cmax = max(c for _, c in b.grid)
    nrows, ncols = rmax - rmin + 1, cmax - cmin + 1
    solution = [[b.grid.get((r + rmin, c + cmin)) for c in range(ncols)]
                for r in range(nrows)]

    # number the slots: a start cell (top-left of each word) gets a number, in
    # row-major order (the crossword convention).
    starts = sorted({(p.row - rmin, p.col - cmin) for p in b.placements})
    number_of = {cell: i + 1 for i, cell in enumerate(starts)}
    across: list[dict] = []
    down: list[dict] = []
    for p in sorted(b.placements, key=lambda p: (p.row - rmin, p.col - cmin)):
        cell = (p.row - rmin, p.col - cmin)
        entry = {"number": number_of[cell], "row": cell[0], "col": cell[1],
                 "answer": p.word, "clue": p.clue, "length": len(p.word)}
        (across if p.horizontal else down).append(entry)
    across.sort(key=lambda e: e["number"])
    down.sort(key=lambda e: e["number"])
    return CrosswordPuzzle(title=title, nrows=nrows, ncols=ncols, solution=solution,
                           across=across, down=down)


# ============================================================================
# 2) SUCHSEL — word search with an accidental-duplicate refill guard
# ============================================================================
_ALPHABET_KEEP = "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ"
_ALPHABET_AE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_DIRS_FWD = [(0, 1), (1, 0), (1, 1), (1, -1)]        # →  ↓  ↘  ↙
_DIRS_REV = [(0, -1), (-1, 0), (-1, -1), (-1, 1)]    # ←  ↑  ↖  ↗


def _grid_alphabet() -> str:
    return _ALPHABET_KEEP if UMLAUT_MODE == "keep" else _ALPHABET_AE


def build_suchsel(words: list[str], *, seed: int = 1, klasse: int = 2,
                  size: int | None = None, title: str = "Suchsel") -> Suchsel:
    """A word search. Places each normalised word in a random legal direction (reversed
    directions only from `REVERSE_FROM_KLASSE` — age scaling), fills the rest with seeded
    random letters, then VERIFIES that every target word occurs exactly once (any other
    word appears zero times); on an accidental duplicate/extra it refills the free cells and
    re-checks. Deterministic per seed."""
    targets = []
    seen = set()
    for w in words:
        n = normalize_answer(w)
        if len(n) >= 3 and n not in seen:
            targets.append(n)
            seen.add(n)
    if not targets:
        raise ValueError("Suchsel needs at least one answer of length ≥ 3")
    longest = max(len(t) for t in targets)
    n = size or max(longest, min(14, longest + 3), 8)
    dirs = _DIRS_FWD + (_DIRS_REV if klasse >= REVERSE_FROM_KLASSE else [])

    rng = random.Random(seed)
    for _attempt in range(200):
        placed = _place_suchsel_words(targets, n, dirs, rng)
        if placed is None:
            continue
        grid, placements = placed
        alphabet = _grid_alphabet()
        # fill free cells, then verify no accidental duplicate; refill up to a bound
        for _fill in range(200):
            filled = [[grid[r][c] if grid[r][c] is not None else rng.choice(alphabet)
                       for c in range(n)] for r in range(n)]
            if _each_word_unique(filled, targets):
                return Suchsel(title=title, size=n, grid=filled,
                               words=[PlacedWord(word=t, **pl) for t, pl in placements])
    raise ValueError(f"could not build a clean Suchsel for {targets} at size {n}")


def _place_suchsel_words(targets, n, dirs, rng):
    """Try to place every target; return (grid, [(word, placement_dict)]) or None if a word
    would not fit anywhere (caller re-tries with fresh RNG state)."""
    grid: list[list[str | None]] = [[None] * n for _ in range(n)]
    placements = []
    for word in sorted(targets, key=lambda w: -len(w)):   # hardest (longest) first
        spots = []
        for dr, dc in dirs:
            for r0 in range(n):
                for c0 in range(n):
                    if _word_fits(grid, word, r0, c0, dr, dc, n):
                        spots.append((r0, c0, dr, dc))
        if not spots:
            return None
        r0, c0, dr, dc = rng.choice(spots)
        for i, ch in enumerate(word):
            grid[r0 + dr * i][c0 + dc * i] = ch
        placements.append((word, {"row": r0, "col": c0, "drow": dr, "dcol": dc}))
    return grid, placements


def _word_fits(grid, word, r0, c0, dr, dc, n) -> bool:
    for i, ch in enumerate(word):
        r, c = r0 + dr * i, c0 + dc * i
        if not (0 <= r < n and 0 <= c < n):
            return False
        if grid[r][c] is not None and grid[r][c] != ch:
            return False
    return True


def _all_occurrences(grid, word) -> int:
    """How many DISTINCT places `word` occupies in the grid, over all eight directions. A run
    and its reverse cover the SAME set of cells, so they count as ONE occurrence (this is what
    makes a palindrome like OTTO placeable — found forwards and backwards from one placement is
    one place, not two); an accidental second occurrence elsewhere is a different cell-set and
    IS counted. So a target placed exactly once reads back as exactly one occurrence."""
    n = len(grid)
    L = len(word)
    dirs = _DIRS_FWD + _DIRS_REV
    seen: set[frozenset] = set()
    for r in range(n):
        for c in range(n):
            for dr, dc in dirs:
                rr, cc = r + dr * (L - 1), c + dc * (L - 1)
                if not (0 <= rr < n and 0 <= cc < n):
                    continue
                if all(grid[r + dr * i][c + dc * i] == word[i] for i in range(L)):
                    seen.add(frozenset((r + dr * i, c + dc * i) for i in range(L)))
    return len(seen)


def _each_word_unique(grid, targets) -> bool:
    """Correct-by-construction check: every target occupies EXACTLY one place in the grid (see
    `_all_occurrences` — a run and its reverse are the same place, so palindromes are fine)."""
    return all(_all_occurrences(grid, w) == 1 for w in targets)


# ============================================================================
# 3) DOMINO / TRIMINO CHAINS — closed iff every match is correct
# ============================================================================
def build_domino(pairs: list[tuple[str, str]], *, seed: int = 1,
                 title: str = "Domino") -> DominoChain:
    """A closed domino loop from curated (question, answer) pairs. Tile i shows
    [answer_{i-1} | question_i]; laid in a ring, the RIGHT half of one tile (a question) sits
    next to the LEFT half of the following tile (an answer). The loop closes **iff every such
    (question, answer) meeting is a correct pair** — the self-check property, guaranteed by
    construction for the true order and broken by any mis-lay. A student who lays the ring and
    checks that every touching pair matches has verified every answer (self-checking by graph
    construction). The printed tile order is a deterministic scramble; the derived answer is
    the correct cyclic sequence. Deterministic per seed."""
    clean = [(str(q).strip(), str(a).strip()) for q, a in pairs if str(q).strip() and str(a).strip()]
    if len(clean) < 3:
        raise ValueError("a domino loop needs at least three pairs")
    if len({q for q, _ in clean}) != len(clean) or len({a for _, a in clean}) != len(clean):
        raise ValueError("questions and answers must each be distinct for a unique loop")

    n = len(clean)
    # the CORRECT loop: tile i = [answer of pair (i-1) | question of pair i]. Reading around
    # the ring, question_i (tile i, right) always sits next to answer_i (tile i+1, left).
    tiles = []
    for i in range(n):
        prev_answer = clean[(i - 1) % n][1]
        this_question = clean[i][0]
        tiles.append({"left": prev_answer, "right": this_question})
    correct_order = list(range(n))

    # a deterministic scramble for printing. It must NOT already close as laid — and a plain
    # rotation of a closed loop is still closed, so we reject any order whose ring closes (that
    # would hand the student the answer). n≥3 always admits such an order.
    pair_dicts = [{"question": q, "answer": a} for q, a in clean]
    rng = random.Random(seed)
    order = list(range(n))
    for _ in range(200):
        rng.shuffle(order)
        if not chain_closes([tiles[i] for i in order], pair_dicts):
            break
    scrambled = [tiles[i] for i in order]
    return DominoChain(title=title, tiles=scrambled,
                       solution=[tiles[i] for i in correct_order],
                       pairs=pair_dicts)


def chain_closes(tiles: list[dict], pairs: list[dict]) -> bool:
    """True iff laying `tiles` as a ring makes every touching (right, left) a correct pair.

    Each tile's right half is a question and the next tile's left half is an answer; the ring
    closes when, for every i, (tiles[i].right, tiles[i+1].left) is one of the curated
    (question, answer) pairs. This is the self-check property: a student's laid-out order is
    correct **iff** this returns True, and any wrong tile order breaks it."""
    n = len(tiles)
    if n == 0:
        return False
    valid = {(str(p["question"]), str(p["answer"])) for p in pairs}
    return all((str(tiles[i]["right"]), str(tiles[(i + 1) % n]["left"])) in valid
               for i in range(n))


# ============================================================================
# 4) RECHENMAUERN — number pyramid, unique-solution masking
# ============================================================================
def build_rechenmauer(*, seed: int = 1, klasse: int = 2, levels: int = 4,
                      title: str = "Rechenmauer") -> Rechenmauer:
    """A number pyramid: a seeded base row of `levels` bricks; each brick above = the SUM of
    the two below (derived). A subset of bricks is then masked (blanked for the student) such
    that the solution is still UNIQUE — verified honestly by solving the masked wall
    (constraint propagation), never assumed. Value ranges scale with Klasse (age scaling).
    Deterministic per seed."""
    lo, hi = rechenmauer_range(klasse)
    rng = random.Random(seed)
    for _ in range(400):
        base = [rng.randint(lo, hi) for _ in range(levels)]
        rows = _pyramid(base)                          # rows[0] = base, rows[-1] = apex
        mask = _choose_unique_mask(rows, rng)
        if mask is not None:
            given = [[None if (i, j) in mask else rows[i][j]
                      for j in range(len(rows[i]))] for i in range(len(rows))]
            return Rechenmauer(title=title, rows=rows, given=given,
                               masked=sorted([list(m) for m in mask]))
    raise ValueError("could not build a uniquely-solvable Rechenmauer")


def _pyramid(base: list[int]) -> list[list[int]]:
    """Build every row from the base up (each brick = sum of the two below)."""
    rows = [list(base)]
    while len(rows[-1]) > 1:
        prev = rows[-1]
        rows.append([prev[j] + prev[j + 1] for j in range(len(prev) - 1)])
    return rows


def _choose_unique_mask(rows: list[list[int]], rng: random.Random) -> set | None:
    """Pick a random subset of cells to hide such that the wall is still uniquely solvable.
    We try to hide as many as we honestly can: start from an ambitious count and shrink until
    a uniquely-solvable mask is found. Returns the mask (set of (row,col)) or None."""
    cells = [(i, j) for i in range(len(rows)) for j in range(len(rows[i]))]
    total = len(cells)
    # aim high (roughly half the wall), fall back to fewer masked cells if needed
    for k in range(total - 1, 0, -1):
        for _try in range(40):
            mask = set(rng.sample(cells, k))
            if _uniquely_solvable(rows, mask):
                return mask
    return None


def _uniquely_solvable(rows: list[list[int]], mask: set) -> bool:
    """Is the wall with `mask` hidden solvable to EXACTLY the original values, uniquely?

    We solve by constraint propagation over the two relations that tie the wall together:
      (up)   parent = left_child + right_child
      (down) a child = parent − sibling   (when the parent and the other child are known)
    Iterating these to a fixed point fills every cell that is *forced*. The mask is uniquely
    solvable iff propagation recovers every hidden cell (nothing left ambiguous)."""
    known: dict[tuple[int, int], int] = {}
    for i in range(len(rows)):
        for j in range(len(rows[i])):
            if (i, j) not in mask:
                known[(i, j)] = rows[i][j]
    changed = True
    while changed:
        changed = False
        for i in range(len(rows)):
            for j in range(len(rows[i])):
                if (i, j) in known:
                    continue
                v = _forced_value(rows, known, i, j)
                if v is not None:
                    known[(i, j)] = v
                    changed = True
    # uniquely solvable ⇔ every hidden cell got forced (and to the true value by construction)
    return all((i, j) in known for i in range(len(rows)) for j in range(len(rows[i])))


def _forced_value(rows, known, i, j) -> int | None:
    """The value of brick (i,j) if it is FORCED by its known neighbours, else None.
    Relations: parent = left+right; child = parent − sibling."""
    # (up) both children known → this is their sum
    if i > 0:
        lc, rc = known.get((i - 1, j)), known.get((i - 1, j + 1))
        if lc is not None and rc is not None:
            return lc + rc
    # (down) parent and sibling known → this child = parent − sibling
    if i + 1 < len(rows):
        # (i,j) is the left child of (i+1, j-1) [needs sibling (i, j-1)] …
        parent = known.get((i + 1, j - 1))
        sib = known.get((i, j - 1))
        if parent is not None and sib is not None and j - 1 >= 0:
            return parent - sib
        # … or the right child of (i+1, j) [needs sibling (i, j+1)]
        parent = known.get((i + 1, j))
        sib = known.get((i, j + 1))
        if parent is not None and sib is not None:
            return parent - sib
    return None


# ============================================================================
# THE WRAPPER: a Puzzle → a TaskBlock (+ empty & solved grid assets)
# ============================================================================
@dataclass
class PuzzleTask:
    """A puzzle wrapped for the corpus: the schema `Puzzle`, the `TaskBlock` that carries it
    (the grid is the response surface — no write-space), and the two grid `Asset`s (empty for
    the student, solved for the teacher). `assets` is the full list to attach to
    `WorksheetContent.assets`; the block already references them."""
    puzzle: Puzzle
    block: TaskBlock
    assets: list[Asset] = field(default_factory=list)


# clue-list / cognitive-level defaults per puzzle type
_PUZZLE_PROMPTS = {
    "crossword": "Löse das Kreuzworträtsel. Trage die gesuchten Wörter waagrecht und "
                 "senkrecht in das Gitter ein.",
    "suchsel": "Finde die versteckten Wörter im Buchstabengitter und markiere sie.",
    "domino": "Lege die Domino-Steine zu einer geschlossenen Kette: An jeden Stein passt "
              "rechts die Frage, deren Antwort links auf dem nächsten Stein steht. Die "
              "Kette geht genau dann auf, wenn alle Paare stimmen.",
    "rechenmauer": "Fülle die Rechenmauer: Jeder Stein ist die Summe der beiden Steine "
                   "darunter.",
}
_PUZZLE_LEVEL = {"crossword": "remember", "suchsel": "remember",
                 "domino": "understand", "rechenmauer": "apply"}
_PUZZLE_MIN = {"crossword": 12, "suchsel": 8, "domino": 8, "rechenmauer": 6}


def _crossword_clue_lines(p: CrosswordPuzzle) -> str:
    """The waagrecht/senkrecht clue lists as a printable prompt appendix."""
    def fmt(entries):
        return "  ".join(f"{e['number']}. {e['clue']} ({e['length']})" for e in entries)
    parts = [_PUZZLE_PROMPTS["crossword"]]
    if p.across:
        parts.append("Waagrecht: " + fmt(p.across))
    if p.down:
        parts.append("Senkrecht: " + fmt(p.down))
    return "\n".join(parts)


def puzzle_task(puzzle: Puzzle, *, block_id: str, subject: str,
                competence_id: str | None = None, dimension: str | None = None,
                cognitive_level: str | None = None, est_minutes: int | None = None,
                answer_key: RichText | None = None) -> PuzzleTask:
    """Wrap any `Puzzle` into a `TaskBlock` with an empty-grid figure (student-visible) and a
    solved-grid figure (teacher-only, via `solution_asset_refs`). `kind="puzzle"` (a CORE
    kind); the grid is the response surface, so the response is `none` (no write-space). The
    `answer_key` defaults to the puzzle's own derived solution text."""
    ptype = puzzle.puzzle_type
    empty = Asset(id=f"{block_id}-grid", role="figure", generator="matplotlib:puzzle_grid",
                  spec={**puzzle.grid_spec(solved=False)},
                  caption=f"{puzzle.title} (Aufgabe)")
    solved = Asset(id=f"{block_id}-grid-solved", role="figure",
                   generator="matplotlib:puzzle_grid",
                   spec={**puzzle.grid_spec(solved=True)},
                   caption=f"{puzzle.title} (Lösung)")
    prompt: RichText = (_crossword_clue_lines(puzzle)
                        if isinstance(puzzle, CrosswordPuzzle) else _PUZZLE_PROMPTS[ptype])
    serves = ([Serves(competence_id=competence_id, relation="exercises")]
              if competence_id else [])
    block = TaskBlock(
        id=block_id, kind="puzzle", prompt=prompt,
        response=NoneResponse(),
        cognitive_level=cognitive_level or _PUZZLE_LEVEL[ptype],
        dimensions=[dimension] if dimension else [],
        serves=serves,
        est_minutes=est_minutes or _PUZZLE_MIN[ptype],
        answer_key=answer_key if answer_key is not None else puzzle.solution_text(),
        asset_refs=[empty.id],
        solution_asset_refs=[solved.id])
    return PuzzleTask(puzzle=puzzle, block=block, assets=[empty, solved])
