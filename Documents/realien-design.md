# Annotated Realien — CEFR-leveled communicative reading for modern FS

**Status:** **Phase 1 BUILT (30 Jun 2026)** — design settled with the SME, flagship shipped.
Extends the annotated-text engine (`schema/texts.py`, `pipeline/text_tasks.py`) — no new top-level
type. Built: the `RolePlayPayload` (Sprechkarte) + `rb.cue_cards`; the `AnnotatedText` Realie fields
(`cefr`/`origin`/`scene`/`facts`, optional `source`) + the `communicative`/`roleplay` annotation
kinds; the derivation (scan · write-a-message · oral Sprechkarte with no write-space); the
internal-consistency `pipeline/realie_lint.py`; the simplified rights gate (`orch.ingest_text`);
the **A2 English "At the station"** flagship (`library/realie_bahnhof.py`); `tests/test_realien.py`
(9). Verify-clean, all three projections render, full suite green. Sibling of the Sachverhalt
content layer, deliberately at a **lower fact-rigor** (§0). Reuses the four correct-by-construction
mechanisms (`invariants.md §3`) and the breadth seam. Author-of-record: SME + Claude.

**Scope of this doc:** the design + the settled decisions (D1–D5) for the **Realien** asset —
CEFR-leveled, *communicative* reading material for the modern foreign languages (Englisch /
Französisch, subjects FS1/FS2), where the Lehrplan is can-do (A1–B2) and authentic native text is
the wrong difficulty. First build target: one or two flagships; breadth scales via the seam.
Latein and Deutsch keep the existing sourced-authentic-text path (they have abundant PD text at
the right level) — Realien is specifically the **modern-FS leveling answer**.

---

## 0. The organizing principle — *purpose-appropriate rigor*

Our correctness machinery exists to defeat the incumbent's failure — "the AI gets the facts
wrong." But the rigor must match the **didactic goal**, not be applied uniformly. The goal of a
Realie is **communicative competence** — the handful of useful phrases you need at a train station
— *not* conveying a true timetable. So the fact-rigor is relaxed **knowingly**: leniency is
allowed precisely because we can say *why* we grant it. A made-up `08:14 → Wien` misleads no one
and teaches "*Wann fährt der nächste Zug nach …?*" perfectly. Carrying the full Sachverhalt
fact-discipline here would be cargo-cult rigor — guarding a fact nobody is asserting.

> **The Realie is the *Anlass*, not the *Aussage*** — the pretext that provokes language, not a
> claim about the world. **Invent the timetable, vet the French.**

This principle is the load-bearing idea of the whole asset class; every decision below follows
from it. It is *not* a loosening of `invariants.md §3` — it is §3 applied correctly: the rule
binds **facts**, and a Sprechanlass has almost none. Where a Realie *does* assert a real-world
fact (§5, informational genres), the full rigor snaps back.

## 1. The problem — CEFR leveling fights "authentic"

Modern FS is the one subject the existing engines don't reach cleanly (`feature-roadmap.md`,
`matura-languages-coverage.md`):

1. **Half the Lehrplan is oral** (Sprechen is the largest KB, + Hören) — unreachable on a printable
   sheet (Hören is solved by the TTS engine; Sprechen is the residue).
2. **It is can-do / CEFR-leveled** (A1/A2 in the Unterstufe) — and **native PD text is the wrong
   difficulty**: a real French newspaper is C1, useless at A2.
3. **Modern, level-appropriate L2 text is not PD** — so it can't be *selected* verbatim and
   redistributed.

The reductionist read of "select, never author" says a Realie must be a real, rights-cleared,
verbatim everyday text — and then dead-ends on all three points at once. That read mis-applies the
FACT rule to EXPRESSION (`invariants.md §3` boundary).

## 2. The reframe — mechanism #4, then the didactic demotion

A Realie has the same **fact vs expression split** as a Sachverhalt:

