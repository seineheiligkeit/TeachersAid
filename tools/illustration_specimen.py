"""Render a contact sheet from SME-approved file-backed illustration specimens.

    python -m tools.illustration_specimen
    python -m tools.illustration_specimen --out runs/illustration-specimen.png

The contact sheet is visual QA only. It never changes approval status and skips
missing cross-machine binaries while listing them in the footer.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from teachersaid.config import RUNS_DIR
from teachersaid.store.assetstore import AssetStore, LibraryAsset

PAPER = "#f4f1ea"
INK = "#1f3a52"
MUTED = "#4f6f8f"


def _loadable(records: list[LibraryAsset]) -> tuple[list[tuple[LibraryAsset, Image.Image]], list[str]]:
    images: list[tuple[LibraryAsset, Image.Image]] = []
    skipped: list[str] = []
    for record in records:
        if not record.file or not Path(record.file).exists():
            skipped.append(record.id)
            continue
        try:
            with Image.open(record.file) as opened:
                images.append((record, opened.convert("RGBA").copy()))
        except OSError:
            skipped.append(record.id)
    return images, skipped


def render(
    out: Path | None = None,
    *,
    store: AssetStore | None = None,
) -> Path:
    store = store or AssetStore()
    records = [
        a for a in store.approved()
        if (a.klass in {"decorative", "depictive"}
            or a.asset.lane in {"decorative", "depictive"}
            or "style-specimen" in a.tags)
    ]
    loaded, skipped = _loadable(records)
    cols, cell_w, cell_h = 3, 340, 270
    rows = max(1, math.ceil(len(loaded) / cols))
    sheet = Image.new("RGB", (cols * cell_w + 40, rows * cell_h + 110), PAPER)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((20, 16), "TeachersAid \u00b7 Illustration specimens \u00b7 approved only",
              fill=INK, font=font)
    draw.text((20, 36), f"{len(loaded)} shown \u00b7 {len(skipped)} missing/skipped",
              fill=MUTED, font=font)

    if not loaded:
        draw.text((20, 84), "No approved specimen binaries are available on this machine.",
                  fill=MUTED, font=font)
    for i, (record, image) in enumerate(loaded):
        row, col = divmod(i, cols)
        x, y = 20 + col * cell_w, 66 + row * cell_h
        draw.rounded_rectangle((x, y, x + 320, y + 245), radius=8,
                               fill="white", outline="#d8d2c4")
        preview = ImageOps.contain(image, (300, 185))
        white = Image.new("RGBA", preview.size, "white")
        white.alpha_composite(preview)
        px = x + 10 + (300 - preview.width) // 2
        py = y + 10 + (185 - preview.height) // 2
        sheet.paste(white.convert("RGB"), (px, py))
        lane = record.asset.lane or record.klass
        draw.text((x + 10, y + 202), f"{record.id}  [{lane}]", fill=INK, font=font)
        if record.asset.intended_claim:
            claim = record.asset.intended_claim[:72]
            draw.text((x + 10, y + 220), claim, fill=MUTED, font=font)

    if skipped:
        draw.text((20, sheet.height - 22), "Missing: " + ", ".join(skipped)[:150],
                  fill=MUTED, font=font)
    out = out or (RUNS_DIR / "illustration_specimen.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    print(render(args.out))


if __name__ == "__main__":
    main()
