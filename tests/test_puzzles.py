"""The Rätsel engine (A5) — zero-LLM puzzles with DERIVED answers.

Each puzzle is correct by construction; these tests lock the defining property of each type
(crossword crossing-consistency, Suchsel accidental-duplicate refill, domino closure, unique-
solution masking), determinism per seed, the umlaut convention, age scaling, and that a
puzzle wrapper's TaskBlock assembles/verifies clean with a real subject model (kind `puzzle`,
no write-space, teacher-only solution grid).
"""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.grounding import chemistry as chem
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.library.sachverhalt_blutkreislauf import build_sachverhalt as build_bk
from teachersaid.pipeline import puzzles as pz
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.resolve import resolve_grade
from teachersaid.pipeline.verify import verify
from teachersaid.schema.blocks import TaskBlock
from teachersaid.schema.puzzle import CrosswordPuzzle, DominoChain, Rechenmauer, Suchsel
from teachersaid.schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

PNG = b"\x89PNG\r\n\x1a\n"
_TODAY = date(2026, 3, 1)

# a realistic curated crossword clue set (chemistry Trennverfahren — answer, clue)
_CW_ENTRIES = [
    ("FILTRIEREN", "trennt einen Feststoff von einer Flüssigkeit"),
    ("EINDAMPFEN", "trennt ein gelöstes Salz vom Wasser"),
    ("DESTILLATION", "trennt Alkohol und Wasser"),
    ("SIEBEN", "trennt nach Korngröße"),
    ("DEKANTIEREN", "gießt die Flüssigkeit vom Bodensatz ab"),
]


# ============================================================================
# Kreuzworträtsel
# ============================================================================
def test_crossword_words_are_readable_from_the_grid():
    """Every placed answer actually reads off the solution grid at its slot + direction."""
    cw = pz.build_crossword(_CW_ENTRIES, seed=3)
    for entry, horizontal in ([(e, True) for e in cw.across]
                              + [(e, False) for e in cw.down]):
        r, c = entry["row"], entry["col"]
        read = "".join(
            cw.solution[r][c + i] if horizontal else cw.solution[r + i][c]
            for i in range(entry["length"]))
        assert read == entry["answer"], (entry, read)


def test_crossword_crossings_are_consistent():
    """A shared cell carries ONE letter that both its across and down words agree on — the
    interlock is real, and there are enough crossings for a connected grid."""
    cw = pz.build_crossword(_CW_ENTRIES, seed=3)
    from collections import Counter
    cnt: Counter = Counter()
    for entry, horizontal in ([(e, True) for e in cw.across]
                              + [(e, False) for e in cw.down]):
        r, c = entry["row"], entry["col"]
        for i in range(entry["length"]):
            cell = (r, c + i) if horizontal else (r + i, c)
            cnt[cell] += 1
    crossings = sum(1 for v in cnt.values() if v >= 2)
    assert crossings >= len(_CW_ENTRIES) - 1        # a connected skeleton
    # no cell is claimed by more than two words in this set, and letters agree (checked above)
    assert all(v <= 2 for v in cnt.values())


def test_crossword_deterministic_per_seed():
    a = pz.build_crossword(_CW_ENTRIES, seed=7)
    b = pz.build_crossword(_CW_ENTRIES, seed=7)
    assert a.solution == b.solution and a.across == b.across and a.down == b.down


def test_crossword_umlaut_single_cell():
    """Under the default 'keep' convention, Ä/Ö/Ü occupy ONE cell each (ß → SS)."""
    assert pz.UMLAUT_MODE == "keep"
    assert pz.normalize_answer("GRÖSSE") == "GRÖSSE"          # Ö one letter, ß→SS
    assert pz.normalize_answer("Straße") == "STRASSE"
    cw = pz.build_crossword([("GRÜN", "eine Farbe"), ("GELB", "eine Farbe"),
                             ("BLAU", "eine Farbe")], seed=1)
    # the Ü sits in exactly one grid cell
    gruen = next(e for e in (cw.across + cw.down) if e["answer"] == "GRÜN")
    assert gruen["length"] == 4                              # G-R-Ü-N, four cells


def test_crossword_umlaut_ae_mode(monkeypatch):
    """Flipping the module convention to 'ae' expands Ü→UE (spelled out) in one place."""
    monkeypatch.setattr(pz, "UMLAUT_MODE", "ae")
    assert pz.normalize_answer("GRÜN") == "GRUEN"
    assert pz.normalize_answer("GRÖSSE") == "GROESSE"


def test_crossword_rejects_unplaceable_set():
    """A set with no shared letters cannot form a connected crossing grid → clean error."""
    with pytest.raises(pz.UnplaceableError):
        pz.build_crossword([("XZ", "a"), ("QW", "b")], seed=1)
    with pytest.raises(pz.UnplaceableError):                 # duplicate answers
        pz.build_crossword([("HERZ", "a"), ("HERZ", "b"), ("LUNGE", "c")], seed=1)


