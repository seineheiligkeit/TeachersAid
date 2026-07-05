# Illustrations — design for the image program (decorative · depictive · sourced)

**Status: design accepted by the SME (5 Jul 2026); build not started.** This document governs the
illustration *program*; `diffusion-handover.md` remains the operative batch-brief for the existing
decorative lane and gets extended when the local backend lands. Companion decisions live in
`feature-roadmap.md` "▶ Start here (5 Jul 2026)" Wave B.

## 1 · Why (and why now)

Worksheets compete — visually — with real Schulbücher, and pupils notice. Everything content-bearing in
the engine is correct-by-construction, but the sheets are visually austere: the only images are data/
structure figures plus a small content-free decorative kit. This program adds **warmth** (fun graphics
pupils enjoy) and **depictive concept images** (what a thing looks like) without touching the rule the
product rests on.

The frame is build-for-joy: this is done because a beautiful worksheet is intrinsically better, not for
a market.

## 2 · The load-bearing reframe: an image is a CLAIM plus a RENDERING

The reason "diffusion in education" usually fails is treating an image as one thing. It is two:

- the **claim** — what it purports to show ("this depicts a Fliegenpilz", "roughly what a medieval
  castle looks like"). Claims are FACTS: they must be curatable and checkable.
- the **rendering** — how it is drawn. Rendering is EXPRESSION: it may be authored (by diffusion)
  *under constraint* — a style contract, deterministic lints, and the SME gate.

This is exactly `invariants.md` §3 extended to pixels: **mechanism 4 (re-expressed under constraint)
applies to images.** Select the claim, author the rendering.

**The corpus model is what makes this viable at all.** In a live-generation product every image is seen
once by nobody — diffusion hallucination is fatal. Here an image is generated once, **vetted once,
reused forever** (an illustration is like a dataset: curate once, serve many). `AssetStore` already has
the shape (file-backed, tags/status/reuse). The hallucination risk is not zero; it has been *converted*
from a runtime risk into a review-time cost — the same trade the offline-first pivot made for text.

## 3 · The policy: a THIRD media-policy lane, not a loosened rule

`media_policy` today knows two lanes. Neither changes; one is added between them:

| lane | definition | source | gate |
|---|---|---|---|
| **decorative** (exists) | content-free ornament — mood, banners, motifs | svg/code or diffusion | content-free rule (machine) + HITL |
| **depictive** (NEW) | shows a *thing the material mentions* — **no labels, no numbers, no text, no structure a task asks about**. A red blood cell in plasma, a volcano, a market square. | diffusion or sourced | declared `intended_claim` + mandatory HITL checklist + no-text lint |
| **content** (exists) | diagrams, charts, maps, labeled anything, data | code-gen or vetted-sourced — **never diffusion, forever** | media-policy as today |

The depictive lane's discipline: the asset record carries an **`intended_claim`** ("depicts a
Sonnenblume, botanically plausible, no readable parts") and the SME certifies **that claim**,
checklist-style — not vibes. If an image would need a label to do its job, it is content, and it moves
to code-gen/sourced.

## 4 · The resolution hierarchy (select-never-author, applied to pictures)

When a worksheet wants an image, resolve in this order — the delivery-loop philosophy applied to images:

1. **Reuse** an approved library asset (tag search — the `relevant_datasets` discovery pattern);
2. **Sourced** PD/CC (a Wikimedia Commons fetch tool with machine-readable per-file rights — shared
   with the PD-Bildquellen asset class, Wave B5);
3. **Generate** (diffusion, this program);
4. **Go without.**

Rule of thumb: **prefer real PD art where the topic has real sources.** For the Wiener Kongress you
want the Isabey engraving, not a diffusion ballroom — real Zeitkolorit, zero hallucination, and the
image *is a Quelle* (feeds Bildquellenkritik). Diffusion is the lane for what has no source: invented
contexts (Realien!), abstractions, modern everyday scenes, warmth.

## 5 · Applications, ranked by risk-to-payoff

1. **Realien backdrops — the beachhead, risk-free BY CONSTRUCTION.** Realien are declared fictions
   ("invent the timetable, vet the French"), so an invented picture of an invented café makes **zero
   world-claims** — the hallucination risk for the whole class is structurally nil. An illustrated
   awning on the café menu card, a station scene behind the departure board: the `rb.material_card`
   "real artifact" feel jumps a league. Perfect proving ground for backend + style + review flow.
2. **Worksheet header vignettes.** One themed mood image per sheet in the title zone (volcano sheet →
   volcano vignette). Schema: an optional worksheet-level `theme_asset` slot (blocks already carry
   assets per composer-3c). Big warmth, minimal didactic interference.
3. **Task spot illustrations (Sachaufgaben).** A small basket of apples beside the apple task. Governed
   by the seductive-details policy (§8): the spot must depict the task's actual context (situational
   grounding), small, placed out of the solving zone, density-capped.
4. **The Beschriftungs-hybrid — the flagship.** Labeling tasks (beschrifte das Herz / die Blüte / das
   Auge) decompose perfectly: a **vetted base image** (diffusion or sourced) + **curated anchor
   points** (metadata on the asset) + a **code-drawn label layer** in house style (leader lines via
   `figtext`), **maskable** like everything else (`show_value=False` → student gets blank lines,
   teacher gets labels). Text never enters the pixel layer — diffusion's worst failure mode is made
   structurally impossible. One vetted heart illustration becomes a task engine.
5. **Color-by-answer finishers** *(optional, gimmick-lane — SME: nice, not load-bearing)*: posterize a
   vetted illustration into numbered regions, map computed answers → colors. Deterministic
   post-processing; rides Phase 4 only if it stays fun.
