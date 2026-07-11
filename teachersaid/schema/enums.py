"""Closed enumerations from schema v0.3 (+ v0.4 Medium).

Open sets (TaskKind extensions, ArrangementFormat) are intentionally plain
strings elsewhere, not enums.
"""

from __future__ import annotations

from enum import StrEnum


class Stufe(StrEnum):
    UNTERSTUFE = "Unterstufe"
    OBERSTUFE = "Oberstufe"


class AnchorMode(StrEnum):
    """The primary, honestly rendered basis on which a worksheet is offered."""
    COMPETENCE = "competence"
    UET = "uet"
    HORIZONT = "horizont"


class Modality(StrEnum):
    # Scope boundary: oral/enactive competences don't fully render to paper.
    PRINTABLE = "printable"
    ORAL = "oral"
    ENACTIVE = "enactive"


class CognitiveLevel(StrEnum):
    # The formal depth contract (schema §3). Maps to the Lehrplan's own
    # Anforderungsbereiche (Reproduktion/Transfer/Reflexion/Problemlösung).
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


# Rank for "at or above" depth-target checks.
COGNITIVE_RANK: dict[str, int] = {
    CognitiveLevel.REMEMBER: 0,
    CognitiveLevel.UNDERSTAND: 1,
    CognitiveLevel.APPLY: 2,
    CognitiveLevel.ANALYZE: 3,
    CognitiveLevel.EVALUATE: 4,
    CognitiveLevel.CREATE: 5,
}


class Mark(StrEnum):
    BOLD = "bold"
    ITALIC = "italic"
    TERM = "term"
    CODE = "code"


class InfoKind(StrEnum):
    PROSE = "prose"
    KEY_FACT = "key_fact"
    EXAMPLE = "example"
    PROCEDURE = "procedure"
    FIGURE = "figure"
    DATA_REFERENCE = "data_reference"
    CALLOUT = "callout"
    SOURCE_TEXT = "source_text"  # an authentic text rendered with line numbers (Deutsch/Lesen)


class CalloutRole(StrEnum):
    NOTE = "note"
    WARNING = "warning"
    REVEAL = "reveal"
    TIP = "tip"


class CoreTaskKind(StrEnum):
    OPEN_RESPONSE = "open_response"
    MATCHING = "matching"
    ORDERING = "ordering"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE_JUSTIFY = "true_false_justify"
    TABLE_FILL = "table_fill"
    DATA_INTERPRETATION = "data_interpretation"
    DECISION_SCENARIO = "decision_scenario"
    CREATE_PRODUCE = "create_produce"
    # A5 (the Rätsel engine): a puzzle — Kreuzworträtsel / Suchsel / Domino / Rechenmauer.
    # Cross-subject and zero-LLM (answers DERIVED by pipeline/puzzles.py), so it belongs in
    # the CORE set, not any per-subject task_kind_extension. The grid figure IS the response
    # surface (like ordering/matching): a puzzle block carries no generic write-space.
    PUZZLE = "puzzle"


CORE_TASK_KINDS = frozenset(k.value for k in CoreTaskKind)


class CoverageRelation(StrEnum):
    EXERCISES = "exercises"
    BUILDS_PREREQUISITE = "builds_prerequisite"


class Medium(StrEnum):  # v0.4 A3
    VISUAL = "visual"
    AUDIO = "audio"
    INTERACTIVE = "interactive"


class Role(StrEnum):
    INFO = "info"
    TASK = "task"
