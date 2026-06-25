"""QA gate: rasterise a PDF to PNG(s) so output can be eyeballed before shipping.

Uses PyMuPDF (no system poppler/pdftoppm needed). This is the use-ready-output
check (handoff §9) — rendering isn't "done" until the raster is produced.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def rasterise(pdf_path, out_dir=None, dpi: int = 110) -> list[Path]:
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir) if out_dir else pdf_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc, 1):
            pix = page.get_pixmap(matrix=mat)
            out = out_dir / f"{pdf_path.stem}.p{i}.png"
            pix.save(out)
            pages.append(out)
    return pages
