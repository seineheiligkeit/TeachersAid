# Matura orientation & the SRDP Operatoren grounding

*Session record + decisions, 29 Jun 2026. The AHS endpoint — the standardisierte kompetenz­
orientierte Reife- und Diplomprüfung (SRDP / Matura) — is the capstone the whole competence
model points at. This is what we took from it, and what we deliberately did **not**.*

## 1 · What the Matura offers (matura.gv.at)

- **Licensing is unusually clean.** Published exam tasks are **CC BY 4.0** under the
  *Informationsweiterverwendungsgesetz (IWG 2022)*, cleared for private, school **and
  commercial** reuse (attribution: *"Datenquelle: Bundesministerium für Bildung"*). **Caveat
  — our kind of caveat:** third-party texts/images/audio *embedded* in tasks are not covered;
  clearing those is the reuser's responsibility. So the *task scaffold* is CC-BY; embedded
  authentic source material may carry separate rights.
- **A structured, competence-coded item pool** ([aufgabenpool.at](https://aufgabenpool.at)).
  For **Mathematik (AHS)** it mirrors our own model closely: Teil 1 = 24 *Typ-1* items, each
  serving **one Grundkompetenz** (0/½/1); Teil 2 = 4 context-rich multi-part tasks. Plus a
  published **Beurteilungsschema** (rubric) per exam.
- **The three Anforderungsbereiche** — *Reproduktion / (Reorganisation und) Transfer /
  Reflexion und Problemlösung* — are **exactly** the cognitive-level↔AFB ladder we already
  use (`pipeline/difficulty.py`). The Matura *confirms* our depth contract rather than
  changing it.
- **Supply is inverted vs. our MINT wedge.** The rich, archived, standardized corpus is
  **Mathematik + Deutsch + Fremdsprachen + Latein**. For **Physik/Chemie/Biologie the Matura
  is oral/teilstandardisiert** — no yearly archive of real papers, only Leitfäden + example
  tasks. The value lands on our *newest* tracks (Oberstufe, parametric Maths, texts), not the
  founding wedge.

## 2 · Decisions

- **Use the Matura two cheap, high-value ways** (agreed): **#1 calibration** (tune our
  difficulty/cognitive-level model against real point-weighted items — attacks our hardest
  open problem) and **#2 harvest the Operatoren** (done, below).
- **No dedicated "Matura item" asset class.** The rule we settled on:
  > *An external corpus earns an asset class only when we wrap it in a curation/derivation
  > layer that compounds. Verbatim Matura items add none — they re-shelve a public resource,
  > cut against the "creative partner, not an AI worksheet" thesis, and read as teach-to-the-
  > test backwash.*
  The Matura is the **horizon that shapes the ladder, not the daily diet**. Where we want a
  real anchor on a worksheet, we **reference** an Aufgabenpool item (b2, "vgl. Aufgabenpool …")
  rather than redistribute it — and an occasional genuine Matura question given scaffolding +
  time is pedagogically strong (a *usage pattern*, not an asset class).
- **Operators are GROUNDING, not content** — a controlled vocabulary injected into the
  generation brief, like the competence catalog or the ÜT legend. *Select, never author.*

## 3 · What was built — the Operatoren grounding (`teachersaid/grounding/operators.py`)

The SRDP publishes one operator catalog **per subject (group)**, and they do **not** share a
shape — so each is stored faithfully rather than forced into one mould:

| Subjects (code) | Source | Shape |
|---|---|---|
| **Deutsch** (DEU) | BIFIE/IQS, Abraham & Saxalber, Okt. 2016 | AFB-banded + definitions |
| **Bio/Phy/Che** (BIO/PHY/CHE) | AECC-Bio, Reichstädter & Müllner, 2018 (V3) | AFB **and** the science **W/E/S** model — read cell-by-cell from the catalog's grid |
| **Mathematik/AMT** (MAT) | IQS, 13.3.2023 | **flat, not AFB-banded** + a preferred **Antwortformat** (o/ho/k/mc/z/l) |
| **GWB / Geographie** (GWB) | Ch. Sitte 2011 (after Fraedrich/Hieber/Lenz) | AFB-banded + definitions |

All four are CC BY (IWG 2022). Other subjects fall back to a clearly-flagged **generic
palette** (`DEFAULT`).

Design notes:
- **One ladder, two surfaces.** `_RANK_TO_AFB` is kept identical to
  `pipeline/difficulty._RANK_TO_BAND` (a test locks it). Two official fidelity notes are
  honoured: operators are **not strictly 1:1 with an AFB** (a verb may appear under more than
  one band; the brief says so), and the AFB hierarchy is rising **Eigenständigkeit, not
  difficulty** — which is precisely why our AFB→difficulty mapping is an overridable default,
  not a measurement.
- **Sciences share one base (SME decision).** The three sciences share the W/E/S model
  verbatim and no separate official PHY/CHE operator catalog exists, so the AECC-Bio
  *Naturwissenschaften* list serves all three (`SUBJECT_OPERATORS` maps BIO/PHY/CHE → it).
  Its W/E/S tags map onto our science `SubjectCompetenceModel` dimensions — a real grounding
  asset, not just verbs. (Chemie Oberstufe uses WO/EG/KZ; the W/E/S tags ride along unused
  there — the verb palette is unaffected.)
- **Math format → task kind.** Math's Antwortformat is wired to our task `kind`:
  `mc→multiple_choice · z→matching · k→construction · l→table_fill · o/ho→open_response`
  (`FORMAT_TO_KIND` / `kinds_for_answer_format`), surfaced in the Math brief — so a Math
  operator's preferred answer format suggests an apt response affordance.
- **Routing is by canonical code, not display name.** `get_subject_model` stamps
  `model.subject` with the *caller's* string (the GWB demo passes the long *"Geographie und
  wirtschaftliche Bildung"*), so name-keying was fragile. `operator_set` resolves
  subject→code via `lehrplan_store._code_for` (the helper `prompts.build_user` already uses);
  verified across both Stufen and aliases.
- **Integration:** `llm/prompts.build_system` injects the subject's operator palette in the
  shape that fits its catalog (AFB-grouped, or flat-with-answer-formats). Tests in
  `tests/test_operators.py`.

## 4 · Open / still to curate

- **Remaining operator catalogs** (lower priority, drop the PDF and it slots in the same way):
  Fremdsprachen, Latein, Geometrisches Zeichnen, Ethik.
- **Subagent breadth path** (`tools/breadth_prompt.py`) does not yet inject the operators —
  the obvious next integration now the vocabulary is authoritative.
- **Physik/Chemie refinements** — none planned; the shared Naturwissenschaften base stands.

## 5 · Next — #1 Calibration (the handoff)

Goal: tune our honest **difficulty** estimate (`pipeline/difficulty.py`, 1–3) and the
cognitive-level↔AFB ladder against **real, field-tested, point-weighted** Matura items — the
closest thing to ground-truth difficulty in the Austrian system, and a direct attack on our
single hardest open problem (handoff §7, *"the unproven core of the MINT claim"*).

Plan once exams are provided (egress proxy blocks matura.gv.at — the SME supplies the PDFs):
1. Take 2–3 released **Mathematik AHS** exams + their **Beurteilungsschemata** (cleanest:
   self-contained, point-weighted, GK-coded).
2. For a sample of items, record (Teil, Grundkompetenz, points, our inferred cognitive_level
   & AFB) and compare our band assignment to the item's actual demand/weight.
3. Check whether our `_RANK_TO_BAND` defaults and the `difficulty` heuristic hold; adjust the
   heuristic (not a measurement — an honest estimate) if a systematic skew shows.
4. Write the findings as a short calibration note; fold any change into `difficulty.py`.

No new asset class, no stored corpus — calibration tunes existing code + a note.

### The extractor (built — `tools/extract_matura.py`)

A deterministic, no-LLM extractor (the `parse_lehrplan`/`fetch_*` precedent) turns the
official PDFs into per-task JSON, so the ~10-year archive becomes a usable corpus. The math
content is largely vector/image, so it captures **structure + text**, not formulas:

- **From the filename** (stable `KL25_PT1_AHS_MAT_00_DE_{AU,LO}`): year, Termin, Teil,
  Schulform, subject, language, kind.
- **Aufgabenheft (AU):** per task — title, context, instruction, the **operator** (from the
  imperative), the **answer format** (`[2 aus 5]`), point marker.
- **Korrekturheft (LO):** per task — title, the **operator + point scheme** (from the
  point-key sentence), **Grundkompetenz** where printed, plus the exam **Beurteilungs­
  schlüssel** (point→grade). AU+LO of one exam are auto-paired and merged.

Pure parsers are unit-tested offline (`tests/test_extract_matura.py`); only PDF reading
touches PyMuPDF.

**What the 2025 AHS exam yielded** (the shape calibration will work from): 28 tasks
(24 Teil 1 @ 1 pt + 4 Teil 2, Best-of on 26–28), total 36 pts; every task's operator is one
of our catalogued **Mathematik** operators (a test locks this), AU↔LO operators agree on 21
of 28 (the rest are multi-operator Teil-2 tasks); **half-point** tasks flagged. Two honest
limits: (a) **GK codes are sparse** — the Korrekturheft prints `Grundkompetenz:` only on
genuinely open-format tasks (3 of 28 in 2025), so a full GK-per-task mapping needs the
separate Aufgabenpool metadata; (b) **Teil-1 is all 1-point/binary**, so within Teil 1 point
weight ≠ difficulty — the differentiating signal is the *operator × format × GK*, not points.
Calibration will therefore lean on operator/format/GK demand, with Teil-2 point allocation as
the graded-difficulty signal.
