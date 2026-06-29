"""Standardized SRDP *Operatoren* — the controlled task-verb vocabulary (grounding).

Austria's *standardisierte kompetenzorientierte Reife- und Diplomprüfung* (SRDP) uses a
published set of **Operatoren** (task verbs) sorted by **Anforderungsbereich (AFB)**:

    AFB I  — Reproduktion
    AFB II — Transfer / Reorganisation
    AFB III— Reflexion und Problemlösung

This is exactly the depth ladder we already use: ``CognitiveLevel`` maps to an
Anforderungsbereich (see ``pipeline/difficulty.py``). Anchoring generated task prompts to
these standardized verbs makes our tasks read as genuinely *Matura-oriented* and gives the
abstract ``cognitive_level`` a concrete, recognisable surface form a teacher trusts.

**This is GROUNDING, not an asset class.** Like the competence catalog or the ÜT legend,
it is a small controlled vocabulary *injected into the generation brief*
(``llm/prompts.build_system``) — selected, never authored. The Matura shapes *what our
tasks ask*, it is not stored as content.

Note (per the official guidance): an operator is not strictly 1:1 with one AFB — the same
verb can sit in different bands depending on context and prior knowledge. The banding
below is therefore the *typical* home of each operator, offered to the generator as a
palette, not a hard rule.

⚠ **PROVISIONAL VOCABULARY (2026-06-29).** The verb lists below are a working draft. The
authoritative catalog is *"Typen sprachlichen Handelns (Operatoren) in der SRDP"*
(BMBWF/IQS, matura.gv.at) plus the subject-specific operator Handreichungen; the egress
proxy blocks those hosts this session, so the SME will supply the PDF(s) and fact-check
the German. **Replace the lists, keep the structure** — everything downstream
(``afb_for_level`` / ``format_operators_brief`` / the prompt wiring / the test) stays put.
"""

from __future__ import annotations

from ..schema.enums import COGNITIVE_RANK, CognitiveLevel

AFB_LABEL: dict[int, str] = {
    1: "Reproduktion",
    2: "Transfer/Reorganisation",
    3: "Reflexion und Problemlösung",
}

# cognitive rank (0..5) → AFB band (1..3). Kept IDENTICAL to
# ``pipeline.difficulty._RANK_TO_BAND`` so operators and difficulty speak one ladder
# (a test locks this invariant).
_RANK_TO_AFB: dict[int, int] = {0: 1, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3}

# AFB band → standardized operators (PROVISIONAL — see module docstring).
OPERATORS: dict[int, list[str]] = {
    1: ["nennen", "benennen", "angeben", "aufzählen", "beschreiben", "darstellen",
        "wiedergeben", "skizzieren", "zusammenfassen", "definieren"],
    2: ["erklären", "erläutern", "vergleichen", "analysieren", "einordnen", "anwenden",
        "berechnen", "ermitteln", "begründen", "charakterisieren", "ableiten",
        "interpretieren", "untersuchen"],
    3: ["beurteilen", "bewerten", "Stellung nehmen", "diskutieren", "erörtern",
        "überprüfen", "entwickeln", "reflektieren", "rechtfertigen", "argumentieren"],
}


def afb_for_level(cognitive_level: str) -> int:
    """The Anforderungsbereich band (1..3) of a ``cognitive_level`` string."""
    rank = COGNITIVE_RANK.get(cognitive_level, 1)
    return _RANK_TO_AFB.get(rank, 2)


def operators_for_afb(band: int) -> list[str]:
    """The standardized operators typically used at an AFB band (1..3)."""
    return OPERATORS.get(band, [])


def operators_for_level(cognitive_level: str) -> list[str]:
    """The standardized operators that fit a ``cognitive_level`` (via its AFB band)."""
    return operators_for_afb(afb_for_level(cognitive_level))


def format_operators_brief() -> str:
    """A compact palette for the generation system prompt: AFB band → its cognitive
    levels → its standardized operators."""
    lines = [
        "Standardized SRDP Operatoren (task verbs) by Anforderungsbereich — phrase each "
        "task's prompt with an apt operator for its cognitive_level (these are the typical "
        "homes, not a strict 1:1 mapping):"
    ]
    for band in (1, 2, 3):
        levels = [cl.value for cl in CognitiveLevel
                  if _RANK_TO_AFB[COGNITIVE_RANK[cl]] == band]
        lines.append(
            f"  - AFB {band} ({AFB_LABEL[band]}) [{', '.join(levels)}]: "
            f"{', '.join(OPERATORS[band])}"
        )
    return "\n".join(lines)
