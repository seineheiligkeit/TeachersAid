# Matura → Deutsch coverage (demand map)

*The German counterpart to `matura-math-coverage.md` — same Matura-backward strategy, applied
to Deutsch. Source: the 2 AHS/BHS/BRP Deutsch Haupttermin exams **KL25 + KL26** (2024/25 +
2025/26). German is text (not vector), so PyMuPDF extraction is clean; the structure here is
read directly rather than via a parser.*

## The Matura Deutsch structure

A 300-minute Klausur of **3 Themenpakete → the candidate picks one → 2 Aufgaben**:

- **Aufgabe 1** (long, **540–660 Wörter**): an analytical/interpretive Textsorte —
  *Textinterpretation · Textanalyse · Erörterung · Meinungsrede* — on 1–2 substantial
  Textbeilagen.
- **Aufgabe 2** (short, **270–330 Wörter**): a pragmatic Textsorte — *Kommentar · Leserbrief ·
  Zusammenfassung* — on 1 Textbeilage.

Each Aufgabe = **a target Textsorte** + **Textbeilage(n)** (authentic source text) + **three
operator-driven Arbeitsaufträge**. Example (KL26, Aufgabe 1, Textinterpretation of two Sahl
poems): *„Beschreiben Sie die dargestellten Situationen / Analysieren Sie die formale und
sprachliche Gestaltung / Deuten Sie die Gedichte im Hinblick auf Abschied und Ankunft.“*

The Korrekturheft makes the model explicit: per Aufgabe it names the **Textsorte**, the
**Schreibhandlungen, die im Sinne der Textsorte erfüllt werden sollen** (e.g. *Argumentation,
Deskription/Rekapitulation, Explikation*), and the content **Erwartungshorizont** (Kernaussagen
der Textbeilagen). So the demand chain is:

> **Textsorte → Schreibhandlungen → operator-driven Arbeitsaufträge → (on a source text)**

## Demand map (both exams)

- **Operators** (the Arbeitsauftrag heads): *beschreiben, analysieren, untersuchen, erschließen,
  deuten, wiedergeben, bewerten, Stellung nehmen, diskutieren, nennen, appellieren*. **Every one
  is already in our authoritative `DEUTSCH` operator catalog** (AFB-banded) — the Matura
  independently validates the operator grounding.
- **Textsorten** demanded (7 of the ~10 official SRDP Deutsch types seen in just 2 exams):
  *Textinterpretation, Textanalyse, Erörterung, Meinungsrede* (long) · *Kommentar, Leserbrief,
  Zusammenfassung* (short). (Repertoire also: Empfehlung, Offener Brief, Rede.)
- **Schreibhandlungen** (macro writing-acts, between Textsorte and operator):
  *Zusammenfassen/Rekapitulieren, Deskription, Analyse, Interpretation/Deutung, Explikation,
  Argumentation, Bewertung, Appell*.
- **Textbeilage types** (the authentic source texts read): *Gedicht, Interview, Sachtext,
  Bericht, Kommentar, Essay, Beitrag*.

## Matura-backward design for German

The endpoint: a candidate **produces a Textsorte** from an authentic text by performing
operator-driven Arbeitsaufträge. The Klausur assumes the genre is *already mastered* — it
doesn't teach it. **We invert it:** earlier in the curriculum, build worksheets that pair a
**rights-clean source text** (our annotated-text engine) with **scaffolded, operator-driven
Arbeitsaufträge that explicitly teach the Textsorte** (what a Kommentar/Erörterung/
Textinterpretation *is*, its Schreibhandlungen, its structure), richly explained — so a Klasse-6
student learns to *build* what the Klasse-8 Matura merely *checks*.

## Coverage vs our engine — what's covered, what's the gap

**Already in place:**
- **Operators** — the `DEUTSCH` catalog (AFB-banded, definitions). ✓ validated by both exams.
- **Annotated authentic texts** — `schema/texts.py` + `pipeline/text_tasks.build_worksheet`:
  a rights-cleared source text rendered line-numbered + annotation-derived tasks. This *is* the
  Textbeilage + Arbeitsauftrag machinery; the rights gate (AT 70-p.m.a./CC) is exactly what the
  Matura's third-party-text caveat needs.

