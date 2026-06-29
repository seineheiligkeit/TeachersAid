# Invariants — the hard rules, why they exist, and where they stop

**Purpose.** This is the single place that states the project's *load-bearing* rules — and, just as
importantly, **their boundaries**. Many of our docs phrase a rule as an absolute ("select, never author",
"the model never invents", "no HTML→PDF") because the *strong form* is a good day-to-day proxy. But a proxy
stated as an absolute can **block good thinking** in a later session. So each rule below carries three lines:

- **Rule** — the actual invariant.
- **Why** — what breaks if we drop it (it earns its place or it isn't here).
- **Boundary** — what it does **not** forbid. *This is the line that keeps us from over-constraining.*

> When a rule feels like it's blocking a good idea, come here first. If it's a genuine load-bearing
> invariant, respect it. If the thing blocking you is the *proxy* and not the *invariant*, relax it to its
> boundary. (This document was written after exactly that happened — see §3.)

The dependency graph in code enforces several of these mechanically (`rendering/` imports only `schema/`,
generation views can't carry derived fields). Where code enforces it, that's noted.

---

## 1. Rendering is a pure projection of one `WorksheetContent`

- **Rule.** Every projection — student / teacher / homework — is a pure function of the *same*
  `WorksheetContent`. `rendering/` imports only `schema/`; it holds no copy of task data and never reaches
  into `pipeline/`.
- **Why.** The answer key cannot drift from the task. The incumbent's "mismatched teacher guide" bug is
  *structurally impossible*, not merely tested-against. This is the system's deepest correctness guarantee.
- **Boundary.** The renderer is **swappable** — ReportLab today; HTML→PDF / Typst / docx are all fair game
  (see `rendering-handoff-brief.md`). The renderer may be richly *creative* about layout, typography, and
  figures. **"No HTML→PDF" is not the invariant** — projection-purity is. What's forbidden is rendering
  *holding or altering* content, not any particular rendering technology.

## 2. Derived trust-artifacts are computed, never authored

- **Rule.** `Nachweis`, `DepthProfile`, `grade_check`, and the provenance obligation booleans
  (`attribution_required` / `share_alike_applies`) are **derived** by pipeline code, absent from generation
  views, and never produced by hand or LLM.
- **Why.** These *are* the trust claims (coverage, depth, rights). A claim you **assert** instead of
  **compute** is unverifiable — and "provably competence-aligned" is the product. Code enforces it: the
  validation-schema omits these fields so the model literally cannot emit them.
- **Boundary.** Applies to the *derived trust-artifacts* only. It is **not** a general "the LLM authors
  nothing" — authored `TeacherOverview` / talking-points / extensions are fine; they're pedagogy, not trust
  claims. The line is "is this a *claim the product vouches for*?" — if yes, derive it.

## 3. The LLM never originates a load-bearing FACT — but it may author EXPRESSION over facts it was handed  ⭐

*This is the rule most often mis-stated, and the one a future session is most likely to over-apply. Read the
boundary.*

- **Rule.** The **substance** — numbers, dates, names, quotes, events, causal claims, competence ids — is
  always **selected** from a vetted source (the Lehrplan catalog, a cited `Dataset`, an `AnnotatedText`, a
  `Sachverhalt` fact-set) or **computed** (sympy). The LLM never originates a load-bearing fact. It **may**
  freely author **expression**: prose, framing, connective narrative, task wording, explanations — *as a
  projection over a frozen, given fact-set*, never reaching outside it for a new fact.
- **Why.** "The AI gets the facts wrong" is the incumbent's failure and our entire differentiator.
  Correctness must be guaranteed by **structure**, not by trusting the model. Crucially, correct-by-
  construction has **four mechanisms, not one**:
  1. **Computed** — sympy derives the answer (math/chem recipes).
  2. **Selected** — a number from a cited dataset, a quote from a real source, a competence from the catalog.
  3. **Curated** — vetted truth fact-checked at the gate (annotated texts, history facts, qual. chem tables).
  4. **Re-expressed under constraint** — authored prose over a *frozen sourced fact-set*, with a
     **deterministic entity-lint** (every date/name/quote in the prose must appear in the fact-set) — so the
     *authoring itself* is correct-by-construction. This is the Sachverhalt Darstellung
     (`sachverhalt-content-layer-design.md` §12-Q1). *"Select the facts, author the expression."*
- **Boundary** *(the anti-over-constraint clause).* **"Select, never author" is the strong proxy that applies
  to FACTS. It was never meant to forbid EXPRESSION.** Authoring prose, narrative, explanation, and didactic
  framing is **allowed and wanted** wherever it is a projection of given facts — it is the *same shape* as the
  rendering layer (§1): a projection that cannot reach back and invent content. The mechanism that keeps it
  honest is not "don't author" but: (a) the pass sees only the frozen fact-set; (b) a deterministic entity-
  lint; (c) the SME/teacher as final guard (§7); (d) a `sensitive` flag for the ~5 topics where *tone* (not
  factual contestation) has real stakes. **Do not read "select, never author" as "the LLM may not write
  prose."** That blocks the single highest-value content direction we have. The line is **FACT vs
  EXPRESSION**, not prose vs no-prose. And a teaching tool is not a research citation: conveying *what
  happened and what it means* outweighs pedantic precision — the entity-lint keeps the dates right anyway, so
  we don't trade them away.

## 4. Grounding is real; gaps are honest

- **Rule.** Anchor to the real catalog (`lehrplan/`), verbatim competences, `grade_check` against curated
  grounding. Anything uncurated surfaces as an **honest gap note** — never a faked anchor.
- **Why.** "Provably competence-aligned" is a trust feature. An admitted gap is recoverable; a fabricated
  anchor poisons the guarantee.
- **Boundary.** The catalog is *editable* (re-run the parser / edit the JSON) — correcting grounding is not a
  code change and not a violation. Gaps are an expected output, not a failure state.

## 5. Two model layers, one seam

- **Rule.** `schema/` holds full-fidelity canonical models; `schema/generation_views.py` holds recursion-free
  mirrors the LLM emits; **all** LLM↔storage conversion goes through `to_canonical()`.
- **Why.** Isolate the brittle LLM-emission shape from storage; one up-conversion point to reason about.
- **Boundary.** An implementation seam, not a product limit. The generation views *are* a place the model
  authors structured output — validated on the way in. (So "the model emits nothing structured" is false; it
  emits generation views, which the seam validates.)

## 6. Provenance & rights gates guard EXPRESSION, not facts

- **Rule.** Embedding someone's **expression** (a quote, a close paraphrase, a whole text, an image, a voice)
  needs a clear basis: CC / explicit-redistributable / **PD by the AT 70-Jahre-p.m.a. rule** / **Zitatrecht**
  (§42f öUrhG) for short quotes. A `role="facts"` source carries **no** obligation. Media-policy: content-
  bearing visuals must be code-gen or vetted-sourced; decorative must be content-free.
- **Why.** Legal redistributability + the *mandatory-internal* fact-check (an `original` fact block must name
  a `role="facts"` source, so the fact is checked at the gate, not asserted).
- **Boundary.** These gates are about **rights and fact-checkability**, **not** a brake on authoring. *Facts
  are free* — copyright protects expression, not facts; a date or a causal claim needs no licence. A short
  quote *rides* Zitatrecht (it's a green light, not a prohibition). The gate's job is to say "yes, with this
  attribution", not "no".

## 7. A human (SME) is the final gate — and that is what *lets* us author

- **Rule.** Two HITL review gates; nothing reaches the approved library without SME approval. The store holds
  review items + the approved library only — **no gradebook, no classroom state, no student PII**.
- **Why.** The SME is the final guard on correctness and tone. Scope discipline: *we make the material, we do
  not run the room.*
- **Boundary.** The SME guard is an **enabler**, not only a constraint: it is *why* we can relax authoring
  (§3) and present a finished Darstellung — there is always a domain expert between us and a student. At
  breadth scale the guard thins (one teacher per sheet, no feedback loop), which is exactly why §3's
  *deterministic* entity-lint matters more than a human skim there.

## 8. `intentionally_flawed` assets are built wrong on purpose

- **Rule.** An asset flagged `intentionally_flawed` is generated incorrectly *by design* and never
  "corrected"; a guard prevents the correct generator from being substituted.
- **Why.** Pedagogy — these teach error-spotting. "Fixing" one destroys the lesson.
- **Boundary.** Narrow; applies only to flagged assets. Everywhere else, correctness rules.

## 9. Every store is a `JsonStore`; upsert preserves review status

- **Rule.** All stores subclass `store/base.py::JsonStore` (shared I/O, sequential ids, status-preserving
  `upsert`). Re-seeding never un-approves.
- **Why.** One persistence seam (a future SQLite backend swaps behind it); SME decisions survive re-seeds.
- **Boundary.** Implementation. The backend is swappable; the seam is the invariant, not the JSON files.

---

## Looks like a hard rule, but isn't (don't let these block you)

| Phrase you'll see | What it really means | Free to change |
|---|---|---|
| "select, **never author**" | never originate a *fact*; **expression is fine** (§3) | author prose/narrative over given facts |
| "no HTML→PDF" | rendering is a *pure projection* (§1) | the renderer tech (Typst/HTML/docx all OK) |
| "breadth is render-free" | a pragmatic default for bulk ingest | render any batch when you want to |
| "the model produces nothing" | it produces *generation views*, validated at the seam (§5) | what the model emits, within the seam |
| German output · Carlito font · ReportLab | product/UX conventions | freely, per need |

## How to change an invariant

These are durable, not sacred. If one genuinely blocks the product, **change the rule explicitly here**
(with a dated note and the new rationale) rather than quietly working around it — a worked-around invariant
is how the codebase and the docs drift apart. §3 is the worked example: it moved from "select, never author"
to "never originate a fact; expression is fine" on 29 Jun 2026, and that change is recorded, not implied.
