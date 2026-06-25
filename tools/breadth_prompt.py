"""Build fully-grounded breadth-generation briefs from the catalog (one per subject).

Each `runs/ingest/prompt_<CODE>.md` is a self-contained brief: a subagent reads it,
picks N distinct Kernfragen spanning the subject's themes, and writes one wrapper JSON
per Kernfrage to `runs/ingest/gen/<CODE>_<n>.json`. The deterministic grounding
(verbatim competences grouped by Kompetenzbereich + grade, allowed dims/kinds, the JSON
shape) lives here so agents can't invent it. Run with the venv:

    python tools/breadth_prompt.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.schema.enums import CORE_TASK_KINDS

N_KERNFRAGEN = 5

# code, subject, anchor ("kb" content/skill-KBs | "grade" strand/None-KB), practical(enactive)
SUBJECTS = [
    ("DEU", "Deutsch", "kb", False),
    ("GWB", "Geographie und wirtschaftliche Bildung", "kb", False),
    ("GPB", "Geschichte und politische Bildung", "grade", False),
    ("DGB", "Digitale Grundbildung", "kb", False),
    ("GEZ", "Geometrisches Zeichnen", "kb", False),
    ("MUS", "Musik", "kb", True),
    ("KUG", "Kunst und Gestaltung", "kb", True),
    ("TED", "Technik und Design", "kb", True),
    ("BUS", "Bewegung und Sport", "kb", True),
]

_TEMPLATE = """# Breiten-Generierung: {subject} — {n} Kernfragen

Du erzeugst **{n} verschiedene** Arbeitsblatt-Inhalte (je eine eigene **Kernfrage**) für die
**AHS-Unterstufe** auf österreichischem Lehrplan-Niveau. Sprache: **Deutsch**, AHS-Niveau (nicht zu niedrig).
Wähle **{n} klar unterschiedliche Themen/Bereiche** (Breite!), nicht Varianten desselben Themas.

## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein), gruppiert nach Kompetenzbereich
{competences}

## Erlaubte Dimensionen (`dimensions`, primäre zuerst — Teilmenge dieser Codes)
{dims}

## Erlaubte Aufgaben-`kind`-Werte
{kinds}
{ab_block}{anchor_rule}

## Regeln (für jede der {n} Kernfragen)
- 5–7 Aufgaben (`blocks` mit role "task") + optional 1 kurzer Info-Block. Realistische `est_minutes`.
- Verankere **jede** Aufgabe via `serves` an einer der oben gelisteten IDs; nutze mehrere verschiedene.
- `dimensions` ⊆ erlaubte Codes; `kind` ∈ erlaubte kinds; `cognitive_level` steigt
  (remember→…→create; baue analyze/evaluate/create ein), nicht alles „remember".
