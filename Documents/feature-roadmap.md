# Feature roadmap — the live plan

Forward-looking *capability* features only. History lives in `project-handoff.md` (dated session
blocks); design depth lives in per-feature docs (map: `README.md`). The previous roadmap —
everything planned 26 Jun – 10 Jul 2026, now essentially built (Waves A · B · C, the eight tracks,
the two external-agent programs) — is archived verbatim at
[`archive/feature-roadmap-2026-06--07.md`](archive/feature-roadmap-2026-06--07.md).

## ▶ Start here — the 11 Jul 2026 idea pass (SME verdicts recorded)

A free brainstorm ranged over new task genres, beyond-curriculum topics, untouched subjects and
platform mechanics; the SME gave per-idea verdicts the same day. The frame stays **build-for-joy**
(intrinsic axis: new correct-by-construction domains · deeper engines · corpus structure · craft).
Every idea below carries its correct-by-construction angle — that is the admission test.

### The enabler — ✅ BUILT 11 Jul 2026

- **Three-tier anchoring.** ✅ `competence | uet | horizont` now travels from request/idea through
  resolution → planning → generation → verification → derived Nachweis → PDF/review summary.
  Existing content defaults to competence; ÜT requires the exact numbered subject/grade hook;
  Horizont hard-rejects hidden `serves`. Record: [`anchoring-modes.md`](anchoring-modes.md).

### Ready to build (greenlit 11 Jul)

**The flagship — der Tiefenregler („das Mischpult").** *(P1–P4 ✅ BUILT — P1 11 Jul; P2 Gerüst +
P3 Textlast + P4 capability discovery/dashboard Mischpult 12 Jul; composer faders investigated and
documented OUT (design doc §8 — the envelope is the composer's honest size control); lesson-purpose
presets ✅ BUILT 16 Jul (design doc §9). Still open from the description below:
Zusatz-★-blocks/tiered sub-questions as content genres. Contract:
[`tiefenregler-design.md`](tiefenregler-design.md).)* Depth as a teacher-facing control surface:
one worksheet, independent faders tuned *per sheet or per Baustein* before printing —
**Gerüst** (bare ↔ worked first step from `solution_steps` + misconception-fed hints +
Formulierungshilfen) · **Tiefe** (practice ↔ Begründen/Transfer/`solution_paths`) · **Umfang**
(kompakt ↔ extended; scope variants + time-fit) · **Abstraktion** (concrete entry + dense figure via
`Scene.select` ↔ formal, masked) · **Textlast** (simplified prose twin + glosses ↔ full register —
WSTF-measured) · **Offenheit** (auto-MC via the misconception engine ↔ guided ↔ open). Presets are
**lesson purposes**, not student levels (Wiederholung vor der Schularbeit · Vertiefungsstunde ·
Vertretungsstunde · Hausübung). Within-class depth lives INSIDE one shared sheet: optional
Zusatz-★-blocks, tiered a)→b)→c) sub-questions, and *selbstdifferenzierende* task genres. Every
fader is a **derivation over one master** (no forked content, ever; ONE teacher guide with the
profile stamped); the **Regler-Lint** verifies each fader measurably moves what it claims (WSTF ·
C4-estimate · AFB mix · competence coverage intact or honestly reported). Build shape: **P1–P4
built** — P1 pure-computation faders (Umfang · Tiefe · Abstraktion · Offenheit) → P2 Gerüst
(leak-guarded worked first step + misconception hints + Formulierungshilfen) → P3 Textlast (curated
`prompt_simple` twins + Wortschatz-Kasten, WSTF strict-decrease in the one lint) → P4 capability
discovery + dashboard Mischpult (composer integration investigated, documented out — design doc §8).
*(The rejected sibling is recorded under Rejected.)*

