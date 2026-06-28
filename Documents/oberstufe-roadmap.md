# Oberstufe Roadmap — extending TeachersAid to AHS Sek II (5.–8. Klasse)

**Status: planning + Phase 0 in progress (28 June 2026).** Output of a structured brainstorming pass
(5 subagent clusters over the full Oberstufe Lehrplan). Companion to
[feature-roadmap.md](feature-roadmap.md) (the Unterstufe/forward backlog) and
[project-handoff.md](../project-handoff.md) (intent). The Unterstufe remains the shipped product; this
doc is the deliberate, sequenced expansion upward.

---

## 0 · The headline finding

The handoff deferred the Oberstufe on the assumption it was **"largely legacy prose."** That is **partly
outdated.** The consolidated RIS Lehrplan (same `Documents/RIS Dokument.html`, *Achter Teil → A.
Pflichtgegenstände → 2. Oberstufe*) organises the Oberstufe into **semesterised Kompetenzmodule
(KM 3–7)** across grades 5–8, fully competence-oriented. **Physik reuses the exact W/E/S model** of the
Unterstufe, with the same Anforderungsbereiche. The strategic consequence: this is **extend-don't-rebuild.**
Our competence-anchoring + correct-by-construction engine carries upward with minimal schema change, and
the Oberstufe's higher cognitive demand (Reflexion/Problemlösung) plays *to* our depth-ladder strength.

---

## 1 · What we learned (per cluster)

- **Competence models are familiar, with one trap.** W/E/S holds verbatim for **Physik + Biologie**
  (Biologie even pre-numbers competences **W1–S5** — free clean grounding). **Chemie deviates**: it uses a
  *dreidimensionales Modell* — Handlungsdimension *Wissen organisieren / Erkenntnisse gewinnen /
  Konsequenzen ziehen* + *Niveau 1/2* — **not** W/E/S. Encoding it as W/E/S would make the derived Nachweis
  cite dimensions that do not exist in the Chemie Lehrplan.
