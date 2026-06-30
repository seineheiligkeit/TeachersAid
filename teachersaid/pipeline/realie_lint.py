"""Internal-consistency lint for Realien — the entity-lint, degraded to internal coherence.

A Realie is a *Sprechanlass*, not a world-claim (`Documents/realien-design.md` §0/§8): the facts
are invented-coherent fiction, so this lint deliberately does **NOT** check that they are true, and
it **cannot** check L2 correctness or CEFR level — those are SME-gated (the one thing only a human
can do). Its single job is **internal consistency**: every hard DATA token (a clock time, a price)
that a TASK ANSWER references must actually appear in the Realie the student sees (its `text` or its
`facts` set) — so a scan task can't have an answer the board doesn't support. Times/prices are the
hard guarantee (the analogue of the Sachverhalt year-lint); names + level + language are SME-gated.
"""
from __future__ import annotations

import re

from ..schema.richtext import plain_text
from ..schema.texts import AnnotatedText

_TIME = re.compile(r"\b\d{1,2}:\d{2}\b")
# €9,50 · $12 · 9.50 € · £8 — the price tokens a menu/board answer would reference
_PRICE = re.compile(r"(?:[€$£]\s?\d+(?:[.,]\d{1,2})?|\b\d+[.,]\d{2}\s?(?:€|EUR|Euro))")
# an answer that SHOWS a sum ("£2.00 + £3.00 = £5.00", "… altogether") is a computation over the
# menu, not a literal lookup → its prices are exempt from the presence check (the SME verifies the
# arithmetic; pedagogically the working should be shown). A BARE price must still be a menu value.
_SUM = re.compile(r"\+|\b(?:total|together|altogether|insgesamt|zusammen|macht|summe)\b", re.I)


def _rt(v) -> str:
    if v is None:
        return ""
    return v if isinstance(v, str) else plain_text(v)


def _prices(text: str) -> set[str]:
    return {m.group().replace(" ", "") for m in _PRICE.finditer(text)}


def _universe(at: AnnotatedText) -> str:
    parts = [at.text]
    for f in at.facts:
        parts.append(f.label)
        if f.value:
            parts.append(f.value)
    return "  ".join(parts)


def lint(at: AnnotatedText) -> tuple[list[str], list[str]]:
    """(problems, warnings) — internal consistency only (see the module docstring).

    A `problem` is a hard contradiction (an answer cites a time/price absent from the Realie);
    there are currently no warnings (names/level/L2 are SME-gated, not machine-checkable)."""
    problems: list[str] = []
    base = _universe(at)
    for a in at.annotations:
        ans = _rt(a.answer)
        if not ans:
            continue
        label = (a.label or a.kind)[:40]
        # the task's OWN prompt counts too: a constraint it introduces (a deadline "before 09:00",
        # a budget "£4") may legitimately reappear in the answer.
        uni = base + "  " + _rt(a.label)
        uni_times, uni_prices = set(_TIME.findall(uni)), _prices(uni)
        for t in _TIME.findall(ans):
            if t not in uni_times:
                problems.append(f"Antwort zu „{label}“ nennt die Zeit {t}, die nicht im "
                                f"Realie-Text/facts/Aufgabe steht (interne Inkonsistenz).")
        if not _SUM.search(ans):       # a shown sum is a computation over the menu (exempt)
            for p in _prices(ans):
                if p not in uni_prices:
                    problems.append(f"Antwort zu „{label}“ nennt den Preis {p}, der nicht im "
                                    f"Realie-Text/facts/Aufgabe steht (interne Inkonsistenz).")
    return problems, []
