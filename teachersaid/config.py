"""Central configuration: model, generation params, paths, and the current Fassung.

Kept dependency-free (stdlib only) so every layer can import it.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- LLM configuration -------------------------------------------------------
# Default to the latest, most capable Claude model. Adaptive thinking + high
# effort per the claude-api guidance for intelligence-sensitive generation.
MODEL = os.environ.get("TEACHERSAID_MODEL", "claude-opus-4-8")
THINKING = {"type": "adaptive"}
OUTPUT_CONFIG = {"effort": "high"}
# Streaming-safe default: generation can be long, so keep headroom.
MAX_TOKENS = 32000

# --- Paths -------------------------------------------------------------------
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
GROUNDING_DATA = PACKAGE_ROOT / "grounding" / "data"
# The full competence catalog (deterministic-parser output) the engine grounds in.
LEHRPLAN_DIR = Path(os.environ.get("TEACHERSAID_LEHRPLAN", REPO_ROOT / "lehrplan"))
# Where generated PDFs / rasters / store records land for the demo.
RUNS_DIR = Path(os.environ.get("TEACHERSAID_RUNS", REPO_ROOT / "runs"))

# --- Fassung (the consolidated AHS Lehrplan window) --------------------------
# BGBl. II Nr. 204/2024, DokNr NOR40264237, valid 2024-09-01 .. 2026-08-31.
# Expires at the end of this school year; versioning against Fassung windows is
# a real requirement (handoff §2), so this is a first-class constant.
FASSUNG = {
    "kurztitel": "AHS-Lehrplan (konsolidiert)",
    "bgbl": "BGBl. II Nr. 204/2024",
    "doknr": "NOR40264237",
    "valid_from": "2024-09-01",
    "valid_to": "2026-08-31",
}