**Mischpult follow-ups:** lesson-purpose **presets** — ✅ **BUILT 16 Jul** (`LESSON_PRESETS` over
the one typed profile + dashboard chips with client-side capability intersection;
`tiefenregler-design.md` §9; the four didactic bundles await SME vetting). Still open: the
within-class depth genres — optional **Zusatz-★-blocks** and tiered a)→b)→c) sub-questions
(*selbstdifferenzierend*, inside ONE shared sheet) — which are content-genre work on
templates/blocks, not fader work.

**New task genres (engines):**
- ✅ **BUILT 16 Jul** · **Fermi-Werkstatt** — estimation as a curated decomposition chain
  (`schema/grounding/pipeline/fermi.py`): anchors with dataset/cited/vetted-estimate provenance →
  computed worked chain + interval-propagated acceptable range + Größenordnung framing;
  selbstdifferenzierend, leak-guarded on all projections; verbatim MAT anchors under MOD. 6
  problems. Design: [`fermi-design.md`](fermi-design.md).
- ✅ **BUILT 16 Jul** · **Fehlersuche engine** — worked solutions with one PLANTED, catalogued
  Fehlermuster, computed + honestly propagated (`pipeline/fehlersuche.py`;
  `TaskBlock.flawed_solution` student-facing, correct chain + location teacher-only); 3 MAT
  templates. Design: [`fehlersuche-design.md`](fehlersuche-design.md).
- **Messdaten-Werkstatt** — real measurement series (GeoSphere · NOAA · Statistik Austria) analysed
  as lab protocols: uncertainty, outliers, conclusions. The parked Versuch class side-stepped — no
  apparatus, pure data layer.
- **Beweis-Puzzles** — proofs as ordering/fill-the-gap tasks computed from a curated proof-step
  graph (Pythagoras, Winkelsumme, √2). Begründen/Argumentieren is a verbatim MAT dimension.
- **Kontrafaktisches Urteilen (GPB)** — "Was wäre, wenn …?" with the Sachverhalt as frozen
  fact-set, the counterfactual explicitly labelled speculation, the rubric rewarding fact-grounded
  reasoning (Urteilskompetenz).

**Content programs (ÜT-anchored / Horizont):**
- ✅ **BUILT 11 Jul** · **Finanzführerschein** (ÜT 13 verbatim) — Lohnzettel lesen (brutto/netto computed from
  Stand-stamped curated SV/Lohnsteuer tables, refreshed yearly like datasets), Handyvertrag-
  Vergleich, Inflation mit echtem VPI, Zinseszins als Freund und Feind.
- ✅ **BUILT 11 Jul** (GPB competence-mode; ÜT-7 tag missing on GPB competences → catalog correction is future work) · **Wahl-Werkstatt** (ÜT 7 + GPB; Wählen ab 16) — real Nationalrat results (BMI open data),
  **d'Hondt/Mandatsberechnung as a parametric engine** (seat allocations computed), coalition
  arithmetic; the Wahlkabinen-Simulation part is arrangement-shaped → parked with that family.
- **Alltagsdokumente entschlüsseln** — the Realien mechanism aimed at German adult life
  (Mietvertrag, Beipackzettel, Polizze, Behördenbrief): constructed-coherent fiction, language
  load-bearing. Exact placement (subject/anchor) open — build anyway, place at review.
- **Gesundheitsdaten** — health *data literacy* on the real curated series (sleep/screen/nutrition,
  life expectancy), incl. risk literacy (absolute vs relative, natural frequencies — computed
  pairs). **Guardrail (SME, verbatim intent): hard cited data only — no health preaching; teachers
  are not health educators.**

**The physicist's corner:**
- ✅ **BUILT 11 Jul — the first `horizont` flagship** · **Sternkarten-Engine** — `star_chart` scene computed from date + location over a curated
  bright-star catalog (ephemeris math = pure computation); moon phases, eclipse geometry, ISS
  passes. Partly PHY-anchored, proudly Horizont beyond that.