6. **Mascots — deliberately NOT per-sheet diffusion.** A recurring companion lives on *consistency*,
   diffusion's known weakness. Mascots are **fixed art**: design once (AI-assisted fine), commit a
   small pose set as static assets in the decorative kit. Diffusion for variety, fixed assets for
   identity.

## 6 · The craft layer

- **Backend = the TTS pattern replayed.** CUDA torch has no cp314 wheel → a **Python 3.12 subprocess**
  drives the GPU, exactly like `teachersaid/audio/`: a new `teachersaid/imagegen/` sibling —
  `backend.py` (core, no torch: spec normalisation, lint calls, ffmpeg-free) + `render.py` (the GPU
  worker, *executed* never *imported*). Wired via the existing `assets.register_diffusion_backend`;
  offline stays `DiffusionNotConfigured` — no silent slop, as designed.
- **Model: Flux.1-schnell** (Black Forest Labs) — fits the RTX 4070 (12 GB) quantized, 4-step fast,
  and **Apache-2.0** licensed (rare in this space; suits a project that reads licences first). Config
  knobs mirror TTS (`IMG_PYTHON`/`IMG_PYTHON_SITE`).
- **`DiffusionSpec` — the spec that makes images REPLAYABLE.** Store
  `(model, prompt, negative_prompt, seed, steps, cfg, size)` on the asset — the diffusion analogue of
  a recipe spec. Same spec → same image: generation is reproducible, the asset is *spec + vetted
  artifact*, provenance is total. (The `runs/` split holds: spec JSON in git, PNG binary ignored,
  rebuildable from the spec.)
- **The illustration style contract — `figstyle`'s twin.** The `diffusion-handover.md` palette is the
  seed; grow it into: a fixed style-prompt prefix + standing negative prompts, the figstyle roles as
  the palette, flat/lightly-shaded look, Austrian/Central-European context where a setting is implied,
  and a **specimen sheet** (`tools/illustration_specimen.py`, like the scene specimens) that renders
  the contract so style drift is visible.
- **The LoRA compounding loop (Phase 4).** Once ~50 SME-approved images exist, train a style LoRA **on
  the project's own vetted corpus** — the style locks itself in, trained on nothing but what was
  already approved.

## 7 · Deterministic gates BEFORE the SME sees anything (review economy for pixels)

1. **OCR no-text lint** — run rapidocr/tesseract over every candidate; any detected text → auto-reject.
   Catches diffusion's most common failure (garbled pseudo-text) by machine.
2. **Photocopy-survival check** — grayscale conversion + contrast/histogram analysis; an image that
   turns to mid-tone mush in B/W fails. (The same discipline as the dash ramp: worksheets get copied.)
3. **Resolution/alpha checks** — printed size at A4 ≥ ~150 dpi; RGBA where the slot expects
   transparency.

**Review UX: best-of-N.** Generate 4 seeds per spec, show a grid in the Abbildungen tab, the SME picks
one (or none) — *choosing beats judging*; far better review economics than accept/reject on singletons.
The focus card shows the `intended_claim` + the lane's checklist (decorative: content-free? style? —
depictive: claim plausibly depicted? anachronisms? anatomy? no readable parts?).

## 8 · Didactic policy (the honesty section)

- **The seductive-details effect is real** — interesting-but-irrelevant decoration measurably *hurts*
  learning in some conditions. The design answer is policy, not taste: a **relevance rule** (a spot
  must depict the task's actual context), a **density cap** per sheet, and **placement** away from
  solving zones.
- **Age register** (curated policy, applied at compose/assemble — rendering stays pure): Klasse 1–2 →
  vignette + spots; Klasse 3–4 → vignette; Oberstufe → sober/none by default. Worksheets grow up with
  their readers.

## 9 · Hard lines — never diffusion, regardless of lane

Historical persons' likenesses (a generated Metternich is a fabricated historical record — PD portraits
exist and are better) · maps · labeled anatomy/apparatus *as learning structure* · Versuchsaufbauten
students must replicate (exactness → scene engine) · photorealistic humans, especially children
(stylized-illustrated humans only) · religious/political iconography · any text in the pixel layer.

## 10 · Phasing

1. **P1 — the backend + gates:** `imagegen/` subprocess (Flux.1-schnell) · `DiffusionSpec` provenance ·
   the three auto-lints · the style contract + specimen sheet. *(No policy change yet — everything
   generated is still decorative-lane.)*
2. **P2 — warmth:** Realien backdrops + worksheet header vignettes (`theme_asset` slot) through the
   best-of-N review flow. The corpus starts feeling warm.
3. **P3 — the depictive lane:** the `media_policy` third lane + `intended_claim` + checklist review;
   the **Beschriftungs-hybrid** (anchor-point metadata + code label layer, maskable). Task spots under
   the §8 policy.
4. **P4 — compounding:** style LoRA from the approved corpus · mascot pose set (fixed art) · optional
   color-by-answer.

**What already exists and is reused untouched:** the `diffusion:` dispatch seam +
`DiffusionNotConfigured` · `media_policy` (gains one lane in P3) · `AssetStore` + ingest gate + the
Abbildungen tab (gains the grid picker) · the decorative kit + `diffusion-handover.md` manifest (stays
valid; the batch-agent path remains an alternative to the local backend).

## 11 · Open decisions for the SME (before/at P1)

- **Lock ONE style direction** via the specimen sheet (flat vector-ish is the working default) — the
  LoRA later cements whatever this pass chooses.
- **Mascot art**: which character(s), and confirm fixed-art (not diffusion) production.
- **P3 timing**: whether the depictive lane waits for P2 experience (recommended) or lands together.
