# External experiment report — Wave B image program

Date: 2026-07-11  
Branch: `ext/images`, from fetched `origin/main` at `213cbf1d4a72e1d89f9c94c18f7bb00f82e0d92c`  
Order: I1 → I2 → I4 → I3  
Baseline: 702 passed, 1 skipped  
Final: 734 passed, 1 skipped; one existing Starlette deprecation warning  
Tests are offline.

## Outcome

Wave B is implemented end to end. The system now separates decorative, depictive
and content claims; stores honest agent-time generation provenance; performs
deterministic raster preflight; reviews best-of-N sets; adds optional reviewed
warmth without putting task facts in pixels; ingests Commons images with independent
work/reproduction rights; derives ImageSource tasks from annotations; and overlays
code-authored leaders and labels on a vetted raster background.

All twelve generated candidates remain `in_review`. Stable ids are provisional
integration choices, not SME approval. Content approval now rejects an unapproved
file-backed dependency.

## I1 — review gates

Delivered:

- `decorative | depictive | content` lanes and mandatory depictive `intended_claim`;
- hard rejection of synthetic content pixels;
- `GenerationRecord`: origin, generator/model disclosure, full prompt, negative
  prompt, style, date, parameters, and forced `replayable=false` without a seed;
- offline resolution, alpha, grayscale/photocopy, and conservative text-risk checks;
- coherent candidate sets, choose-one/reject-all actions, and Abbildungen grid;
- locked v1 style contract and approved-only specimen contact sheet.

Files: `schema/assets.py`, `pipeline/media_policy.py`, `pipeline/image_lint.py`,
`pipeline/illustration_style.py`, `pipeline/orchestrator.py`, `store/assetstore.py`,
`api/app.py`, `api/static/index.html`, `Documents/illustration-style-contract.md`,
`tools/illustration_specimen.py`, `tests/test_media_policy.py`,
`tests/test_image_program.py`.

Decision: the no-text heuristic is advisory; edge density cannot prove absence of
pseudo-glyphs. Low resolution blocks approval; photocopy/alpha/text findings do not.

SME: confirm the v1 direction, inspect every candidate for pseudo-text/task facts,
and make the actual best-of-N selections.

## I2 — warmth without content smuggling

Delivered:

- `AnnotatedText.backdrop_asset` → `InfoBlock.backdrop_asset_ref`;
- optional Realie material-card backdrop, pure over an id→path map;
- stable ids `img-realie-bahnhof-backdrop` and `img-realie-cafe-backdrop`;
- one explicit `WorksheetContent.theme_asset`, unset by default;
- orchestration resolves only approved AssetStore files for normal delivery;
- missing files degrade to the original text-only layout.

Files: `schema/texts.py`, `schema/blocks.py`, `schema/worksheet.py`,
`pipeline/text_tasks.py`, `rendering/_document.py`,
`rendering/blocks_to_flowables.py`, `rendering/reportlab_base.py`,
`library/realie_bahnhof.py`, `library/realie_cafe.py`, `store/textstore.py`,
`runs/texts/fs1-realie-bahnhof.json`, `runs/texts/fs1-realie-cafe.json`,
`tests/test_image_warmth.py`.

Provisional choices: Bahnhof #2, Café #2, theme #3. Timetables, places, prices
and answers remain live text. The two provisional student pages were visually
inspected; the image stays a small atmosphere band and layout is clean.

SME: choose/reject both backdrops; use a theme vignette only if it earns its density.

## I4 — Commons and ImageSource

Delivered:

- fail-closed `tools/fetch_commons.py` using machine `imageinfo/extmetadata`;
- independent work copyright and exact-reproduction rights;
- `ImageSource` with Beschreibung → Analyse → Interpretation annotations;
- annotation-derived GPB/BE tasks and answers;
- first-class store and API list/detail/file/approve/reject/compose routes;
- archival original preserved; 1400px print derivative keeps PDFs practical.

Flagship: Bernhard J. Dondorf after Jean Baptiste Isabey, Rijksmuseum
RP-P-OB-87.274 via Commons. SHA-1
`305042160df70540a974b9f6efe4b6ede3979bab`, 6474×5356 JPEG. Work is PD-p.m.a.
(Dondorf died 1902); exact reproduction is separately CC0. It links to
`sv-wiener-kongress` and `deu-anno-lehrertag-1871`.

Source record: `runs/image_sources/gpb-isabey-wiener-kongress.json` (`in_review`).
Staged worksheet: `runs/store/c0200.json` (`pending`, clean verification).

Files: `schema/image_sources.py`, `store/imagesourcestore.py`,
`pipeline/image_sources.py`, `library/image_sources.py`, `tools/fetch_commons.py`,
`tests/fixtures/commons_imageinfo.json`, `tests/test_fetch_commons.py`,
`tests/test_image_sources.py`.

Visual QA: both student pages inspected; source, attribution and staged responses
are legible with no clipping.