- **Facts (substance):** a menu's dishes + prices; a Fahrplan's times + destinations + platforms.
- **Form (expression):** the target-language wording, at a target CEFR level, in the genre's
  conventions — *authored as a projection over the held set*. The Darstellung move, except the
  "Darstellung" **is** the everyday text, and the constraint gains "*in language L, at level C*."

That places Realien in **mechanism #4 (re-expressed under constraint)**, not blocked by mechanism
#2 (select). **But then §0 demotes the fact half:** because the Realie is a Sprechanlass, the facts
are a *coherence scaffold*, not world-claims. The learning is the interaction the board triggers
("*Frag am Schalter, wann der nächste Zug nach Salzburg fährt*"), and that is **essentially
independent of whether the facts are real.** So Realien keep mechanism #4's *shape* — authored
expression over a held set, with a deterministic guard — but the guard degrades from
*world-grounding* to *internal consistency* (§8).

## 3. The didactic core — communicative-first

The headline is the **interaction**, not comprehension. Comprehension / scanning is the *warm-up*
(and even there, see the bonus in §4). The value tasks:

- **Written-communicative** (printable, fully in scope): write the reply to "*verpasst — wann
  kommst du?*", complete the dialogue, fill the email, order from the menu in writing.
- **Role-play cue / Sprechkarte** (printable *cue*; the speaking happens in the room): "*A: am
  Bahnhof, frag nach dem nächsten Zug; B: am Schalter, antworte vom Plan.*" The Realie is the
  shared material both partners read.

The **oral core can't live on paper** — which is exactly the gap the **Lernarrangement**
`competence_anchor` already models (a competence served by the *interaction*, not by any printable
task; `schema/arrangement.py`, `pipeline/arrange.py`). So a communicative Realie composes with the
arrangement engine: v1 ships a printable Realie + a Sprechkarte (oral competence noted as
served-in-room); a later phase wraps it as a small Lernarrangement (Realie = shared material,
speaking = interaction anchor). **Two engines we already built meet here.**

## 4. What's load-bearing vs lenient

