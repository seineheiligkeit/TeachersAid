"""Deterministic, offline pre-review checks for file-backed raster images.

These checks protect review economy, not factual correctness.  In particular,
``attempt_text_heuristic`` is deliberately conservative: edge density can flag a
page-like image but cannot prove that diffusion did not draw pseudo-writing.  A
human must still inspect every candidate for text, labels, numbers and arrows.
No OCR engine or network service is required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from PIL import Image, ImageFilter, ImageStat

from ..schema.assets import ImageLintFinding, ImageLintReport

AlphaExpectation = Literal["opaque", "transparent", "either"]


def _percentile(histogram: list[int], fraction: float) -> int:
    target = sum(histogram) * fraction
    seen = 0
    for value, count in enumerate(histogram):
        seen += count
        if seen >= target:
            return value
    return 255


def lint_image(
    path: str | Path,
    *,
    min_width: int = 600,
    min_height: int = 300,
    alpha_expectation: AlphaExpectation = "either",
    attempt_text_heuristic: bool = False,
) -> ImageLintReport:
    """Inspect one raster without mutating it.

    Resolution failures are errors because upscaling cannot restore print detail.
    Photocopy and alpha findings are warnings: a deliberately pale vignette or
    soft transparent edge can be valid, but the SME should see the risk before
    approval.  The optional text-risk heuristic only recognises unusually dense,
    page-like edge fields.  It misses isolated glyphs and can flag natural texture;
    it is never a substitute for visual review.
    """
    with Image.open(path) as opened:
        image = opened.copy()

    width, height = image.size
    has_alpha = "A" in image.getbands()
    if has_alpha:
        print_view = Image.new("RGBA", image.size, "white")
        print_view.alpha_composite(image.convert("RGBA"))
        gray = print_view.convert("L")
    else:
        gray = image.convert("L")
    hist = gray.histogram()
    lo, hi = _percentile(hist, 0.05), _percentile(hist, 0.95)
    stddev = float(ImageStat.Stat(gray).stddev[0])
    findings: list[ImageLintFinding] = []

    if width < min_width or height < min_height:
        findings.append(ImageLintFinding(
            code="resolution",
            severity="error",
            message=(f"Nur {width}\u00d7{height} px; erwartet mindestens "
                     f"{min_width}\u00d7{min_height} px f\u00fcr den Druck."),
        ))
    if hi - lo < 55 or stddev < 20:
        findings.append(ImageLintFinding(
            code="photocopy_contrast",
            message=("Geringer Graustufen-Kontrast: Das Bild kann in einer "
                     "Schwarzwei\u00dfkopie an Lesbarkeit verlieren."),
        ))

    alpha_extrema = image.getchannel("A").getextrema() if has_alpha else (255, 255)
    if alpha_expectation == "opaque" and alpha_extrema != (255, 255):
        findings.append(ImageLintFinding(
            code="stray_alpha",
            message="Der f\u00fcr wei\u00dfen Druckgrund gedachte Raster enth\u00e4lt Transparenz.",
        ))
    elif alpha_expectation == "transparent" and alpha_extrema == (255, 255):
        findings.append(ImageLintFinding(
            code="missing_alpha",
            message="Der freigestellte Slot erwartet Transparenz, das Bild ist vollst\u00e4ndig deckend.",
        ))

    text_check = "manual_required"
    if attempt_text_heuristic:
        # Normalise size so the score is independent of source resolution.  Text
        # tends to produce many sharp edges across several horizontal bands.
        probe = gray.copy()
        probe.thumbnail((512, 512))
        edges = probe.filter(ImageFilter.FIND_EDGES)
        binary = edges.point(lambda px: 255 if px >= 72 else 0)
        pixels = binary.load()
        row_counts = [sum(1 for x in range(binary.width) if pixels[x, y])
                      for y in range(binary.height)]
        dense_rows = sum(c >= max(8, binary.width // 8) for c in row_counts)
        dense_ratio = dense_rows / max(1, binary.height)
        text_check = f"edge_density:{dense_ratio:.3f}"
        if dense_ratio > 0.42:
            findings.append(ImageLintFinding(
                code="possible_text",
                message=("Viele glyphen\u00e4hnliche Hochfrequenzkanten; auf Text, "
                         "Pseudo-Schrift, Zahlen und Pfeile visuell pr\u00fcfen."),
            ))

    return ImageLintReport(
        width=width,
        height=height,
        mode=image.mode,
        grayscale_span=hi - lo,
        grayscale_stddev=round(stddev, 2),
        findings=findings,
        text_check=text_check,
    )