- **Korrektheit by construction**; Fehlvorstellungen/Hinweise in `watch_outs` (tragend).
- **Keine Bilder/Assets**: kein `kind:"figure"`, kein `data_interpretation`, keine `asset_refs`,
  keine `response.mode` ∈ {{diagram, drawing, artifact}}. {modality_note}
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
Schreibe **{n} Dateien**, eine pro Kernfrage, nach `runs/ingest/gen/{code}_1.json` … `runs/ingest/gen/{code}_{n}.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{{
  "subject": "{subject}", "klasse": <1-4, eine Klasse mit Kompetenzen im gewählten Bereich>,
  {anchor_field}
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {{
    "intro": [],
    "sections": [ {{ "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {{"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{{"mode":"lines","n":3}},"cognitive_level":"understand","dimensions":["{dim0}"],
        "serves":[{{"competence_id":"<ID>","relation":"exercises"}}],"est_minutes":7,
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]}} ] }} ]
  }}
}}
```
"""

_ANCHOR_KB = ('## Verankerung\nJede Kernfrage gehört zu **einem** Kompetenzbereich; setze im JSON '
              '`"kompetenzbereich": "<exakter KB-Name>"` und die passende `klasse` (eine Klasse, in der '
              'dieser KB Kompetenzen hat). Alle Aufgaben dieser Kernfrage dienen Kompetenzen aus diesem '
              '(KB, Klasse).\n')
_ANCHOR_GRADE = ('## Verankerung\nDie Kompetenzen sind fachübergreifend/Prozess-Kompetenzen — das Thema '
                 'liefert der Inhalt. Setze im JSON `"scope_label": "<Thema/Anwendungsbereich>"` und die '
                 '`klasse`; jede Aufgabe dient einer Kompetenz dieser Klasse (siehe Liste).\n')


def _klassen(subject: str) -> list[int]:
    """Grades that actually carry competences (robust to None-KB competences, which
    grade_map drops)."""
    return [k for k in (1, 2, 3, 4) if ls.competences_for(subject, k)]


def _competence_block(subject: str, anchor: str) -> tuple[str, str]:
    """Returns (competences_grouped_text, anchor_field_template)."""
    klassen = _klassen(subject)
    by_kb: dict[str, list] = defaultdict(list)
    for kl in klassen:
        for c in ls.competences_for(subject, kl):
            by_kb[c.kompetenzbereich].append((kl, c))
    lines = []
    for kb in sorted(by_kb, key=lambda x: x or ""):
        lines.append(f"\n### {kb}")
        seen = set()
        for kl, c in by_kb[kb]:
            if c.id in seen:
                continue
            seen.add(c.id)
            dims = ",".join(c.dimensions) if c.dimensions else "—"
            lines.append(f"- `{c.id}` (Kl {c.klasse}) [dims {dims}]: {c.text.strip()}")
    field = '"kompetenzbereich": "<KB-Name>",' if anchor == "kb" else '"scope_label": "<Thema>",'
    return "\n".join(lines), field


def _ab_block(subject: str) -> str:
    items = []
    for kl in _klassen(subject):
        ab = ls.anwendungsbereiche_for(subject, kl)
        if ab:
            items.append(f"- Kl {kl}: " + " · ".join(ab[:8]))
    if not items:
        return ""
    return "\n## Anwendungsbereiche (Themen-Ideen für die Kernfragen)\n" + "\n".join(items) + "\n"


def build():
    outdir = RUNS_DIR / "ingest"
    (outdir / "gen").mkdir(parents=True, exist_ok=True)
    manifest = []
    for code, subject, anchor, practical in SUBJECTS:
        model = ls.get_subject_model(subject)
        comps_text, anchor_field = _competence_block(subject, anchor)
        dims = "\n".join(f"- `{d.id}` — {d.label}" for d in model.dimensions)
        kinds = ", ".join(sorted(CORE_TASK_KINDS | set(model.task_kind_extensions)))
        modality_note = (
            "Praktisches Fach: nutze `modality` \"enactive\" (Tun/Üben) oder \"oral\" (mündlich) wo "
            "passend, sonst \"printable\". Beschreibe Tätigkeiten in Worten."
            if practical else "Reiner Text (modality \"printable\")."
        )
        prompt = _TEMPLATE.format(
            subject=subject, n=N_KERNFRAGEN, competences=comps_text, dims=dims, kinds=kinds,
            ab_block=_ab_block(subject), anchor_rule=(_ANCHOR_KB if anchor == "kb" else _ANCHOR_GRADE),
            modality_note=modality_note, code=code, anchor_field=anchor_field,
            dim0=model.dimensions[0].id,
        )
        (outdir / f"prompt_{code}.md").write_text(prompt, encoding="utf-8")
        manifest.append({"code": code, "subject": subject, "anchor": anchor, "practical": practical})
        n_comp = len({c.id for kl in _klassen(subject) for c in ls.competences_for(subject, kl)})
        print(f"{code}: {n_comp} competences, anchor={anchor} -> prompt_{code}.md")
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                          encoding="utf-8")


if __name__ == "__main__":
    build()
