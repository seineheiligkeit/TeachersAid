# Platform Definition & Positioning — v0.1

*Written against the Teachino pilot study (PH Wien / BMB, Oct 2025). Companion to the v0.2 schema
and the project handoff. This is the "what we are and what we deliberately are not" document.*

---

## 1 · The thesis (one paragraph)

An **on-demand generator of Austrian-Lehrplan-anchored teaching material**. A teacher names a
**topic, a grade, and how much time** they have; they get back a **ready-to-use bundle** — student
material plus a curated teacher depth-layer — that is **correct by construction**, **provably
competence-aligned** (the Nachweis), and **drops straight into the tools they already use**. It does
**one job extremely well** and refuses to be anything else.

**Promise deliberately modest, execution ruthlessly high.** We do not promise to revolutionise
teaching. We promise the right material, when you need it, without the hassle. The modesty is
strategic: it is the direct counter-position to the overpromising that turned the category into
"AI-slop."

## 2 · Why now (the timing thesis)

Teachino spent its first-mover advantage when the models couldn't deliver — wrong math, broken
formulas, shallow examples, stale Einstiege — and in doing so **poisoned the well**: teachers now
carry a "these tools are slop" prior. We therefore enter not as pioneers but as the **fast follower
who cleans up the bad first impression**. The models now clear the bar *if* scope is disciplined; the
binding constraint is no longer model capability but **scope discipline and curation quality**. Our
wedge is demonstrable reliability, never "AI magic."

## 3 · Who it's for — and explicitly not for

**For (the loyal base the study identified):**
- The **structure-seeker**: digitally secure but not hyper-tech-affine, ~30–49, skews strongly female
  (the study: 37% of women used Teachino regularly/often vs 19% of men), values reliability,
  structure, and curricular guarantee over open-ended flexibility.
- The segment **general AI doesn't reach**: ~15% of teachers who barely touch other AI used Teachino
  regularly. A distinct, underserved market.
- **MINT teachers specifically**, as the entry beachhead (see §4) — AI-comfortable in general (58%)
  but tool-averse because text-only generation failed their content.

**Explicitly NOT for:**
- **ChatGPT power users** who want an open, flexible prompt surface. We lose to general AI on
  flexibility, and the study shows these users (high-tech-affinity, under-30) churned off Teachino
  anyway. They are not our market; chasing them turns us into a worse ChatGPT.

## 4 · MINT-first, not MINT-only *(the function/subject distinction)*

**Focus is on the function, not the subject.** Our identity — *right, ready, curriculum-guaranteed
material on demand* — is subject-agnostic. "Focused" means **one job done excellently across
subjects**, not one subject.

