"""Build wedge-campaign briefs from the coverage planner's gap export (Track 3).

The planner-driven sibling of `tools/breadth_prompt.py`: where the breadth brief covers a
whole subject, a campaign brief targets the NON-GREEN cells of one (subject, Klasse) —
`stats.campaign_gaps` supplies the cells + verbatim competence anchors, and the brief
carries the *grün* criterion itself (>= GREEN_MIN_TASKS tasks spanning all three
Anforderungsbereiche), so a subagent's output is sized to turn its cells green at the
gate. Two anchor modes, mirroring `breadth_prompt`:

  kb    — content-KB subjects (MAT, PHY): one worksheet per gap KB, anchored via
          `"kompetenzbereich"`; a `teil` cell notes which Bänder are missing.
  grade — strand-KB subjects (BIO, CHE): worksheets span all strands via `scope_label`;
          the grün arithmetic is stated per strand. An all-`teil` group becomes a single
          top-up sheet targeting exactly the missing (strand x Band) combos.

Run with the venv (writes runs/ingest/<CAMPAIGN_DIR>/prompt_<CODE>_kl<k>.md):

    python tools/campaign_prompt.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import data_store as ds
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.pipeline.assets import GENERATION_RECIPES
from teachersaid.schema.enums import CORE_TASK_KINDS
from teachersaid.stats import campaign_gaps
from teachersaid.store.blockstore import BlockStore

STUFE = "Unterstufe"
CAMPAIGN_DIR = "campaign_mint_us"  # the MINT-US wedge push (5 Jul 2026)
SHEETS_FULL_GRADE = 3              # sheets per fully-open grade-mode group

# code -> (display name, anchor mode, subject hint injected into the brief)
SUBJECTS: dict[str, tuple[str, str, str]] = {
    "MAT": ("Mathematik", "kb",
            "Nutze Abbildungen aktiv: für *Figuren und Körper* die Geometrie-Recipes "
            "(`right_triangle`, `rectangle`, `polygon`, `circle`, `coordinate_plane`, ab der 3. Kl. "
            "auch `triangle_construction`), für *Zahlen und Maße* den `number_line`, für *Variablen "
            "und Funktionen* `function_graph`. Beschriftungen so wählen, dass die Abbildung die "
            "Lösung NICHT verrät (Maskierung: \"c = ?\", \"A = ?\")."),
    "PHY": ("Physik", "kb",
            "Abbildungen tragen Physik: `function_graph` für Weg-Zeit-/v-t-Verläufe, `number_line` "
            "für Skalen (Frequenz, Schallpegel, Brennweite), `line` für Messreihen. Alltagsnahe "
            "Kontexte (Brille, Fotoapparat, Musikinstrument, E-Bike) statt Formel-Drill."),
    "CHE": ("Chemie", "grade",
            "Der Tafel-Test gilt hier besonders (nackte Chemie-Drills wurden bereits abgelehnt): "
            "jeder Aufgabenblock braucht einen echten Kontextrahmen (Haushalt, Labor, Umwelt, "
            "Technik), eine gestufte Struktur und Teilschritte mit eigenem Denkwert."),
    "BIO": ("Biologie und Umweltbildung", "grade",
            "Echte biologische Kontexte (Organismus, Lebensraum, Körper, Ökosystem) mit "
            "Beobachtungs-/Auswertungsaufgaben; wo Daten helfen, eine `data_figures`-Abbildung "
            "(intent-deklariert). Keine reinen Benenn-Listen."),
}

_BAND_RULE = ("**Anforderungsbereiche (Bänder)** — abgeleitet aus `cognitive_level`:\n"
              "- **AB I (leicht)** = `remember` | `understand`\n"
              "- **AB II (mittel)** = `apply` | `analyze`\n"
              "- **AB III (anspruchsvoll)** = `evaluate` | `create`\n")

_BLACKBOARD = ("## Qualitätslatte — der Tafel-Test (tragend)\n"
               "Jedes Blatt muss MEHR Wert liefern als das, was eine Lehrkraft in einer Minute an "
               "die Tafel schreibt: echter Kontext statt nackter Drill-Reihe, ein roter Faden mit "
               "ansteigender Struktur, Aufgaben, die ohne das Blatt nicht stellbar wären "
               "(Abbildung, Datenbezug, Fallkontext, gestufte Teilschritte). Reine Rechen-/"
               "Abfragepäckchen (\"Löse: a) … b) … c) …\") ohne Rahmen werden am Gate abgelehnt.\n")

_RULES = """## Regeln (für jedes Blatt)
- 5–7 Aufgaben (`blocks` mit role "task") + optional 1 kurzer Info-Block. Realistische `est_minutes`.
- Verankere **jede** Aufgabe via `serves` an einer der oben gelisteten IDs; nutze mehrere verschiedene.
- `dimensions` ⊆ erlaubte Codes; `kind` ∈ erlaubte kinds; die kognitive Leiter steigt
  (remember→…→create), nicht alles „remember".
