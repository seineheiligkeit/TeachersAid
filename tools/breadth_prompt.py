"""Build fully-grounded generation prompts for the breadth push, from the catalog.

For each configured subject it writes `runs/ingest/prompt_<CODE>.md` — a self-contained
brief a subagent follows to emit one AHS-Unterstufe worksheet body (the GenWorksheetBody
shape) anchored to REAL competence ids. The deterministic grounding (verbatim
competences, allowed dimensions, allowed kinds, the JSON shape + a worked example) lives
here so the agent can't invent it. `python -m teachersaid` is not needed; run with the venv:

    python tools/breadth_prompt.py            # writes runs/ingest/prompt_*.md
"""
from __future__ import annotations

import json
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.schema.enums import CORE_TASK_KINDS

# Pilot: the MINT core. (code, subject, klasse, anchor_type, anchor_value, theme, note)
SUBJECTS = [
    ("PHY", "Physik", 4, "kb", "Wetter und Klima", "Wetter, Klima und Energiehaushalt",
     "Inhaltlicher Kompetenzbereich — die Aufgaben bedienen die unten gelisteten WET-Kompetenzen."),
    ("MAT", "Mathematik", 4, "kb", "2: Variablen und Funktionen",
     "Variablen, Terme und lineare Funktionen",
     "MAT-Kompetenzen tragen KEINE W/E/S-Dimensionen — ordne jeder Aufgabe genau eine der "
     "Modell-Dimensionen (MOD/OPE/DAR/BEG) zu, primäre zuerst."),
    ("CHE", "Chemie", 4, "grade", "Säuren, Basen und Neutralisation",
     "Säuren, Basen und Neutralisation",
     "Die Kompetenzen sind PROZESS-Kompetenzen (beobachten, interpretieren, argumentieren, "
     "bewerten); der Inhalt 'Säuren und Basen' ist das Vehikel. Jede Aufgabe dient einer "
     "dieser Prozess-Kompetenzen, gezeigt am Säure-Base-Inhalt."),
    ("BIO", "Biologie", 4, "grade", "Vererbung, DNA und Genetik",
     "Vererbung, DNA und Genetik",
     "Prozess-Kompetenzen; Inhalt 'Vererbung/Genetik' als Vehikel. NICHT Immunsystem "
     "(dieses Arbeitsblatt existiert bereits)."),
]

