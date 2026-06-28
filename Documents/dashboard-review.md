# Dashboard review — structuring + homes for the new builds (28 Jun 2026)

A critical pass over the HITL dashboard (`api/app.py` + `api/static/index.html`) after the Oberstufe
expansion (Phase 0/1) and the parametric-Maths pack. What's well-placed, what now lacks a home, and a
prioritised restructuring list. **Statistik is already updated** (stage-aware — see below).

## Current state
Two review gates, one SPA; **10 tabs**: Brainstorm · Bausteine · Inhalte · Bibliothek · Arrangements ·
Abbildungen · Datensätze · Texte · Statistik · Insights. The Oberstufe content from the breadth push and
the parametric variants land as ordinary **content items** (Inhalte → Bibliothek) and **blocks**
(Bausteine), so they ARE reviewable today — but the dashboard doesn't yet *distinguish* stage or expose
the variant engine.

## ✅ Done this pass
- **Statistik is stage-aware** (`stats.py`): per-subject rows now exist for **both** Unterstufe and
  Oberstufe (keyed by stage; blocks routed by Klasse via `stufe_for_klasse`), a **Stufe** column + a
  per-stage summary line (`totals.by_stufe`) were added. Oberstufe-only subjects (Ethik, PUP, Informatik,
  Griechisch, DG, Haushaltsökonomie) now appear instead of being silently dropped.

## Gaps / structuring issues (prioritised)

**P1 — Stage (US/OS) is invisible in the review tabs.** Inhalte, Bausteine, and Bibliothek mix Unterstufe
and Oberstufe with no badge or filter; with ~16 US + ~14 OS subjects this gets crowded fast.
*Fix:* a small `stufe` badge on every item/block card (the data is on `meta.stufe` / block `klasse`), plus
a stage filter in the toolbar. Low risk, high legibility.

**P1 — The parametric variant engine has no UI home.** `library/templates.PARAM_TEMPLATES` (now incl. the
6 `mat-os-*` Oberstufe templates) + `orch.compose_variants` exist, but a teacher can only trigger them in
code. *Fix:* a **"Varianten"** surface — list the templates (subject/Klasse/Kompetenzbereich), an "N
Varianten erzeugen" button → `POST /api/variants` (wraps `compose_variants`) → a content item in Inhalte.
This is the single biggest "new build without a home". The engine is done; it needs ~1 endpoint + 1 tab.

**P2 — Semester/Kompetenzmodul + the descriptor/lehrstoff `kind` aren't surfaced.** Oberstufe blocks/
content carry `semester`/`kompetenzmodul`/`kind` but the cards don't show them. *Fix:* show "KM5 · 7. Kl"
and a descriptor/lehrstoff tag on Oberstufe items.

**P2 — Tab sprawl (10 flat tabs).** They fall into three natural groups: the **review pipeline**
(Brainstorm → Bausteine → Inhalte → Bibliothek → Arrangements → *Varianten*), the **source/asset
libraries** (Abbildungen · Datensätze · Texte · *Stimmen*), and **insight** (Statistik · Insights).
*Fix:* group the tab bar into these three clusters (section labels or a 2-level nav) so it scales.

**P3 — The audio voice library ("Stimmen") has no tab** (noted in `tts-audio-engine.md §7`). Deferred —
audio runs only on the workhorse PC — but it's the obvious next source-library tab when audio is wired.

## Recommended next (tomorrow's focused session)
1. The **Varianten** surface (P1) — gives the Maths pack a home and is mostly wiring.
2. **Stage badge + filter** (P1) across Inhalte/Bausteine/Bibliothek.
3. Group the tab bar into the three clusters (P2).

None of these block the breadth review: the Oberstufe worksheets are already in Inhalte/Bausteine and
countable in Statistik. This doc is the punch-list for the dashboard restructure.
