# History asset class — facts-layer reuse & expression provenance (design note)

**Status:** design proposal, agreed-before-build. Decisions taken with the SME (28 Jun 2026):
(1) a Wikipedia-sourced *original* history block must carry a **mandatory facts-source record + HITL
fact-check** — legally optional, but required for our trust posture; (2) design **all three
`expressionOrigin` values at once** (original · adapted · quoted), i.e. both the facts-layer and the
embedded-source-stimulus paths together; (3) this session's deliverable is **this doc + the schema
proposal**, no engine code yet.

**Companion brief:** `facts-layer-extraction-design-note.md` (the SME's IP rationale; the
facts-vs-expression line we engineer around). *Not legal advice — a defensible default posture.*

---

## 1. What this is, and where it sits

The project already has four "asset classes", each built by finding the thing that is
*correct-by-construction* (or *by-curation*) and making it the durable, reusable, HITL-vetted asset:

| asset class | subject | the durable thing | trust guarantee |
|---|---|---|---|
| Grounded-facts data layer | GWB/MINT | a cited dataset (real numbers) | (a) select-never-author; figures derived |
| Parametric Maths engine | MAT | a sympy recipe | (a) computed answer + Rechenweg |
| Annotated authentic texts | DEU/LAT/FS | a PD text + vetted annotation layer | by-curation; answer = the annotation |
| Audio / Hörverstehen | FS | a vetted script + TTS seam | by-curation; transcript = fallback |

**This note adds the fifth: GPB (Geschichte und politische Bildung) — history.** Its durable asset is a
**curated, provenance-stamped facts layer** plus, where a real source is embedded, a **rights-gated
source stimulus**. The subject is a near-perfect fit: GPB's own first competence is
`GPB.US.2.ALL.01 — "Quellen und Darstellungen unterscheiden"` (distinguish **sources** from
**accounts/representations**). The facts-vs-expression line the IP brief makes us engineer around **is**
GPB's Historische Methodenkompetenz. Here the legal posture and the pedagogy are the same act — citing
and weighing a source *is* the curriculum (as Quellenkritik/Datenkompetenz already is for the data layer).

## 2. The principle, and the tension it creates with our core discipline

**The IP principle (from the brief):** copyright protects *expression*, not *facts*. CC BY-SA's
attribution + ShareAlike attach to Wikipedia's specific wording/selection/arrangement, never to the
underlying facts. So the question to track per block is **not** "where did the facts come from?" but
**"where did the *expression* come from?"** Author a block fresh from facts → no obligation, even if
those facts were read off Wikipedia. Paraphrase or copy Wikipedia's text → obligation attaches.

**The tension with the project.** Our load-bearing rule is **select, never author**: facts come from a
*deterministic tool that fetches and parses a real source*, never from the model — because "a fabricated
citation is worse than an invented number; it looks verified." The brief's *headline* mechanism is the
opposite: the model **reads** Wikipedia, **extracts** facts, and **authors fresh prose**
(`expressionOrigin: original`), rendering clean with no citation. That is the strongest *copyright*
move — and, taken literally, it reintroduces exactly the risk we engineered out everywhere else: an LLM
asserting historical facts with no deterministic check.

**Why we can't just reuse the data-layer guarantee.** There is no CSV for *"why the Congress of Vienna
mattered."* History prose facts (events, dates, causation, significance) don't reduce to a parseable
dataset, so the **(a) correct-by-construction** guarantee is structurally unavailable. This is a *new
category* — the **prose-facts case** — and it can only be made trustworthy the way the annotated-texts
class is: **correct by curation** (HITL-vetted), not by computation.

**The resolution (decision 1).** We adopt the brief's facts-vs-expression encoding for *copyright*, but
we **harden it for trust**: an `original` history block that asserts real facts must carry **at least one
recorded `role:"facts"` source** (stored, reviewer-visible, fact-checked at the GPB review gate), even
though that record is legally optional and not student-rendered. The brief calls this "optional editorial
transparency"; in our pipeline it is **mandatory-internal**. That single move keeps a Wikipedia-sourced
history block *inside* the project's identity — "the model never asserts an unchecked fact" — instead of
quietly outside it. The provenance stamp is what makes both the vetting and the rendering auditable.

