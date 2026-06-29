# Sachverhalt — the curated content / exposition layer (History first)

**Status:** design / planning (29 Jun 2026). Author-of-record: SME + Claude.
**Scope of this doc:** the **History (GPB) extension** is the concrete build (Phase 1); the schema is
deliberately designed to **generalise across subjects** (Phase 2+), because the gap it closes is
cross-subject. Sibling docs: `history-facts-provenance-design.md` (the provenance machinery this reuses),
the **data layer** (`CLAUDE.md` "Grounded facts & data layer") and **annotated texts** — the two existing
grounding/provenance siblings this is modelled on.

---

## 1. The problem — prose is a *thin intro*, not a content layer

The engine is excellent at **tasks** (correct-by-construction) and at the **method/Quellenkritik** face of
history. What it does *not* yet produce is a **didactic presentation of the substance** — the
"what-happened-and-why-it-matters", the Sachwissen, explained and structured for learning.

This was measured across the staged corpus (info/expository blocks vs task blocks, expository words per
worksheet):

| subject | items | info blocks | task blocks | expository words/item |
|---|---|---|---|---|
| Geographie (GWB) | 34 | 24 | 220 | 42 |
| Geschichte (GPB) | 12 | 7 | 59 | 39 |
| Physik | 10 | 8 | 65 | 31 |
| Chemie | 14 | 4 | 86 | 13 |
| Latein · Musik · Kunst · GZ · Sport · FS2 | 5 each | **0** | 30 | **0** |

The shape is identical everywhere: **task-generative, prose-thin**. Several subjects ship pure task sheets
with *no* content layer. Where a subject carries real substance to teach — Bio processes, Geo processes,
Physik mechanisms, History events, Ethik concepts — the exposition is a couple of framing sentences, not a
presentation.

**The curriculum demands the opposite balance for the content face.** GPB has an explicit **Sachkompetenz**
pillar (US "Historische und politische Sachkompetenz"; OS "Historische" + "Politische Sachkompetenz") and
four **content/epoch Kompetenzbereiche** (Antike→Mittelalter, Neuzeit→1. WK, 1. WK→Gegenwart,
Transformationsprozesse 20./21. Jh). Yet GPB's `task_kind_extensions` are **all method-oriented**
(`source_analysis`, `position_argument`, `dekonstruktion`, `argumentation`) — there is no Sachkompetenz task
kind. Even the flagship [`gpb_wiener_kongress.py`](../teachersaid/library/gpb_wiener_kongress.py) has a
~5-sentence learn-text whose job is to set up `Quelle ≠ Darstellung`; the causes, course, consequences and
long-term significance of 1815 are not the payload.

## 2. Why it ended up this way — the real tension

The engine rests on **select-never-author / correct-by-construction**. Numbers compute (math/chem); quotes
are selected; sources carry provenance. But a **didactic historical account is inherently authored prose** —
you cannot *compute* why the Wiener Kongress mattered. So history was modelled through the one face that fits
the philosophy cleanly (provenance + Quellenkritik). The `role="facts"` provenance exists, but only as a
*fact-checking hook for source tasks*, never as a *content primitive*. The substance fell into the gap
between "we don't author" and "we can't compute".

## 3. The reframe — a Darstellung is a first-class product

A well-made **Darstellung** (a didactic historical account) is a legitimate, central product — the Lehrplan
demands it. The honest reconciliation with select-never-author is a **split**:

- **Structured facts are facts** — a date, an actor and its role, a cause→effect link, a Begriff, a Folge.
  These are curatable and **sourced exactly like the data layer's numbers** (copyright protects *expression*,
  not facts), and fact-checked at the HITL gate. *Select, never author* holds for the substance.
- **The connective narrative is authored-then-vetted** — an already-accepted pattern in this repo (the TTS
  scripts, the text annotations are authored, then SME-vetted) — but **grounded in those structured facts**,
  so every sentence is checkable against a sourced fact, never asserted free-hand.

That yields didactic richness *and* the honesty discipline. It is **not** in tension with the existing
philosophy — it is the same philosophy applied to a third kind of material.

## 4. Where it sits — the third grounding/provenance sibling

| layer | unit | "select, never author" applies to | gate |
|---|---|---|---|
| **Grounded data** | `Dataset` | real **numbers** (cited) | (c)-label / `figure_lint` |
| **Annotated texts** | `AnnotatedText` | real **texts** (rights-cleared) | rights gate (`is_clear`) |
| **Sachverhalt (new)** | `Sachverhalt` | structured **Sachwissen** (sourced facts) | prose-provenance gate (`prose_lint`) + facts-required |

