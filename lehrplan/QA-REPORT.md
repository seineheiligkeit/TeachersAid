# Lehrplan extraction — QA report (first pass)

Deterministic parser (`tools/parse_lehrplan.py`) → per-subject JSON, then a per-subject
**subagent QA pass** comparing each `lehrplan/<CODE>.json` against its source slice and the
`subject-coverage-audit.md`. Physik was validated by hand (clean). This report consolidates the
16 QA agents' findings and drives the fix batch.

**Headline:** verbatim competence *text* extraction is sound across subjects. The defects are
structural and fall into a small number of **systematic, fixable** patterns — almost all traceable
to the parser having been tuned to Physik's exact markup shape.

## Per-subject summary

| Code | Verdict | JSON n | True comp. | Headline issue |
|---|---|---:|---:|---|
| PHY | ✅ clean | 29 | 29 | validated by hand — reference shape |
| DEU | ❌ needs_fix | 47 | 41 | 6 Lehraufgabe bullets + 1 duplicate misfiled as competences; model empty |
| MAT | ❌ needs_fix | 285 | ~42 | Anwendungsbereiche + "Vorschläge" counted as competences; dims misfiled |
| CHE | ❌ needs_fix | 20 | 10 | 10 Anwendungsbereiche misfiled; W/E/S model empty; variant unlabelled |
| CHE2 | ❌ needs_fix | 28 | 10 | 18 Anwendungsbereiche misfiled; W/E/S model empty |
| BIO | ❌ needs_fix | 46 | 10 | 36 Anwendungsbereiche misfiled; W/E/S model empty |
| GPB | ❌ needs_fix | 33 | 30 | 7 competence strands flattened to `ALL`; 3 Konzepte misfiled |
| GWB | ❌ needs_fix | 48 | 48 | grouping OK, but model (O/U/H) empty; heavy ÜT drops |
| LAT | ⚠ minor | 20 | 20 | text correct; ÜT drops; one wrong ÜT value |
| FS1 | ❌ needs_fix | 37 | 37 | model empty; multi-value ÜT drops; listening-conditions lost |
| FS2 | ⚠ minor | 19 | 19 | model empty; ÜT drops; shares FS1 model |
| DGB | ❌ needs_fix | 53 | 72 | ~27 competences misrouted (KB headings undetected); ORI→`ALL` |
| GEZ | ❌ needs_fix | 29 | 9 | 20 Lehraufgabe/label bullets misfiled; H/I axes empty |
| MUS | ⚠ minor | 40 | 40 | correct; model (S/T/H) empty; 11 Handlungsverben uncaptured |
| KUG | ⚠ minor | 40 | 40 | correct; model empty; 2 ÜT drops |
| TED | ❌ needs_fix | 40 | 40 | grouping OK; model empty; 9 ÜT drops; Ergänzende AB misfiled |
| BUS | ❌ needs_fix | 58 | 61 | 3 SGA-contingent competences dropped; 25-bullet `ALL` leak |

Only **DGB** and **BUS** under-count (data dropped/misrouted); all other count-mismatches are
*over*-counts (non-competence bullets misfiled as competences — straightforward to reclassify).

## Systematic parser issues (fix once, benefits all)

1. **Multi-value ÜT superscripts dropped.** 127 footnote refs are single `Hoch` spans like
   `2, 7` / `8, 13`; the `text.isdigit()` test rejects them. → extract all `\d+` groups. *(universal)*
2. **Space lost at superscript-strip site** → `Beziehungenverwenden`, `Informationssystemedifferenziert`.
   `drop()` must leave a separating space. *(verbatim integrity — universal)*
3. **`competence_model.handlungsdimensionen` empty for 15/16 subjects.** The parser only recognised
   Physik's `… (W)`-style dimension headings. Every subject's *correct* model is now known (below);
   supply them via a curated overlay rather than 16 bespoke detectors.
4. **Kompetenzbereich headings without the literal "Kompetenzbereich " prefix go undetected** →
   competences fall into a `…US.x.ALL.*` bucket (DGB ORI, etc.). Detect KB headings structurally
   (ErlUeberschr headings inside the Kompetenzbeschreibungen section), not by prefix.
5. **Anwendungsbereiche misfiled as competences** for the cross-class-competence subjects
   (CHE/CHE2/BIO, and the MINT "Vorschläge" lists in MAT). Detect the Anwendungsbereiche boundary
   even when competences are not Klasse-grouped.
6. **Pre-class / model / concept bullets misfiled as competences** (`…x.ALL.*`): Grunderfahrungen &
   Lehraufgabe bullets (MAT, GEZ, BUS), process-dimension descriptors (MAT, DGB, GEZ, BUS), zentrale
   Konzepte (GPB, GWB, MUS). Route these to `prose` / `competence_model` / `zentrale_konzepte`.
7. **Dropped competences:** DGB ~27 `(I)` (misrouted via #4); BUS 3 SGA-contingent (Gleiten/Schwimmen/
   Rollen). Must not silently drop — diagnose and capture (flag SGA-contingent).
8. **Minor:** Anwendungsbereiche sub-grouping/ÜT refs flattened; some prose duplicated per Klasse;
   OCR doubling in BUS prose (`turnerischeturnerische`).