> **The sharper history subtleties the brief flags — and we must enforce at the curation gate:**
> brute fact vs. interpretation ("Battle X, 1815" is a fact; "X was the turning point because…" is
> authorial *analysis* = expression — re-derive or attribute, never lift as a "fact"); selection &
> arrangement carry thin protection, so the **Lehrplan competence structure sets the order**, not the
> article's outline; distinctive phrasing is expression → quote-and-attribute, don't paraphrase. The EU
> sui-generis database right is a non-issue here (per-worksheet extraction is insubstantial *and* CC BY-SA
> licenses database rights anyway). These are reviewer-facing checks, surfaced in the GPB review UI.

## 3. The invariant, extended to prose

Today `verify` enforces — for **numbers/figures** — that every content-bearing claim is exactly one of:
**(a)** correct-by-construction · **(b)** vetted-sourced + cited · **(c)** explicitly illustrative
(`pipeline/media_policy.py` + `figure_lint.py`). We extend the *same* invariant to **prose history
claims**, mapped through expression provenance:

| block actually contains | `expression_origin` | obligation | our trust gate (verify) | rendered |
|---|---|---|---|---|
| brute fact / fresh synthesis from facts | `original` | none | **facts-source required** (≥1 `role:"facts"`) | clean — no attribution line |
| close paraphrase tracking the article | `adapted` | CC BY-SA (derivative) | redistribution gate + ShareAlike flag | "Quelle/Lizenz" line |
| verbatim quotation | `quoted` | short = Zitatrecht; long = CC BY-SA | quote-length flag for review | attribution always |

Two derived booleans, **computed never authored** (like `Nachweis`/`DepthProfile`):
`attribution_required = expression_origin != "original"` and `share_alike_applies = attribution_required
and any source licence is CC-BY-SA`. The renderer emits a source line **only** when `attribution_required`.

**The new prose gate** (`pipeline/prose_lint.py`, run inside `verify`, a *warning* like the (c)-label —
not an error, to tolerate false positives): a history InfoBlock (or a TaskBlock with source-derived
stimulus) that asserts real-looking facts must carry `provenance`; an `original` block with **no**
`role:"facts"` source warns ("history block asserts facts with no facts-source recorded"); an
`adapted`/`quoted` block whose source is not redistributable, or whose verbatim span is long, warns for
review. **Scope of the gate:** subject == GPB, *plus* an opt-in `historical_fact` content flag so the
cross-subject cases (GWB local history, KUG art history) are covered without false-flagging every prose
block in every subject.

## 4. Schema proposal

A new **third provenance axis**, orthogonal to the two we already have:

- **fact provenance** (numbers): `SourceRef`/`DataRef` — *where the number came from* (`schema/datasets.py`)
- **rights provenance** (whole texts): `TextSourceRef.is_clear()` — *may we redistribute this text*
  (`schema/texts.py`)
- **expression provenance** (prose blocks) — **new** — *where the wording came from*

It attaches to **`BlockBase`** (so both `InfoBlock` and `TaskBlock` inherit it — a TaskBlock can embed
source-derived stimulus), optional, defaulting to absent for the common case (math, original prose with no
source). New file `schema/provenance.py`, imported by `schema/blocks.py`:

```python
# schema/provenance.py  — pure schema, imports nothing from llm/ or pipeline/
ExpressionOrigin = Literal["original", "adapted", "quoted"]
SourceRole       = Literal["facts", "expression"]   # consulted | wording-derives-from

class ProvenanceSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    url: str | None = None
    publisher: str | None = None          # "Wikipedia (de)", "ANNO/ÖNB", …
    licence: str | None = None            # "CC-BY-SA-4.0" | "public-domain" | "CC-BY-4.0" | …
    licence_url: str | None = None
    retrieved: str | None = None          # ISO date the source was consulted
    role: SourceRole                      # "facts" = no obligation; "expression" = obligation
    redistributable: bool = False         # may the wording be embedded? (gated at ingest)
    author_death_year: int | None = None  # AT 70-p.m.a. check for PD `expression` sources
    quote_span: str | None = None         # the verbatim snippet, for `quoted` (length → review flag)

class BlockProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expression_origin: ExpressionOrigin = "original"
    sources: list[ProvenanceSource] = Field(default_factory=list)

    # DERIVED — computed, never authored (mirrors Nachweis/DepthProfile discipline):
    @property
    def attribution_required(self) -> bool:
        return self.expression_origin != "original"
    @property
    def share_alike_applies(self) -> bool:
        return self.attribution_required and any(
            (s.licence or "").upper().startswith("CC-BY-SA") for s in self.sources)
```

`BlockBase` gains: `provenance: BlockProvenance | None = None`. `ContentFlags` gains
`historical_fact: bool = False` (the cross-subject opt-in for the prose gate).

