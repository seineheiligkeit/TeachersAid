"""Latin Wortbildung recipes — the Latein twin of the chemistry qualitative engine.

Same contract as ``pipeline/parametrize.py`` / ``pipeline/chemistry.py``: the recipes
register into the SHARED ``_RECIPES`` registry, so ``make_variants`` / templates /
``compose_variants`` drive Latein unchanged. The facts live in ``grounding/latin.py``
(curated, attested compounds); a recipe **selects** an entry and reads the answer
straight from it — the composition, the assimilated surface form and the German meaning
are all curated data, never synthesized (**no invented Latin, ever**). This is the
deterministic recipe family the Matura demand map calls for — *trennen (Wortbildung)*
is the most frequent IT-Arbeitsaufgaben family (``Documents/matura-latein-coverage.md``).

- ``wortbildung_decompose`` — zerlege ein Kompositum in Präfix + Grundverb und gib die
  Bedeutung an (the *trennen* ask, direction word → parts).
- ``wortbildung_meaning``   — bilde aus Grundverb + Präfix das Kompositum und erschließe
  seine Bedeutung (direction parts → word). Draws only ``transparent`` entries — a
  non-compositional meaning like *amittere = verlieren* cannot honestly be "erschlossen".
- ``wortbildung_matching``  — ordne N Komposita ihren Bedeutungen zu. The scrambled
  listing is deterministic per seed; the answer key is the pairing read from the table.
"""

from __future__ import annotations

import random

from ..grounding.latin import BASE_VERBS, DERIVED_WORDS, PREFIXES, DerivedWord
from ..schema.blocks import SolutionStep
from ..schema.parametric import Instance
from .parametrize import _recipe


def _formation_steps(e: DerivedWord) -> list[SolutionStep]:
    """The worked decomposition for one entry — every line read from the curated row
    (grounding/latin.py), never derived by string surgery on uncurated forms."""
    p = PREFIXES[e.prefix]
    steps = [
        SolutionStep(text=f"Präfix: {e.prefix} („{p.meaning}“)"),
        SolutionStep(text=f"Grundverb: {e.base} („{BASE_VERBS[e.base]}“)"),
    ]
    if e.surface_prefix() != e.prefix.rstrip("-"):
        steps.append(SolutionStep(
            text=f"Lautangleichung: {e.prefix} erscheint hier als {e.surface_prefix()}-"))
    if e.surface_base() != e.base:
        steps.append(SolutionStep(
            text=f"Stammform: {e.base} erscheint im Kompositum als -{e.surface_base()}"))
    steps.append(SolutionStep(text=f"{e.word} = {e.prefix} + {e.base} → „{e.meaning}“"))
    if e.note:
        steps.append(SolutionStep(text=f"Beachte: {e.note}"))
    return steps


@_recipe("wortbildung_decompose")
def _wortbildung_decompose(rng: random.Random) -> Instance:
    """Zerlege ein Kompositum in Präfix + Grundverb und gib seine Bedeutung an."""
    e = rng.choice(DERIVED_WORDS)
    p = PREFIXES[e.prefix]
    answer = (f"{e.prefix} („{p.meaning}“) + {e.base} („{BASE_VERBS[e.base]}“); "
              f"{e.word} bedeutet „{e.meaning}“")
    return Instance(params={"wort": e.word}, answer=answer, steps=_formation_steps(e))


@_recipe("wortbildung_meaning")
def _wortbildung_meaning(rng: random.Random) -> Instance:
    """Bilde aus Grundverb + Präfix das Kompositum und erschließe seine Bedeutung.

    Only ``transparent`` entries: the curated meaning must actually be derivable from
    the parts, otherwise "erschließen" would be a trick question."""
    pool = [w for w in DERIVED_WORDS if w.transparent]
    e = rng.choice(pool)
    p = PREFIXES[e.prefix]
    return Instance(
        params={"basis": f"{e.base} („{BASE_VERBS[e.base]}“)",
                "praefix": f"{e.prefix} („{p.meaning}“)"},
        answer=f"{e.word} — „{e.meaning}“",
        steps=_formation_steps(e))


_MATCH_N = 4
_LETTERS = "ABCDEFGH"


@_recipe("wortbildung_matching")
def _wortbildung_matching(rng: random.Random) -> Instance:
    """Ordne Komposita ihren Bedeutungen zu — the pairing is read from the table.

    Self-contained (no ``Unsuitable``, so a direct call is always valid — like the
    sibling recipes): the two degenerate draws are resampled INTERNALLY — a repeated
    meaning string (an ambiguous right column) and the identity permutation (a trivially
    pre-aligned matching). Both terminate at once on the curated table (all meanings are
    distinct; the identity permutation has probability 1/24)."""
    entries = rng.sample(DERIVED_WORDS, _MATCH_N)
    while len({e.meaning for e in entries}) < _MATCH_N:   # ambiguous: repeated meaning
        entries = rng.sample(DERIVED_WORDS, _MATCH_N)
    perm = rng.sample(range(_MATCH_N), _MATCH_N)
    while perm == list(range(_MATCH_N)):                  # trivial: already aligned
        perm = rng.sample(range(_MATCH_N), _MATCH_N)
    left = "   ".join(f"{i + 1}) {e.word}" for i, e in enumerate(entries))
    right = "   ".join(f"{_LETTERS[j]}) {entries[perm[j]].meaning}"
                       for j in range(_MATCH_N))
    slot = {perm[j]: j for j in range(_MATCH_N)}          # entry index → letter slot
    answer = ", ".join(f"{i + 1} → {_LETTERS[slot[i]]}" for i in range(_MATCH_N))
    steps = [SolutionStep(text=f"{e.word} ({e.prefix} + {e.base}) = „{e.meaning}“")
             for e in entries]
    return Instance(params={"liste": f"{left} — {right}"}, answer=answer, steps=steps)