_TEMPLATE = """# Generierungs-Auftrag: {subject}, {klasse}. Klasse — Thema „{theme}“

Du erzeugst **ein** Arbeitsblatt für die **AHS-Unterstufe (4. Klasse)** auf österreichischem
Lehrplan-Niveau. Sprache des Inhalts: **Deutsch**. Niveau: AHS — nicht zu niedrig.

{note}

## Kompetenzen, an die du verankerst (verbatim — `serves.competence_id` muss eine dieser IDs sein)
{competences}

## Erlaubte Dimensionen (`dimensions`, primäre zuerst — Teilmenge dieser Codes)
{dims}

## Erlaubte Aufgaben-`kind`-Werte (genau diese Strings)
{kinds}

## Regeln
- Verankere **jede** Aufgabe mit `serves` an genau einer der oben gelisteten Kompetenz-IDs. Nutze
  über das Blatt **mehrere verschiedene** Kompetenzen (2–{n_comp}).
- `dimensions` ⊆ den erlaubten Codes; `kind` ∈ den erlaubten kinds; `cognitive_level` ∈
  remember/understand/apply/analyze/evaluate/create und **steigt** (eine Leiter, nicht alles „remember“;
  baue analyze/evaluate/create ein).
- **Korrektheit by construction:** behaupte nichts Unsicheres. Was eine Lehrkraft beachten muss
  (häufige Fehlvorstellungen), kommt in `watch_outs` (tragend).
- **Keine Bilder/Assets:** kein `kind:"figure"`, kein `data_interpretation`, keine `asset_refs`,
  keine `response.mode` aus {{diagram, drawing, artifact}}. Reiner Text.
- **Schülertext ist für Schüler:innen:** in `prompt`, Optionen und Intro **niemals** Kompetenz-IDs,
  Dimensionen oder „Lehrplan“ erwähnen.
- Pro Aufgabe: `answer_key` (erwartete Lösung) und `watch_outs`. Für offene/Erstellungs-Aufgaben
  optional `acceptable_reasoning` (akzeptabler Spielraum) und `rubric` — Liste von Objekten der
  Form `{{"criterion":"...","levels":["...","..."]}}` (**englische Schlüssel**: `criterion`, `levels`).
- Pro Section die **Lehrkraft-Ebene**: `throughline` (Roter Faden, 1 Satz), `talking_points`
  (2–4 Gesprächsanker/Fragen für die Klasse), `extensions` (1–3 Vertiefungs-/Differenzierungsideen).
- Umfang: **5–7 Aufgaben** + optional 1 kurzer Info-Block (Intro). Realistische `est_minutes`
  (Summe ~ eine Doppelstunde, ~90–110 min).

## Antwort-Formen (`response`) — nutze nur diese
- `{{"mode":"lines","n":<int>}}`  ·  `{{"mode":"box","min_height_mm":<float>}}`
- `{{"mode":"table","columns":[...],"rows":<int>}}`  ·  `{{"mode":"choices","options":[...],"select":"one"|"many"}}`
- `{{"mode":"none"}}`

## Payload (`payload`, optional) — passend zum kind, sonst `null`
- multiple_choice: `{{"kind":"multiple_choice","options":[...],"select":"one"|"many"}}`
- true_false_justify: `{{"kind":"true_false_justify","statements":[...]}}`
- ordering: `{{"kind":"ordering","items":[...]}}`  ·  matching: `{{"kind":"matching","left":[...],"right":[...]}}`
- table_fill: `{{"kind":"table_fill","columns":[...],"rows":[[<str|null>,...]]}}`  ·  decision_scenario: `{{"kind":"decision_scenario","stem":"..."}}`

## Ausgabe
Schreibe **ausschließlich** das folgende JSON-Objekt nach `runs/ingest/{code}.json` (kein Fließtext,
keine ``` Code-Zäune in der Datei):

```json
{{
  "subject": "{subject}", "klasse": {klasse},
  {anchor_field}
  "title": "<prägnanter Titel>",
  "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {{
    "intro": [ {{"role":"info","id":"i1","kind":"prose","content":"...","watch_outs":[]}} ],
    "sections": [ {{
      "id":"s1","title":"<Abschnittstitel>",
      "throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[
        {{"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
         "response":{{"mode":"lines","n":3}},"cognitive_level":"understand",
         "dimensions":["{dim0}"],"serves":[{{"competence_id":"{ex_comp}","relation":"exercises"}}],
         "est_minutes":7,"answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]}}
      ]
    }} ]
  }}
}}
```
"""


def _competence_lines(comps) -> str:
    out = []
    for c in comps:
        dims = ",".join(c.dimensions) if c.dimensions else "—"
        out.append(f"- `{c.id}` [dims {dims}]: {c.text.strip()}")
    return "\n".join(out)


def build():
    outdir = RUNS_DIR / "ingest"
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for code, subject, klasse, atype, avalue, theme, note in SUBJECTS:
        model = ls.get_subject_model(subject)
        allc = ls.competences_for(subject, klasse)
        comps = [c for c in allc if c.kompetenzbereich == avalue] if atype == "kb" else allc
        dims = "\n".join(f"- `{d.id}` — {d.label}" for d in model.dimensions)
        kinds = ", ".join(sorted(CORE_TASK_KINDS | set(model.task_kind_extensions)))
        if atype == "kb":
            anchor_field = f'"kompetenzbereich": "{avalue}",'
        else:
            anchor_field = f'"scope_label": "{theme}",'
        prompt = _TEMPLATE.format(
            subject=subject, klasse=klasse, theme=theme, note=note,
            competences=_competence_lines(comps), dims=dims, kinds=kinds,
            n_comp=len(comps), code=code, anchor_field=anchor_field,
            dim0=model.dimensions[0].id, ex_comp=comps[0].id,
        )
        (outdir / f"prompt_{code}.md").write_text(prompt, encoding="utf-8")
        manifest.append({"code": code, "subject": subject, "klasse": klasse,
                         "anchor": atype, "value": avalue, "theme": theme,
                         "n_competences": len(comps)})
        print(f"{code}: {len(comps)} competences, {len(model.dimensions)} dims -> prompt_{code}.md")
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                          encoding="utf-8")


if __name__ == "__main__":
    build()