- **Mathematik** uses a **3-dimensional model** (Inhalts- / Handlungs- / Komplexitätsdimension) and is the
  single richest fit for the **parametric engine** (Analysis, Stochastik, Vektoren, LGS — symbolically
  solvable, correct-by-construction, attacking the incumbent's worst documented failure: wrong AHS math).
- **Six Oberstufe-only subjects** appear: **Ethik, Psychologie und Philosophie, Informatik (Pflicht 5. Kl),
  Griechisch, Darstellende Geometrie, Haushaltsökonomie und Ernährung.**
- **Languages** extend strongly: annotated-text engine → Deutsch epoch literature (PD through ~7. Kl;
  Schnitzler enters PD 1 Jan 2026), **Latein** (all-PD, lowest-risk/highest-leverage), **Griechisch**
  (clean reuse of the Latein engine; needs a polytonic-Greek font). Fremdsprache is reading/writing-strong
  but audio-bound at B2 (TTS realism, not content, is the bottleneck; ceiling is B2, no C1).
- **Social sciences** extend strongly: **GWB** → data layer (richer quantitative competences), **GPB** →
  history/expression-provenance across PD epochs.
- **The standout new idea is general, not ethics-only.** A **structured-argument / dilemma object** serves
  Ethik, PUP, GPB controversies, GWB policy trade-offs, Biology bioethics, the sciences' *Standpunkte
  bewerten*, Deutsch Erörterung, **and Informatik** (logic/KI — where it gets an *auto-verifiable*
  truth-table/fallacy corner). It turns our existing neutrality norm ("steel-man each side, no verdict")
  into a **schema invariant.**
- **Honest exclusions (no manufactured fit):** **Bewegung und Sport is out** (performed subject, wrong
  tool). **Musik / Kunst** stay marginal (thin printable slivers; Kunst is rights-blocked behind the
  deferred sourced-image lane). **Chemie's** best quantitative content needs a chemistry engine we don't
  have yet (bigger lift).

## 2 · Opportunity map

| Subject | Fit | Primary engine | Reuse vs. new |
|---|---|---|---|
| Mathematik | Strong | Parametric (sympy) | **Reuse** — the goldmine |
| GWB | Strong | Grounded data layer | Reuse |
| GPB | Strong | History/expression-provenance | Reuse |
| Latein | Strong | Annotated texts | Reuse (all-PD) |
| Griechisch | Strong | Annotated texts | Reuse + polytonic-Greek font |
| Haushaltsökonomie (theory) | Strong | Data layer + parametric | Reuse |
| Physik | Strong | Parametric | Reuse + **units engine** |
| Biologie | Strong | Data layer + parametric | Reuse + **genetics recipe** |
| Deutsch | Strong | Annotated texts | Reuse + **Zitatrecht excerpts** |
| Informatik (Prakt. core) | Partial→Strong | Parametric (execution-verified) | New recipe type + sandbox |
| Ethik / PUP | Strong-with-new-class | **Dilemma object** | **New asset class** |
| Darstellende Geometrie | Partial | Code-gen figures | **New 3D-projection backend** |
| Chemie | Partial | (none yet) | New chemistry engine (big) |
| Fremdsprache | Partial | Audio/TTS | Reuse; realism-bound |
| Musik / Kunst | Marginal | — | Parked |
| Bewegung und Sport | Out | — | — |

---

## 3 · The phased roadmap

### Phase 0 — The enabler (✅ DONE, 28 Jun 2026; gated everything else)
Built the **Oberstufe competence catalog** + **semester/Kompetenzmodul-aware resolution & Fassung**.
Delivered: `lehrplan/oberstufe/*.json` (18 subjects, ~1360 typed `descriptor`/`lehrstoff` competences)
via `tools/parse_lehrplan_oberstufe.py`; `_meta.json` + `subject_models.json` via
`tools/build_oberstufe_meta.py`; stage-aware `lehrplan_store`/`resolve` (`stufe_for_klasse`,
`ResolvedCompetence.semester/kompetenzmodul/kind`, `resolve_grade(kompetenzmodul=, semester=)`); locked by
`tests/test_oberstufe.py`. Chemie's model is WO/EG/KZ (not W/E/S). Original plan:
- Re-parse the RIS Oberstufe (extend `tools/parse_lehrplan.py`, which is Unterstufe-scoped and stops at
  the `2. Oberstufe` marker; recover the formulae/italics the quick extraction dropped).
- Per-subject `SubjectCompetenceModel`s for the Oberstufe — **mirroring the Lehrplan's own dimensions**
  (decision below), incl. **Chemie's non-W/E/S model** and the **semesterised Kompetenzmodul** structure.
- Engine: semester/KM as a resolution key + Fassung handling in `grounding/lehrplan_store.py` / `resolve.py`.
- *Strategic timing:* the current Fassung expires **2026-08-31** and the 2026/27 refresh was already
  deferred — fold the Oberstufe parse into that refresh rather than parsing twice.
- *Effort: M · Risk: Low · This is the critical path.*

### Phase 1 — Reuse proven engines (highest ROI, lowest risk)
- **Mathematik parametric pack — ✅ DONE (28 Jun 2026).** 6 sympy recipes + 6 `mat-os-*` templates
  (Kurvendiskussion, bestimmtes Integral, LGS 2/3 Var., Binomialverteilung, Skalarprodukt+Winkel) across
  all 4 Inhaltsbereiche; correct-by-construction, renders SME-clean, Nachweis binds the served OS
  competence. *Next here:* more recipes (Kettenregel, Extremwertaufgaben, Bayes, Vektoren ℝ³,
  Kegelschnitte) + a "Varianten erzeugen" dashboard surface.
- **Oberstufe breadth push — in progress (28 Jun 2026):** subagents generate OS worksheets per subject
  (`runs/ingest/gen_os/`), ingested `in_review` via the stage-aware seam.
- **GWB data + GPB provenance** — demography/globalization/climate/finance (datasets largely curated);
  Quellen-vs-Darstellung across PD epochs.
- **Latein + Griechisch** annotated texts (all-PD corpus; Griechisch needs a polytonic-Greek font).
- **Haushaltsökonomie** — an `energy_requirement` recipe + Austrian nutrition/Konsum datasets (licence
  check on the food tables).

### Phase 2 — Modest new engines (high value)
- **Physics-formula + units parametric family** (SME's domain — fix canonical formulae/conventions first).
- **Biology genetics (Mendel/Punnett) recipe** — combinatorially clean, correct-by-construction.
- **Informatik execution-verified recipes** — algorithm-trace tables, SQL-against-SQLite, truth tables
  (the answer key is the program's output). Curated-code execution approved (decision below).
- **Deutsch epoch literature** (PD through ~7. Kl) + **Zitatrecht-excerpt handling** for in-copyright work.

### Phase 3 — The strategic bet: the dilemma asset class
A curated **structured-argument / dilemma object** (contested question + steel-manned positions +
Gegenargumente + theory tags; derived Nachweis) + an **auto-verifiable logic/fallacy task kind**.
**General-purpose from the start** (decision below). Neutrality-gated — the gate (steel-man each side, no
leaked verdict) is the whole game. Prototype on two contrasting hosts at once (an Ethik dilemma + an
Informatik logic/KI case) to prove generality before scaling. *Effort: M–L · Risk: High on neutrality.*

### Phase 4 — Bigger lifts / deferred
Chemie quantitative engine (stoichiometry/balancing/pH); Darstellende Geometrie 3D-projection figure
backend (read/interpret tasks only — do **not** compete with GeoGebra/CAD on construction); Fremdsprache
B2 audio. **Parked:** Musik notation, Kunst annotated-image (revisit only if the sourced-image rights lane
is built). **Out:** Bewegung und Sport.

---

## 4 · Decisions (settled with the SME, 28 June 2026)

- **Maths competence framework:** **mirror the Lehrplan's 3 dimensions** (Inhalts-/Handlungs-/
  Komplexitätsdimension), **not** the Reifeprüfung *Grundkompetenzen-Katalog*. The Matura framing is not the
  goal for 5.–7. Kl; mirroring the Lehrplan is the more robust grounding for those grades. (Revisit a
  Matura-aligned overlay only if/when we target 8. Kl Maturavorbereitung specifically.)
- **Dilemma asset class:** **general-purpose from the start** (cross-curricular object, not Ethik-scoped).
- **Informatik:** **executing curated code/SQL in the offline pipeline is acceptable** (curated templates
  only, no LLM-authored code in the exec path — same select-never-author discipline as the data/text layers).

## 5 · Open questions / SME fact-checks carried forward

- Physics variant engine: canonical formula set + sign/unit conventions (frame-dependence, SRT) — SME to fix.
- Biologie Basiskonzepte count differs Pflicht (7) vs Wahlpflicht (6) — confirm canonical.
- Two Physik Lehrstoff variants (>7 vs ≤7 Wochenstunden) — worksheets must be tagged to the right variant.
- Rights cliffs: 8.-Kl Deutsch Gegenwartsliteratur (Bachmann/Celan/Bernhard/Jelinek — in copyright);
  translation copyright for PUP/Ethik Originaltexte (translator death-year, not author); food-table licences.
- Neutrality landmines: NS-era GPB sources; contested economics (GWB *Wachstum und Krise*); the dilemma gate.

## 6 · Start here

**Phase 0.** Parse the Oberstufe into a competence catalog and teach the engine about semesters/Kompetenzmodule.
See the parser work under `tools/` and the new `lehrplan/` Oberstufe outputs.
