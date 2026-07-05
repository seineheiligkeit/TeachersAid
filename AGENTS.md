# AGENTS.md

Guidance for Codex (and any non-Claude agent runner) working in this repository.

**Read [`CLAUDE.md`](CLAUDE.md) — it is the operating manual, and everything in it applies here
verbatim.** This file used to be a parallel copy of that guide and drifted stale (it sat several
sessions behind); one manual is the fix. Where CLAUDE.md says subagents "run via Claude Code", read
"run via your agent runner" — the seams are runner-agnostic: emit the same `Gen*` JSON bodies and go
through the same `tools/ingest_*.py` validators.

Orientation order: [`CLAUDE.md`](CLAUDE.md) (operating manual) → [`project-handoff.md`](project-handoff.md)
(intent + session history) → [`Documents/README.md`](Documents/README.md) (the doc map) →
[`Documents/feature-roadmap.md`](Documents/feature-roadmap.md) (the plan).