It **reuses** the History/GPB provenance machinery wholesale: `schema/provenance.py`
(`BlockProvenance` · `ProvenanceSource` · `role="facts"`/`"expression"` · `expression_origin`),
`pipeline/prose_lint.py` (the mandatory-internal `role="facts"` rule for `original` fact blocks), the rights
gate (`rights_gate` / AT 70-Jahre-p.m.a. / Zitatrecht), and
[`tools/fetch_wikipedia.py`](../teachersaid/tools/fetch_wikipedia.py) (metadata-only permalink records, no
LLM in the fact path). The Sachverhalt is the **content object** those mechanisms were always implying.

## 5. The load-bearing idea — one module, three projections

A `Sachverhalt` is a **curated module of structured Sachwissen** about one topic. Like one `WorksheetContent`
projects to student/teacher/homework, **one Sachverhalt deterministically yields three outputs** — and that
is why the substance stops drifting and starts compounding:

```
                         ┌──────────────► Darstellung  (didactic learn-text, authored-then-vetted,
                         │                              grounded in the facts → InfoBlocks + provenance)
   Sachverhalt module ───┼──────────────► Figures       (DERIVED: timeline ← events, Wirkungsgefüge ←
   (sourced facts)       │                              causal links, Längsschnitt ← comparisons)
                         └──────────────► Sachkompetenz  (GENERATED, several correct-by-construction:
                                          tasks         order the real events, match cause→effect,
                                                        Begriff-Zuordnung; method tasks still attach)
```

The same `assemble`/`verify`/`render` path runs at the end — a Sachverhalt **produces a `WorksheetContent`**
(or a richer `Lernarrangement`), so nothing downstream changes.

## 6. Schema sketch (v0 proposal — decide field-by-field at review)

Reuse `ProvenanceSource`; add a content module. Structured facts each carry/reference a source; the narrative
sections **link the fact ids they rest on** (`grounded_by`) — the checkability mechanism.

```python
class HistEvent(BaseModel):      # → timeline figure + chronology tasks
    at: int | str                # year (or ISO) — numeric drives the timeline axis
    label: str                   # short tag
    text: RichText = ""          # one-line description
    source_ref: str | None       # index into sources[]

class Actor(BaseModel):          # who, and their role
    name: str; role: RichText; source_ref: str | None = None

class CausalLink(BaseModel):     # → Wirkungsgefüge figure + cause-effect-match tasks
    cause: str; effect: str
    kind: Literal["ursache","verlauf","folge","wirkung","voraussetzung"] = "folge"
    source_ref: str | None = None

class Concept(BaseModel):        # Begriffe → concept-match tasks
    term: str; definition: RichText; source_ref: str | None = None

class DarstellungSection(BaseModel):   # the authored-then-vetted narrative, grounded
    heading: str
    body: RichText
    grounded_by: list[str] = []        # fact ids this paragraph rests on (checkability)
    provenance: BlockProvenance        # expression_origin="original", sources include role="facts"

class Sachverhalt(BaseModel):
    id: str; subject: str
    klasse_range: tuple[int,int]
    kompetenzbereiche: list[str]; competences: list[str]   # discovery tags (cf. Dataset)
    topic: str; leitfrage: RichText
    sources: list[ProvenanceSource]                        # role="facts" mandatory
    # --- the structured substance (facts) ---
    timeline: list[HistEvent] = []
    actors: list[Actor] = []
    causes: list[CausalLink] = []
    concepts: list[Concept] = []
    bedeutung: RichText = ""            # significance / Nachwirkung
    gegenwartsbezug: RichText = ""      # the "implications" / present-day link (Lehrplan-mandated)
    # --- the authored-then-vetted narrative, grounded in the above ---
    darstellung: list[DarstellungSection] = []
```

**Cross-subject generalisation (Phase 2+).** The skeleton is generic; only the *fact mix* shifts: Biology
leans on `Concept` (structures/functions) + a process/cycle fact-type; Geography on spatial
processes/systems + maps; Physik on phenomena/mechanisms (a cause-effect cousin); Ethik on positions/thinkers.
**Decision for the build:** start with the history fields above; add subject fact-types behind the same
`Sachverhalt` container only when Phase 2 needs them (don't over-generalise the schema before a second
subject exercises it).

## 7. Derivation — how each projection is built (deterministic where it can be)

- **Darstellung → InfoBlocks.** Each `DarstellungSection` → an `InfoBlock` (`prose`/`key_fact`) with its
  `BlockProvenance`. `bedeutung`/`gegenwartsbezug` → closing key_fact blocks. Pure projection, rendered by
  the existing path; the prose-provenance gate already enforces that fact blocks name a `role="facts"`
  source.
