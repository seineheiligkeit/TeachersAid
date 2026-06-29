# Matura calibration (#1) — results

*Calibration of our `cognitive_level → Anforderungsbereich → difficulty` model against real,
field-tested Zentralmatura items. Method + corpus below; the honest headline is that the
**model holds** and the data confirms our depth philosophy — plus one grounded gap-fill.*

## Corpus & method

Six **AHS Mathematik Haupttermin** exams extracted with `tools/extract_matura.py` (the
deterministic, no-LLM extractor; AU+LO merged per exam): **2013/14** (Teil 1 + Teil 2, the
first Zentralmatura), **2019/20, 2020/21, 2022/23, 2024/25**. **141 tasks** (120 Teil 1, 21
Teil 2). The extractor is format-tolerant across the decade (early split T1/T2 booklets with
`CC` language and descriptive point-keys; modern combined files with nominalised operators).

Operator is the most year-stable per-task signal (the AU imperative). For analysis each Math
operator was assigned an **AFB tendency** — note this is **corpus/inference, not official**:
the SRDP Mathematik operator list is deliberately *not* AFB-banded (unlike Deutsch/GWB/
Naturwissenschaften), so we do **not** inject these bands into the authoritative catalog
(`grounding/operators.py` stays faithfully flat). The mapping used here:

| AFB | tendency | Math operators |
|---|---|---|
| 1 Reproduktion | recognise / state / fill given | ankreuzen, angeben, ergänzen, zuordnen, eintragen, skizzieren, einzeichnen, beschreiben, kennzeichnen, vervollständigen |
| 2 Transfer | compute / apply / model | berechnen, ermitteln, aufstellen |
| 3 Reflexion | reason / interpret / argue | interpretieren, argumentieren, begründen, nachweisen, überprüfen |

## What the corpus shows

Operator frequency (Teil 1 / Teil 2): ankreuzen 36/1, angeben 21/10, ermitteln 13/3,
berechnen 12/1, ergänzen 8/0, zuordnen 6/1, aufstellen 5/4, skizzieren 4/0, the rest ≤2.

AFB tendency by Teil (by leading operator):

| | AFB 1 | AFB 2 | AFB 3 |
|---|---|---|---|
| **Teil 1** (foundational, 1 pt each) | **72 %** | 26 % | ~0 % |
| **Teil 2** (context-rich, multi-part) | 61 % | 38 % | ~0 % |

## Findings

1. **A real competence exam is reproduction/transfer-heavy, with reflection as the *apex*,
   not the bulk.** Teil 1 (the Grundkompetenz foundation) is ~¾ AFB 1, ~¼ AFB 2, and
   essentially no standalone AFB-3 operator. Genuine reflection (argumentieren / interpretieren
   / begründen) is rare and concentrated in Teil-2 *structure*, not in the surface verb.
2. **Our `cognitive_level → AFB` ladder is confirmed.** Every Matura operator maps cleanly
   onto `_RANK_TO_BAND` (recognise→1, compute/apply→2, reason→3); `angeben` is the one genuine
   borderline (1 vs 2), which is exactly the official "operators aren't strictly 1:1 with an
   AFB" caveat. **No change to `pipeline/difficulty.py` is warranted** — the honest, measured
   result, consistent with that module's "estimate, not measurement" stance.
3. **Our `DepthTarget` philosophy is validated.** We require a *floor* of higher-level tasks,
   not that everything be high. The corpus says that is exactly right: depth is a few
   well-placed AFB-3 moments on a reproduction/transfer base — a foundational sheet that were
   all "beurteile/erörtere" would be *less* authentic than the Matura, not more.
4. **Gap-fill (grounded, kept out of the faithful catalog):** the corpus gives an empirical
   AFB tendency for the otherwise-unbanded Math operators (the table above). Recorded here as
   calibration evidence — not authored into `operators.MATHEMATIK`.

## Honest limits

- **Teil 1 is all 1-point/binary**, so it can't differentiate *fine* difficulty within the
  band — it calibrates the *mix* and the operator→AFB mapping, not a numeric difficulty scale.
- **The operator understates Teil-2 load**: a context-rich multi-part task's cognitive demand
  lives in its structure/modelling, not its leading verb — so Teil-2's AFB-3 share is higher
  than the operator view suggests.
- **GK codes are sparse** (printed only on open-format tasks; 0 in 2013/14) — a full
  GK-per-task layer still needs the separate Aufgabenpool metadata.
- Sample = 6 exams (one subject). Trends are stable across years but this is a calibration,
  not a psychometric study (we deliberately collect no student-response data).

## Recommendation

- **Keep `difficulty.py` as is** — the AFB→difficulty default ladder is confirmed.
- **Calibrate generation *expectations*, not code:** a realistic foundational-Maths worksheet
  should sit near **~70 / 25 / 5** across AFB 1/2/3, with reflection as a deliberate apex. A
  future `DepthTarget` profile could encode this "Matura-realistic mix" (optional; not built).
- **Keep the Math operator catalog faithfully flat** (no inferred AFB bands) — *select, never
  author*; the empirical tendency lives here as evidence.
- Re-run on more years / other subjects (Angewandte Mathematik, the language exams) to widen
  the corpus; `tools/extract_matura.py` handles them.
