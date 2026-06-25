"""Homework projection — third view: drops teacher-present / equipment-dependent
blocks, migrates watch-outs into student-facing tips, surfaces self_check."""

from __future__ import annotations

from pathlib import Path

from ..schema.worksheet import WorksheetContent
from ._document import build_pdf


def render_homework(content: WorksheetContent, out_path, assets=None) -> Path:
    return build_pdf(content, "homework", out_path, assets)
