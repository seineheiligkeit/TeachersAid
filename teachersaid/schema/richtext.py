"""RichText: an inline-run model, NOT html (schema §4).

Canonical form accepts `str | list[InlineRun]`; a bare string is normalised to
a single unmarked run on the way in, and single unmarked runs collapse back to
a plain string for clean storage. `InlineRef` (v0.4 B2) is a run that points at
another block instead of carrying text.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from .enums import Mark


class InlineRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = ""
    mark: Mark | None = None
    ref_block: str | None = None  # v0.4 B2: an intra-sheet reference run

    @model_validator(mode="after")
    def _check(self) -> "InlineRun":
        if self.ref_block is not None and self.mark is not None:
            raise ValueError("an InlineRun cannot be both a ref_block and marked")
        if self.ref_block is None and self.text == "":
            raise ValueError("a non-ref InlineRun needs text")
        return self


# Canonical RichText: union of plain string or a list of runs.
RichText = str | list[InlineRun]


def to_runs(value: RichText) -> list[InlineRun]:
    """Normalise any RichText value to a list of runs."""
    if isinstance(value, str):
        return [InlineRun(text=value)]
    return list(value)


def plain_text(value: RichText) -> str:
    """Flatten RichText to plain text (refs render as a placeholder)."""
    out: list[str] = []
    for run in to_runs(value):
        out.append(f"[→{run.ref_block}]" if run.ref_block else run.text)
    return "".join(out)


def collapse(value: RichText) -> RichText:
    """Collapse a single unmarked, non-ref run list back to a plain string."""
    if isinstance(value, list) and len(value) == 1:
        run = value[0]
        if run.mark is None and run.ref_block is None:
            return run.text
    return value