- **Größenordnungs-Reise** — powers-of-ten ordering/scale arithmetic from the data layer.
- ✅ **BUILT 16 Jul** · **Einheiten-Detektiv** — dimensional-analysis puzzles by INVERTING the
  `sympy.physics.units` validator (`pipeline/einheiten.py` + the shared `pipeline/dimensions.py`
  guard; catalogued wrong-formula transforms proven wrong at build; `phy-einheiten-*`).
  Design: [`einheiten-detektiv-design.md`](einheiten-detektiv-design.md).

**The untouched subjects** (taken seriously; there are teachers who will use these):
- **MUS** — rhythm arithmetic: Notenwerte/Taktarten as computed fraction tasks (no staff-notation
  engine — that stays parked); Quintenzirkel via nodelink.
- **KUG** — the B5 Bildquellen ladder *is* Bildbetrachtung; Farbkreis/Komposition analysis over PD
  artworks (the Commons pipeline serves KUG for free).
- **TED** — **Konstruktions-Werkstatt**: read a Riss, build the net — scene3d × nets, the
  cross-engine kit; overlaps GEZ.
- **BUS** — Trainingsdaten-Mathematik (pulse curves, pacing — computed), Spielfeld-Geometrie.
  Thin but charming.

**Carried-forward ready items (from the built program):**
- ✅ BUILT 12 Jul · PHY/CHE prerequisite edge catalogs (PHY 30 edges, US strands + US→OS
  continuations; CHE 35, Oberstufe-only — CHE US is honestly graph-free; 7 edges SME-flagged).
- More verbatim texts (Wikisource) + more ANNO media texts (second batch shipped 12 Jul: 7 texts
  Kl 1–4 + LAT, plus the 1873 Weltausstellungs-Gegenstimme + GPB Quellenarbeit #2 — the standing
  item stays open); Realien-backdrop rollout once the SME makes the best-of-N picks.
- ✅ tooling BUILT 12 Jul · authored `difficulty` labels: 138 proposals staged
  (`runs/difficulty/difficulty_proposals.{json,md}`) + the SME-run apply tool
  (`tools/apply_difficulty.py`); the labels themselves await SME acceptance — then
  `tools/fit_difficulty.py` becomes genuinely evaluable.

### Ready for further discussion (design-first — do not build from this list)

- **Manipulations-Museum** — statistical/graphical manipulation literacy as a systematic curriculum
  (chart crimes · survivorship · Simpson · correlation≠causation; computed exhibits + sourced PD
  propaganda). SME: could be very powerful, needs real design work first. → its own design doc.
- **Schularbeiten-Generator** — derived point schemes (C4), balanced Anforderungsbereiche, A/B
  Gruppen. SME: park until the platform is more finalized; the Mischpult × parametric Gruppen is
  the natural on-ramp. Keep in mind, do not start.
- **KI-Bildung** — valuable, but too new/large didactically (teachers not firm on it yet). Future
  session.
- **The Lernarrangement family** — Dilemma-/Debatten-Kits, Escape-Room-Kits, Wahlkabinen-
  Simulation, and arrangement-shaped ideas generally: everything that steps away from *sheets*
  gets a dedicated future session (SME decision 11 Jul).
- **Dramaturgy engine** — `dramaturgy-design.md` is written; awaiting the SME's three ► decisions
  (envelope→arc mapping · phase cardinality · unconfirmed-inference trust). No code before then.
- **Zeitleiste redesign** — `zeitleiste-design.md` + rendered mockups (`tools/zeitleiste_mockup.py`,
  SME-praised 18 Jul: Zeitband · Synchronoptik · Lupe · Arbeitsobjekt) are written; awaiting the six
  ► decisions (label policy · HistEvent spans/strands · Lupe trigger · Arbeitsobjekt default ·
  migration shape · strand vocabulary). The current recipe's lane-geometry fix + the tall-tower
  regression test shipped 18 Jul (c0213/c0214 healed); the redesign is the successor form.
- **Informational Realien** — fact-care genres; design-first (carried).
- **The far-later shelf** (explicitly not now; product-finish features): Elternbrief-Projektion ·
  Leichte-Sprache/Großdruck accessibility projections · Jahresplaner.

