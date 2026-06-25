"""ResponseSpec: an affordance, not layout (schema §4) + v0.4 B1 modes.

The content object has no concept of a page; the renderer turns these into
space/inputs at projection time.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LinesResponse(_Base):
    mode: Literal["lines"] = "lines"
    n: int


class BoxResponse(_Base):
    mode: Literal["box"] = "box"
    min_height_mm: float


class TableResponse(_Base):
    mode: Literal["table"] = "table"
    columns: list[str]
    rows: int


class ChoicesResponse(_Base):
    mode: Literal["choices"] = "choices"
    options: list[str]
    select: Literal["one", "many"]


class NoneResponse(_Base):
    mode: Literal["none"] = "none"


class DiagramResponse(_Base):  # v0.4 B1
    mode: Literal["diagram"] = "diagram"
    kind: Literal["causal_web", "concept_map", "flow"]
    seed_nodes: list[str] = Field(default_factory=list)


class DrawingResponse(_Base):  # v0.4 B1
    mode: Literal["drawing"] = "drawing"
    guide: str | None = None


class ArtifactResponse(_Base):  # v0.4 A4 — student produces something off the sheet
    mode: Literal["artifact"] = "artifact"
    produces: str


ResponseSpec = Annotated[
    LinesResponse
    | BoxResponse
    | TableResponse
    | ChoicesResponse
    | NoneResponse
    | DiagramResponse
    | DrawingResponse
    | ArtifactResponse,
    Field(discriminator="mode"),
]
