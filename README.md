# TeachersAid — Austrian Lehrplan-anchored Teaching-Material Generator

On-demand generator of **Austrian-curriculum-anchored teaching material** for AHS secondary schools.
A teacher inputs topic + grade + time → a ready-to-use, competence-anchored bundle that is correct by
construction, provably competence-aligned, and drops into the tools they already use.

**Status:** design phase (no engine/UI yet). Source of truth for the data model is **schema v0.3**;
v0.4 and v0.5 are specced in the roadmap. Working language is English; the product's output is German.

## Start here

Read **[project-handoff.md](project-handoff.md)** first — it's the single read-me-first document.
Then follow the reading order it gives:

1. [project-handoff.md](project-handoff.md) — master takeover doc
2. [Documents/platform-definition.md](Documents/platform-definition.md) — positioning, scope, Teachino gap-check
3. [Documents/lehrplan-bundle-schema-v0.3.md](Documents/lehrplan-bundle-schema-v0.3.md) — the data model (source of truth)
4. [Documents/subject-coverage-audit.md](Documents/subject-coverage-audit.md) — 16-subject audit + per-subject competence models
5. [Documents/schema-roadmap-v0.4-v0.5.md](Documents/schema-roadmap-v0.4-v0.5.md) — v0.4 deltas + v0.5 Lernarrangement
6. [Documents/worked-examples-three.md](Documents/worked-examples-three.md) — content-object examples validating v0.4

Reference material: [strahlung-rack.md](Documents/strahlung-rack.md), [zwentendorf-faden.md](Documents/zwentendorf-faden.md), and the Strahlung PDFs.

## Not in the repo

The Lehrplan source (`RIS Dokument.html`, ~2.7 MB) and its 104 extracted images are kept locally only
(see [.gitignore](.gitignore)); the grounded facts derived from them live in the design docs. The
code-generated `spectrum.png`/`spectrum.svg` EM-spectrum figure referenced by the handoff is not yet
present and can be regenerated with matplotlib.