## Corrected competence models (recovered by QA — the enrichment layer)

| Code | Handlungsdimensionen | Content axis / notes |
|---|---|---|
| PHY/CHE/CHE2/BIO | **W** Fachwissen/Wissen · **E** Erkenntnisgewinnung · **S** Standpunkte | Naturwissenschaften; shared model. Inhaltsdimension via zentrale Konzepte |
| MAT | **MOD** Modellieren · **OPE** Operieren · **DAR** Darstellen · **BEG** Vermuten/Begründen | content_areas: **ZAH** Zahlen u. Maße · **VAR** Variablen u. Funktionen · **FIG** Figuren u. Körper · **DAT** Daten u. Zufall |
| DEU | **SPR** Sprachbewusstsein (integrativ) · **ZUH** Zuhören/Sprechen (oral) · **LES** Lesen · **SCH** Schreiben | — |
| FS1/FS2 | **HOR** Hören (audio) · **LES** Lesen · **SPR** Sprechen (oral) · **SCH** Schreiben | CEFR per Klasse (FS1 A1→B1, FS2 A1→A2). **No** Sprachmittlung in Unterstufe |
| LAT | (no separate Handlungsdim.) | Kompetenzbereiche: **SPR** Sprach-/textbezogen · **INH** Inhalts-/themenbezogen |
| GWB | **OK** Orientierungs- · **UK** Urteils- · **HK** Handlungskompetenz | 8 zentrale Konzepte; Anforderungsbereiche (Reprod./Transfer/Reflexion) |
| GPB | 7 strands: hist. **Frage/Methoden/Orientierung/Sach** · pol. **Urteils/Methoden/Handlungs** (+ joint Sach) | Anforderungsbereiche; 3 zentrale Konzepte |
| DGB | Frankfurt Dreieck **T** technisch · **G** gesellschaftlich · **I** interaktionsbezogen | Kompetenzbereiche: ORI/INF/KOM/PRO/HAN |
| GEZ | **H1** Analysieren/Argumentieren · **H2** Darstellen/Operieren · **H3** Interpretieren/Reflektieren | content_areas **I1** Objekte · **I2** Transformationen · **I3** Projektionen/Risse |
| MUS | Kompetenzbereiche **SIN** Singen/Musizieren · **TAN** Tanzen/Bewegen/Darstellen · **HOR** Hören/Erfassen | 11 Handlungsverben; 4 zentrale Konzepte; SIN/TAN enactive |
| KUG | **BIL** Bildnerische Praxis · **WAH** Wahrnehmen u. Reflektieren · **BK** Bildsprachen/Kommunizieren | content: bildende Kunst · gestaltete Umwelt · visuelle Kommunikation |
| TED | **ENT** Entwicklung · **HER** Herstellung (enactive) · **REF** Reflexion | Ergänzende Anwendungsbereiche are cross-Klassen |
| BUS | **FAC** Fach- · **MET** Methoden- · **SOZ** Sozial- · **SEL** Selbstkompetenz | Inhalt: sport categories + Sinndimensionen; mostly enactive |

## Discrepancies vs `subject-coverage-audit.md` (for SME confirmation)

1. **Ethik** — appears only under *2. Oberstufe* in this Fassung; the audit lists "Ethik (1–4)" as
   Unterstufe. Likely an audit error (Ethik rolled out Sek-II-first). → Ethik is **not** in the
   Unterstufe foundation.
2. **Sprachmittlung** — the audit lists it as a 5th Fremdsprache Kompetenzbereich; it is **absent**
   from FS1/FS2 Unterstufe (only Hören/Lesen/Sprechen/Schreiben). Likely Oberstufe/GeR bleed-through.
3. **Chemie = two curricula:** **CHE** = AHS (Gym/RG), 2-stündig, 4. Klasse · **CHE2** =
   Wirtschaftskundliches RG, 4-stündig, 3.+4. Klasse. The audit's single "Chemie (4)" covers only CHE.
4. **GPB** is a **dual** historisch/politisch model (7 Kompetenzbereiche), richer than a flat list.
5. **KUG** — source has one "Wahrnehmen und Reflektieren" Kompetenzbereich (audit splits it).
6. **Anforderungsbereiche** (Reproduktion/Transfer/Reflexion/Problemlösung) are explicit in GPB/GWB —
   corroborates the schema's `CognitiveLevel` ↔ Anforderungsbereiche mapping; not yet captured.

## Fix plan (proposed)

- **A. Universal parser bugs** (#1, #2, #4, #5, #6): heading/section detection reworked to be
  structure-driven; ÜT regex + space-preserving strip. Re-run regenerates all subjects.
- **B. Curated model overlay** `lehrplan/subject_models.json` (hand-authored from the table above),
  merged by the parser → populates `handlungsdimensionen`, `content_areas`, per-dimension `modality`,
  and the `kompetenzbereich → dimension` mapping. Keeps verbatim extraction deterministic.
- **C. Dropped data** (#7): diagnose DGB `(I)` routing + BUS SGA-contingent; capture with a flag.
- **D. Audit reconciliation:** apply confirmed corrections (1–6) to `subject-coverage-audit.md`.
- Re-run → re-QA the previously-broken subjects to confirm green.