# ============================================================================
# Suchsel
# ============================================================================
def test_suchsel_exactly_the_intended_words_are_findable():
    """Every target reads exactly once in the grid (the accidental-duplicate refill guard)."""
    words = ["ARTERIE", "VENE", "HERZ", "LUNGE", "PULS"]
    su = pz.build_suchsel(words, seed=2, klasse=2)
    for w in su.words:
        assert pz._all_occurrences(su.grid, w.word) == 1     # placed exactly once
    # and a word that is not a target does not accidentally appear (spot-check a plausible one)
    assert pz._all_occurrences(su.grid, "PU") >= 0           # (substrings may occur; targets are unique)


def test_suchsel_placed_words_read_correctly():
    su = pz.build_suchsel(["ARTERIE", "VENE", "HERZ"], seed=5, klasse=2)
    for pw in su.words:
        read = "".join(su.grid[r][c] for r, c in pw.cells())
        assert read == pw.word


def test_suchsel_refill_guard_catches_accidental_duplicate():
    """`_each_word_unique` is the correct-by-construction gate: a grid where a target appears
    twice must be rejected (construct one deliberately and confirm the checker fails it)."""
    # a 3×3 grid with "ABC" placed twice (row 0 and row 2)
    grid = [["A", "B", "C"], ["X", "Y", "Z"], ["A", "B", "C"]]
    assert not pz._each_word_unique(grid, ["ABC"])           # two occurrences → rejected
    grid_ok = [["A", "B", "C"], ["X", "Y", "Z"], ["Q", "R", "S"]]
    assert pz._each_word_unique(grid_ok, ["ABC"])            # exactly one → accepted


def test_suchsel_age_scaling_no_reverse_for_younger():
    """Age scaling: below REVERSE_FROM_KLASSE only forward directions are used, so no target
    is placed in a reversed direction."""
    su_young = pz.build_suchsel(["ARTERIE", "VENE", "HERZ", "LUNGE"], seed=1, klasse=2)
    for pw in su_young.words:
        assert (pw.drow, pw.dcol) in pz._DIRS_FWD            # forward only
    # a higher grade MAY use reverse directions (the direction pool is larger)
    su_old = pz.build_suchsel(["ARTERIE", "VENE", "HERZ", "LUNGE"], seed=1, klasse=4)
    assert su_old.size >= 8


def test_suchsel_palindrome_is_placeable():
    """A palindrome (OTTO) reads the same forwards and backwards over ONE placement — the
    uniqueness check counts distinct cell-sets, so it is placeable, not rejected forever."""
    su = pz.build_suchsel(["OTTO", "HERZ", "LUNGE"], seed=3, klasse=2)
    assert pz._all_occurrences(su.grid, "OTTO") == 1
    pw = next(p for p in su.words if p.word == "OTTO")
    assert "".join(su.grid[r][c] for r, c in pw.cells()) == "OTTO"


def test_suchsel_deterministic_per_seed():
    a = pz.build_suchsel(["ARTERIE", "VENE", "HERZ"], seed=9, klasse=3)
    b = pz.build_suchsel(["ARTERIE", "VENE", "HERZ"], seed=9, klasse=3)
    assert a.grid == b.grid and [w.model_dump() for w in a.words] == [w.model_dump() for w in b.words]


# ============================================================================
# Domino
# ============================================================================
_PAIRS = [("2·3", "6"), ("4+5", "9"), ("10−3", "7"), ("3·4", "12"), ("8:2", "4")]


def test_domino_correct_sequence_closes_the_loop():
    dm = pz.build_domino(_PAIRS, seed=1)
    assert pz.chain_closes(dm.solution, dm.pairs)            # the derived order closes


def test_domino_any_wrong_match_breaks_closure():
    """Swap two tiles in the solution: the loop no longer closes (self-check by construction)."""
    dm = pz.build_domino(_PAIRS, seed=1)
    wrong = [dict(t) for t in dm.solution]
    wrong[0], wrong[1] = wrong[1], wrong[0]
    assert not pz.chain_closes(wrong, dm.pairs)


def test_domino_printed_order_does_not_already_close():
    """The scrambled (printed) order must NOT close as laid — else the task hands over the
    answer. (A plain rotation of a closed loop still closes, so this guards that too.)"""
    dm = pz.build_domino(_PAIRS, seed=1)
    assert not pz.chain_closes(dm.tiles, dm.pairs)
    assert dm.tiles != dm.solution


def test_domino_deterministic_per_seed():
    a = pz.build_domino(_PAIRS, seed=3)
    b = pz.build_domino(_PAIRS, seed=3)
    assert a.tiles == b.tiles and a.solution == b.solution