**Two model layers, one seam (the project rule).** The generation view mirrors the *authored* fields the
LLM/subagent declares — `expression_origin` + `sources` (with `role`) — exactly as it mirrors
`serves`/`data_source`. The **derived** booleans are absent from the generation view and computed at
`assemble` (never let the model produce `attribution_required`). `to_canonical()` builds `BlockProvenance`
from the flattened mirror. This is the same split as `Serves`/`DataRef` everywhere else.

**Why a new model and not a reuse of `TextSourceRef`/`SourceRef`:** those answer different questions.
`SourceRef` cites *a number's dataset*; `TextSourceRef.is_clear()` gates *redistributing a whole text*.
`BlockProvenance` records *per-block expression origin* — the legal-obligation pivot the other two don't
carry. It *reuses* their rights vocabulary (licence, `author_death_year` for the AT-pma rule,
`redistributable` as an ingest gate) so the three stay consistent.

## 5. The two paths — designed together, used very differently

### Path #1 — Wikipedia as a *facts source* for original blocks (`expression_origin: original`)
The headline, **lower legal risk, higher leverage.** No redistribution → no CC BY-SA, no ShareAlike,
renders clean. The cost is **not** licensing; it is the **fact-vetting obligation** (decision 1): the
`role:"facts"` source is mandatory-internal and the block is fact-checked at the GPB gate. A worksheet is
composed/generated normally; the new thing is the provenance stamp + the prose gate. *This is the default
posture for the history asset class.*

