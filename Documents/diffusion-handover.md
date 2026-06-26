# Diffusion handover — generating decorative assets for TeachersAid

**Audience:** the SME's image-generation agent (and the human directing it). This is a
self-contained brief: read it, generate the requested images, hand them back. You do **not**
need to read the codebase. TeachersAid does not call you live; this document is the contract.

---

## 1. What TeachersAid is, and where you fit

TeachersAid generates Austrian-Lehrplan-anchored teaching material (AHS Unterstufe, grades 1–4,
i.e. ages ~10–14). Worksheets are built from a reviewed **library** of blocks and **assets**.

Assets come in three classes, and only **one** of them is yours:

| class | examples | who produces it | YOUR JOB? |
|---|---|---|---|
| content / code-generated | number line, graph, data table, function plot, formula | parameterized code (matplotlib/svg) | **No** — code, never diffusion |
| content / sourced | photographs, historical sources, artworks, recordings | external + provenance/rights | **No** |
| **decorative / content-free** | mascots, motifs, icons, spot illustrations, borders, backgrounds | svg/code **or diffusion** | **Yes — this is you** |

The rule the whole product rests on: **content-bearing visuals must be correct** (so they are
code-generated or vetted-sourced — never diffusion, because subtle wrongness survives a skim);
**decorative visuals must be content-free** (then any source, including diffusion, is fine once
vetted). You generate *only* the decorative, content-free class.

---

## 2. The hard rule: CONTENT-FREE (this is enforced)

A decorative asset must carry **no information a student could read, use, or be misled by**. It is
ornament. If it teaches, states, labels, quantifies, or depicts a fact, it is **content** and is
out of scope for you — that asset must be code-generated or sourced instead.

A machine gate (`media_policy`) rejects any decorative asset that claims content, so getting this
right is not optional — a violating asset will not enter the library.

| ✅ Decorative (generate these) | ❌ Content (NOT for diffusion) |
|---|---|
| A friendly owl mascot reading a book | A labelled diagram of the human ear |
| An abstract header band / corner motif | A map of Austria with rivers named |
| A stylised atom motif for a Physik page | A correct Bohr model with electron counts |
| A warm flat-illustration of a forest scene | A food-web with arrows between species |
| A decorative beaker silhouette (no scale) | A beaker showing a pH value or volume |

Concretely, a decorative asset must NOT contain: readable numbers/data, a graph or chart, a
scientifically/historically checkable depiction, a map with named places, formula text, or any
label a task could ask about. **No baked-in text** except purely ornamental lettering (a single
initial in a badge is fine; a sentence or a labelled part is not).

Avoid anything that would later need fact-checking. When in doubt, make it more abstract.

---

## 3. Style guide

- **Audience:** AHS Unterstufe, ages 10–14. Friendly and clean, not childish, not corporate.
- **Look:** flat / lightly-shaded vector illustration; clear silhouettes; generous whitespace;
  works small (it sits in a worksheet margin or header, not full-bleed).
- **Palette (match the product):** ink `#1f3a52` / `#33506e`, warm accent `#b5651d`, green
  `#2e6b3a`, muted blue `#4f6f8f`, paper `#f4f1ea`. Decorative assets may use these or a tasteful
  neighbouring tone; avoid neon and heavy gradients.
- **Neutral & inclusive:** no real people/likenesses, no brands/logos/trademarks, no copyrighted
  characters, no text in any language unless purely ornamental. Austrian/Central-European context
  where a setting is implied (architecture, landscape), nothing nationalistic.
- **Background:** transparent (PNG alpha) unless the asset *is* a background panel.

---

## 4. Output spec

- **Format:** PNG, RGBA, transparent background (except backgrounds/banners).
- **Size:** ~1024 px on the long edge for spot art/mascots; ~1200×120 for banners; square for
  badges/icons. Crisp at the printed size (a worksheet is A4 @ ~150 dpi).
- **Filename:** exactly the asset **`id`** from the manifest, `.png` (e.g. `deco-mascot-owl.png`).
- One file per manifest entry. No text overlays, no watermarks.