| Aspect | Status | Mechanism / guard |
|---|---|---|
| The **facts** (times, prices, names) | **lenient** — invent coherently | internal-consistency lint only (§8) |
| The **L2 language** (grammar, idiom) | **load-bearing** | curated — SME gate (mechanism #3) |
| The **CEFR level** | **load-bearing**, but | curated / SME-judged; *honestly not machine-verified* (§5-D4) |
| **Communicative-task soundness** | **load-bearing** | curated — SME + didactic review |
| **Internal consistency** (task answer ↔ shown text) | **load-bearing** | the light lint (§8), deterministic |
| **Real-world claims** (informational genres only) | **load-bearing** | fact-care / sourced (§5) |

> **Invent the timetable, vet the French.** Facts you can make up coherently; the language you
> cannot.

**Bonus property:** on a data-bearing hook, a scan answer ("*Was kostet das Tagesmenü?*" → "€9,50")
is a **datum from the held set** — *selected* and consistency-checked, not a curated judgment. So
even the warm-up comprehension is more correct-by-construction than a German interpretation task.

## 5. The honesty model — constructed-default, genre-driven

Two modes, but with the weighting **inverted** from the data/text layers:

- **Constructed (the DEFAULT).** Authored L2 over an invented-coherent set. **No `TextSourceRef`,
  no rights gate** — it is original pedagogical fiction (an authorship note suffices). The only
  residual honesty rule: a constructed Realie must be **recognizably pedagogical** (or labelled),
  so no false real-world belief is induced. `expression_origin="original"`.
- **Sourced (the exception).** The rare genuinely-authentic text you use verbatim (a real PD sign,
  a CC / open-data transit feed). `TextSourceRef` + the existing rights gate, as today.
- **Adapted (discouraged).** Simplify a real copyrighted text → `expression_origin="adapted"`,
  carrying rights/ShareAlike obligations — same policy as the GPB provenance layer. Prefer
  constructed-from-scratch over adapt-and-encumber.

**Fact-care is genre-driven** (cleaner than "data-bearing vs prose-y"):

- **Hook genres** — menu, Fahrplan, role-play scene, SMS/email, Einkaufszettel: **invent-coherent**.
  These assert nothing about the real world; the content is a pretext.
- **Informational genres** — "news-in-levels" snippet, a factual sign about a real place, a poster
  of real facts: **fact-care snaps back** (sourced or fact-checked), because a student *can* form a
  false real-world belief. Here the full §3 rigor (or a `Sachverhalt`/`Dataset` grounding) applies.

The `genre` tag therefore carries didactic *and* honesty weight: it selects whether the facts are
free.

## 6. Schema (extends `AnnotatedText`, no new top-level type)

Add to `schema/texts.py`:

- `cefr: Literal["A1","A2","B1","B2"] | None` — the controlled-input level tag (drives authoring,
  discovery, and the SME's level check).
- `origin: Literal["constructed","sourced","adapted"] = "constructed"` — the honesty mode (§5).
  `source: TextSourceRef | None` becomes **optional** (required only when `origin != "constructed"`).
- `scene: str | None` — the communicative situation ("am Bahnhof", "im Café") = the Sprechanlass framing.
- An **optional light internal fact-set** for hook data (`facts: list[RealieFact]` — e.g.
  `{slot, value}` rows like `{nach:"Wien", ab:"08:14", gleis:3}`) so the consistency lint (§8) and
  scan tasks have something to check against. Absent for prose-y hooks; the SME gate carries those.
- New `AnnotationKind`s: `communicative` (a write-a-reply / dialogue-completion task; `answer` =
  a model response) and `roleplay` (a Sprechkarte cue; `answer` = the teacher's expected moves).
  Existing `vocab` / `comprehension` are reused (comprehension = the scan warm-up).
- `serves` may include an **oral** competence flagged served-in-room (the arrangement-anchor hook).

`Realie` is just an `AnnotatedText` with `genre ∈ {Speisekarte, Fahrplan, …}`, `cefr` set, and
`origin="constructed"` as the norm. No second store, no second renderer.

## 7. Derivation (`pipeline/text_tasks.py` extension)

`build_worksheet(at)` gains the new kinds:

- `vocab` → a glossed Wortschatz scaffold (as today).
- `comprehension` → a **scan/locate** warm-up; its answer is the held datum (consistency-checked).
- `communicative` → a printable written task with a model answer in the teacher layer.
- `roleplay` → a **Sprechkarte** flowable (two cue boxes, A/B), printable; the oral competence is
  served-in-room — surfaced to the teacher, no write-space for the speaking itself.
- The Realie text renders as the line-/slot-referenced material block (a menu/timetable can render
  as a small `grid_table`; the legibility discipline of `reportlab_base` applies).

**Later (Phase 2):** `arrange.py` wraps a Realie as a `Lernarrangement` — the Realie as
`shared_product`/material, the speaking as an `interaction` anchor — reusing the v0.5 engine whole.

## 8. The lint — internal consistency, honest about its limits

`pipeline/realie_lint.py` repurposes the Sachverhalt entity-lint, **degraded to internal
consistency**: every price / time / platform / name referenced in a **task answer** (or
`grounded_by`) must appear in the shown Realie text or `facts` set (a genre-aware token matcher,
not the year-regex). It guards "*the worksheet doesn't contradict itself*", **not** "*the facts are
true*" — because for a hook there is no truth to check.

It explicitly does **NOT** (and cannot) verify **L2 correctness** or **CEFR level** — those are
SME-gated (mechanism #3). The doc and the lint say so plainly; we never claim a guarantee we can't
keep (cf. the CEFR honesty, D4). A later soft aid: a controlled per-level wordlist to *flag*
out-of-level vocabulary as a warning (advisory, never a hard gate).

## 9. Rights gate (simplified)

In `orch.ingest_text` (or a thin `ingest_realie`): `origin="constructed"` → **no source, no rights
gate** (original pedagogical fiction). `origin="sourced"` → `TextSourceRef.is_clear(year)` as
today. `origin="adapted"` → the provenance rights gate (CC / PD-pma / Zitatrecht) + the discouraged
flag. The facts (being invented) need no provenance; an informational-genre Realie that makes real
claims must instead carry a `role="facts"` source or ground in a `Dataset`/`Sachverhalt` (§5).

## 10. HITL + scaling — the Phase-3 seam, reused

Realien scale exactly like the Sachverhalte we just shipped:

- `tools/realien_prompt.py` — a per-scenario grounded brief: the **target language**, the **CEFR
  level**, the **genre + scene**, the **communicative goal**, the allowed FS competences (Lesen +
  the served-in-room Sprechen anchor), the load-bearing rules (*invent the facts coherently; the L2
  must be correct + at level; the task is communicative-first*), and the JSON shape.
- `tools/ingest_realien.py` — the `ingest_sachverhalte.py` twin: normalize the agent slips →
  schema → the **light gate** (origin/rights per §9 + the internal-consistency lint) →
  `build_worksheet` → `verify` → stage `in_review`. The SME gate then checks **the L2 and the
  level** (the part no lint can).
- Surface: the existing **Texte** tab hosts Realien (they are `AnnotatedText`s); `feedback`
  target kind `text`.

## 11. Phasing

- **Phase 1 — one flagship, end-to-end. DONE (30 Jun 2026).** The **A2 English "At the station"**
  Realie (`library/realie_bahnhof.py`, FS1 Kl 2): a *constructed* (no-source) departure board + a
  vocab scaffold + 3 scan tasks (Lesen) + a write-a-message task (Schreiben, boxed) + a Sprechkarte
  A/B pair (Sprechen, oral — `RolePlayPayload`→`rb.cue_cards`, **no write-space**). Verify-clean,
  the consistency lint green, all three projections render. `tests/test_realien.py` (9) locks the
  schema, the derivation, the lint (clean + catches an answer the board can't support), the oral
  no-write-space affordance, and that constructed rides no rights gate while sourced still does.
- **Phase 2 — a second genre + the arrangement wrap.** A café-menu A2 scene, then wrap a Realie as
  a Lernarrangement (speaking as an interaction anchor) — proving the two engines compose.
- **Phase 3 — breadth via the seam.** Menus, signs, messages, schedules, news-in-levels across
  A1–B2, EN + FR, subagent-authored, SME-gated for language + level.

## 12. Decisions (settled with the SME, 30 Jun 2026)

- **D0 — the meta-principle: *purpose-appropriate rigor*.** Match the correctness machinery to the
  didactic goal; grant leniency *knowingly*. The Realie is the Anlass, not the Aussage. **SETTLED.**
- **D1 — constructed mode is IN, and is the DEFAULT** (not a flagged exception). Most Realien are
  invented-coherent pedagogical fiction. **SETTLED.**
- **D2 — fact-care is GENRE-DRIVEN:** hook genres → invent-coherent; informational genres → fact-care
  / sourced. The `genre` tag carries the honesty weight. **SETTLED.**
- **D3 — rights model simplified:** constructed → no source / no gate (authorship note); sourced →
  `TextSourceRef` as today; adapted → discouraged + provenance gate. **SETTLED.**
- **D4 — CEFR level is curated / SME-judged, *honestly not machine-verified*.** No readability
  formula is trusted; a per-level wordlist may later *flag* (advisory) out-of-level vocab. **SETTLED.**
- **D5 — the task layer is communicative-first** (write-a-reply + role-play cue are the headline;
  scan/comprehension is warm-up); the **oral core is served via the Lernarrangement interaction
  anchor**, not faked on paper. **SETTLED.**

The substance is light by design; the language and the didactics are what the gate protects. The
SME (teacher) fact-checks the L2 and the level — the one thing only a human can.