### Path #2 — Wikipedia *text* embedded as a source stimulus (`adapted` / `quoted`)
Real Quellenarbeit on the article's wording — **rights-heavier**, and it **reuses the existing
`AnnotatedText` engine**: an embedded excerpt is the line-numbered `source_text` block, and Quellenkritik
annotations (who/when/why/bias → GPB Methodenkompetenz) drive tasks whose answers are the vetted
annotations. What's new on top of the existing engine:
- **CC BY-SA is a redistributable-but-encumbering licence.** ShareAlike means an `adapted` derivative can
  push the *worksheet* under CC BY-SA — a **worksheet-level** consequence, not just a per-block
  attribution line. For a product that may be sold, this matters. **Recommendation: `adapted` is rare and
  deliberate; prefer `original` (path #1) or short `quoted`.**
- **Short verbatim quotes → lean on the Austrian Zitatrecht (§42f öUrhG)**, not CC BY-SA — the
  Austria-correct version of the brief's "short = citation/fair dealing." `quote_span` length drives a
  review flag; attribution is always rendered.
- **AT 70-p.m.a., not US PD**, and **PD work ≠ PD reproduction** — already in `TextSourceRef`; a `quoted`
  PD source records `author_death_year` and is checked against the AT rule, as the texts engine does.

**Rights gate at ingest** (the `orch.ingest_text` analogue): a block may carry embedded wording
(`adapted`/`quoted`) only on a recorded redistributable basis (CC BY-SA *with* the ShareAlike consequence
recorded, or Zitatrecht for a short quote, or PD-pma-clear); `original` needs no rights gate, only the
facts-source record.

### Images — out of band (the brief's separate reminder)
Wikipedia/Wikimedia images are **licensed individually**; never inherit the text licence. These route
through the **existing asset rights gate** (media-policy "vetted-sourced" class, per-file rights tag,
"PD work ≠ PD reproduction"), **not** through `BlockProvenance`. No new mechanism — just the rule that an
image's licence is resolved at ingestion independently of any text on the same block.

## 6. Rendering (pure projection — no new renderer)
Same discipline as the `Quelle:` line under data figures: a pure function of `BlockProvenance`. The
renderer prints a source/attribution line + the licence link **only** when `attribution_required`;
`original` blocks stay clean. The line is **student-visible** — Quellenkritik is curriculum, and the
teacher projection additionally shows the full `sources` list (incl. the `role:"facts"` records hidden
from students) so the teacher sees the evidentiary basis. Nothing reaches into `pipeline/`; `rendering/`
keeps importing only `schema/`.

## 7. HITL — review surface, verify gate, ingest
- **verify:** `pipeline/prose_lint.py` (the prose analogue of `figure_lint`), run in `verify` as a
  warning lane (§3 above).
- **review surface:** the GPB worksheet review (Inhalte/Bausteine) shows each block's
  `expression_origin`, its `sources` with `role`, the derived obligation, and the history subtleties
  checklist (fact vs. interpretation, structure-not-borrowed, quote-length) so the SME fact-checks and
  signs off. Reuses the central feedback store (a new target kind isn't needed — blocks already carry
  feedback).
- **ingest:** the rights gate of §5 (only `adapted`/`quoted` are gated; `original` needs the facts-source
  record). The data path stays LLM-free where it can: a small deterministic helper records the Wikipedia
  `ProvenanceSource` (title/url/retrieved/licence) from the article metadata, so the *citation* is never
  model-authored even when the prose is.

## 8. Flagship worked example (to build after agreement)
**"Der Wiener Kongress" (GPB, ~3. Klasse Unterstufe)** — Austria-central (Metternich), the brief's own
example:
- an `original` InfoBlock authored fresh from facts, `provenance.expression_origin = "original"`,
  `sources = [Wikipedia "Wiener Kongress", role:"facts", retrieved 2026-06-28]` → renders clean, the
  facts-source visible only to the teacher and at review;
- a Quellenarbeit TaskBlock embedding **one short `quoted` snippet** (Zitatrecht, attribution rendered)
  to exercise `GPB.US.…ALL.01` "Quellen und Darstellungen unterscheiden" — the path-#2 demonstration;
- competences: Historische Methodenkompetenz + Orientierungskompetenz; verify-clean incl. the new prose
  gate. Locked by a test like `tests/test_library.py` does for the other flagships.

## 9. Build plan (phased — each phase agreed before the next)
1. ✅ **DONE (28 Jun 2026) — Schema.** `schema/provenance.py` (`ExpressionOrigin`, `SourceRole`,
   `ProvenanceSource`, `BlockProvenance`); `BlockProvenance` on `BlockBase` + `ContentFlags.historical_fact`;
   generation-view mirror on `GenInfoBlock`/`GenTaskBlock` + `to_canonical` pass-through; the obligation
   booleans (`attribution_required`/`share_alike_applies`) are `@computed_field` properties — present in the
   *serialization* schema (API/review surface) but absent from the *validation* schema (the model is never
   asked to author them), and a `mode="before"` validator strips any echoed booleans so the
   `model_dump()→model_validate()` JsonStore round-trip stays clean. 4 new round-trip tests; full suite **170 green**.
2. ✅ **DONE (28 Jun 2026) — verify.** `pipeline/prose_lint.py` (the prose analogue of `figure_lint`),
   wired into `verify` as a warning-lane (advisory, never blocking — like the (c)-label). Two checks:
   **(A) consistency** wherever provenance is present (any subject) — `adapted`/`quoted` must name a
   `role="expression"` source; an `adapted` redistribution needs `redistributable`; a long `quoted` span
   exceeds Zitatrecht; CC-BY-SA trips ShareAlike; and **(B) the mandatory-internal facts-source rule**,
   scoped to **GPB ∪ `historical_fact`** (GPB detected by the served competence-id prefix `GPB.`, the
   robust signal) — an `original` history fact block with no `role="facts"` source warns, as does a
   fact-bearing InfoBlock (`prose`/`key_fact`/`example`/`source_text`; `callout` exempt) with no
   provenance at all. The PD-70-p.m.a./redistribution *rights* gate stays at ingest (Phase 4); verify is
   date-free. 10 new tests; full suite **180 green**; existing non-GPB worksheets stay clean.
3. ✅ **DONE (28 Jun 2026) — rendering.** A pure `_provenance_flowables(prov, projection, S)` in
   `rendering/blocks_to_flowables.py`, called from both info + task blocks (no new imports — reads
   `block.provenance`, so `rendering/` still imports only `schema/`). **Student/homework:** a
   `Quelle: „…“ · Lizenz: CC BY-SA 4.0 (link)` line **only** when `attribution_required` — `original`
   blocks stay clean. **Teacher:** the full `Provenienz: …` panel listing every source incl. the
   `role="facts"` records hidden from students (the evidentiary basis to fact-check), plus the derived
   `Quellenangabe erforderlich`/`ShareAlike` flags. 4 new projection tests; full suite **184 green**.
4. ✅ **DONE (28 Jun 2026) — ingest/HITL, proven on a real ingestion.**
   - **Rights gate:** `ProvenanceSource.rights_clear(year)` + `BlockProvenance.rights_gate(year)`
     (schema, mirroring `TextSourceRef.is_clear`) — a CC / explicit-redistributable / AT-70-p.m.a.-PD
     basis clears embedding; a short `quoted` span (≤`SHORT_QUOTE_MAX_CHARS=300`) rides the Zitatrecht.
     Wired into `orch.ingest_generated` via `_check_provenance_rights` **before** assemble: a non-clear
     `adapted`/`quoted` block raises → the item carries the error and **nothing is staged/harvested**
     (the `ingest_text` discipline; compliance is legal, not cosmetic). `original`/facts-only is always
     clear.
   - **Wikipedia source-record helper:** `tools/fetch_wikipedia.py::fetch_source(title, lang, role)` —
     **deterministic, metadata-only** (REST summary → canonical title + a **permalink to the exact
     revision** + CC-BY-SA licence + retrieved date), no article prose, **no LLM in the fact path**.
   - **Review surface:** a `prov(b)` panel in the dashboard (`api/static/index.html`) on every block —
     origin + the derived `Quellenangabe erforderlich`/`ShareAlike` flags + the full sources list incl.
     the `role="facts"` records, so the SME fact-checks the basis. The API already serializes provenance
     (incl. the computed booleans), so the panel populates with no endpoint change.
   - **Real ingestion (proof):** live-fetched the *Wiener Kongress* facts record and ran three bodies
     through `ingest_generated`: **(A)** original-from-Wikipedia-facts → verify-clean, 4 blocks
     harvested, the permalink record survives the harvest, students see no source line; **(B)** adapted
     from CC-BY-SA → permitted but ShareAlike-warned; **(C)** adapted from a copyrighted textbook →
     rights gate rejects, 0 harvested. Artifact: `runs/ingest/gpb_history/wiener_kongress.json`
     (git-ignored). 6 new offline tests (mocked fetch — no network in CI); full suite **190 green**.
   - **Honesty note:** the real ingestion proves **path #1** (facts → original) only; we deliberately did
     **not** fabricate a historical quotation for shipped content (that would violate select-never-author).
     The `quoted`/`adapted` paths are exercised by the rights gate + the deterministic tests; a real
     embedded primary-source quote belongs to the Phase-5 flagship (a verifiable PD text).
5. ✅ **DONE (28 Jun 2026) — flagship.** `library/gpb_wiener_kongress.py::build_content()` — GPB 3. Kl.
   *Der Wiener Kongress*, verify-clean **and warning-clean** (the quality bar). It exercises **both**
   provenance paths on real content: an **original-from-Wikipedia-facts** learn text (the baked permalink
   record, renders clean for students) **and** a **real PD primary source** — a short verbatim excerpt of
   the **Deutsche Bundesakte, Artikel I (8. Juni 1815)** from Wikisource, `quoted` under Zitatrecht
   (272 chars ≤ 300), attributed on the student sheet. The through-line is the asset class's own competence,
   *Quellen und Darstellungen unterscheiden* (Wikipedia = Darstellung, Bundesakte = Quelle). Staged via the
   new `orch.stage_worksheet` primitive + `library.seed_history()` (wired into `python -m teachersaid seed`,
   the Inhalte tab). Locked by `tests/test_gpb_wiener_kongress.py` (6 tests). The quotation is **selected,
   not authored** — verified verbatim against the Wikisource transcription, never fabricated.

   *Verified by render:* the student sheet shows the learn text with no source line + the Bundesakte
   "Quelle: … Lizenz: gemeinfrei"; the teacher guide shows the hidden `[Fakten]` Wikipedia permalink +
   the `[Formulierung]` Bundesakte record. Full suite **196 green**.

---

**FEATURE COMPLETE (Phases 1–5, 28 Jun 2026).** The History/GPB asset class — the 5th — is built end to
end: expression-provenance schema → prose verify gate → pure attribution rendering → ingest rights gate +
Wikipedia fetch helper + review surface → the test-locked *Wiener Kongress* flagship. **Next (optional):**
a subagent breadth pass for GPB the way the data layer was scaled, and — only if a real embedded source-text
demand appears — revisit the discouraged `adapted` path under an explicit ShareAlike product decision.

## 10. Open questions still to settle
- **ShareAlike product stance:** do we ever want a worksheet to become CC BY-SA-encumbered (any `adapted`
  block)? Default proposal: **no** — `adapted` is allowed by the schema but discouraged by policy/UI;
  prefer `original` + short `quoted`. Confirm.
- **Multi-source triangulation:** the brief recommends triangulating facts across >1 source so no single
  article's selection/arrangement dominates. Do we *require* ≥2 `role:"facts"` sources for an `original`
  history block, or treat it as a review nudge? (Proposed: nudge, not a hard gate.)
- **Where the facts-record helper draws metadata:** Wikipedia REST summary API (title/url/revision/
  timestamp) vs. manual entry. (Proposed: deterministic API fetch for the *citation fields only* — never
  the facts — mirroring `tools/fetch_*`.)
