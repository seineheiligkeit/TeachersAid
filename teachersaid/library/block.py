"""The block as the master-library unit.

A `LibraryBlock` wraps a schema `Block` (an InfoBlock or TaskBlock — see
`schema/blocks.py`) with the metadata needed to *find and compose* it: what it
serves, how deep it goes, how long it takes, its modality, and — new for the
library — its **scope** (content richness: compact → extended) and an optional
**family** grouping richness variants of one concept.

The block is the durable, reusable unit; a worksheet is a composition of blocks
(see `Documents/block-library-design.md`). Granularity is flexible: a block may be
one item or a full multi-step arc. Standalone learn-from texts are blocks too.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..grounding import lehrplan_store as ls
from ..schema.blocks import Block
from ..schema.enums import Role
from ..schema.worksheet import WorksheetContent

SCOPES = ("compact", "standard", "extended")  # content richness/extent (not thinking depth)


class LibraryBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    block: Block                       # the actual content (discriminated InfoBlock|TaskBlock)
    role: str                          # "info" | "task"
    kind: str                          # block kind (task kind or info kind)
    subject: str
    klasse: int | None = None
    kompetenzbereich: str | None = None
    competences: list[str] = Field(default_factory=list)  # served competence ids (tasks)
    cognitive_level: str | None = None
    dimensions: list[str] = Field(default_factory=list)
    modality: str = "printable"
    scope: str = "standard"            # compact | standard | extended
    family: str | None = None          # groups richness variants of one concept
    status: str = "in_review"          # in_review | approved | rejected
    provenance: str = ""               # harvested:<key> | authored | llm
    source: str = "ai"                 # user | ai
    created_at: str = ""
    updated_at: str = ""

    def summary(self) -> dict:
        return {
            "id": self.id, "role": self.role, "kind": self.kind,
            "subject": self.subject, "klasse": self.klasse,
            "kompetenzbereich": self.kompetenzbereich, "competences": self.competences,
            "cognitive_level": self.cognitive_level, "dimensions": self.dimensions,
            "modality": self.modality, "scope": self.scope, "family": self.family,
            "status": self.status, "provenance": self.provenance, "source": self.source,
            "prompt": _block_text(self.block)[:140],
            "updated_at": self.updated_at,
        }


def _block_text(b: Block) -> str:
    raw = getattr(b, "prompt", None) or getattr(b, "content", None) or ""
    if isinstance(raw, list):
        return "".join(getattr(r, "text", "") for r in raw)
    return str(raw)


def harvest(content: WorksheetContent, *, example_key: str, scope: str = "standard") -> list[LibraryBlock]:
    """Extract every block of a worksheet into LibraryBlocks, tagged from the
    worksheet meta + the catalog (competence → Kompetenzbereich)."""
    subject, klasse = content.meta.subject, content.meta.klasse
    out: list[LibraryBlock] = []
    for b in content.iter_blocks():
        is_task = b.role == Role.TASK
        serves = [s.competence_id for s in b.serves] if is_task else []
        kb = None
        for cid in serves:
            m = ls.competence_meta(cid)
            if m and m.get("kompetenzbereich"):
                kb = m["kompetenzbereich"]
                break
        out.append(LibraryBlock(
            id=f"{example_key}.{b.id}",
            block=b,
            role="task" if is_task else "info",
            kind=b.kind,
            subject=subject, klasse=klasse, kompetenzbereich=kb,
            competences=serves,
            cognitive_level=getattr(b, "cognitive_level", None) if is_task else None,
            dimensions=list(getattr(b, "dimensions", []) or []),
            modality=getattr(b, "modality", None) or "printable",
            scope=scope,
            provenance=f"harvested:{example_key}",
            source="ai",
        ))
    return out
