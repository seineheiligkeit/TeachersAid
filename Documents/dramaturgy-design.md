# The dramaturgy engine — a phase grammar for inter-block coherence

**Status: DESIGN, 11 Jul 2026 — no code yet (SME decision, roadmap C5: "PLAN CAREFULLY, design-first;
first deliverable is a design doc — no code before the doc is agreed").** This doc settles the phase
model, the block-metadata delta, how the grammar composes with the existing `compose` selection, the
bridging-prose mechanism, how coherence is *measured*, the phased build (cheapest falsification first),
and the anti-goals. Author-of-record: SME + Claude. Sibling register: the two hand-built dramaturgies it
generalises ([`textsorte_scaffold.py`](../teachersaid/pipeline/textsorte_scaffold.py),
[`sachverhalt.py`](../teachersaid/pipeline/sachverhalt.py)); the mechanism it reuses is
[`invariants.md`](invariants.md) §3 (re-expression under constraint) and the pattern is
[`frame.py`](../teachersaid/pipeline/frame.py) (the no-drift framing pass). Nothing here overrides
invariants §10 — bridging prose is a **corpus-loop** pass, never a live delivery step.

---

## 0. The problem — composition orders by ladder, not by lesson

The composer selects the right vetted blocks (KB/angle/difficulty/time-fit) and then does one crude
dramaturgic thing: it puts up-to-2 readable infos + 1 figure in the `intro`, and sorts the tasks by
`COGNITIVE_RANK` ascending ([`compose.py`](../teachersaid/pipeline/compose.py) line ~153). That is a
*monotone difficulty ramp*, not a *lesson*. The block-library design already flagged this as the open
risk ("**Coherence is the thing to watch** — a worksheet is more than on-target blocks",
[`block-library-design.md`](block-library-design.md) §4), and `deliver()` names it outright: "inter-block
coherence (the Track-2 hard problem) is deliberately NOT here yet"
([`deliver.py`](../teachersaid/pipeline/deliver.py) docstring). Two independently-vetted, on-target blocks
can still clash in context — redundant, mis-ordered, notationally inconsistent, or simply reading as a
*pile* rather than an *arc*.

The insight of C5: **a worksheet has a dramaturgy — a shape it moves through** — and that shape is not
mysterious. Austrian AHS didactics has a name for it (Unterrichtsphasen), our best hand-built modules
already instantiate it (§2), and our existing ladders (`COGNITIVE_RANK`, the Anforderungsbereich bands
in [`difficulty.py`](../teachersaid/pipeline/difficulty.py)) are *shadows* of it. C5 makes the shape
first-class: a typed **phase grammar**, a soft per-block **phase affinity**, an **ordering** that honours
the grammar, and **bridging prose** that makes the Roter Faden explicit — all correct-by-construction,
offline-safe, and advisory where judgment is required.

> **The composer today knows what belongs on the sheet. The dramaturgy engine gives it a sense of
> what comes first, what it builds toward, and how one block hands off to the next.**

## 1. The phase grammar — Einstieg → Erarbeitung → Sicherung → Transfer

**Recommendation: adopt the four-phase model E–E–S–T as the working grammar**, typed as an ordered enum
with a rank map (mirroring `COGNITIVE_RANK`).

| Phase | Function in the lesson | Typical block kinds | cognitive_level | AFB band | paper's share |
|---|---|---|---|---|---|
| **Einstieg** | orient · activate prior knowledge · pose the Kernfrage | callout/prose intro, a hook figure, one low-stakes activating question | remember/understand | 1 | *partial* — motivation lives in the room |
| **Erarbeitung** | build the new — learn-*from* text, worked example, guided discovery | prose/key_fact/example/figure InfoBlocks; apply & data-interpretation tasks | understand/apply | 1–2 | full |
| **Sicherung** | consolidate · practise · check | matching/ordering/MC, short drills, a Zusammenfassung | remember/understand/apply | 1–2 | full — **paper's strength** |
| **Transfer** | apply to a *new* situation · judge · produce | open_response, position_argument/Urteilsfrage, create/text_production, novel-context task | analyze/evaluate/create | 2–3 | full |

**Why this model, against Austrian AHS practice.** The three-phase core (Einstieg / Erarbeitung /
Sicherung) is the minimal working scheme every AHS Referendar learns; the four-phase form that adds
**Transfer/Anwendung** is the dominant lesson-planning template in Austrian Fachdidaktik. It earns its
place here for four independent reasons: (a) it is what teachers actually plan against; (b) it maps
cleanly onto the cognitive ladder we *already* compute (remember/understand → Erarbeitung-entry &
Sicherung; analyze/evaluate/create → Transfer); (c) it maps onto the three Anforderungsbereiche
(Reproduktion/Transfer/Reflexion) our difficulty engine already derives — so the grammar and the
difficulty model are the *same ladder seen twice*, not two competing orderings; and (d) our two richest
hand-built modules already walk exactly this arc (§2), so the model is **abstracted from what works, not
imposed**.

**Variants considered and rejected:**

- **Three-phase (E–E–S).** Too coarse. It folds Transfer into Sicherung and loses the "apply to a *new*
  situation / judge / produce" beat — which is precisely where our highest-value tasks live (the
  Sachverhalt Urteilsfrage, the Textsorten capstone, every `evaluate`/`create` task). We keep Transfer
  distinct because our engine *already* distinguishes Reflexion as its own AFB band.
