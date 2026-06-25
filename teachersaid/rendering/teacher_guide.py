"""Teacher guide projection — adds Nachweis, DepthProfile, keys, reasoning, watch-outs.

A pure function of the SAME WorksheetContent as the student sheet, so the answer
key cannot fall out of sync with the task (the mismatched-teacher-guide bug is
structurally impossible).
"""

from __future__ import annotations

from pathlib import Path

from ..schema.worksheet import WorksheetContent
from ._document import build_pdf


def render_teacher_guide(content: WorksheetContent, out_path, assets=None) -> Path:
    return build_pdf(content, "teacher", out_path, assets)
