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

**The flagship — der Tiefenregler („das Mischpult").** Depth as a teacher-facing control surface:
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
C4-estimate · AFB mix · competence coverage intact or honestly reported). Build shape: **P1 built** —
pure-computation faders on parametric sheets (Umfang · computed strategy depth · figure abstraction ·
misconception-MC↔open, typed profile + structural Regler-Lint; contract in
`tiefenregler-design.md`) → P2 scaffold fader → P3 text fader + WSTF lint → P4 composer integration +
dashboard surface. *(The rejected sibling is recorded under Rejected.)*

**New task genres (engines):**
- **Fermi-Werkstatt** — estimation problems; decomposition chains with curated fact-anchors from
  the data layer; acceptable ranges + worked chain COMPUTED. Verbatim MAT modelling competences;
  also the archetype of a selbstdifferenzierende Aufgabe (feeds the Mischpult).
- **Fehlersuche engine** — worked solutions with a PLANTED catalogued misconception ("Finde und
  korrigiere den Fehler"); the wrong step is computed by applying a Fehlermuster, the teacher guide
  names it. Extends the MC-distractor engine into worked examples.
- **Messdaten-Werkstatt** — real measurement series (GeoSphere · NOAA · Statistik Austria) analysed
  as lab protocols: uncertainty, outliers, conclusions. The parked Versuch class side-stepped — no
  apparatus, pure data layer.
- **Beweis-Puzzles** — proofs as ordering/fill-the-gap tasks computed from a curated proof-step
  graph (Pythagoras, Winkelsumme, √2). Begründen/Argumentieren is a verbatim MAT dimension.
- **Kontrafaktisches Urteilen (GPB)** — "Was wäre, wenn …?" with the Sachverhalt as frozen
  fact-set, the counterfactual explicitly labelled speculation, the rubric rewarding fact-grounded
  reasoning (Urteilskompetenz).

**Content programs (ÜT-anchored / Horizont):**
- **Finanzführerschein** (ÜT 13 verbatim) — Lohnzettel lesen (brutto/netto computed from
  Stand-stamped curated SV/Lohnsteuer tables, refreshed yearly like datasets), Handyvertrag-
  Vergleich, Inflation mit echtem VPI, Zinseszins als Freund und Feind.
- **Wahl-Werkstatt** (ÜT 7 + GPB; Wählen ab 16) — real Nationalrat results (BMI open data),
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
- **Sternkarten-Engine** — `star_chart` scene computed from date + location over a curated
  bright-star catalog (ephemeris math = pure computation); moon phases, eclipse geometry, ISS
  passes. Partly PHY-anchored, proudly Horizont beyond that.
- **Größenordnungs-Reise** — powers-of-ten ordering/scale arithmetic from the data layer.
- **Einheiten-Detektiv** — dimensional-analysis puzzles generated by INVERTING the
  `sympy.physics.units` validator ("this formula cannot be right — why?").

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
- PHY/CHE prerequisite edge catalogs (the C1 pattern, proven on MAT).
- More verbatim texts (Wikisource) + more ANNO media texts; Realien-backdrop rollout once the SME
  makes the best-of-N picks.
- authored `difficulty` labels, starting with C4's 48 review cues (unlocks a learnable model).

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
  c0201 · C5's ► decisions · C1 edge flags · C4's 48 cues · C3 shared-product German · C2 registry
  dates · the standing breadth-content queue.

## Recently completed (ledger — details in `project-handoff.md`)

Waves A (task/figure engines) · B (image program, external agent) · C (corpus structure) · the
eight 10-Jul tracks (figstyle port, physics scenes, Matura pack, figure emission, Textsorten,
Latein, texts, re-grounding) · nets/variants/boxplot/ANNO/BIO+Bezirk (external agent) · the
two-machine reconciliation. Suite at 783.
