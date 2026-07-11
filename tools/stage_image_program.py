"""Stage the Wave-B generated image candidates with complete review provenance.

The tool never generates pixels.  It ingests already-generated local files through
the normal media-policy, lint, and AssetStore gates so a reviewer sees best-of-N
sets rather than an untracked folder of images.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from teachersaid.pipeline import orchestrator as orch
from teachersaid.pipeline.illustration_style import (
    STYLE_NEGATIVE_PROMPT,
    STYLE_PROMPT_PREFIX,
)
from teachersaid.schema.assets import Asset
from teachersaid.store.assetstore import AssetStore


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runs" / "ingest" / "image_program"


REQUESTS = [
    {
        "set": "realie-bahnhof-backdrop-v1",
        "lane": "decorative",
        "role": "background",
        "claim": None,
        "tags": ["realie", "bahnhof", "backdrop", "warmth"],
        "ids": ["img-realie-bahnhof-backdrop-cand-1", "img-realie-bahnhof-backdrop", "img-realie-bahnhof-backdrop-cand-3"],
        "files": ["img-realie-bahnhof-backdrop-cand-1.png", "img-realie-bahnhof-backdrop-cand-2.png", "img-realie-bahnhof-backdrop-cand-3.png"],
        "prompts": [
            """Use case: stylized-concept
Asset type: Austrian school worksheet Realie backdrop candidate 1 of 3
Primary request: a fictional small Central European railway station concourse as a calm contextual backdrop for a German-language Bahnhof exercise
Scene/backdrop: covered platform edge and station hall, simple benches, ticket machine silhouettes without screens or writing, a few distant travelers as quiet scale cues
Style/medium: locked TeachersAid editorial illustration v1; flat vector-like shapes with very light paper-grain shading; warm, humane, age-appropriate for Austrian AHS ages 10–14
Composition/framing: wide landscape, eye-level, uncluttered center, generous quiet margins, strong simple silhouettes
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: optional visual warmth behind a code-authored material card; decorative only, never task-bearing
Constraints: entirely fictional; no readable text; no letters; no numbers; no signs; no clocks; no timetables; no maps; no arrows; no logos; no trademarks; no watermark; no UI; no dense detail""",
            """Use case: stylized-concept
Asset type: Austrian school worksheet Realie backdrop candidate 2 of 3
Primary request: a fictional regional railway platform beneath a graceful metal-and-glass canopy, providing quiet context for a Bahnhof language exercise
Scene/backdrop: Central European station architecture, stationary regional train partly visible at the far edge, luggage and two small traveler silhouettes, all surfaces free of signage
Style/medium: locked TeachersAid editorial illustration v1; clean flat editorial shapes, gently rounded geometry, minimal soft shading, subtle uncoated-paper texture
Composition/framing: wide landscape with a shallow three-quarter view, broad open area through the middle for overlaid worksheet material
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: optional non-instructional backdrop behind a code-authored material card
Constraints: no readable text; no letters; no numbers; no platform numbers; no clock; no timetable; no map; no labels; no arrows; no logo; no trademark; no watermark; no visual puzzle; no task-relevant facts""",
            """Use case: stylized-concept
Asset type: Austrian school worksheet Realie backdrop candidate 3 of 3
Primary request: a fictional Austrian-adjacent town railway station entrance and sheltered platform, warm but restrained
Scene/backdrop: simple stucco station building, canopy, rails receding softly, a bicycle and two distant people, no identifiable real place
Style/medium: locked TeachersAid editorial illustration v1; modern educational editorial art, flat vector-like color fields, barely shaded, tactile paper finish
Composition/framing: panoramic landscape, symmetrical calm composition, low-detail background and generous negative space for a foreground material card
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: reusable decorative context only
Constraints: no text of any kind; no letters; no numbers; no signs; no clocks; no timetables; no maps; no arrows; no logos; no trademarks; no watermark; no photorealism; no task-bearing information""",
        ],
    },
    {
        "set": "realie-cafe-backdrop-v1",
        "lane": "decorative",
        "role": "background",
        "claim": None,
        "tags": ["realie", "cafe", "backdrop", "warmth"],
        "ids": ["img-realie-cafe-backdrop-cand-1", "img-realie-cafe-backdrop", "img-realie-cafe-backdrop-cand-3"],
        "files": ["img-realie-cafe-backdrop-cand-1.png", "img-realie-cafe-backdrop-cand-2.png", "img-realie-cafe-backdrop-cand-3.png"],
        "prompts": [
            """Use case: stylized-concept
Asset type: Austrian school worksheet Realie backdrop candidate 1 of 3
Primary request: a fictional quiet Central European café interior as warm context for a beginner language menu exercise
Scene/backdrop: bentwood chairs, small round tables, a service counter with cups and pastry shapes, daylight through tall windows
Style/medium: locked TeachersAid editorial illustration v1; flat vector-like forms, minimal soft shading, subtle uncoated-paper grain; warm and age-appropriate for Austrian AHS ages 10–14
Composition/framing: wide landscape, uncluttered middle, low visual density, generous margins for a code-authored material card
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: optional decorative atmosphere only; menu items and prices remain live code-authored text
Constraints: no readable text; no letters; no numbers; no menu board; no prices; no signs; no logos; no trademarks; no watermark; no labels; no arrows; no task-bearing facts""",
            """Use case: stylized-concept