SME: confirm the three annotation answers. The object is a Dondorf lithograph after
Isabey, not a photograph. Commons raw `Copyrighted=True` and CC0 are both retained.
Original title text in a sourced print is legitimate; the generated-pixel rule is unaffected.

## I3 — hybrid raster plus code

Delivered:

- `RasterImage` Scene primitive with explicit file, extent, alpha and z-order;
- labeled-parts background resolution by AssetStore id;
- generated flower depiction under seven curated anchors;
- numbered student and named teacher projections from one `parts` list;
- content approval blocked until the depictive background is independently approved;
- figure-heavy teacher solutions paginate without an orphan heading.

Flagship asset: `img-bio-flower-cutaway` (`in_review`). Intended claim:
“Stylized longitudinal section of one generalized bisexual flower, showing petals,
sepals, stamens, and a continuous central pistil with stigma, style, ovary, and ovules.”
Staged worksheet: `runs/store/c0201.json` (`pending`, clean verification).

Files: `pipeline/scene.py`, `pipeline/labeled_diagram.py`, `pipeline/assets.py`,
`library/bio_bluete_hybrid.py`, `library/__init__.py`,
`tests/test_labeled_diagram.py`, `tests/test_hybrid_image.py`.

Visual QA: student page and all teacher pages inspected. The first render exposed an
orphan heading; pagination was corrected and re-rendered. Final labels and leaders
are clean and unclipped.

SME: validate the depictive claim, each anchor, and the “generalized flower” limitation.

## Every generation prompt used

Exactly twelve built-in generation calls were made; no edits and no CLI fallback.
`tools/stage_image_program.py` is the canonical tracked manifest and contains every
full prompt verbatim, including scene, medium, composition, palette, output intent,
scientific constraints, and all negative constraints. The same exact full prompt is
stored in each asset JSON's `generation.prompt`, so it travels with the candidate:

1. Bahnhof #1 — `tools/stage_image_program.py:35` — `img-realie-bahnhof-backdrop-cand-1.json`.
2. Bahnhof #2 — line 44 — `img-realie-bahnhof-backdrop.json`.
3. Bahnhof #3 — line 53 — `img-realie-bahnhof-backdrop-cand-3.json`.
4. Café #1 — line 73 — `img-realie-cafe-backdrop-cand-1.json`.
5. Café #2 — line 82 — `img-realie-cafe-backdrop.json`.
6. Café #3 — line 91 — `img-realie-cafe-backdrop-cand-3.json`.
7. Theme #1 — line 111 — `img-theme-learning-vignette-cand-1.json`.
8. Theme #2 — line 120 — `img-theme-learning-vignette-cand-2.json`.
9. Theme #3 — line 129 — `img-theme-learning-vignette.json`.
10. Flower #1 — line 149 — `img-bio-flower-cutaway-cand-1.json`.
11. Flower #2 — line 159 — `img-bio-flower-cutaway-cand-2.json`.
12. Flower #3 — line 169 — `img-bio-flower-cutaway.json`.

Shared style and negative prompts are versioned in
`teachersaid/pipeline/illustration_style.py` and copied into every record. The built-in
tool exposed no model id or seed; metadata says so and marks all generations non-replayable.

## Binary paths for Drive sync

All workspace paths below are relative to
`C:\Users\sebas\Desktop\TeachersAid`; binaries are git-ignored.

Raw candidates (12):

- `runs/ingest/image_program/img-realie-bahnhof-backdrop-cand-{1,2,3}.png`
- `runs/ingest/image_program/img-realie-cafe-backdrop-cand-{1,2,3}.png`
- `runs/ingest/image_program/img-theme-learning-vignette-cand-{1,2,3}.png`
- `runs/ingest/image_program/img-bio-flower-cutaway-cand-{1,2,3}.png`

Durable candidates/stable copies (16):

- `runs/assets_lib/files/img-realie-bahnhof-backdrop-cand-{1,2,3}.png`
- `runs/assets_lib/files/img-realie-bahnhof-backdrop.png`
- `runs/assets_lib/files/img-realie-cafe-backdrop-cand-{1,2,3}.png`
- `runs/assets_lib/files/img-realie-cafe-backdrop.png`
- `runs/assets_lib/files/img-theme-learning-vignette-cand-{1,2,3}.png`
- `runs/assets_lib/files/img-theme-learning-vignette.png`
- `runs/assets_lib/files/img-bio-flower-cutaway-cand-{1,2,3}.png`
- `runs/assets_lib/files/img-bio-flower-cutaway.png`

Commons binaries (2):

- `runs/ingest/image_sources/gpb-isabey-wiener-kongress.jpg`
- `runs/image_sources/files/gpb-isabey-wiener-kongress.jpg`

Staged renders (12):

- `runs/store/c0200/{student,teacher,homework}.pdf`
- `runs/store/c0200/assets/gpb-isabey-wiener-kongress-image.png`
- `runs/store/c0200/raster/student.p{1,2}.png`
- `runs/store/c0201/{student,teacher,homework}.pdf`
- `runs/store/c0201/assets/bio-flower-parts-{student,teacher}.png`
- `runs/store/c0201/raster/student.p1.png`

