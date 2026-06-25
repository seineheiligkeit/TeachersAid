"""Student sheet projection — hides keys/notes/watch-outs; drops non-printable blocks."""

from __future__ import annotations

from pathlib import Path

from ..schema.worksheet import WorksheetContent
from ._document import build_pdf


def render_student_sheet(content: WorksheetContent, out_path, assets=None) -> Path:
    return build_pdf(content, "student", out_path, assets)