Asset type: Austrian school worksheet Realie backdrop candidate 2 of 3
Primary request: a fictional small Viennese-adjacent café corner with a restrained, welcoming educational-editorial mood
Scene/backdrop: tiled floor, simple banquette, two empty tables, coat stand, leafy plant, counter far in the background with unlabeled objects
Style/medium: locked TeachersAid editorial illustration v1; clean flat shapes, softly rounded geometry, only a trace of shading and paper texture
Composition/framing: panoramic interior, eye-level, broad open central field behind a future worksheet card, no busy patterns
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: non-instructional warmth behind a separately typeset café Realie
Constraints: no text of any kind; no letters; no numbers; no menus; no price list; no signs; no logos; no trademark; no watermark; no task-relevant information""",
            """Use case: stylized-concept
Asset type: Austrian school worksheet Realie backdrop candidate 3 of 3
Primary request: a fictional Central European sidewalk café under a simple awning, calm and welcoming
Scene/backdrop: a few empty small tables and chairs, potted greenery, stucco façade, distant generic town street without identifiable landmarks
Style/medium: locked TeachersAid editorial illustration v1; modern flat editorial art, very light tactile paper shading, restrained detail
Composition/framing: wide landscape, open quiet area in the center and right for a code-authored material overlay, simple silhouettes
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: decorative reusable café context only
Constraints: awning and façade completely blank; no text; no letters; no numbers; no menus; no prices; no signs; no logos; no trademarks; no watermark; no arrows; no data""",
        ],
    },
    {
        "set": "theme-learning-vignette-v1",
        "lane": "decorative",
        "role": "header",
        "claim": None,
        "tags": ["theme_asset", "header", "learning", "vignette"],
        "ids": ["img-theme-learning-vignette-cand-1", "img-theme-learning-vignette-cand-2", "img-theme-learning-vignette"],
        "files": ["img-theme-learning-vignette-cand-1.png", "img-theme-learning-vignette-cand-2.png", "img-theme-learning-vignette-cand-3.png"],
        "prompts": [
            """Use case: stylized-concept
Asset type: small worksheet header vignette candidate 1 of 3
Primary request: a restrained cluster of an open blank notebook, pencil, and two simple leaves for an Austrian school worksheet header
Scene/backdrop: off-white paper field with no environment
Style/medium: locked TeachersAid editorial illustration v1; flat vector-like shapes, minimal soft shading, subtle uncoated-paper texture
Composition/framing: compact horizontal vignette, centered, generous blank padding, simple silhouette suitable for a narrow header band
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: sparse theme_asset decoration, never instructional
Constraints: notebook pages completely blank; no text; no letters; no numbers; no equations; no diagrams; no labels; no arrows; no logos; no trademarks; no watermark""",
            """Use case: stylized-concept
Asset type: small worksheet header vignette candidate 2 of 3
Primary request: a restrained arrangement of three overlapping blank index cards, a pencil, and a small sprig
Scene/backdrop: plain off-white paper field
Style/medium: locked TeachersAid editorial illustration v1; clean flat editorial geometry, very light shading and paper texture
Composition/framing: low wide cluster, compact and balanced, large surrounding negative space for a worksheet title
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: optional one-per-sheet header vignette
Constraints: all cards blank; no text; no letters; no numbers; no symbols; no labels; no arrows; no logos; no trademarks; no watermark""",
            """Use case: stylized-concept
Asset type: small worksheet header vignette candidate 3 of 3
Primary request: a simple stack of two closed school notebooks with a pencil and a small leaf, calm and understated
Scene/backdrop: plain off-white paper field
Style/medium: locked TeachersAid editorial illustration v1; modern flat educational editorial art, restrained shading, tactile paper finish
Composition/framing: compact horizontal silhouette placed low in a wide empty canvas, suitable beside a worksheet title
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d and green #2e6b3a
Output intent: sparse decorative theme asset only
Constraints: notebook covers entirely blank; no text; no letters; no numbers; no symbols; no logos; no trademarks; no watermark""",
        ],
    },
    {
        "set": "bio-flower-cutaway-v1",
        "lane": "depictive",
        "role": "anatomy_base",
        "claim": "Stylized longitudinal section of one generalized bisexual flower, showing petals, sepals, stamens, and a continuous central pistil with stigma, style, ovary, and ovules.",
        "tags": ["biology", "flower", "labeled_parts", "hybrid", "depictive"],
        "ids": ["img-bio-flower-cutaway-cand-1", "img-bio-flower-cutaway-cand-2", "img-bio-flower-cutaway"],
        "files": ["img-bio-flower-cutaway-cand-1.png", "img-bio-flower-cutaway-cand-2.png", "img-bio-flower-cutaway-cand-3.png"],
        "prompts": [
            """Use case: scientific-educational
