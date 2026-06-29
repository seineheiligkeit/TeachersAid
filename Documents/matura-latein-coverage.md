# Matura → Latein coverage (demand map)

*The Latein counterpart to `matura-math-coverage.md` / `matura-deutsch-coverage.md` — same
Matura-backward strategy. Source: **41 AHS Latein Klausuren** (4-jährig + 6-jährig, Haupt-/
Herbst-/Winter-/Nebentermin, 2018/19–2025/26), downloaded with `tools/fetch_matura.py` and
parsed with the Latein branch of `tools/extract_matura.py`; aggregated by `tools/matura_demand.py`.
Latein is text (not vector), so PyMuPDF extraction is clean.*

## The Matura Latein structure (rock-stable)

Every one of the 41 exams has the **identical two-part shape** — a strong, machine-confirmed
demand signal:

- **A. Übersetzungstext (ÜT)** — *Übersetzen Sie …* — **36 points** (41/41 exams). One coherent
  Latin passage (~70–100 words) + a German Einleitung + lemma/Konstruktion notes + a source line.
- **B. Interpretationstext (IT)** — **24 points** (41/41), driving **10 numbered Arbeitsaufgaben**
  on a second Latin text. Total **60 points** (positive ≥ 18 ÜT + 12 IT).

So the endpoint is **translate one text + perform 10 short analytic operations on another** — a
clean, durable target, far more stable than the rotating Deutsch Themenpakete.

## Demand map (41 exams)

### IT Arbeitsaufgabe operators (frequency)
`finden 64 · trennen/Wortbildung 29 · ankreuzen 29 · ergänzen 29 · belegen 26 · gliedern 25 ·
verfassen 24 · vergleichen 23 · angeben 21 · auseinandersetzen 18 · zuordnen 13 · analysieren 7 ·
benennen 3 · beschreiben 1`. Plus the ÜT's single operator **übersetzen** (41×).

### Source authors (selection, 41 exams — huge breadth)
Antiquity dominates — **Cicero** (De officiis, De natura deorum, Laelius, Tusculanae, In Verrem,
Ad Atticum/familiares, De re publica, …), **Ovid** (Metamorphosen, Heroides, Fasti, Remedia),
**Vergil** (Aeneis, Georgica), **Seneca**, **Plinius**, **Phaedrus**, **Sallust**, **Terenz** —
but the corpus reaches deep into **medieval & humanist Latin** too: Petrus Alphonsi, Augustinus,
Gregor von Tours, Einhard, Jacobus de Voragine, Erasmus, Melanchthon, Comenius, Piccolomini,
Sebastian Brant. *Every one is centuries past the 70-Jahre-p.m.a. line → public domain.*

## Coverage vs our engine — what's covered, what's the gap

**Already in place** — the **annotated-text engine** (`schema/texts.py` +
`pipeline/text_tasks.build_worksheet`) already covers Latein: the `translation` / `grammar` /
`culture` annotation kinds (the Phaedrus *Vulpes et Corvus* flagship). The Matura **validates the
engine shape exactly**: ÜT = a `translation` task; the IT Arbeitsaufgaben = `grammar` /
`text_analysis` / `open_response` tasks. The rights gate (AT 70-p.m.a./PD) is exactly what a
selected Latin text needs — and Latin's corpus is overwhelmingly PD.

**The gaps (the Latein analogue of "missing recipes"):**
1. **A Latein operator catalog — NOT yet curated** (`operators.py` routes LAT → the generic
   `DEFAULT`; *"still to curate: …Latein"*). This map gives the **empirical seed**: of the observed
   IT operators, **9 are absent from any current catalog** — `finden · trennen (Wortbildung) ·
   zuordnen · ergänzen · verfassen · gliedern · ankreuzen (Auswahl) · belegen · auseinandersetzen`
   — alongside the 5 generic-palette hits (`angeben · vergleichen · analysieren · benennen ·
   beschreiben`). Curating a faithful **SRDP-Latein Operatorenliste** (the official source exists)
   and wiring `LAT → it` is the highest-value next step; these frequencies tell us what it must cover.
2. **Wortbildung (Präfix/Suffix-Analyse)** — the single most frequent IT task type (`trennen` +
   `finden` lead the table). A *deterministic* recipe is feasible (the BMBWF Präfix-Suffix-Liste is
   published): split a word into morphemes + give each part's meaning. The Latin analogue of a
   parametric recipe — correct-by-construction morphology, not curation.
3. **A real ÜT corpus** — select-never-author PD Latin passages (Phaedrus, Cicero, Ovid, the
   medieval texts above), annotated with the lemma/Konstruktion notes the Matura always provides.
   This is pure curation on an essentially unlimited PD source — the cleanest possible select-layer.

## How Latein differs (the cross-subject insight)

Like Deutsch, Latein extends by **curation, not computation** — except **Wortbildung**, which is
genuinely *parametric* (deterministic morphology). So Latein sits between Maths (recipes) and
Deutsch (scaffold): a **PD-text + annotation** engine (already built) **plus one computable recipe
family** (Wortbildung) **plus an operator catalog** to seed it. The 36/24 ÜT-IT split and the
operator frequencies above are the spec.
