"""Versioned prompt contract for all agent-time raster generation."""

STYLE_VERSION = "teachersaid-illustration-v1"

STYLE_PROMPT_PREFIX = (
    "TeachersAid house illustration, version v1. Flat to lightly shaded editorial "
    "illustration for Austrian AHS learners aged 10 to 14; friendly, calm and "
    "precise without looking childish or corporate; clear silhouettes, restrained "
    "detail, generous whitespace, print-first composition; Central-European context "
    "when a setting is implied. Use the house palette: ink #1f3a52 and #33506e, "
    "warm accent #b5651d, green #2e6b3a, muted blue #4f6f8f, paper #f4f1ea."
)

STYLE_NEGATIVE_PROMPT = (
    "No readable text, letters, numbers, labels, captions, signs, logos, brands, "
    "watermarks, arrows, charts, maps, formulae, task data, photorealistic people, "
    "real-person likenesses, copyrighted characters, neon colours, heavy gradients, "
    "clutter, or decorative details unrelated to the requested context."
)