Built-in recovery originals outside the workspace (12):

- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-ea8fac06-e08b-4261-b738-72767cb67529.png`
- `...\exec-ae7627f6-72ea-4d52-8107-9943be021025.png`
- `...\exec-ba8543a3-f1b8-48cd-b590-2d96248100f5.png`
- `...\exec-ea0cd121-3205-496e-8f78-f3d832550933.png`
- `...\exec-70f2d5da-6ba5-4cf7-9243-a3e159cdf788.png`
- `...\exec-9834685e-cf10-4d0f-b6de-7751d8f78031.png`
- `...\exec-e8564fb7-85ed-4830-84cc-c6578003e652.png`
- `...\exec-61862786-f8aa-4bcb-8708-8477f6e8bc49.png`
- `...\exec-54052b13-0186-471e-a987-e46e75199f4a.png`
- `...\exec-2b428a8e-3748-43f5-9a38-994198dce968.png`
- `...\exec-a7265d55-4ff1-4050-83f8-45cc65dd9344.png`
- `...\exec-812ff5cd-8f93-4064-8c53-c15e21174c90.png`

Brace notation above enumerates each literal numbered file. Temporary QA rasters under
`tmp/pdfs/` are reproducible and intentionally excluded from sync.

### Literal expansion (authoritative sync list)

- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-realie-bahnhof-backdrop-cand-1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-realie-bahnhof-backdrop-cand-2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-realie-bahnhof-backdrop-cand-3.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-realie-cafe-backdrop-cand-1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-realie-cafe-backdrop-cand-2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-realie-cafe-backdrop-cand-3.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-theme-learning-vignette-cand-1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-theme-learning-vignette-cand-2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-theme-learning-vignette-cand-3.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-bio-flower-cutaway-cand-1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-bio-flower-cutaway-cand-2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_program\img-bio-flower-cutaway-cand-3.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-realie-bahnhof-backdrop-cand-1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-realie-bahnhof-backdrop-cand-2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-realie-bahnhof-backdrop-cand-3.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-realie-bahnhof-backdrop.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-realie-cafe-backdrop-cand-1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-realie-cafe-backdrop-cand-2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-realie-cafe-backdrop-cand-3.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-realie-cafe-backdrop.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-theme-learning-vignette-cand-1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-theme-learning-vignette-cand-2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-theme-learning-vignette-cand-3.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-theme-learning-vignette.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-bio-flower-cutaway-cand-1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-bio-flower-cutaway-cand-2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-bio-flower-cutaway-cand-3.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\assets_lib\files\img-bio-flower-cutaway.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\ingest\image_sources\gpb-isabey-wiener-kongress.jpg`
- `C:\Users\sebas\Desktop\TeachersAid\runs\image_sources\files\gpb-isabey-wiener-kongress.jpg`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0200\student.pdf`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0200\teacher.pdf`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0200\homework.pdf`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0200\assets\gpb-isabey-wiener-kongress-image.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0200\raster\student.p1.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0200\raster\student.p2.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0201\student.pdf`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0201\teacher.pdf`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0201\homework.pdf`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0201\assets\bio-flower-parts-student.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0201\assets\bio-flower-parts-teacher.png`
- `C:\Users\sebas\Desktop\TeachersAid\runs\store\c0201\raster\student.p1.png`

Recovery originals, fully expanded:

- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-ea8fac06-e08b-4261-b738-72767cb67529.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-ae7627f6-72ea-4d52-8107-9943be021025.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-ba8543a3-f1b8-48cd-b590-2d96248100f5.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-ea0cd121-3205-496e-8f78-f3d832550933.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-70f2d5da-6ba5-4cf7-9243-a3e159cdf788.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-9834685e-cf10-4d0f-b6de-7751d8f78031.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-e8564fb7-85ed-4830-84cc-c6578003e652.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-61862786-f8aa-4bcb-8708-8477f6e8bc49.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-54052b13-0186-471e-a987-e46e75199f4a.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-2b428a8e-3748-43f5-9a38-994198dce968.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-a7265d55-4ff1-4050-83f8-45cc65dd9344.png`
- `C:\Users\sebas\.codex\generated_images\019f4fbf-9bb9-7593-8d34-00b5439b7b70\exec-812ff5cd-8f93-4064-8c53-c15e21174c90.png`

## Verification and honest leftovers

- Baseline full suite: 702 passed, 1 skipped.
- Focused integrated image suite: 39 passed.
- Final full suite: 734 passed, 1 skipped.
- `git diff --check`: clean except configured CRLF conversion notices.
- I1 dashboard JavaScript: `node --check` passed.
- No LoRA/fine-tune (B4 out of scope).
- Human selection and factual SME review remain intentionally open.
- Generated binaries are not in git and must be synced using the paths above.
