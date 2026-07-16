# Content-campaign workflow — how to run a breadth generation pass

The repeatable process for a **content pass**: generate many worksheets across a stufe's subjects
via subagents, validate them through the real seam, and stage them for HITL review. This is the
**corpus loop** (invariants §10) — subagents are the generator (they run in Claude Code, no
`ANTHROPIC_API_KEY`); nothing they produce reaches delivery ungated. It builds on the breadth seam
described in CLAUDE.md ("Breadth generation — subagents → ingest"); this doc is the *operator's
runbook* for driving one end to end.

## The pipeline (five steps)

```
1. briefs     tools/breadth_prompt.py --stufe … [--subjects …] [--n N] --gen-dir <fresh>
2. fan out    one Opus subagent per subject → each writes N JSON files to runs/ingest/<gen-dir>/
3. track      tools/campaign_status.py --dir runs/ingest/<gen-dir>       (the babysitter)
4. gate       tools/ingest_batch.py --dry-run --dir runs/ingest/<gen-dir>  (resolve→assemble→verify)
5. stage      tools/ingest_batch.py --dir runs/ingest/<gen-dir>          (persist → Prüfen queue)
```

Steps 1, 3, 4, 5 are deterministic local Python (no API key, no network). Step 2 is the only
generative step. **Persist + git commit stay in the main session** (judgment calls), never inside a
fan-out.

## Step 1 — briefs (grounded, with Korpus-Kontext)

`tools/breadth_prompt.py` writes one `runs/ingest/prompt_<CODE>.md` per subject + a `manifest.json`.
Each brief is self-contained: verbatim competences grouped by Kompetenzbereich, allowed
dims/kinds, the full allowed figure-generator vocabulary, the exact output JSON shape + a worked
example, the language clause for target-language subjects — **and a `## Korpus-Kontext` section**
listing the worksheets already in the review store for that (subject, stufe) so agents pick NEW
angles ("automatically ingests what we already have"), plus a one-line coverage summary.

- `--stufe Unterstufe|Oberstufe` — the subject registry + Klasse range follow the stufe
  (`SUBJECT_SETS` in the tool; all current Pflichtgegenstände are `kb`-anchored).
- `--subjects MAT,PHY` — a subset by code (default: all subjects for the stufe).
- `--n N` — Kernfragen (worksheets) per subject (default 2).
- `--gen-dir NAME` — **always a FRESH dir per pass** (see invariants below).

## Step 2 — fan out (one Opus subagent per subject)

Spawn one background Opus subagent per subject (the `Agent` tool, `model: "opus"`,
`subagent_type: "general-purpose"`). The agent's contract — bake all of it into the prompt:

- Read the brief `runs/ingest/prompt_<CODE>.md` IN FULL; it is the single source of truth.
- Read the `<CODE>` slice of the Korpus-Kontext (or `runs/ingest/existing_os_titles.json` if present)
  and choose N genuinely different NEW Kernfragen.