- **Why MINT is the beachhead:** it is where the competitor is provably weakest (math 9% usage,
  NaWi 28% — vs 51%/58% for AI generally) *and* where our sharpest, least-copyable advantage
  (correct-by-construction + the W/E/S model that *is* the science Lehrplan's structure) decides the
  outcome. Winning here is the strongest possible proof and the hardest thing to copy.
- **Why it's not the ceiling:** the core engine — competence-anchoring + correct-by-construction
  assets + curated creative depth + the Nachweis — generalises. Language and humanities are *easier*
  for current models (Teachino already did acceptably there), so they're not the wedge, but they're a
  natural expansion once the hard MINT core proves the quality bar — and our anchoring depth
  differentiates us even where Teachino was merely shallow.
- **The discipline that keeps us focused:** we expand **by subject and competence coverage**, never
  **by platform features**. Each new subject is the same engine pointed at a new Lehrplan area. That
  is how we are simultaneously "not limited to MINT" and "focused on what we do right."

## 5 · The anti-scope — what we deliberately do NOT build

*The study's clearest lesson: the platform ambition is what killed adoption. The most-cited blocker
was onboarding/time cost, and the mechanism was that Teachino wanted to be the teacher's entire
workspace.* So:

- **Not a workspace / LMS.** No "hinterlege your whole Unterrichtsstruktur to get value." No being the
  place teachers live.
- **Not a workflow owner.** Not a WebUntis replacement, file manager, gradebook, or communication
  tool. (These are exactly the everything-features.)
- **Not a general chatbot / open prompt surface.** No competing with ChatGPT on flexibility.
- **Not (initially) student-facing in the classroom.** We stay on the **planning side** — higher
  adoption (58% use AI for planning vs 30% in class) and far lower datenschutz exposure.
- **Output is portable, not a destination.** Near-zero onboarding; the bundle drops into Word / Canva
  / Teams / Moodle / whatever they use. We *interoperate*, we don't *absorb*.

## 6 · Teachino pain-point elimination — honest gap-check

Verdicts: ✅ eliminated by design · ◐ partially / must invest · ⚠ intrinsic or currently exposed ·
🔒 hygiene gate (must match) · 🧭 GTM truth (not a product fix).

| Teachino pain point (from the study) | Our stance |
|---|---|
| **Onboarding/time cost** — must hinterlege whole structure; double-maintain Teams/Moodle; "der Umstieg ist auch der Hauptgrund, warum manche das Tool wieder verlassen" | ✅ **Structurally avoided.** We're not a workspace. One request → material. Friction is near-zero *because* we refuse to be a platform. This is the #1 killer and we sidestep it by design. |
| **MINT failure** — math wrong, fractions as code-symbols, examples "zu niedrig für AHS" | ✅ **Core / but the hard part.** Content-bearing assets generated by code, computed verification, difficulty calibrated to the actual Lehrplan competence. Caveat: this is engineering we must *deliver*, and grade-accurate difficulty is designed but unproven at scale. |
| **Rework / not use-ready** — text-heavy, must reformat in Word/Canva | ◐⚠ **Partially, and currently our weakest spot.** Correct-by-construction removes *re-solving*. But polished, hand-out-ready output (proper worksheet/PDF, the decorative layer) is a real recurring demand we under-weighted, and our prototypes are markdown/text. **This is an exposure, not a strength, today.** |
| **Stale/schematic creativity** — "Na Nett Geschichten", repetitive Einstiege | ✅ **Design intent / ongoing cost.** The curated, overproduced thread rack + lens kit + anchoring is the direct answer. Caveat: staying non-stale at scale is a continuous editorial cost (we felt it building Zwentendorf), not a one-time win. |
| **Shallow competence-fidelity** — KI "die intendierte Aufgabenlogik nicht immer korrekt erfasst"; used only as Gegencheck | ✅ **Deepest moat.** Deterministic Lehrplan resolution, verbatim competences + W/E/S, `exercises` vs `builds_prerequisite`, the Nachweis as *proof*. Caveat: operator/Aufgabenlogik fidelity is exactly where their AI failed — we must *prove* our scaffolding does better, not just claim anchoring. |
| **Datenschutz / DSGVO / EU hosting** | 🔒 **Must match.** It was a Teachino *plus*; we equal it (EU hosting, DSGVO-native, minimal student PII). Planning-side scope reduces exposure. A gate, not a differentiator. |
| **Longevity fear** — won't invest in a tool that might vanish (Planungssicherheit) | ✅ **Eased by low commitment.** Because we require near-zero investment, "what if it disappears" costs the teacher far less than losing a whole Teachino workspace. Low switching cost removes this blocker. |
| **Visual/multimedia output gap** | ◐⚠ **Designed, unbuilt.** Per-subject visual policy (code for content-bearing, diffusion for decorative). Not yet built — folds into the use-ready-output exposure above. |
| **Integration desire** (WebUntis/Teams/OneNote loved) | ◐ **Interoperate, don't own.** Export/portability = yes; becoming the workspace = no. The study shows integration was loved *and* the platform ambition behind it was the killer — so we thread the needle with clean export, not absorption. |
| **Voluntary adoption doesn't scale; collegial non-use** | 🧭 **GTM, not product.** The study says scaling needs BMB/school-wide procurement and that the ministry favours an interoperable *ecosystem*, not platform duplication. → We aim to be the best-in-class content engine that **plugs into the ecosystem**, adopted institutionally. (Also reinforces §5.) |

**Net:** the deep, judgment-heavy moats (competence-fidelity, MINT correctness, non-stale depth) are
exactly where we're designed to be strong, and the #1 adoption killer we avoid structurally. The
**honest weak flank is use-ready output polish** — the one place the study says matters and our
current build is thinnest.

## 7 · The positioning statement (quotable)

> For Austrian secondary teachers who want reliable, ready-to-use, curriculum-guaranteed material on
> demand — beginning with the MINT subjects where generic AI and existing tools fall down —
> **[Product]** generates competence-anchored teaching bundles, correct by construction and provably
> aligned to the Lehrplan, that drop straight into the tools you already use. Unlike Teachino, it is
> **not a workspace you must move into**; unlike ChatGPT, it **requires no prompting and guarantees
> curricular fit**. It does one thing extremely well: the right material, when you need it, without
> the hassle.

## 8 · What must be true (the real risks)

1. We must actually deliver **correct-by-construction MINT** — hard engineering, not a slide.
2. **Use-ready polished output** is unbuilt and is a genuine bar; this is our current weakest flank.
3. **Curated non-stale depth** is a continuous editorial cost, not a one-time asset.
4. We inherit **category skepticism** ("AI teaching tool = slop"); our antidote is demonstrable
   reliability and a narrow, honest promise.
5. The incumbent has **first position, a BMB relationship, and the Lehrplan-USP claim** we'd make —
   but the study shows it is weakest exactly where we're strongest.
6. The realistic GTM is **institutional / ecosystem-plugin**, which is slower than viral consumer
   adoption — patience and partnership, not growth-hacking.

## 9 · One-line identity to hold onto

**Do one thing extremely well — the right Lehrplan-anchored material, on demand, ready to use —
across subjects, for the teachers who want reliability over flexibility; and refuse, always, to
become the platform that tried to be everything.**
