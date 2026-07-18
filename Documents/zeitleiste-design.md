# Zeitleiste redesign — from paragraph towers to a Schulbuch-Zeitband

*Status (18 Jul 2026): **BUILT** — same-day, after the SME greenlit the design ("lets build
this"): `pipeline/zeitleiste.py` (the computed Scene family) + the `matplotlib:zeitband` recipe,
the additive schema deltas, the Sachverhalt derivation + hard strand gate, 19 tests, engine
specimens. The ► decisions below were resolved at build per this doc's recommendations —
resolutions noted inline at each ►. Still with the SME: the German surfaces + the M2 curated
Austrian events (gate backlog), and the `arbeitsobjekt`-default call (built default-OFF).
Trigger: SME revise on c0213 (Kolonialismus) and c0214 (Europäische Integration) — "overlapping
again … this is really something that has to be properly redesigned." The geometry FIX in the
legacy recipe shipped first and independently (§1), so nothing staged could overlap while the
redesign landed.*

Design mockups: `python -m tools.zeitleiste_mockup` → `runs/specimens/zeitleiste/m{1..4}_*.png`
(the REAL c0213/c0214 content in house figstyle). Engine specimens (the built recipe's actual
output, same cases + demotion): `python -m tools.zeitband_specimen` → `engine_*.png` beside them.

## 1 · Diagnosis — why the old form kept failing

**The bug (fixed 18 Jul).** `lane_pack` solved horizontal collisions, but the old `_timeline`
sized lanes with a fixed data-unit constant while text is sized in *points*: the y-range was
widened after drawing, proportional to the lane count, so with many lanes each text line
occupied ~3× the data-height the constant assumed — labels overtopped their lanes. The fix:
the vertical layout is computed in TRUE inches (one data-y unit == one inch; figure height
derives from the packed lane count), so a lane is exactly as tall as its measured text.
Regression-locked by `tests/test_layout.py::test_timeline_no_overlap_with_tall_label_towers`
(the real c0213 events). Why no gate caught it: breadth ingest is deliberately render-free and
the dashboard's self-heal render runs no layout lint — `overlap_pairs` fired only in tests,
on a fixture too short to break the constant.

**The didactic weaknesses (the real problem — the bug was a symptom).**

1. **Paragraph labels.** Full sentences floating on leaders are a text block scattered in
   space, not a timeline; the figure competes with the Darstellung instead of complementing
   it. (`HistEvent` already HAS the right split — short `label` + one-line `text` — nothing
   enforces it, so generated content stuffs sentences into `label`.)
2. **Points only.** History is Zeiträume und Prozesse; the spec smuggles "(bis 1908)" into
   prose because there is no end date. Ereignis-vs-Zeitraum is core Zeitvorstellung and the
   figure cannot draw it.
3. **No structure.** Equal dots, no phases, no Zäsuren, no perspective — the figure adds
   nothing over the chronology task's sorted list. Fails the blackboard test.
4. **Linear axis + clustered history = dead space.** And the fix must NOT be a log or silently
   broken axis: *gleicher Abstand = gleiche Dauer* IS the didactic point of a Zeitleiste.

## 2 · Principles (the admission test for any timeline form)

- **Stichwort statt Satz** — the axis carries year + short name; the sentence lives in the
  Darstellung (or a numbered legend). Enforced, not hoped for (►1).
- **The scale is visible** — regular decade/century ticks + the Zeitpfeil arrowhead. Equal
  spacing = equal duration, *shown*. Linearity is sacred; a zoom is allowed only as an
  explicit, honest window (M3), never as a break.
- **Ereignis = dot · Zeitraum = bar** — the distinction is itself teachable content.
- **Structure over listing** — phases (Periodisierung), Zäsuren, semantic lanes, and the
  `focus` role for the event the sheet is actually about.
- **Prefer the work object** — a timeline students *construct* beats one they look at.

## 3 · The four forms (one visual language, rising ambition)

| form | what it adds | when |
|---|---|---|
| **M1 Zeitband** (default) | short labels alternating above/below · ticks + Zeitpfeil · phase band · Zäsur rule · focus event | every timeline |
| **M2 Synchronoptik** | two SEMANTIC lanes (e.g. europäische Ebene ↑ / Österreich ↓) with lane captions; lanes mean something instead of being overflow parking | when the fact-set carries a curated strand split (Herrschaft/Widerstand · Europa/Österreich · …) |
| **M3 Lupe** | main band full-span + shaded window expanded into a second, internally-linear zoom band (explicit connectors); spans as bars | when events cluster (deterministic trigger, ►3) |
| **M4 Arbeitsobjekt** | student projection: year chips on the axis + Ereignis-bank with blanks ("trage das passende Jahr ein"); teacher projection = the solved M1 band; harder variant masks the years | Sachverhalt sheets — fuses with the chronology task (►4) |

M2 note: the mockup's Austrian events (1955 Staatsvertrag/Neutralität · 1972
Freihandelsabkommen · 1989 Beitrittsansuchen · 1994 Volksabstimmung 66,6 % Ja) are curated
ADDITIONS for the mockup, not in the c0214 spec — in production strands and their events come
from the Sachverhalt fact-set, SME-gated like everything else.

## 4 · Proposed data-model deltas (all additive — old JSON loads unchanged)