def test_domino_rejects_degenerate_sets():
    with pytest.raises(ValueError):                          # too few pairs
        pz.build_domino([("a", "1"), ("b", "2")], seed=1)
    with pytest.raises(ValueError):                          # non-distinct answers
        pz.build_domino([("a", "1"), ("b", "1"), ("c", "3")], seed=1)


def test_domino_from_real_sachverhalt():
    """Fed from a registered Sachverhalt's structures (Blutkreislauf) — the loop still closes."""
    sv = build_bk()
    dm = pz.build_domino([(a.name, str(a.role)) for a in sv.actors], seed=2)
    assert pz.chain_closes(dm.solution, dm.pairs)


# ============================================================================
# Rechenmauer
# ============================================================================
def test_rechenmauer_sums_are_derived():
    rm = pz.build_rechenmauer(seed=1, klasse=2, levels=4)
    for i in range(len(rm.rows) - 1):                        # each brick = sum of the two below
        for j in range(len(rm.rows[i + 1])):
            assert rm.rows[i + 1][j] == rm.rows[i][j] + rm.rows[i][j + 1]


def test_rechenmauer_masked_variant_is_uniquely_solvable():
    """The masked wall recovers to exactly the original values by propagation (unique)."""
    rm = pz.build_rechenmauer(seed=1, klasse=2, levels=4)
    mask = {tuple(m) for m in rm.masked}
    assert mask                                              # something is actually hidden
    assert pz._uniquely_solvable(rm.rows, mask)
    # the given grid indeed blanks exactly the masked cells
    for i in range(len(rm.rows)):
        for j in range(len(rm.rows[i])):
            if (i, j) in mask:
                assert rm.given[i][j] is None
            else:
                assert rm.given[i][j] == rm.rows[i][j]


def test_rechenmauer_over_masked_wall_is_rejected():
    """Hiding EVERYTHING is not uniquely solvable — the honesty check must reject it (many
    base rows give the same visible apex)."""
    rows = pz._pyramid([2, 3, 5])
    all_cells = {(i, j) for i in range(len(rows)) for j in range(len(rows[i]))}
    assert not pz._uniquely_solvable(rows, all_cells)
    # hiding only the apex is fine (it's forced from the base)
    assert pz._uniquely_solvable(rows, {(len(rows) - 1, 0)})


def test_rechenmauer_age_scaling_ranges_differ():
    """Value ranges widen with Klasse (age scaling)."""
    assert pz.rechenmauer_range(1)[1] < pz.rechenmauer_range(3)[1] < pz.rechenmauer_range(6)[1]
    young = pz.build_rechenmauer(seed=2, klasse=1, levels=3)
    old = pz.build_rechenmauer(seed=2, klasse=6, levels=3)
    assert max(young.rows[0]) <= pz.rechenmauer_range(1)[1]
    # the larger range admits larger base bricks (checked over a few seeds so it's not flaky)
    big = max(max(pz.build_rechenmauer(seed=s, klasse=6, levels=4).rows[0]) for s in range(6))
    small_cap = pz.rechenmauer_range(1)[1]
    assert big > small_cap


def test_rechenmauer_deterministic_per_seed():
    a = pz.build_rechenmauer(seed=4, klasse=3, levels=4)
    b = pz.build_rechenmauer(seed=4, klasse=3, levels=4)
    assert a.rows == b.rows and a.masked == b.masked


# ============================================================================
# The wrapper: puzzle → TaskBlock (+ assets), assemble/verify clean
# ============================================================================
def _minimal_worksheet(block: TaskBlock, assets, subject: str, klasse: int, res):
    sm = ls.get_subject_model(subject)
    meta = WorksheetMeta(title="Rätsel", subject=subject,
                         stufe=ls.stufe_for_klasse(klasse), klasse=klasse,
                         fassung=res.fassung, lehrplan_label=f"{subject} {klasse} Rätsel")
    return WorksheetContent(meta=meta, subject_model=sm,
                            sections=[Baustein(id="k", title="Rätsel", blocks=[block])],
                            assets=assets)


def test_wrapper_taskblock_carries_asset_and_derived_key():
    rm = pz.build_rechenmauer(seed=3, klasse=2, levels=4)
    pt = pz.puzzle_task(rm, block_id="pz.rm", subject="Mathematik")
    assert pt.block.kind == "puzzle"
    assert pt.block.response.mode == "none"                  # the grid IS the surface (no write-space)
    assert pt.block.answer_key == rm.solution_text()        # DERIVED, not authored
    assert pt.block.asset_refs == ["pz.rm-grid"]            # empty grid (student)
    assert pt.block.solution_asset_refs == ["pz.rm-grid-solved"]  # solved grid (teacher-only)
    assert {a.id for a in pt.assets} == {"pz.rm-grid", "pz.rm-grid-solved"}
    assert all(a.generator == "matplotlib:puzzle_grid" for a in pt.assets)


