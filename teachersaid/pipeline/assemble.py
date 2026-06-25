"""Assemble (deterministic) — schema §7. Fills the DERIVED fields.

This is the only place nachweis/depth_profile get populated. It also runs the
cheap structural validations that the no-drift / coverage guarantees rely on.
"""

from __future__ import annotations

from ..schema.enums import Role
from ..schema.worksheet import LehrplanResolution, WorksheetContent
from .derive import compute_depth, derive_nachweis


def validate_against_model(content: WorksheetContent) -> list[str]:
    """Structural checks: task kinds and dimensions must be legal for the subject
    model. Returns a list of problems (empty = clean)."""
    from ..schema.enums import CORE_TASK_KINDS

    problems: list[str] = []
    allowed_kinds = CORE_TASK_KINDS | set(content.subject_model.task_kind_extensions)
    allowed_dims = content.subject_model.dimension_ids()
    for b in content.iter_blocks():
        if b.role != Role.TASK:
            continue
        if b.kind not in allowed_kinds:
            problems.append(f"{b.id}: unknown task kind '{b.kind}'")
        for d in b.dimensions:
            if d not in allowed_dims:
                problems.append(f"{b.id}: dimension '{d}' not in subject model")
    return problems


def assemble(
    content: WorksheetContent, resolution: LehrplanResolution
) -> WorksheetContent:
    """Populate derived Nachweis + DepthProfile on a content object."""
    content.depth_profile = compute_depth(content)
    content.nachweis = derive_nachweis(content, resolution)
    return content
