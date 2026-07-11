# Illustration style contract

**Version:** `teachersaid-illustration-v1`. This contract governs every synthetic raster that enters
the corpus. The exact strings also live in `teachersaid/pipeline/illustration_style.py`; a generation
record stores both strings verbatim so later style changes never rewrite history.

## Locked style prefix

> TeachersAid house illustration, version v1. Flat to lightly shaded editorial illustration for
> Austrian AHS learners aged 10 to 14; friendly, calm and precise without looking childish or
> corporate; clear silhouettes, restrained detail, generous whitespace, print-first composition;
> Central-European context when a setting is implied. Use the house palette: ink #1f3a52 and
> #33506e, warm accent #b5651d, green #2e6b3a, muted blue #4f6f8f, paper #f4f1ea.

Standing negative prompt:

> No readable text, letters, numbers, labels, captions, signs, logos, brands, watermarks, arrows,
> charts, maps, formulae, task data, photorealistic people, real-person likenesses, copyrighted
> characters, neon colours, heavy gradients, clutter, or decorative details unrelated to the
> requested context.

The request-specific prompt follows the prefix; the standing negative prompt accompanies it. If a
generator has no separate negative-prompt field, append it as an explicit constraint and record that
fact. If it exposes no seed, record `replayable: false` rather than inventing one.

## Age and warmth

The register is **ages 10 to 14**: confident shapes, recognisable contexts and one or two delightful details,
never babyish faces or corporate stock-art polish. Warmth means paper-toned light, humane scale,
rounded-but-not-toy-like forms, restrained texture, and the ink/warm-accent/green/muted-blue palette.
It does not mean visual noise. Austrian or Central-European architecture and everyday objects may set
the scene; flags, brands and nationalistic shorthand do not.

## Didactic restraint

- **Relevance:** a spot or backdrop must depict the material's actual context. Pure mood art is
  limited to the header-vignette slot. No pixel may carry a datum used by a task.
- **Density:** at most one header vignette and two small contextual spots per worksheet; Oberstufe is
  sober or image-free by default. Clear educational figures do not consume this decorative budget.
- **Placement:** keep images outside solving and writing zones. Decorative details may frame content
  but may not compete with prompts, source cards, tables or answer spaces.

## Review contract

Every request is a candidate set. The Abbildungen grid shows all candidates with their claim and
preflight findings; the SME chooses one or none. Decorative review checks content-freedom, relevance
and house style. Depictive review additionally checks the declared `intended_claim`, plausibility,
anachronism/anatomy, and the absence of text, numbers, labels and arrows.

Offline preflight catches low resolution, suspicious alpha and weak grayscale contrast. Its optional
edge-density heuristic can only flag page-like high-frequency regions: it cannot prove an image is
text-free and can mistake natural texture for glyphs. Visual inspection is therefore mandatory.

Run `tools/illustration_specimen.py` to build a contact sheet from **approved** library assets. The
sheet is a drift detector, not an approval mechanism; only the AssetStore status is authoritative.
