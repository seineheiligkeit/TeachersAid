"""Derive a worksheet from an annotated authentic text (Deutsch).

The reading analogue of `pipeline/parametrize.py`: an `AnnotatedText` → a `WorksheetContent`
whose tasks' answers come FROM the vetted annotations (never authored at task time). The
text itself renders as a line-numbered `source_text` block so tasks can reference "Zeile N".
Deterministic; an optional LLM phrasing pass could later smooth the question wording (no new
content), like the compose framing — offline this stands on its own.
"""

from __future__ import annotations

from datetime import date

from ..schema.blocks import InfoBlock, Serves, TaskBlock
from ..schema.response import BoxResponse, LinesResponse
from ..schema.texts import AnnotatedText
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

# annotation kind → (task kind, default dimension, default cognitive level, render order)
_TASK_KIND = {
    "comprehension": ("open_response", "LES", "understand", 2),
    "translation": ("translation", "SPR", "apply", 2),       # Latin: Übersetzung
    "structure": ("text_analysis", "LES", "analyze", 3),
    "grammar": ("text_analysis", "SPR", "analyze", 3),       # Latin: Formen/Konstruktion
    "stilmittel": ("text_analysis", "SPR", "analyze", 4),
    "argument_move": ("text_analysis", "LES", "analyze", 4),
    "media_technique": ("text_analysis", "LES", "evaluate", 5),
    "culture": ("open_response", "INH", "understand", 5),    # Latin: Kultur-/Sachkompetenz
    "erwartungshorizont": ("text_production", "SCH", "evaluate", 6),
}
_BOXED_KINDS = {"text_production", "translation"}            # need writing space, not lines


def _serves_for(dim: str, pool: list[Serves]) -> list[Serves]:
    """Pick a competence from the text's pool whose id carries the task's dimension code
    (.LES./.SCH./.SPR./.INH./.ZUH.); fall back to the first. Subject-agnostic (DE & LAT)."""
    hit = next((s for s in pool if f".{dim}." in s.competence_id), None)
    return [hit or pool[0]] if pool else []


def _prompt_for(kind: str, ann) -> str:
    where = f" (Zeile {ann.zeile})" if ann.zeile else ""
    quote = f" „{ann.span}“" if ann.span else ""
    if kind == "translation":
        return f"Übersetze{where}{quote} ins Deutsche."
    if kind == "stilmittel":
        return (f"Welches sprachliche Mittel steckt{where}{quote}? "
                f"Benenne es und erkläre seine Wirkung.")
    if kind == "media_technique":
        return f"Wie versucht der Text{where}{quote}, die Leser:innen zu beeinflussen?"
    if kind == "argument_move":
        return f"Welche Funktion hat die Textstelle{where}{quote} im Argumentationsgang?"
    if kind == "structure":
        return f"Beschreibe den Aufbau{where}: {ann.label}"
    return ann.label    # comprehension/grammar/culture/erwartungshorizont: label is the question


def build_worksheet(at: AnnotatedText, *, today: date | None = None):
    """An AnnotatedText → (WorksheetContent, LehrplanResolution), assemble-ready."""
    from ..grounding import lehrplan_store as ls
    from .resolve import resolve_grade

    res = resolve_grade(at.subject, at.klasse, today=today)
    blocks: list = []

    # 1) the authentic text, line-numbered, with its citation as the caption
    blocks.append(InfoBlock(
        id="text", kind="source_text", content=at.text,
        teacher_note=None, watch_outs=[], asset_refs=[]))
    blocks.append(InfoBlock(id="quelle", kind="prose",
                            content=f"Quelle: {at.source.attribution}"))

    # 2) vocabulary scaffold (one Wortschatz block from all vocab annotations)
    vocab = [a for a in at.annotations if a.kind == "vocab"]
    if vocab:
        lines = "; ".join(f"{a.label} – {a.answer}" for a in vocab if a.answer)
        blocks.append(InfoBlock(id="wortschatz", kind="key_fact",
                                content=f"Wortschatz: {lines}"))

    # 3) tasks, derived from the remaining annotations (answer = the vetted annotation)
    ordered = sorted((a for a in at.annotations if a.kind != "vocab"),
                     key=lambda a: _TASK_KIND.get(a.kind, ("", "", "", 9))[3])
    n = 0
    for a in ordered:
        spec = _TASK_KIND.get(a.kind)
        if spec is None:
            continue
        task_kind, default_dim, default_cl, _ = spec
        dims = a.dimensions or [default_dim]
        n += 1
        boxed = task_kind in _BOXED_KINDS
        blocks.append(TaskBlock(
            id=f"t{n}", kind=task_kind, prompt=_prompt_for(a.kind, a),
            response=BoxResponse(min_height_mm=45) if boxed else LinesResponse(n=3),
            cognitive_level=a.cognitive_level or default_cl, dimensions=dims,
            serves=_serves_for(dims[0], at.serves),
            est_minutes=8 if task_kind == "text_production" else (6 if boxed else 4),
            answer_key=a.answer,
        ))

    meta = WorksheetMeta(
        title=at.title, subject=at.subject, stufe="Unterstufe", klasse=at.klasse,
        kernfrage=f"Wir lesen und untersuchen: „{at.title}“", fassung=res.fassung,
        lehrplan_label=f"{at.subject} · {at.klasse}. Kl."
        + (f" · {at.genre}" if at.genre else ""))
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(at.subject),
        intro=[InfoBlock(id="intro", kind="prose",
                         content="Lies den Text aufmerksam. Die Zeilennummern helfen dir, "
                                 "deine Antworten zu belegen.")],
        sections=[Baustein(id="text-arbeit", title=at.title, blocks=blocks)], assets=[])
    return content, res
