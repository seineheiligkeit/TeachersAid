# Handover — the image program (Wave B): you own the image axis

You are the external AI agent that completed `Documents/handover-roadmap-leftovers.md` (reviewed:
clean, merged). This brief hands you **Wave B — the image program — end to end**. You bring your own
native image generation; that replaces the planned local-GPU diffusion backend and changes some
architecture, spelled out below. Everything else about how this repo works still binds.

## 0. Read first, in this order

1. `CLAUDE.md` — the operating manual. Binding.
2. **`Documents/illustration-design.md`** — the accepted design for this program (image = CLAIM +
   RENDERING; the three lanes; the resolution hierarchy; the Beschriftungs-hybrid; the
   seductive-details policy). This is the authoritative design — your work implements it.
3. `Documents/diffusion-handover.md` — the older batch-agent brief (context; superseded where it
   conflicts with this document).
4. `teachersaid/pipeline/media_policy.py`, `teachersaid/store/assetstore.py`,
   `teachersaid/pipeline/assets.py` (the `diffusion:` seam + `register_diffusion_backend`),
   `teachersaid/pipeline/labeled_diagram.py` (the code-label layer you will reuse in I3),
   the **Abbildungen** tab in `teachersaid/api/`.

## 1. What changes because you generate images yourself

The design assumed images are generated at engine build time by a local Flux backend (replayable via
a stored seed). Your generation happens at *agent time* instead. Consequences — these are decisions,
not suggestions:

- **Generated images enter the corpus as FILE-BACKED assets** through the existing ingest gate
  (`orch.ingest_asset` → `AssetStore`), exactly like sourced images — NOT as build-time `Asset`
  specs. The corpus model carries the weight: **vet once, reuse forever**. The vetted file is the
  asset.
- **Provenance is recorded honestly.** Store a generation record per image (extend the stored asset
  metadata): `origin="synthetic"`, generator/model name, the full prompt (and negative/style prefix),
  date, and any reproducibility parameters your generator exposes. If your generator cannot replay
  from a seed, say so in the record (`replayable: false`) — an honest non-replayable record beats a
  fake seed. Never record an image as sourced/PD when it is synthetic.
- **Binaries do NOT go into git.** The persistence policy is git = text, binaries = Drive/rebuild.
  Generated PNGs are not rebuildable, so they follow the sourced-asset pattern (like the VCTK voice
  clips): the provenance/metadata JSON is tracked, the image files live under the asset store's
  materialised paths (git-ignored) and the human syncs them via Drive. Your final report MUST list
  every binary path you produced so the human can sync them.
- **B4 (style LoRA) is out of scope for you** — it is backend-specific to the local-Flux future.
  Your substitute discipline: a **locked style-prompt prefix** (one constant, versioned in code, used
  for every generation) so the corpus stays visually coherent; document it in the style contract.

## 2. The rules that do not bend

- **The content lane stays code-gen/sourced FOREVER.** No generated image may carry text, numbers,
  labels, arrows, or any datum a task uses. Text never enters the pixel layer — labels are drawn by
  CODE over the image (that is the whole point of I3).
- **Three lanes** (you implement the third): `decorative` (content-free framing) · **`depictive`**
  (shows a *thing* — no labels/numbers/text; carries an `intended_claim` the SME can check) ·
  `content` (code-gen or vetted-sourced only — never yours to generate).
- **Resolution hierarchy** when a visual is wanted: reuse an approved asset › sourced PD/CC ›
  generate › none. Generation is the third choice, not the first.
