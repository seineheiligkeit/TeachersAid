# TeachersAid — Austrian Lehrplan-anchored Teaching-Material Generator

On-demand generator of **Austrian-curriculum-anchored teaching material** for AHS secondary schools.
A teacher inputs topic + grade + time → a ready-to-use, competence-anchored bundle that is correct by
construction, provably competence-aligned, and drops into the tools they already use.

**Status:** a runnable **demo** now exists (the `teachersaid/` Python package) on top of the design.
Source of truth for the data model is **schema v0.3** (+ the additive v0.4 deltas, implemented);
v0.5 is specced but out of scope. Working language is English; the product's output is German.

## Run the demo

```bash
pip install -e .            # or: pip install pydantic fastapi uvicorn anthropic reportlab matplotlib pillow pyyaml pymupdf
python -m pytest -q         # 30 tests, all offline (no API key needed)
python -m teachersaid       # dashboard at http://127.0.0.1:8000
```

In the dashboard: create a request (or **Batch über Kompetenzkarte**) → approve the **idea** (Gate 1) →
the engine generates, verifies, assembles and renders → review the **content** (Gate 2) with the derived
Nachweis (coverage + gaps), the Tiefenprofil, and the embedded student/teacher/homework PDF → approve into
the material library. **Request changes** re-queues with your feedback.

- **With `ANTHROPIC_API_KEY` set** (`claude-opus-4-8`, adaptive thinking), generation is live for any
  curated subject/topic. **Without a key**, the Physik *Strahlung* hero falls back to the hand-authored
  content object so the whole loop is demoable offline.
- Generated PDFs + rasters land under `runs/`.

### Architecture (engine = `teachersaid/`)

`schema/` (typed model, v0.3+v0.4) → `grounding/` (curated Lehrplan facts) → `pipeline/`
(**resolve → plan → generate → verify → assemble(+derive) → render**) → `rendering/` (pure ReportLab
projections of one `WorksheetContent`, QA-rastered) → `store/` + `api/` (two-stage HITL dashboard).
The dependency rule (`rendering` imports only `schema`) makes the mismatched-answer-key bug structurally
impossible. See **[CLAUDE.md](CLAUDE.md)** for the codebase guide,
**[Documents/implementation-notes.md](Documents/implementation-notes.md)** for what was built, and the
design docs below for the why.

## Start here

Read **[project-handoff.md](project-handoff.md)** first — it's the single read-me-first document.
Then follow the reading order it gives:

1. [project-handoff.md](project-handoff.md) — master takeover doc
2. [Documents/platform-definition.md](Documents/platform-definition.md) — positioning, scope, Teachino gap-check
3. [Documents/lehrplan-bundle-schema-v0.3.md](Documents/lehrplan-bundle-schema-v0.3.md) — the data model (source of truth)
4. [Documents/subject-coverage-audit.md](Documents/subject-coverage-audit.md) — 16-subject audit + per-subject competence models
5. [Documents/schema-roadmap-v0.4-v0.5.md](Documents/schema-roadmap-v0.4-v0.5.md) — v0.4 deltas + v0.5 Lernarrangement
6. [Documents/worked-examples-three.md](Documents/worked-examples-three.md) — content-object examples validating v0.4
7. [Documents/implementation-notes.md](Documents/implementation-notes.md) — **what the demo build is and how it maps to the design**
8. [CLAUDE.md](CLAUDE.md) — codebase guide for working in `teachersaid/`

Reference material: [strahlung-rack.md](Documents/strahlung-rack.md), [zwentendorf-faden.md](Documents/zwentendorf-faden.md), and the Strahlung PDFs.

## Not in the repo

The Lehrplan source (`RIS Dokument.html`, ~2.7 MB) and its 104 extracted images are kept locally only
(see [.gitignore](.gitignore)); the grounded facts derived from them live in the design docs. The
code-generated `spectrum.png`/`spectrum.svg` EM-spectrum figure referenced by the handoff is not yet
present and can be regenerated with matplotlib.