- **`HistEvent`**: `to: int | str | None` (a Zeitraum; `at`..`to` renders as a bar),
  `zaesur: bool = False`, `strand: str | None` (validated against a per-module
  `timeline_strands: list[str]` of exactly 2 curated lane names when present).
- **Timeline spec** (recipe input): `events[{at, to?, label, zaesur?, strand?}]`,
  `phases[{from, to, label}]` (curated Periodisierung band), `focus` (the highlighted event),
  `lupe: auto | off`. The Sachverhalt derivation fills `label` from `HistEvent.label` and
  keeps the sentence in the Darstellung / `text` — nothing new is authored at build time.
- **Generation views**: the `timeline` intent keeps its shape but the label-length lint (►1)
  applies at ingest, so breadth agents are steered to Stichwörter by the brief AND checked
  deterministically.

## 5 · Lint lanes

- **Label lint (ingest, deterministic):** a timeline event label over the length bound (►1)
  is a slip like any other ingest slip. Options per ►1: hard-reject (agent re-emits) or
  normalizer-style auto-demotion to numbered chips ①–⑦ + a legend built from the same strings
  (robust, matches the normalizer-first philosophy) — with an advisory warn either way.
- **Render-time overlap lint:** with inch-true layout the overlap class is structurally
  closed and test-locked; whether `overlap_pairs` ALSO runs on every QA raster as
  belt-and-braces (flagging into the review item) is ►5's second half.

## 6 · Architecture — promotion to a computed family

The target shape is the established two-tier pattern (`constructions.py` / `optics.py`): a
didactic recipe COMPUTES the figure from a small correct-by-construction spec; the LLM never
authors layout. Concretely: `pipeline/zeitleiste.py` builds a `Scene` (grouped layers: axis ·
phases · marks · labels · legend), so `Scene.select` gives density stages and per-event
masking gives the M4 projections — which also feeds the Mischpult (Abstraktion/Offenheit)
for free, because student and teacher sides derive from ONE master. The flat
`matplotlib:timeline` id stays alive for existing specs until migration (►5).

## 7 · ► Decisions (SME)

- **►1 Label policy.** Hard bound for axis labels (proposal: ≤ 32 chars, no sentence
  punctuation)? Fallback when violated: reject at ingest, or auto-demote to numbered chips +
  legend? And: does the sheet get a numbered legend under the figure at all, or do the full
  sentences live only in the Darstellung?
  — *Resolved: bound 32 (`zeitleiste.LABEL_BOUND`); auto-demotion to numbered chips + a legend
  under the band built from the same strings (no ingest rejection — normalizer-first); the
  advisory curation warn lives in `sachverhalt_lint`.*
- **►2 HistEvent deltas.** `to` / `zaesur` / `strand` (+ per-module `timeline_strands`) as
  proposed?
  — *Resolved: as proposed, plus curated `timeline_phases` (Periodisierung is judgment, so it is
  a curated field, not derived). All additive; strand totality is a HARD gate check.*
- **►3 Lupe trigger.** Auto rule (proposal: ≥ half the events within ≤ a quarter of the
  span → Lupe) vs explicit spec flag only? Max one window?
  — *Resolved: auto — ≥ 5 events AND the densest ⌈n/2⌉ consecutive events span ≤ ¼ of the full
  span; the minimal such window, snapped to round years; ONE window max; `lupe:"off"` or an
  explicit `{from,to}` override.*
- **►4 Arbeitsobjekt default.** Is M4 the DEFAULT student projection for Sachverhalt-derived
  timelines (the chronology ordering task fuses into the figure — no double-asking), or
  opt-in per sheet? Years-masked variant as the harder Offenheit step?
  — *Resolved conservatively: built as `variant="arbeitsobjekt"` off the ONE computed layout,
  default OFF in the derivation — the SME flips it after seeing engine specimens (one line).
  Years-masked variant deferred (follow-up).*
- **►5 Migration shape.** Scene-family promotion now (masking/stages/Mischpult from day one)
  vs flat recipe first? And: run `overlap_pairs` on every QA raster as a belt-and-braces
  review flag?
  — *Resolved: Scene family now (`zeitband_scene` → grouped Scene; inch-true rendering via
  `zeitband_figure`, not `scene_to_png`, because constrained layout would perturb the measured
  box). The legacy `matplotlib:timeline` stays for stored specs; `chart_choose` remaps the
  intent. QA-raster overlap lint deferred (follow-up — the overlap class is test-locked).*
- **►6 Strand vocabulary.** Free curated 2-name pairs per module (recommended) vs a small
  shared enum (Herrschaft/Widerstand · Europa/Österreich · …)?
  — *Resolved: free curated pairs (`timeline_strands`, exactly two when present); totality
  validated at the gate, never silently defaulted.*

## 8 · Out of scope (deliberately)

- Log axes, broken axes, non-linear time — never.
- LLM-authored scenes/layout — recipes compute; strands, phases, Zäsuren are curated facts.
- BC / "um 1500" dates: `at: int | str` keeps today's behavior (a string date doesn't place
  on the axis); a numeric `at_approx` + "um"-prefix display is a possible later delta, not
  part of this redesign.
- The Wirkungsgefüge / process_flow siblings — untouched; this doc governs the time axis only.
