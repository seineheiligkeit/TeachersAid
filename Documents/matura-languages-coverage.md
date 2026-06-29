# Matura → Lebende Fremdsprachen coverage (demand map)

*The modern-language counterpart to the Maths/Deutsch/Latein maps. Source: **41 AHS Englisch
Klausur booklets** (Haupt-/Herbst-/Wintertermin, 2023/24–2025/26), via `tools/fetch_matura.py`
+ the language branch of `tools/extract_matura.py`. Englisch is the probe; Französisch/
Italienisch/Spanisch share the identical four-skill structure (same engine implications).*

## The Matura FS structure — four skill-split booklets

Unlike Deutsch (one Klausur) or Latein (ÜT+IT), the modern-language Matura is **four separate,
independently-graded skill booklets**, each CEFR-leveled:

- **Lesen** (Reading) · **Hören** (Listening) · **Schreiben** (Writing) · **Sprachverwendung im
  Kontext** (Language in use). AHS English Hauptmodul is **B2**; the second living language and the
  4-year AHS strand are **B1**.

The skill split is the load-bearing fact: the durable demand signal is **which skills × levels** are
exercised and **which item formats**, *not* an operator vocabulary — the FS exams are **not
operator-driven** the way Deutsch/Math/Latein are (no SRDP-FS Operatorenliste exists; the rubric is
CEFR can-do descriptors + the four assessment criteria).

## Demand map (41 booklets)

### Skill × CEFR coverage
`Schreiben/B2 8 · Hören/B2 7 · Lesen/B2 7 · Sprachverwendung/B2 7 · Hören/B1 4 · Schreiben/B1 4 ·
Sprachverwendung/B1 4`. All four skills appear at both B1 and B2 — the full AHS matrix. (Schreiben
states its own task count, e.g. *"enthält drei Aufgaben"* → a target text type per task.)

### Item formats detected
`gap_fill 19` (the Sprachverwendung-im-Kontext signature: word-formation / banked-cloze), `matching 1`.
**Honest limit:** Lesen/Hören use item-specific layouts (true/false-justification, MC, short-answer,
matching) that the coarse structural parser under-detects — the FS parser captures *skill · level ·
task-count · gross format*, by design, not a per-item parse. That's enough for the coverage decision;
a deeper per-item parse is a later refinement if we ever build FS reading-item generation.

## Coverage vs our engine — what's covered, what's the gap

**Already in place** — the **audio / Hörverstehen** seam (`AnnotatedText` with `medium="audio"`,
the F5-TTS `audio:` backend, listening tasks `listening_task`/dim HOR) and the **annotated-text
engine** for reading/writing. So **Hören** and **Lesen/Schreiben** both have an engine home.

**The gaps (the FS analogue of "missing recipes"):**
1. **CEFR-leveled authentic reading texts (Realien)** — the Lesen booklets read **B1/B2 authentic
   non-fiction**; our select-never-author text engine needs a *leveled, rights-clean* source supply
   at B1/B2 (the roadmap's "annotated Realien" item). The Matura confirms the demand is B1+B2, four
   skills — so the curation target is concrete.
2. **Sprachverwendung im Kontext recipes** — `gap_fill` (word-formation, banked cloze) is the
   dominant, **computable** format: from a leveled text, a deterministic recipe can blank a derived
   form and check it (the closest FS thing to a parametric recipe). The one skill where computation,
   not curation, applies.
3. **Schreiben task scaffolds** — like Deutsch's Textsorten, the FS Schreiben tasks target text types
   (email, blog, report, article, essay) with input prompts; a genre-scaffold layer (reuse the
   Deutsch `textsorten` pattern, CEFR-leveled) teaches what the Matura assumes.

## How FS differs (the cross-subject insight)

FS spreads across **four skills**, so the engine answer is **multi-modal**: audio (built) for Hören,
leveled annotated texts for Lesen, genre scaffolds for Schreiben, and one **computable** family
(Sprachverwendung gap-fill). No single durable asset — the asset is the **CEFR-leveled, rights-clean
text/audio supply** plus a thin per-skill scaffold. The skill×level matrix above is the curation spec.