**The gap (the German analogue of "missing parametric recipes"):**
1. **A Textsorten catalog (grounding) — ✅ DONE** (`grounding/textsorten.py`, from the official
   *Textsortenkatalog*, Stand Sept. 2020): the 7 SRDP Textsorten, each with definition,
   Schreibhandlungen, Umfang bands, situativer Kontext, Textbasis (literarisch/nicht-fiktional/
   pragmatisch), scope. *Select, never author.*
2. **A Schreibhandlungen taxonomy — ✅ DONE** (same module): the 6 macro writing-acts
   (Deskription, Narration, Explikation, Argumentation, Rekapitulation, Evaluation) +
   `SCHREIBHANDLUNG_OPERATORS`, a curated cross-walk to the Deutsch operator catalog (a test
   locks the targets to real operators). This is the level the Korrekturheft scores against.
3. **Integration into `text_tasks` — NEXT** — emit a *Matura-shaped but scaffolded* worksheet:
   source text + N operator-driven Arbeitsaufträge → a **target Textsorte** (via
   `format_textsorte_brief`), with the genre *taught* (not assumed). Annotation-derived answers
   stay correct-by-curation.

## How German differs from Maths (the key cross-subject insight)

The Matura-backward method generalizes, but the *engine extension differs in kind*:
- **Maths** → new **parametric recipes** (sympy: correct-by-construction numbers + Rechenweg).
- **Deutsch** → a **genre/scaffold layer** (Textsorten + Schreibhandlungen) on top of the
  existing annotated-text engine: **correct-by-curation**, not computation. There is no sympy
  for German — the durable asset is the vetted text + the genre scaffold, not a generator.

## Scaled validation — 33 exams (the full-archive run, 29 Jun 2026)

The original probe read 2 exams; the home-PC archive build (`tools/fetch_matura.py` +
`tools/matura_demand.py`) now aggregates **33 Deutsch Klausuren** (Haupt-/Herbst-/Nebentermin,
2014/15–2025/26), **198 Aufgaben**. The 2-exam reading holds and sharpens:

- **Textsorten demanded** (frequency): *Zusammenfassung 38 · Kommentar 36 · Textinterpretation 33 ·
  Erörterung 24 · Leserbrief 23 · Meinungsrede 20 · Textanalyse 19 · Empfehlung 4 · offener Brief 1*.
  **9 distinct types** — the whole `grounding/textsorten.py` repertoire is exercised; the long-form
  analytic four (Interpretation/Analyse/Erörterung/Meinungsrede) and the short pragmatic three
  (Zusammenfassung/Kommentar/Leserbrief) dominate, exactly as the catalog models. **Build priority =
  frequency order.**
- **Schreibhandlungen** (frequency): *Deskription 172 · Rekapitulation 172 · Argumentation 125 ·
  Explikation 52 · Evaluation 50 · Narration 3*. The six-act taxonomy is confirmed; Deskription +
  Rekapitulation + Argumentation are the backbone of almost every task — the scaffold layer should
  teach those first.
- **Operators — 100 % catalog-covered.** Every operator the parser named across 198 Aufgaben is in
  `operators.DEUTSCH` (0 not-in-catalog). Leaders: *wiedergeben 99 · beschreiben 90 · analysieren/
  untersuchen 63 · kommentieren/Stellung nehmen 60 · bewerten 36 · diskutieren/erörtern 34 · deuten/
  interpretieren 33 · erschließen 32 · (be)nennen 27 · vorschlagen 24*. The Deutsch operator grounding
  is now **empirically validated at scale**, not just by 2 exams.

The conclusion is unchanged and reinforced: Deutsch needs **no new computational engine** — the
durable assets (Textsorten catalog ✅, Schreibhandlungen taxonomy ✅, annotated-text engine ✅) are
in place; the open work is **step 3** (wire the genre scaffold into `text_tasks`), now with a
frequency-ranked build order.

So the same probe (mine the SRDP endpoints → build rich earlier material) pays off, but tells
each subject what *kind* of asset to grow. Next subjects to probe: the sciences (W/E/S +
experiment/Versuch endpoints), GWB, the modern languages (CEFR + the oral wall).