- **Every image passes the HITL gate.** Nothing you generate reaches delivery without SME approval
  in the Abbildungen tab. Your job includes making that review pleasant (I1's best-of-N grid).
- **Rights gates for sourced images**: AT 70-Jahre-p.m.a. + the **PD-work ≠ PD-reproduction**
  per-item caution; Wikimedia Commons machine-readable per-file rights, recorded verbatim. Fail
  closed, like your `public_domain_mark` gate.
- Tests stay OFFLINE (fixtures; never a live generation or network call in pytest). German product
  strings; English code/docs.

## 3. The tasks

### I1 — gates, schema, review surface (build this first; everything rides on it)

- **The `depictive` lane** in `media_policy.py` (+ schema where the lane is declared): between
  decorative and content; carries `intended_claim: str` (what the image asserts it shows — the
  checkable fact half). Content-bearing assets still hard-reject a generated source.
- **The stored generation record** (see §1) on file-backed assets — extend the asset metadata model
  in `store/assetstore.py` additively.
- **Deterministic pre-review lints** (pure PIL/PyMuPDF, offline):
  - *photocopy survival*: grayscale-contrast check (an image that dies in B/W gets flagged);
  - *resolution/alpha sanity* (min dimensions, no stray alpha where print needs white);
  - *no-text*: as far as deterministically possible (e.g. high-frequency glyph-like region
    heuristics are acceptable to attempt but NOT required); the reliable no-text check is YOU
    inspecting your own output at generation time + the SME gate. Be honest in the lint's docstring
    about what it can and cannot catch.
- **Best-of-N review**: generate N candidates per request; the Abbildungen tab shows them as a grid,
  the SME picks one (choosing beats judging). Keep the API/UI change small and consistent with the
  existing tab.
- The **style contract**: a short `Documents/illustration-style-contract.md` — the locked style
  prefix, age register (10–14), what warmth means here, the seductive-details policy applied
  (relevance rule · density cap · placement). Then `tools/illustration_specimen.py` renders a
  contact sheet of approved specimens.

### I2 — warmth: Realien backdrops + header vignettes

- Realien first — **risk-free by construction** (invented world → invented picture; the Realie's
  facts are already fiction, so a generated backdrop asserts nothing). Generate backdrops for 2–3
  existing approved Realien (`library/realie_bahnhof.py`, `realie_cafe.py`, …) and wire an optional
  backdrop slot into the Realien material card rendering (keep `rendering/` pure — the asset id
  travels in the content, the renderer just draws it).
- A `theme_asset` slot for worksheet header vignettes (decorative lane), used sparingly. SME-gated.

### I3 — the Beschriftungs-hybrid (the flagship)

The depictive lane's payoff: a labeling task whose base is a vetted image and whose labels are CODE.

- A vetted base image (sourced PD **or** your generation, per the hierarchy) + **curated anchor
  points** + the existing `labeled_parts` machinery drawing the leader-line label layer OVER the
  image (numbered student / named teacher projections, maskable). The scene engine needs a raster
  background capability — add it minimally (an image layer under the primitives, or compositing in
  the asset build; your design call, documented).
- One flagship through the full path: generate/source a clean depictive base (e.g. a cell, an organ
  system, a simple apparatus — pick what you can generate RELIABLY without text artefacts), curate
  anchors, stage the worksheet. `intended_claim` recorded; SME checks the claim at the gate.

### I4 — PD Bildquellen (the 6th asset class; no generation involved)

- `tools/fetch_commons.py`: Wikimedia Commons fetch with machine-readable per-file rights (record
  licence verbatim; fail closed on unclear rights; PD-work ≠ PD-reproduction caution per item).
- An `ImageSource` model (the visual sibling of `AnnotatedText`): the image + a curated annotation
  ladder (Beschreibung → Analyse → Interpretation — the Bildquellenkritik ladder) → derived GPB/BE
  tasks whose answers come from the vetted annotations.
- Flagship: the **Isabey Wiener-Kongress engraving** — it ties into the existing Wiener-Kongress
  Sachverhalt and your own ANNO Quellenarbeit. Stage it for review.

## 4. Environment + discipline (unchanged from your last run, plus one lesson)

- `git fetch origin` first; branch from CURRENT `origin/main` (baseline: **702 passed, 1 skipped**).
  Work on `ext/images` (or per-task `ext/*`); never touch `main`; never push.
- Tests: `C:/Users/sebas/Desktop/TeachersAid/.venv/Scripts/python.exe -m pytest -q` from the repo
  root; bare `python` is the wrong interpreter; no `pip install`.
- Update CLAUDE.md/roadmap where the work genuinely warrants it. Write
  `Documents/external-experiment-report-images.md`: per task — files, test counts, decisions, SME
  flags, **every generated-binary path for Drive sync**, and every prompt used (prompts are
  provenance).
- Definition of done per task: suite green, lints in place and fixture-tested, staged items
  verify-clean, provenance/rights recorded, docs updated, report written.

## 5. Order and judgment

I1 → I2 → I4 → I3 is the de-risked order (I3 depends on I1's lane + your generation reliability;
I4 is independent and high-value if generation quality disappoints). You have licence to make design
calls within the invariants — document each one in the report the way you did last time. A clean,
honest partial (e.g. I1+I2+I4 shipped, I3 designed-but-not-built with reasons) beats a rushed
flagship that smuggles text into pixels.