- **Five-/six-phase models (AVIVA: Ankommen·Vorwissen·Informieren·Verarbeiten·Auswerten·Bewerten; Roth's
  Artikulationsstufen; Herbart's formal steps).** Too fine *for a printable artifact*. Several of their
  phases are **classroom-social** — Ankommen, the Auswertung/Plenum, motivational framing — which live in
  the *room*, not on paper. Our scope line is load-bearing here: *we make the material, we do not run the
  room* (invariants §7). The purely oral/social phases already have a home — the **Lernarrangement**
  `competence_anchors` (interaction/debrief/shared_product,
  [`arrangement.py`](../teachersaid/schema/arrangement.py)). So the boundary is clean and non-overlapping:

  > **The worksheet grammar is the four *paper* phases. The room phases are arrangement anchors.** A
  > worksheet dramaturgy nests inside an arrangement dramaturgy; we do not smuggle room-orchestration onto
  > the sheet.

**Honest degeneration under a tight envelope.** A 25-minute Einzelstunde or a homework sheet cannot
sustain a full four-act arc, and faking one is worse than admitting it. The grammar therefore has
**declared degenerate forms**, chosen by envelope — not a silently truncated E–E–S–T:

- **Homework (Hausübung) is, by nature, the *back half* of the grammar.** The Einstieg/Erarbeitung
  happened in class; independent practice is Sicherung, and an application task is Transfer. So a homework
  envelope targets a **Sicherung → Transfer** two-phase arc — which is *pedagogically correct*, not a
  compromise. (The homework projection already exists; the grammar just names what it always was.)
- **A ≤~30-min single sheet** targets a **reduced arc** — most often Erarbeitung → Sicherung (learn +
  practise) or a single-phase Übungsblatt (Sicherung only). The plan/Nachweis states the form honestly
  ("Übungsphase", "Anwendung") rather than labelling a fragment as a "vollständige Lernsequenz".

► **SME decision (D-envelope): the envelope→arc mapping.** Recommendation:
`homework → {Sicherung, Transfer}`, `einzelstunde ≤ ~30 min → {Erarbeitung, Sicherung}`,
`doppelstunde/block → full E–E–S–T`. The exact minute thresholds and whether a lone Sicherung sheet is
allowed to ship without any Transfer beat are the SME's call.

## 2. Two dramaturgies we already hand-built (reverse-engineered)

The grammar is not new to the corpus — it is *latent* in the best hand-authored modules. Reading them
back through E–E–S–T is the strongest evidence the model fits, and it is where the harvest heuristic (§3)
comes from.

**Textsorten-Scaffold** ([`textsorte_scaffold.py`](../teachersaid/pipeline/textsorte_scaffold.py)) — its
own docstring narrates the arc: "verstehen (Bauteile), planen (Raster), verfassen (Schreibauftrag)":

| block | phase |
|---|---|
| `tx.intro` callout ("In dieser Stunde lernst du …") | **Einstieg** |
| `tx.i1`/`tx.i2` learn-text (what the Textsorte is, its Aufbau) | **Erarbeitung** |
| `tx.t1` matching (Bauteil ↔ Funktion), `tx.t2` Schreibplan-Raster | **Sicherung** |
| `tx.t3` capstone Arbeitsauftrag (produce the Textsorte, `create`) | **Transfer** |

**Sachverhalt** ([`sachverhalt.py`](../teachersaid/pipeline/sachverhalt.py)) — the intro literally
sequences it ("Lies zuerst den Darstellungstext … Bearbeite danach die Aufgaben"):

| block | phase |
|---|---|
| `sv.intro` callout | **Einstieg** |
| Darstellung learn-text + derived timeline/Wirkungsgefüge/process/map figures | **Erarbeitung** |
| chronology `ordering` (remember), `concept_match` (understand), content-comprehension | **Sicherung** |
| `cause_effect_match` (analyze), structure-overview, the `urteilsfrage` (evaluate) | **Transfer** |

Two subjects, two authors, the same four beats. **The dramaturgy engine's job is to give the *composer*
what these hand-built modules got by hand.**

## 3. Phase affinity on blocks — inferred, then SME-confirmed

**The field (additive, default None).** Phase affinity is *composition metadata* — a block's natural
role in a lesson — so it belongs on `LibraryBlock` beside `scope`/`family`, **not** on the schema `Block`
(which flows through generation views and must not carry compose-time fields). Two fields, both additive:

```python
# library/block.py  (LibraryBlock)
phase: str | None = None       # "einstieg" | "erarbeitung" | "sicherung" | "transfer"
phase_confirmed: bool = False  # False = inferred/unreviewed; True = SME-set. Never silently trusted.
```

**Recommendation: phase is a *soft prior*, not a hard slot.** The same band-2 apply-task can serve
Erarbeitung on one sheet and Sicherung on another; a figure can be a hook (Einstieg), a diagram
(Erarbeitung), or a data set to reason over (Transfer). So `phase` records the block's *natural home*,
and the composer (§4) may place it in an adjacent phase when the arc needs it. (Modelling it as a single
primary — rather than a set of admissible phases — keeps the schema and the review UX minimal; the
adjacency slack recovers the flexibility.) ► **SME decision (D-cardinality): single primary phase vs. a
set of admissible phases.** Recommend single primary; revisit only if review shows blocks that genuinely
straddle two non-adjacent phases.

**What `harvest` can infer mechanically** (deterministic, from data it already sees):

- **kind** is the strongest signal. A pure InfoBlock (`prose`/`key_fact`/`example`/`figure`) → Erarbeitung
  (a learn-*from* block) unless it is the orienting `callout`/first block → Einstieg. A self-contained
  drill (`matching`/`ordering`/`multiple_choice`) → Sicherung. A judgment/production task
  (`position_argument`, `text_production`, `urteilsfrage`, or any `evaluate`/`create` level) → Transfer.
- **cognitive_level** refines it: remember/understand lean Erarbeitung-entry & Sicherung; analyze/
  evaluate/create lean Transfer. (This is why the grammar and the AFB ladder mostly agree — §4.)
- **position in the source worksheet.** `harvest(content)` walks `content.iter_blocks()` in order, and our
  hand-built sheets *are* dramaturgically ordered (§2). Recording the source ordinal lets the first info
  block read as Einstieg and a closing judgment task read as Transfer — a real signal, free at harvest
  time.

**What only the SME can tag** (the contextual calls — default to a best guess, flag as unconfirmed): the
Erarbeitung/Sicherung boundary for a mid-level task (is this apply-task *building* the idea or
*consolidating* it?); a figure's role; whether an info block is *orienting* (Einstieg) or *content*
(Erarbeitung). These are genuinely context-dependent; the heuristic guesses, the SME confirms.

**Migration of the ~960 approved blocks — bulk-infer + review-cue, never silent.** There are ~1140
harvested `LibraryBlock`s today, ~960 approved. A one-shot `tools/infer_phases.py` (the
`scope_variants.py`/ingest-tool pattern) runs the §3 heuristic over every block and `upsert`s
`phase=<inferred>, phase_confirmed=False` — and because `JsonStore.upsert` is **status-preserving**
(invariants §9), re-tagging never un-approves anything. The **Bausteine** tab then shows an "abgeleitet"
(inferred) chip on every unconfirmed phase, with a **per-KB bulk-confirm** (the `approve-all` pattern) so
the SME sweeps a Kompetenzbereich in one pass, correcting outliers. Nothing inferred is ever presented as
truth: `phase_confirmed=False` is visible everywhere it matters. ► **SME decision (D-trust): may the
composer use *unconfirmed* inferences?** Recommendation: **yes** — so the feature works the day the
heuristic lands — but the coherence report (§5) down-weights adjacencies that rest on unconfirmed phases,
and confirmation upgrades trust. The alternative (composer ignores unconfirmed phases, falls back to the
cognitive-rank order until an SME sweeps the KB) is safer but delays every payoff behind a review queue.

## 4. Ordering + selection — the grammar is the outer key, the ramp is the inner key

Selection is **unchanged**: `compose` still picks blocks by KB/competence eligibility, angle-term
overlap, family-dedup, scope-fit, and greedy time-fit ([`compose.py`](../teachersaid/pipeline/compose.py)).
The dramaturgy engine changes only **ordering and phase-balance**, and it composes with the existing keys
by a clean precedence:

1. **Phase rank is the outer sort key** (Einstieg=0 → Transfer=3) — the dramaturgic skeleton.
2. **Within a phase, the existing keys are the inner sort** — on-angle first, then `COGNITIVE_RANK`, then
   scope-fit. (Today's ordering becomes the *intra-phase* ordering, unchanged.)
3. **Phase-balance replaces raw band-seeding.** The current "seed one block per Anforderungsband 1/2/3 so
   a tight budget spans easy→stretch" (`compose.py` ~line 140) is **reinterpreted as per-phase seeding**:
   guarantee the minimal viable arc — at least an Einstieg beat, one Erarbeitung, one Sicherung — *before*
   spending the remaining budget on Transfer extras or a second Erarbeitung block.
4. **Time-fit stays greedy** but respects (3): it never spends the whole budget on Erarbeitung and leaves
   the arc headless (no Sicherung) or gutless (no Transfer, when the envelope calls for one).

**The conflict rule (the load-bearing precedence).** When the difficulty ramp says A→B but the grammar
says B→A: **phase wins on placement; the ramp wins within a phase.** A hard (band-3) recall task tagged
Sicherung is placed in Sicherung *even though* it is harder than a Transfer-tagged band-2 application
task that comes after it. This is not a bug — it is the point:

> A monotone difficulty ramp is *not* the most pedagogically sound curve. Real lessons **consolidate
> before they climb**: Sicherung deliberately drops the cognitive load to secure the new idea, then
> Transfer climbs again. The phase order produces a **phase-shaped intensity curve** (a rise through
> Erarbeitung, a consolidation dip in Sicherung, a final climb in Transfer) — which is *better* than the
> flat monotone ramp we ship today, not a compromise with it.

Because phase and AFB are the same ladder seen twice (§1), the two keys **agree by construction** almost
everywhere; the conflict rule only bites at the exceptions, and there the didactic function (phase) is
the right master. **Graceful degradation:** a block whose `phase is None` (un-inferred, or a subject the
heuristic can't read) falls back to **phase-inferred-from-cognitive_level at order time**, so the composer
degrades smoothly to *today's* behaviour rather than crashing or mis-placing — the grammar is an
enrichment, never a hard dependency.

**Where the grammar lives in code.** A small `pipeline/dramaturgy.py`: the `Phase` enum + `PHASE_RANK`
map + `infer_phase(block)` (the §3 heuristic, shared by harvest and the order-time fallback) + the
ordering function `compose` calls. The grammar is also dual-use on the **corpus side**: `plan.py`'s
block-spec skeleton (already a `_LADDER`) can target a *phase-shaped* spec so campaign generation fills
the *missing phases* of a KB, not just missing competences. The composer is the primary target; the plan
integration is a noted, cheap extension.

## 5. Bridging prose — mechanism-4 re-expression over the two adjacent blocks

The Roter Faden is not just *order*; it is the connective sentence that hands one block off to the next
("Jetzt, wo du die Bauteile kennst, planst du deinen Text"). This is **exactly** the shape of the
existing framing pass — [`frame.py`](../teachersaid/pipeline/frame.py) already writes a Kernfrage, an
orienting intro, and per-task lead-ins as *new InfoBlocks around untouched tasks*. The dramaturgy engine
extends that pattern to **phase-boundary bridges**.

**Mechanism (invariants §3, the fourth correct-by-construction mechanism — re-expression under
constraint).** At each phase boundary the pass authors **one connective sentence**, and it is a
projection over a **frozen, minimal fact-set**:

- **What the LLM sees:** the last block of phase *N* and the first block of phase *N+1* (their rendered
  text only), the two phase labels, and the sheet's Kernfrage. **Nothing else.** It cannot reach the
  wider corpus, the answer keys, or any fact not in those two neighbours.
- **What the LLM writes:** one bridging sentence, emitted as a **new `InfoBlock`** inserted *between* the
  two blocks (the `cmp.lead.*` pattern `frame.py` already uses). It may add framing, rhythm, and a
  didactic hand-off; it may **not** introduce a new task, number, date, name, or claim.

**The deterministic guard (the bridge-lint).** Reuse the entity-lint family
([`sachverhalt_lint.py`](../teachersaid/pipeline/sachverhalt_lint.py) /
[`realie_lint.py`](../teachersaid/pipeline/realie_lint.py)): every
**number/year** in a bridge must appear verbatim in one of the two adjacent blocks (or the Kernfrage) —
**hard, deterministic**; a bridge that invents "1848" is rejected. Novel **proper names** are advisory
(German capitalises every noun — the same rule the Sachverhalt entity-lint uses). A rejected bridge is
**not a failure**: it falls back to the offline template (below). No bridge can smuggle a fact, because
its whole licensed vocabulary is the two neighbours it connects.

**The offline template fallback (the `frame.py` no-op discipline, extended).** With no generator (no API
key), the pass is deterministic: a small curated table keyed by the **phase pair** supplies the bridge
("Erarbeitung → Sicherung" → "Übe jetzt, was du gerade gelernt hast."; "Sicherung → Transfer" →
"Wende dein Wissen nun auf eine neue Situation an."). These are content-free connectives — the same
authored-then-vetted table style as `textsorte_scaffold.py`'s `_OPERATOR_AUFTRAG`/`_DEFAULT_IMPULS`. So
the engine is **fully functional offline**; the LLM only makes the bridges *specific* to the neighbours.

**The precise no-drift guarantee.** State it exactly, because it is the whole safety case:

> Bridging adds *only* new `InfoBlock`s **between** existing blocks. **No existing block's fields are ever
> mutated** — not a prompt, not an `answer_key`, not a `serves`, not a payload. Deleting every bridge
> InfoBlock yields *exactly* the un-bridged composition, byte-for-byte. Vetted task content is therefore
> untouched by construction (the same invariant `frame.py` holds today), and every bridge's content
> tokens are a subset of its two frozen neighbours (the bridge-lint). **The sheet cannot drift; it can
> only gain connective tissue.**

## 6. How coherence is measured — tripwires, not a guarantee

Propose a **`coherence_report`** — advisory, computed like the `verify` lints, **never a gate** (triage
orders, it does not block; invariants §7, §10 boundary). It runs over a composed sheet and reports:

**Deterministic (a defect is a real structural fault):**

- **Phase-sequence validity.** The block order's phase ranks must be non-decreasing (Einstieg=0 …
  Transfer=3). A **phase regression** — a Transfer block followed by an Einstieg block — is a hard defect.
- **Arc completeness.** The sheet contains at least the phases its declared arc requires (§1's degenerate
  forms). An all-Einstieg or all-Transfer sheet that *claims* to be a full lesson is flagged; a *declared*
  Sicherung-only Übungsblatt is not.
- **Intro/outro presence.** An orienting opening beat (Einstieg / a Kernfrage) exists at the top, and the
  sheet ends on a consolidating or transfer beat — not mid-climb, dangling.

**Advisory (a proxy for coherence, honest about being a proxy):**

- **Roter-Faden term continuity.** Reuse `compose._angle_terms`: score the fraction of *adjacent* block
  pairs that share ≥1 content term. A zero-overlap adjacency is a **jump-cut** warning. This is a
  deliberately imperfect proxy — two blocks can be coherent through a concept that shares no surface
  token — so it warns, never fails.
- **Intensity-curve shape.** Map each block to an intensity (AFB band × `est_minutes`, or cognitive rank)
  and flag a curve that is *flat-monotone* or *front-loaded-hard* rather than phase-shaped (§4). A
  heuristic that nudges toward "consolidate before you climb"; it prescribes no exact shape.

**What canNOT be measured without a human — stated plainly** (the realien/sachverhalt honesty register:
*never claim a guarantee we can't keep*). No check verifies that a bridge is **true to the lesson's
idea**; that two blocks are **conceptually** (not lexically) connected; that the Kernfrage genuinely
**governs** every block; that the difficulty *feels* right; or that the sheet is *interesting* — the
**blackboard test** (`master-library-plan.md`) stays the SME's. The coherence report is a set of
**necessary-not-sufficient tripwires**: it catches *structural* incoherence (phase regression, jump cuts,
a headless arc) and nothing more. Treating it as a gate would optimise for term-overlap and breed
keyword-stuffed bridges — so it is **advisory by design**, exactly like the readability and prose-provenance
lints.

## 7. Phasing — cheapest falsification first

The premise ("grammar-ordered sheets read better than ladder-ordered ones") is *falsifiable by a human
looking at two PDFs*. Do that before building anything.

- **Step 0 — the falsifying proof (≈no engine code).** Hand-tag the phase of ~30 already-approved blocks
  from **one well-covered KB** (Physik *Strahlung* — it has families + scope variants). Take one existing
  composed worksheet, hand-reorder its blocks by the grammar, render both the grammar order and today's
  cognitive-rank order, and have the **SME eyeball whether the grammar version reads as a better lesson.**
  If it doesn't, the premise is wrong — **stop, having spent an afternoon.** This is the whole bet, tested
  for the price of a throwaway reorder script.
- **Step 1 — infer + measure (no composer change).** Land the `phase`/`phase_confirmed` fields, the
  `infer_phase` heuristic, `tools/infer_phases.py` (bulk-infer, status-preserving), the Bausteine
  "abgeleitet" chip + per-KB bulk-confirm, and the read-only `coherence_report`. Measure **how often the
  inferred phase matches the SME's correction** — that calibrates the heuristic and tells us how much of
  §3 is truly mechanical.
- **Step 2 — order by grammar.** `compose` orders by phase (outer) + existing keys (inner), with the
  degenerate/homework reductions and the graceful `phase is None` fallback; `coherence_report` runs
  advisory in `deliver`/`verify`. **No bridging prose yet** — prove that *ordering alone* improves sheets
  before adding the LLM.
- **Step 3 — bridging prose.** Extend `frame.py` with phase-boundary bridges + the bridge-lint + the
  offline template table. Last because it is the highest-risk (LLM) piece and only earns its place if
  Step 2 already reads better.

Each step is independently shippable and independently falsifiable — the "cheap proofs before the big
build" discipline the Sachverhalt and Realien builds followed (`sachverhalt-content-layer-design.md` §11).

## 8. Risks & anti-goals

- **The template-engine failure mode (the big one).** If every sheet is forced into a rigid four-act
  Prokrustesbett, the corpus goes monotonous — every worksheet reads the same. **Dramaturgy is a
  *grammar*, not a *template*: it admits many well-formed sentences.** Guards, all already in the design:
  phase affinity is a *soft prior* with adjacency slack (§3); the degenerate forms are first-class, so not
  every sheet is E–E–S–T (§1); the grammar constrains *order and connectivity*, never *content* — the
  angle machinery is untouched, so two Kernfragen on one KB still diverge; and bridging prose is generated
  *per-sheet from the actual neighbours* (offline it is honestly a labelled template fallback, not the
  product).
- **Over-fitting to one subject's rhythm.** Physik's Erarbeitung ≠ Deutsch's ≠ GWB's. Keep the four phases
  **subject-agnostic didactic universals**; subject-specific rhythm lives in the *blocks and their
  affinities*, never in hard-coded per-subject phase rules. Do not encode "Physik opens with a
  phenomenon" — let the harvested affinities carry it.
- **The measurement trap.** Promoting `coherence_report` from advisory to gate would optimise for lexical
  overlap and defeat the point. It stays advisory (§6); the blackboard test stays human.
- **Scope creep into the room.** Dramaturgy tempts extension into "…and then the teacher says…" — but that
  is the arrangement layer. **The worksheet grammar stops at the paper** (§1). The social phases are
  arrangement anchors; we do not run the room.
- **build-for-joy framing.** This is Wave **C** — *corpus structure*, the holistic layer — and inter-block
  coherence is the explicitly-acknowledged Track-2 hard problem, approached didactically. It earns its
  place on the **intrinsic axis** (corpus-level craft: the corpus stops reading as piles and starts
  reading as lessons), not because a teacher asked — there is no teacher-feedback loop, and there is no
  productization clock. The Step-0-falsification-first phasing *is* the anti-over-engineering discipline:
  we spend an afternoon proving the idea before we spend a week building it.

## 9. Decisions

**Settled by this doc (recommendations to ratify):**

- **Phase model = four phases, Einstieg → Erarbeitung → Sicherung → Transfer** (§1), typed with a rank map
  that doubles as the outer ordering key.
- **The room phases are out of scope** — they are Lernarrangement anchors, not worksheet blocks (§1).
- **Phase affinity is a soft prior on `LibraryBlock`** (`phase` + `phase_confirmed`, additive, default
  None/False), inferred by harvest and confirmed by the SME (§3).
- **Precedence: phase is the outer key, the cognitive/difficulty ramp the inner key; phase wins on
  placement, the ramp within a phase** — yielding a phase-shaped (consolidate-then-climb) intensity curve
  (§4).
- **Bridging prose is additive InfoBlocks between frozen neighbours, guarded by a numeric bridge-lint,
  with an offline template fallback; no existing block field is ever mutated** (§5).
- **Coherence is measured by an advisory report, never a gate; structural faults are deterministic, the
  rest is an honest proxy** (§6).
- **Build Step-0-first** — hand-order one sheet and let the SME falsify the premise before any engine work
  (§7).

**Open — marked for the SME (►):**

- ► **D-envelope** (§1): the exact envelope→arc mapping and minute thresholds; whether a Sicherung-only
  sheet may ship with no Transfer beat.
- ► **D-cardinality** (§3): single primary phase (recommended) vs. a set of admissible phases per block.
- ► **D-trust** (§3): may the composer order on *unconfirmed* inferred phases (recommended, with
  down-weighted coherence trust) or only on SME-confirmed ones?