Asset type: hybrid labeled-parts base illustration candidate 1 of 3
Primary request: a simplified longitudinal cutaway of one generalized bisexual flower for lower-secondary biology, without any labels
Subject: one central pistil with a clearly visible stigma at top, slender style, and rounded ovary at the base containing a few ovules; a ring of stamens with distinct filaments and anthers; broad petals outside them; green sepals below the petals; short receptacle and stem
Style/medium: locked TeachersAid editorial illustration v1; clean flat vector-like educational illustration, minimal soft shading, subtle uncoated-paper texture, diagrammatically clear rather than photorealistic
Composition/framing: single flower centered on an off-white field, frontal longitudinal cutaway, bilateral visual balance, each major structure separated by whitespace and easy to point to with code-authored leader lines
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d, botanical green #2e6b3a, muted petal coral
Output intent: vetted depictive base only; code will add all numbers, leaders, and names
Scientific constraints: show exactly one coherent flower, one pistil, plausible radial arrangement of stamens, petals outside stamens, sepals outside/below petals, ovary continuous with style; no detached or duplicated organs
Constraints: no text; no letters; no numbers; no labels; no callout lines; no arrows; no legend; no watermark; no logo; no decorative insects; no background scene""",
            """Use case: scientific-educational
Asset type: hybrid labeled-parts base illustration candidate 2 of 3
Primary request: a clear half-open longitudinal section through a generalized flower for Austrian lower-secondary biology, no labels
Subject: central female organ with stigma, style, and cut-open ovary showing ovules; surrounding stamens with visible anthers; two large petals turned slightly outward; two green sepals at the base; short stem
Style/medium: locked TeachersAid editorial illustration v1; restrained textbook editorial art, flat color fields, lightly shaded for separation, tactile paper finish
Composition/framing: portrait-like biological specimen centered within a landscape off-white canvas; symmetrical front view; unobstructed targets and broad margins for later code-authored leader labels
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d, green #2e6b3a, muted warm petals
Output intent: depictive raster under a deterministic labeling overlay
Scientific constraints: one flower only; one central pistil; ovary at base, style above, stigma at tip; stamens positioned around pistil; petals surround reproductive organs; sepals below petals; no extra organ types
Constraints: no text; no letters; no numbers; no arrows; no leader lines; no labels; no watermark; no logo; no scenery; no insects""",
            """Use case: scientific-educational
Asset type: hybrid labeled-parts base illustration candidate 3 of 3
Primary request: a simplified botanical teaching plate showing a generalized flower in longitudinal section, entirely unlabeled
Subject: clearly separated petals, sepals, stamens with anther and filament, and one central pistil whose stigma, style, ovary, and several ovules are visibly connected
Style/medium: locked TeachersAid editorial illustration v1; modern flat educational editorial rendering, minimal tonal modeling, crisp organ boundaries, subtle paper grain
Composition/framing: isolated central specimen, frontal cutaway, landscape canvas with generous empty margins; no cropping; visual clarity suitable for six code-placed anchor points
Color palette: off-white #f4f1ea, navy #1f3a52, slate #33506e and #4f6f8f, restrained rust #b5651d, green #2e6b3a, muted rose petals
Output intent: candidate for SME selection before code overlays task labels
Scientific constraints: coherent generalized bisexual flower; radial symmetry implied; petals outside stamens; sepals below/outside petals; central pistil continuous from stigma to ovary; ovules remain inside ovary
Constraints: no text; no symbols; no letters; no numbers; no labels; no callouts; no arrows; no watermark; no logo; no decorative background""",
        ],
    },
]


def stage(store: AssetStore | None = None) -> list:
    store = store or AssetStore()
    out = []
    for request in REQUESTS:
        for index, (asset_id, filename, prompt) in enumerate(
            zip(request["ids"], request["files"], request["prompts"]), start=1
        ):
            asset = Asset(
                id=asset_id,
                role=request["role"],
                lane=request["lane"],
                intended_claim=request["claim"],
                spec={"min_width_px": 900 if request["lane"] == "decorative" else 600,
                      "min_height_px": 300, "alpha_expectation": "opaque"},
                illustrative=True,
                caption="Wave-B image-program candidate; not approved until SME selection.",
            )
            out.append(orch.ingest_asset(
                store,
                asset,
                klass=request["lane"],
                tags=request["tags"],
                source="ai",
                status="in_review",
                file=SOURCE / filename,
                generation={
                    "generator": "OpenAI built-in image generation",
                    "model": "built-in image model (identifier not exposed)",
                    "prompt": prompt,
                    "negative_prompt": STYLE_NEGATIVE_PROMPT,
                    "style_prefix": STYLE_PROMPT_PREFIX,
                    "date": date(2026, 7, 11),
                    "reproducibility_parameters": {
                        "mode": "built-in",
                        "candidate_index": index,
                        "seed_available": False,
                    },
                    "replayable": False,
                },
                candidate_set_id=request["set"],
                candidate_index=index,
            ))
    return out


if __name__ == "__main__":
    records = stage()
    for record in records:
        print(record.id, record.status, record.preflight.width, record.preflight.height)