- **Korrektheit by construction**; Fehlvorstellungen/Hinweise in `watch_outs` (tragend).
- **Abbildungen — Code-generiert, korrekt by construction** (nie freie Bilder/Diffusion): wo eine
  Abbildung die Aufgabe wirklich verbessert, fordere eine an und referenziere sie über `asset_refs`.
  Reiner Text bleibt ok, wenn keine Abbildung nötig ist.
  **Für DATEN: deklariere die ABSICHT, nicht den Diagrammtyp** — lege die Figur in `body.data_figures`;
  das System wählt die passende, lesbare Darstellung (so wird nicht alles ein Balkendiagramm).
  Form: `{{"id":str,"intent":str,"title"?,"xlabel"?,"ylabel"?,"categories"?:[str],"values"?:[num],"points"?:[[x,y]],"log"?:bool,"fit"?:bool,"data_source"?:{{"dataset_id":str,"series":str}}}}`
  mit `intent` ∈
    - `trend` — Verlauf/Entwicklung (oft über die Zeit): `categories`+`values` → Liniendiagramm
    - `comparison` — MENGEN-Vergleich zwischen Kategorien: `categories`+`values` → Balkendiagramm
    - `relationship` — Zusammenhang zweier numerischer Größen: `points` (+`fit`) → Streudiagramm
    - `distribution` — Häufigkeit/Streuung einer Größe: `values` → Histogramm
    - `spread` — Fünf-Punkte-Zusammenfassung / Verteilungen vergleichen: `values` → Boxplot
    - `scale` — Position auf einer Skala (z. B. pH-Wert): `categories`+`values` → Zahlenstrahl
    - `demographic` — Alter × Geschlecht: `categories`+`male`+`female` → Bevölkerungspyramide
{data_block}  **Wähle nie selbst „Balken" für eine Zeitreihe, eine Ja/Nein-Klassifikation oder eine Skala** —
  dafür ist der `intent` da; korrekte Zahlen allein genügen NICHT, die Darstellung muss zur Aussage passen.
  **Für STRUKTUR-Abbildungen** (Geometrie, Funktionsgraph, Formel, Zahlenstrahl, Baumdiagramm) nutze
  `body.assets` mit explizitem Generator — **erlaubte Generatoren (nur diese):**
{recipes}
  **Wichtig — eine Abbildung darf die gesuchte Lösung NICHT verraten:** keine Werte/Beschriftungen
  anzeigen, die die Schüler:innen erst bestimmen sollen (Maskierung nutzen, z. B. "c = ?").
  Keine freien Bilder/Diffusion, kein `data_interpretation`-Payload,
  keine `response.mode` ∈ {{diagram, drawing, artifact}}. Reiner Text (modality "printable").