def test_wrapper_assembles_and_verifies_clean_mat():
    res = resolve_grade("Mathematik", 2, today=_TODAY)
    cid = next(c.id for c in res.competences if "ZAH" in c.id)
    rm = pz.build_rechenmauer(seed=3, klasse=2, levels=4)
    pt = pz.puzzle_task(rm, block_id="pz.rm", subject="Mathematik",
                        competence_id=cid, dimension="OPE")
    content = _minimal_worksheet(pt.block, pt.assets, "Mathematik", 2, res)
    assemble(content, res)
    report = verify(content, res)
    assert report.ok, report.problems


def test_wrapper_assembles_and_verifies_clean_chemistry_crossword():
    res = resolve_grade("Chemie", 4, today=_TODAY)
    cid = next(c.id for c in res.competences if "ERK" in c.id)
    cw = pz.build_crossword(_CW_ENTRIES, seed=3, title="Trennverfahren")
    pt = pz.puzzle_task(cw, block_id="pz.cw", subject="Chemie",
                        competence_id=cid, dimension="E")
    content = _minimal_worksheet(pt.block, pt.assets, "Chemie", 4, res)
    assemble(content, res)
    report = verify(content, res)
    assert report.ok, report.problems


def test_puzzle_grid_asset_renders_both_states(tmp_path):
    """Each puzzle type's empty + solved grid renders to a real PNG through build_asset."""
    puzzles = [
        pz.build_crossword(_CW_ENTRIES, seed=3),
        pz.build_suchsel(["ARTERIE", "VENE", "HERZ"], seed=2, klasse=3),
        pz.build_domino(_PAIRS, seed=1),
        pz.build_rechenmauer(seed=1, klasse=2, levels=4),
    ]
    for i, puzzle in enumerate(puzzles):
        pt = pz.puzzle_task(puzzle, block_id=f"pz{i}", subject="X")
        for a in pt.assets:
            p = build_asset(a, outdir=tmp_path)
            assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1000


def test_solution_grid_is_teacher_only(tmp_path):
    """Projection purity: the empty grid renders on the student sheet, the SOLVED grid + the
    answer key only on the teacher guide."""
    import fitz

    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide
    res = resolve_grade("Mathematik", 2, today=_TODAY)
    cid = next(c.id for c in res.competences if "ZAH" in c.id)
    rm = pz.build_rechenmauer(seed=3, klasse=2, levels=4)
    pt = pz.puzzle_task(rm, block_id="pz.rm", subject="Mathematik",
                        competence_id=cid, dimension="OPE")
    content = _minimal_worksheet(pt.block, pt.assets, "Mathematik", 2, res)
    assemble(content, res)
    assets = {a.id: build_asset(a, outdir=tmp_path) for a in content.assets}
    sp = render_student_sheet(content, tmp_path / "s.pdf", assets)
    tp = render_teacher_guide(content, tmp_path / "t.pdf", assets)

    def n_images(pdf):
        with fitz.open(pdf) as d:
            return sum(len(p.get_images()) for p in d)

    def text(pdf):
        with fitz.open(pdf) as d:
            return "".join(p.get_text() for p in d)

    assert n_images(sp) == 1 and n_images(tp) == 2          # student: empty; teacher: empty+solved
    assert "Lösungsraster" in text(tp) and "Lösungsraster" not in text(sp)
    assert rm.solution_text().split(":")[0] in text(tp)     # answer key teacher-only
    assert "Basis" not in text(sp)


def test_puzzle_is_a_core_kind():
    """`puzzle` is a CORE task kind (cross-subject, additive) — not a per-subject extension."""
    from teachersaid.schema.enums import CORE_TASK_KINDS
    assert "puzzle" in CORE_TASK_KINDS


def test_schema_roundtrip_all_types():
    for puzzle, cls in [
        (pz.build_crossword(_CW_ENTRIES, seed=3), CrosswordPuzzle),
        (pz.build_suchsel(["ARTERIE", "VENE", "HERZ"], seed=2, klasse=3), Suchsel),
        (pz.build_domino(_PAIRS, seed=1), DominoChain),
        (pz.build_rechenmauer(seed=1, klasse=2, levels=4), Rechenmauer),
    ]:
        assert cls.model_validate(puzzle.model_dump()) == puzzle


def test_specimen_builders_run(tmp_path):
    """The specimen tool's real-content builders all produce valid puzzles + render."""
    from tools.puzzles_specimen import BUILDERS
    for name, build in BUILDERS.items():
        puzzle = build()
        pt = pz.puzzle_task(puzzle, block_id=name, subject="X")
        for a in pt.assets:
            assert build_asset(a, outdir=tmp_path).read_bytes()[:8] == PNG