- **Figures → DERIVED, correct-by-construction.**
  - `timeline` → `matplotlib:timeline` (**exists**; spec `{events:[{at,label}]}`) straight from `timeline[]`.
  - `causes` → a **new `Wirkungsgefüge`/cause-effect recipe** (boxes + arrows; bundles with the deferred
    MINT/structured-figure track) from `CausalLink[]`.
  - comparisons → Längsschnitt/Querschnitt (later).
- **Sachkompetenz tasks → GENERATED, several gradable by construction.** The module *is* the answer key:
  - chronological **ordering** of the real `timeline[]` (have the `ordering` kind) — deterministic.
  - **cause-effect matching** from `causes[]` — deterministic.
  - **Begriff-Zuordnung** (concept ↔ definition) from `concepts[]` — deterministic.
  - content-comprehension + multiperspectivity-*on-events* — generated, vetted.
  - the existing **method** tasks (source_analysis, position_argument) still attach — a Sachverhalt does not
    replace Quellenkritik, it complements it (and can even *teach* the meta-point: this account is itself a
    Darstellung, here is its provenance).

## 8. New task kinds — the missing Sachkompetenz vocabulary

Extend the GPB `task_kind_extensions` (and the generic core where reusable): `cause_effect_match`,
`concept_match`, `chronology` (alias the existing `ordering`), `structure_overview`, `content_comprehension`.
Deterministic graders where the module provides the truth; the open ones carry a rubric like today's tasks.
Add them to `subject_models.json` so `verify` accepts them — no engine change.

## 9. Honesty gates (unchanged machinery, new content)

- **Facts-required (mandatory-internal):** every `original` `DarstellungSection` and every structured fact
  needs a `role="facts"` source → fact-checked at the HITL gate (`prose_lint` already enforces this for
  GPB ∪ `historical_fact`).
- **Rights gate:** any `quoted`/`adapted` material rides the existing `rights_gate` (CC / PD by AT
  70-Jahre-p.m.a. / Zitatrecht). Structured facts are facts → no expression obligation.
- **`grounded_by` audit:** a narrative section whose claims are not covered by any cited fact is a review
  warning (the "asserted unchecked" smell), surfaced in the dashboard.

## 10. HITL

A `SachverhaltStore` (mirrors `DatasetStore`/`TextStore` on `JsonStore`) + a dashboard **Sachverhalte** tab:
review the **facts + sources** (the fact-check surface), preview the **derived Darstellung + figures +
tasks**, approve. `orch.ingest_sachverhalt` gates (rights + facts-required) → materialises → stores;
`orch.compose_from_sachverhalt(id)` stages a `WorksheetContent` for Gate-2 review. `feedback` target kind
`sachverhalt`.

## 11. Phasing (cheap proofs before the big build)

- **Phase 1 — History, end-to-end on one topic.** Schema (`schema/sachverhalt.py`) + the derivation
  (`pipeline/sachverhalt.py`) + **rebuild *Der Wiener Kongress* content-first**: a real Darstellung
  (Verlauf → Ursachen → Folgen → Bedeutung → 1848/Nationalismus as Gegenwartsbezug), a timeline + a
  cause-effect figure, and the three deterministic Sachkompetenz task kinds — alongside (not replacing) the
  existing Quelle/Darstellung lesson. `SachverhaltStore` + tab + ingest. Tests lock derivation + verify-clean
  + render, and the deterministic graders.
- **Phase 2 — generalise to one content-heavy science.** Biologie *or* Geographie (both scored worst on
  expository depth) — add the subject's fact-type(s), prove the container holds. Confirms the schema isn't
  history-locked.
- **Phase 3 — scale via subagents.** Author **structured modules** from provided/sourced facts (the breadth
  pattern: subagents emit `Sachverhalt` JSON → `tools/ingest_sachverhalte.py` → rights/facts gate → verify →
  stage). The facts are *selected/sourced*, the narrative *authored-then-vetted* — never invented.

## 12. Open questions / decisions for review

1. **Narrative authoring:** how much of `darstellung` is hand/subagent-authored vs assembled from
   templates over the facts? (Lean authored-then-vetted for quality; templated for the deterministic parts.)
2. **Figure dependency:** the `Wirkungsgefüge` recipe — fold into the deferred **CHE+PHY MINT-figure track**
   or a parallel "structured-content figure" track? (It's a box-and-arrow diagram, not a chart.)
3. **Unify with `LibraryBlock`?** A Sachverhalt is, in part, a richer InfoBlock cluster — keep it a separate
   curated primitive (like `Dataset`) or harvest its Darstellung into library blocks for reuse? (Proposal:
   separate primitive; harvest the *derived* blocks like any worksheet.)
4. **Fact-type set:** lock the v0 history fields (§6) now; defer Bio/Geo fact-types to Phase 2.
5. **Scope line (unchanged):** we make the material; we do not assert an uncited historical claim. Every fact
   is sourced and SME-fact-checked at the gate.