- **Schülertext ist für Schüler:innen** — niemals Kompetenz-IDs/Dimensionen/„Lehrplan" im `prompt`/Intro.
- Pro Aufgabe `answer_key` + `watch_outs`; optional `acceptable_reasoning` und `rubric`
  (Liste von `{{"criterion":"...","levels":["...","..."]}}`, **englische Schlüssel**).
- Pro Section die Lehrkraft-Ebene: `throughline` (Roter Faden), `talking_points` (2–4), `extensions` (1–3).

## Antwort-Formen (`response`): `{{"mode":"lines","n":<int>}}` · `{{"mode":"box","min_height_mm":<float>}}` ·
`{{"mode":"table","columns":[...],"rows":<int>}}` · `{{"mode":"choices","options":[...],"select":"one"|"many"}}` · `{{"mode":"none"}}`
## Payload (`payload`, optional, sonst null): multiple_choice `{{"kind":"multiple_choice","options":[...],"select":"one"}}` ·
true_false_justify `{{"kind":"true_false_justify","statements":[...]}}` · ordering `{{"kind":"ordering","items":[...]}}` ·
matching `{{"kind":"matching","left":[...],"right":[...]}}` · decision_scenario `{{"kind":"decision_scenario","stem":"..."}}`

## Ausgabe
Schreibe **{n} Dateien**: `runs/ingest/{gendir}/{code}_kl{klasse}_1.json` … `runs/ingest/{gendir}/{code}_kl{klasse}_{n}.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{{
  "subject": "{subject}", "klasse": {klasse},
  {anchor_field}
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {{
    "intro": [],
    "data_figures": [],
    "assets": [],
    "sections": [ {{ "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {{"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{{"mode":"lines","n":3}},"cognitive_level":"understand","dimensions":["{dim0}"],
        "serves":[{{"competence_id":"<ID>","relation":"exercises"}}],"est_minutes":7,"asset_refs":[],
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]}} ] }} ]
  }}
}}
```
"""

_BAND_LABEL = {1: "AB I (leicht)", 2: "AB II (mittel)", 3: "AB III (anspruchsvoll)"}
# lehrplan_store maps a None Kompetenzbereich to the literal "—" placeholder
_UNNAMED = (None, "", "—")


def _kb_label(kb: str | None) -> str:
    return "(ohne Bereichsname)" if kb in _UNNAMED else kb


def _competence_lines(subject: str, klasse: int, kbs: set[str | None] | None) -> str:
    """Verbatim competences of the Klasse, optionally filtered to the gap KBs, grouped by KB."""
    by_kb: dict[str, list] = defaultdict(list)
    for c in ls.competences_for(subject, klasse, STUFE):
        if kbs is not None and c.kompetenzbereich not in kbs:
            continue
        by_kb[_kb_label(c.kompetenzbereich)].append(c)
    lines = []
    for kb in sorted(by_kb):
        lines.append(f"\n### {kb}")
        for c in by_kb[kb]:
            dims = ",".join(c.dimensions) if c.dimensions else "—"
            lines.append(f"- `{c.id}` (Kl {c.klasse or klasse}) [dims {dims}]: {c.text.strip()}")
    return "\n".join(lines)


def _zusatz_kb(subject: str, klasse: int, cells: list[dict]) -> str:
    """One sheet per gap KB; teil cells carry their missing-band focus."""
    lines = [f"# KAMPAGNEN-AUFTRAG: {subject}, Klasse {klasse} — {len(cells)} Arbeitsblätter, "
             f"EXAKT eines je Kompetenzbereich",
             "",
             "Dieses Set schließt gezielt Korpus-Lücken. Die Blätter:"]
    for i, c in enumerate(cells, 1):
        if c["status"] == "teil":
            missing = " + ".join(_BAND_LABEL[b] for b in c["missing_bands"])
            note = (f" — hier gibt es schon {c['task_blocks']} Aufgaben, es FEHLEN Aufgaben in "
                    f"{missing}: lege den Schwerpunkt dorthin (der Rest der Leiter darf schlank bleiben)")
        else:
            note = " — noch leer: volle Bandbreite nötig"
        lines.append(f"{i}. Blatt {i}: KB **\"{c['kompetenzbereich']}\"**{note}")
    lines += ["", _BAND_RULE,
              "**Grün-Kriterium je Blatt:** mindestens **5 Aufgaben**, alle via `serves` an Kompetenzen "
              "DIESES KBs (dieser Klasse) verankert, und (sofern oben nicht anders fokussiert) alle drei "
              "Bänder vertreten: ≥1× AB I, ≥2× AB II, ≥1× AB III.",
              f"Setze im JSON `\"kompetenzbereich\"` exakt auf den KB-Namen des Blatts und `\"klasse\": {klasse}`. "
              "Wähle je Blatt eine eigene, kreative Kernfrage (kein KB-Namens-Echo)."]
    return "\n".join(lines)


def _zusatz_grade_full(subject: str, klasse: int, cells: list[dict], n: int) -> str:
    strands = [c["kompetenzbereich"] for c in cells]
    lines = [f"# KAMPAGNEN-AUFTRAG: {subject}, Klasse {klasse} — {n} thematisch verschiedene Arbeitsblätter",
             "",
             "Die Kompetenzbereiche dieses Fachs sind **Prozess-Stränge** — ein echtes Thema bedient "
             "mehrere zugleich:"]
    for s in strands:
        lines.append(f"- **{s}**")
    lines += ["", _BAND_RULE,
              f"**Grün-Kriterium (über das ganze Set von {n} Blättern gerechnet, JE STRANG):** "
              "≥5 Aufgaben pro Strang UND alle drei Bänder pro Strang vertreten.",
              "Praktisch heißt das: **jedes Blatt enthält Aufgaben aus allen drei Strängen** — bei echten "
              "Themen natürlich: beschreiben/erklären (W), beobachten/untersuchen/auswerten (E), "
              "bewerten/Stellung nehmen (S) — und du verteilst die Bänder bewusst so, dass am Ende jeder "
              "Strang die volle Leiter hat. Die Strang-Zuordnung einer Aufgabe entsteht über die "
              "`serves`-Kompetenz (siehe deren KB unten).",
              f"Setze im JSON `\"scope_label\": \"<Thema>\"` und `\"klasse\": {klasse}` "
              "(KEIN `\"kompetenzbereich\"`-Feld). Wähle klar unterschiedliche Themen (Breite!)."]
    return "\n".join(lines)


def _zusatz_grade_topup(subject: str, klasse: int, cells: list[dict]) -> str:
    lines = [f"# KAMPAGNEN-AUFTRAG: {subject}, Klasse {klasse} — 1 gezieltes Ergänzungsblatt",
             "",
             "Die Stränge dieser Klasse sind schon TEILWEISE gefüllt; es fehlen exakt diese "
             "(Strang × Band)-Kombinationen:"]
    for c in cells:
        missing = " + ".join(_BAND_LABEL[b] for b in c["missing_bands"])
        # a strand with no KB name (e.g. Chemie's cross-cutting ALL.* competences) is
        # unactionable by name — name the exact competence ids the missing band must serve.
        if c["kompetenzbereich"] in _UNNAMED:
            ids = ", ".join(f"`{i}`" for i in c.get("competences", []))
            head = f"**(fachübergreifender Strang ohne Bereichsnamen)** — verankere hier an: {ids}"
        else:
            head = f"**{c['kompetenzbereich']}**"
        lines.append(f"- {head} (bereits {c['task_blocks']} Aufgaben): es fehlt {missing}")
    lines += ["", _BAND_RULE,
              "**Auftrag:** EIN kohärentes Blatt (ein Thema, das das natürlich hergibt) mit 5–7 Aufgaben, "
              "das **je fehlender Kombination oben ≥2 Aufgaben** liefert (Strang-Zuordnung über die "
              "`serves`-Kompetenz, Band über `cognitive_level`). Übrige Aufgaben frei.",
              f"Setze im JSON `\"scope_label\": \"<Thema>\"` und `\"klasse\": {klasse}` "
              "(KEIN `\"kompetenzbereich\"`-Feld)."]
    return "\n".join(lines)


def build() -> None:
    outdir = RUNS_DIR / "ingest" / CAMPAIGN_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    recipes = "\n".join(f"  - `{gid}` — {hint}" for gid, hint in GENERATION_RECIPES.items())
    gaps = campaign_gaps(BlockStore(), stufe=STUFE)
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for g in gaps:
        if g["code"] in SUBJECTS:
            groups[(g["code"], g["klasse"])].append(g)

    manifest = []
    for (code, klasse), cells in sorted(groups.items()):
        subject, anchor, hint = SUBJECTS[code]
        model = ls.get_subject_model(subject, STUFE)
        all_teil = all(c["status"] == "teil" for c in cells)
        if anchor == "kb":
            n = len(cells)
            zusatz = _zusatz_kb(subject, klasse, cells)
            comp = _competence_lines(subject, klasse, {c["kompetenzbereich"] for c in cells})
            anchor_field = '"kompetenzbereich": "<exakter KB-Name dieses Blatts>",'
        elif all_teil:
            n = 1
            zusatz = _zusatz_grade_topup(subject, klasse, cells)
            comp = _competence_lines(subject, klasse, None)
            anchor_field = '"scope_label": "<Thema>",'
        else:
            n = SHEETS_FULL_GRADE
            zusatz = _zusatz_grade_full(subject, klasse, cells, n)
            comp = _competence_lines(subject, klasse, None)
            anchor_field = '"scope_label": "<Thema>",'

        dims = "\n".join(f"- `{d.id}` — {d.label}" for d in model.dimensions)
        kinds = ", ".join(sorted(CORE_TASK_KINDS | set(model.task_kind_extensions)))
        ab = ls.anwendungsbereiche_for(subject, klasse, STUFE)
        ab_block = ("\n## Anwendungsbereiche (Themen-Ideen)\n- " + " · ".join(ab[:10]) + "\n") if ab else ""
        data_brief = ds.format_available_datasets(ds.relevant_datasets(subject=code))
        data_block = ("\n" + data_brief + "\n") if data_brief else ""

        rules = _RULES.format(n=n, gendir=CAMPAIGN_DIR, code=code, klasse=klasse, subject=subject,
                              anchor_field=anchor_field, dim0=model.dimensions[0].id,
                              recipes=recipes, data_block=data_block)
        brief = (f"{zusatz}\n\nSprache: **Deutsch**, AHS-Unterstufe Klasse {klasse} "
                 f"(altersgerecht, aber nicht zu niedrig).\n\n"
                 f"{_BLACKBOARD}\n## Fach-Hinweis\n{hint}\n"
                 f"\n## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein)\n{comp}\n"
                 f"\n## Erlaubte Dimensionen (`dimensions`, primäre zuerst)\n{dims}\n"
                 f"\n## Erlaubte Aufgaben-`kind`-Werte\n{kinds}\n{ab_block}\n{rules}")
        path = outdir / f"prompt_{code}_kl{klasse}.md"
        path.write_text(brief, encoding="utf-8")
        manifest.append({"code": code, "subject": subject, "klasse": klasse, "sheets": n,
                         "cells": [{"kb": c["kompetenzbereich"], "status": c["status"],
                                    "missing_bands": c["missing_bands"]} for c in cells]})
        print(f"{code} Kl{klasse}: {len(cells)} Zellen -> {n} Blätter -> {path.name}")

    # next to the sheet dir, NOT in it — ingest_batch --dir globs *.json there
    (outdir.parent / f"{CAMPAIGN_DIR}_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(m["sheets"] for m in manifest)
    print(f"\n== {len(manifest)} Briefe, {total} Blätter geplant ==")


if __name__ == "__main__":
    build()