---

## 5. The manifest — what to generate

Generate one image per entry below. `id` is the output filename; `prompt` is the brief (expand it
in your own model's idiom, keeping to the style guide); `tags` drive reuse/search in the library.
All are `role: decoration`, content-free.

```json
[
  {"id": "deco-mascot-owl",      "tags": ["mascot"],            "prompt": "A friendly stylised owl holding a pencil, flat vector, warm palette, transparent background. Mascot, no text."},
  {"id": "deco-mascot-owl-think","tags": ["mascot"],            "prompt": "The same owl mascot in a thinking pose, one wing to its chin. Flat vector, transparent."},
  {"id": "deco-motif-atom",      "tags": ["motif","Physik"],     "prompt": "An abstract atom motif (nucleus + stylised orbits), decorative only, NO electron counts or labels. Flat, accent colour."},
  {"id": "deco-motif-leaf",      "tags": ["motif","Biologie"],   "prompt": "A simple decorative leaf/sprout motif, green, flat vector, no labels."},
  {"id": "deco-motif-beaker",    "tags": ["motif","Chemie"],     "prompt": "A decorative beaker silhouette with abstract bubbles, NO scale marks or values, flat vector."},
  {"id": "deco-motif-globe",     "tags": ["motif","GWB"],        "prompt": "A stylised globe motif, abstract continents (not a real accurate map), flat vector, muted blue."},
  {"id": "deco-motif-book",      "tags": ["motif","Deutsch"],    "prompt": "An open book motif with abstract lines (no readable text), flat vector."},
  {"id": "deco-scene-forest",    "tags": ["scene"],              "prompt": "A calm flat-illustration forest scene, Central-European, decorative header art, no animals labelled, no text."},
  {"id": "deco-banner-dots",     "tags": ["banner","header"],    "prompt": "A wide thin decorative header band of dots and a soft rule, accent colour, transparent, 1200x120."},
  {"id": "deco-corner-leaves",   "tags": ["motif","corner"],     "prompt": "A decorative corner flourish of abstract leaves, flat vector, transparent, for a page corner."}
]
```

This is a starter set; the SME may extend it. Keep new entries content-free and tagged.

---

## 6. How results come back into the product (the review loop)

You hand back the PNGs (named by `id`) plus the manifest. They enter the library through the
existing **asset library** seam — they do **not** go live automatically:

1. Each generated file is ingested as a `decorative` asset (`orchestrator.ingest_asset`, or a
   batch over the folder). Ingest runs the `media_policy` gate — a content-bearing decorative asset
   is rejected here, so the content-free rule is enforced at the door.
2. It lands **`in_review`** in the dashboard **Abbildungen** tab (the asset-review surface).
3. The SME reviews each asset and **approves** it. Approved decorative assets are **reusable**
   (tagged) framing the composer can pull into worksheets.

### Optional: live backend instead of batch

If you ever want TeachersAid to call you on demand instead of batch-ingesting files, register a
backend once:

```python
from teachersaid.pipeline import assets

def my_diffusion_backend(asset, path):
    # asset.generator is "diffusion:<recipe>"; asset.spec carries {"prompt": ..., ...}
    # generate the image and write a PNG to `path`.
    image = my_image_model(asset.spec["prompt"])
    image.save(path)

assets.register_diffusion_backend(my_diffusion_backend)
```

Then any `Asset(generator="diffusion:...")` builds through you. Until a backend is registered,
`build_asset` raises `DiffusionNotConfigured` rather than inventing an image — by design, there is
no silent fallback. The media-policy gate still guarantees only content-free decorative assets ever
carry a `diffusion:` id, so a live backend cannot smuggle content past review either.

---

## 7. Checklist before handing back

- [ ] Every image is **content-free** (no readable data, diagrams, maps, formulae, or labels).
- [ ] No real people, brands, copyrighted characters, or non-ornamental text.
- [ ] Style-guide palette and flat/clean look; transparent PNG (except backgrounds/banners).
- [ ] Filenames are exactly the manifest `id`s.
- [ ] Manifest returned alongside the files.