### Rejected (with reasons, so they stay rejected)

- **Per-class Differenzierungs-Zwillinge** (simultaneous A/B/C level sheets in one room) — the
  classroom reality is a sorting ceremony; stigma outweighs the didactic gain. The LEVERS survive
  as the Mischpult (teacher-tuned, whole-class); within-class depth only as Zusatz/tiered/
  selbstdifferenzierend inside ONE shared sheet.
- **Quartett/card games from the data layer** — creative, but print/cut burden vs a well-designed
  worksheet doesn't pay.
- **Health-topic teaching material** — only data literacy on vetted series; no topical health
  claims (see the Gesundheitsdaten guardrail).
- *(Carried from 5 Jul: music **notation** engine · apparatus-dependent Versuch class ·
  self-checking Lösungswort gimmick — reasons in the archived roadmap.)*

### Standing / maintenance (carried)

- **Audio product surface** (workhorse PC): Stimmen review tab · `text_tasks` turns emission ·
  FLEURS refs (`tts-audio-engine.md` §7). **B4 style LoRA** likewise workhorse-future.
- **Fassung 2026/27 watch** — deferred by decision until published in full text.
- **Geosphere-Klimadiagramm re-decision** (carried since Session 12).
- **Unranked, awaiting an SME call:** Stumme Karten + cartography layers · Typst renderer ·
  vision-Blattkritik · the Nachweis/coverage poster.
- **The SME gate backlog** (the human queue): the 12 image candidates + backdrop picks · c0200/
  c0201 · C5's ► decisions · C1 edge flags (incl. the 7 PHY/CHE flags) · the 138 difficulty
  proposals (`runs/difficulty/difficulty_proposals.md`) · c0202 + the text-batch flags (Wiesel
  edition choice, the two glossed OCR errors) · the Mischpult German surfaces (Formulierungshilfen
  table · Hilfestellung/hint wording · the 6 prompt twins + glossaries · fader/endpoint labels +
  the six "warum nicht" strings) · C3 shared-product German · C2 registry dates · the standing
  breadth-content queue · **the 14–15-Jul breadth batches (c0203–c0262, 60 sheets pending in
  Prüfen)** · **the 16-Jul fleet's German surfaces** (the four preset didactic bundles +
  names/descriptions/UI copy · Fehlersuche prompts/step texts/answer_key patterns · the
  Einheiten-Detektiv transform catalog + prompts · the Fermi anchors — 15 vetted-estimate values
  with bands + rationales, the cited household-size figure to spot-check — and the six problems'
  prose) · **the six Zeitleiste ► decisions** (`zeitleiste-design.md` §7; incl. vetting the M2
  mockup's four curated Austrian events).

## Recently completed (ledger — details in `project-handoff.md`)

Waves A (task/figure engines) · B (image program, external agent) · C (corpus structure) · the
eight 10-Jul tracks (figstyle port, physics scenes, Matura pack, figure emission, Textsorten,
Latein, texts, re-grounding) · nets/variants/boxplot/ANNO/BIO+Bezirk (external agent) · the
two-machine reconciliation · three-tier anchoring + Mischpult P1 (external agent) · the three 11-Jul programs (Finanz, Wahl, Sternkarten) · the 12-Jul carried-forward wave (PHY/CHE prereqs ·
the difficulty-label loop · text batch 2 + the 1873 ANNO pair) · Tiefenregler P2–P4 (Gerüst ·
Textlast · capability discovery + dashboard Mischpult; composer documented out) · the 14–15-Jul
remote breadth campaigns (OS `gen_os_2` 28 sheets + US `gen_us_2` 32 sheets, staged c0203–c0262;
the campaign runbook + `campaign_status.py`) · the 16-Jul five-track build fleet (Fehlersuche ·
Fermi-Werkstatt · Einheiten-Detektiv · Mischpult presets · `breadth_prompt --gaps`). Suite at 1056.