- Write EXACTLY N files `runs/ingest/<gen-dir>/<CODE>_1.json … _N.json`, each **exclusively** one
  JSON object (no prose, no ``` fences). Tip that eliminated JSON slips this session: *build the
  object in memory and `json.dump` it.*
- Strict JSON; German quotes inside values are `„…"` (typographic) or escaped `\"`, never a bare `"`.
- Every task `serves` a VERBATIM competence id from the brief; `dimensions` ⊆ allowed; `kind` ∈
  allowed; `cognitive_level` rises (include analyze/evaluate/create); 5–7 tasks + ≤1 info block.
- Figures only where they help: DATA → `body.data_figures` with an `intent`; STRUCTURE →
  `body.assets` with an allowed generator. A figure must never reveal the asked answer.
- Student text never mentions competence IDs / dimensions / "Lehrplan"; each section carries the
  teacher layer (throughline/talking_points/extensions). Quality bar = the **blackboard test**.

Send all subagents in one message so they run concurrently. They notify on completion.

## Step 3 — track (the babysitter)

`tools/campaign_status.py --dir runs/ingest/<gen-dir>` reports, per subject: files present, how many
load cleanly (through the same repair the gate applies), how many are committed, and a
complete/partial/missing/invalid roll-up with the next suggested command. Run it whenever a batch of
completion notifications lands; commit completed subjects as they finish.

## Step 4 — gate (dry-run) · Step 5 — persist

`ingest_batch.py --dry-run --dir <dir>` runs `resolve → to_canonical → build assets → assemble →
verify` per file and prints `OK/!!` with problem/warning/coverage counts — **the authoritative
gate**. `problems=0` ⇒ clean (warnings are advisory: readability/WSTF, difficulty-band, number/prose
lints). Without `--dry-run` it persists: stages a pending content item + harvests blocks for HITL
review (figure-bearing sheets rendered for Vorschau). New review items land in **Prüfen**.

## Invariants & lessons (do not relearn these the hard way)

- **A pass writes to a FRESH `--gen-dir`.** Review items are `create`d, not upserted — re-ingesting a
  dir already staged would duplicate every item. (`gen/` = US 06-25; `gen_os/` = OS 06-28; `gen_os_2/`
  = OS 07-14; pick the next unused name.)
- **JSON slip ⇒ extend the normalizer, never re-spawn.** `ingest_batch.py`'s first-pass normalizer
  deterministically absorbs the recurring agent slips (the `„…"` open/straight-close quote repair,
  literal control chars, info-blocks shaped like tasks, `answer_text`→`answer_key`, German rubric
  keys, off-enum relations, nested MC). A file that is invalid raw JSON is often clean after repair —
  the dry-run is the arbiter. Only re-generate if the dry-run *also* rejects it.
- **Salvage partials before re-spawning.** A subagent that "failed" (e.g. hit a session limit on
  wrap-up) has often already written valid files — `campaign_status` shows them. Commit what's valid;
  re-generate only the genuinely missing/invalid sheets (a single-sheet fixer agent is fine).
- **Commit per completed subject.** In an ephemeral remote container, committed+pushed is the only
  durable state; commit each subject's files as they land so a later failure costs nothing.
- **Persist only after a clean dry-run**, and keep persist + commit in the main session.

## Targeting modes

- **Uniform breadth** (default): N fresh Kernfragen per subject, agents only avoid the Korpus-Kontext
  titles. Best when a stufe is thin or you want range.
- **Gap-directed** (`--gaps`): aim each brief's Kernfragen at the coverage map's worst
  `leer`/`teil` (Klasse·Kompetenzbereich) cells for the stufe instead of uniform breadth. Best marginal
  value against an already-populated corpus. Per subject the tool queries `stats.campaign_gaps`, picks
  the worst cells **worst-first** (`leer` before `teil`, then by prerequisite leverage
  `blocks_dependents`), distributes the N Kernfragen over them (`min(N, #cells)` cells, worst cells take
  any remainder), and injects a `## Ziel-Lücken` section that lists each target cell (Klasse · KB ·
  Status) **with its verbatim competence ids** and a hard rule: every Kernfrage MUST anchor in its
  assigned cell (`kompetenzbereich`/`klasse` set, each task `serves` an id from THAT cell), driving the
  cell toward green. A subject with no open cell is **honestly skipped** (no brief written; recorded in
  the manifest as `"skipped": true`). The manifest stamps `"targeting": "uniform"|"gaps"` and, per
  targeted subject, the chosen `targets` (so `campaign_status.py` and the operator see what was aimed
  at; skipped subjects are excluded from the babysitter's expected set). Uniform output is unchanged.

  ```
  python tools/breadth_prompt.py --stufe Oberstufe --subjects ETH,MAT --n 3 --gaps --gen-dir gen_os_3
  ```

## History

- **2026-07-14, OS pass (`gen_os_2/`)** — first run of this workflow's shape: 14 Opus subagents,
  28 worksheets, all verify-clean, staged c0203–c0230. Surfaced every lesson above (session-limit
  mid-run → salvaged CHE/GPB, auto-repaired a PUP quote slip, re-spawned FSP/HOE). Tooling
  (parameterized briefs + Korpus-Kontext + `campaign_status.py` + this doc) was extracted right after.
