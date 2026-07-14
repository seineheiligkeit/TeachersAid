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
from teachersaid.grounding import data_store as ds
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.pipeline.assets import GENERATION_RECIPES
from teachersaid.schema.enums import CORE_TASK_KINDS

N_KERNFRAGEN = 2

# Stage of this run (Oberstufe breadth push, 28 Jun 2026). competences_for / get_subject_model /
# anwendungsbereiche_for are stage-aware; the Klasse range follows the stage.
STUFE = "Oberstufe"
KLASSEN = (5, 6, 7, 8) if STUFE == "Oberstufe" else (1, 2, 3, 4)

# code, subject, anchor ("kb" content/skill-KBs | "grade" strand/None-KB), practical, target_language
# Oberstufe breadth set — the strong/partial-tier subjects (Sport out; Musik/Kunst marginal → skipped).
SUBJECTS = [
    ("MAT", "Mathematik", "kb", False, None),
    ("PHY", "Physik", "kb", False, None),
    ("CHE", "Chemie", "kb", False, None),
    ("BIO", "Biologie und Umweltbildung", "kb", False, None),
    ("DEU", "Deutsch", "kb", False, None),
    ("GWB", "Geographie und wirtschaftliche Bildung", "kb", False, None),
    ("GPB", "Geschichte und politische Bildung", "kb", False, None),
    ("ETH", "Ethik", "kb", False, None),
    ("LAT", "Latein", "kb", False, "Latein"),
    ("GRI", "Griechisch", "kb", False, "Griechisch"),
    ("FSP", "Lebende Fremdsprache", "kb", False, "Englisch"),
    ("INF", "Informatik", "kb", False, None),
    ("HOE", "Haushaltsökonomie und Ernährung", "kb", False, None),
    ("PUP", "Psychologie und Philosophie", "kb", False, None),
]
GEN_SUBDIR = "gen_os_2"  # 2nd Oberstufe breadth pass (fresh dir; the 1st is in gen_os/, ingested)

# Prior batches (done 2026-06-25), kept for reproducibility:
#   MINT (single-Kernfrage tool earlier): PHY, CHE, BIO, MAT
#   German (anchor/practical): DEU·kb, GWB·kb, GPB·grade, DGB·kb, GEZ·kb,
#                              MUS·kb·practical, KUG·kb·practical, TED·kb·practical, BUS·kb·practical
#   Language: FS1·Englisch, FS2·Französisch, LAT·Latein (gen_lang/)

_TEMPLATE = """# Breiten-Generierung: {subject} — {n} Kernfragen

Du erzeugst **{n} verschiedene** Arbeitsblatt-Inhalte (je eine eigene **Kernfrage**) für die
**AHS-{stufe_label}** auf österreichischem Lehrplan-Niveau. Sprache: **Deutsch**, AHS-Niveau (anspruchsvoll, Sek II).
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
- **Abbildungen — Code-generiert, korrekt by construction** (nie freie Bilder/Diffusion): wo eine
  Abbildung die Aufgabe wirklich verbessert (v.a. Mathematik, Physik, Daten), fordere eine an und
  referenziere sie aus einer Aufgabe/Info über `asset_refs`. Reiner Text bleibt völlig ok, wenn keine
  Abbildung nötig ist.
  **Für DATEN: deklariere die ABSICHT, nicht den Diagrammtyp** — lege die Figur in `body.data_figures`;
  das System wählt daraus die passende, lesbare Darstellung (so wird nicht alles ein Balkendiagramm).
  Form: `{{"id":str,"intent":str,"title"?,"xlabel"?,"ylabel"?,"categories"?:[str],"values"?:[num],"points"?:[[x,y]],"log"?:bool,"fit"?:bool,"data_source"?:{{"dataset_id":str,"series":str}}}}`
  mit `intent` ∈
    - `trend` — Verlauf/Entwicklung (oft über die Zeit): `categories`+`values` → Liniendiagramm
    - `comparison` — MENGEN-Vergleich zwischen Kategorien: `categories`+`values` → Balkendiagramm
    - `relationship` — Zusammenhang zweier numerischer Größen: `points` (+`fit` für Trendgerade) → Streudiagramm
    - `distribution` — Häufigkeit/Streuung einer Größe: `values` → Histogramm
    - `scale` — Position auf einer Skala (z. B. pH-Wert): `categories`+`values` → Zahlenstrahl
    - `demographic` — Alter × Geschlecht: `categories` (Altersgruppen)+`male`+`female` → Bevölkerungspyramide
{data_block}  **Wähle nie selbst „Balken" für eine Zeitreihe, eine Ja/Nein-Klassifikation oder eine Skala** —
  dafür ist der `intent` da; korrekte Zahlen allein genügen NICHT, die Darstellung muss zur Aussage passen.
  **Für STRUKTUR-Abbildungen** (Funktionsgraph, Formel, fertiger Zahlenstrahl) nutze `body.assets` mit
  explizitem Generator — **erlaubte Generatoren (nur diese):**
{recipes}
  **Wichtig — eine Abbildung darf die gesuchte Lösung NICHT verraten:** z. B. KEINE Funktionsgleichung
  als Diagramm-`title`, wenn die Aufgabe ist, sie abzulesen; keine Werte/Beschriftungen anzeigen, die die
  Schüler:innen erst ablesen/bestimmen sollen. Die Abbildung zeigt das Material, nicht die Antwort.
  Keine freien Bilder/Diffusion, kein `data_interpretation`-Payload,
  keine `response.mode` ∈ {{diagram, drawing, artifact}}. {modality_note}
- **Schülertext ist für Schüler:innen** — niemals Kompetenz-IDs/Dimensionen/„Lehrplan" im `prompt`/Intro.
- Pro Aufgabe `answer_key` + `watch_outs`; optional `acceptable_reasoning` und `rubric`
  (Liste von `{{"criterion":"...","levels":["...","..."]}}`, **englische Schlüssel**).
- Pro Section die Lehrkraft-Ebene: `throughline` (Roter Faden), `talking_points` (2–4), `extensions` (1–3).
{lang_clause}
## Antwort-Formen (`response`): `{{"mode":"lines","n":<int>}}` · `{{"mode":"box","min_height_mm":<float>}}` ·
`{{"mode":"table","columns":[...],"rows":<int>}}` · `{{"mode":"choices","options":[...],"select":"one"|"many"}}` · `{{"mode":"none"}}`
## Payload (`payload`, optional, sonst null): multiple_choice `{{"kind":"multiple_choice","options":[...],"select":"one"}}` ·
true_false_justify `{{"kind":"true_false_justify","statements":[...]}}` · ordering `{{"kind":"ordering","items":[...]}}` ·
matching `{{"kind":"matching","left":[...],"right":[...]}}` · decision_scenario `{{"kind":"decision_scenario","stem":"..."}}`

## Ausgabe
Schreibe **{n} Dateien**, eine pro Kernfrage, nach `runs/ingest/{gendir}/{code}_1.json` … `runs/ingest/{gendir}/{code}_{n}.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{{
  "subject": "{subject}", "klasse": <{klasse_hint}, eine Klasse mit Kompetenzen im gewählten Bereich>,
  {anchor_field}
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {{
    "intro": [],
    "data_figures": [ /* bevorzugt für Daten: {{"id":"abb1","intent":"trend","title":"...","xlabel":"Jahr","ylabel":"%","categories":["1990","2010","2024"],"values":[29,43,57]}} */ ],
    "assets": [ /* nur Struktur-Figuren: {{"id":"abb2","role":"figure","generator":"matplotlib:function_graph","spec":{{"m":2,"b":1}}}} */ ],
    "sections": [ {{ "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {{"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{{"mode":"lines","n":3}},"cognitive_level":"understand","dimensions":["{dim0}"],
        "serves":[{{"competence_id":"<ID>","relation":"exercises"}}],"est_minutes":7,"asset_refs":[],
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
    return [k for k in KLASSEN if ls.competences_for(subject, k, STUFE)]


def _competence_block(subject: str, anchor: str) -> tuple[str, str]:
    """Returns (competences_grouped_text, anchor_field_template)."""
    klassen = _klassen(subject)
    by_kb: dict[str, list] = defaultdict(list)
    for kl in klassen:
        for c in ls.competences_for(subject, kl, STUFE):
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
        ab = ls.anwendungsbereiche_for(subject, kl, STUFE)
        if ab:
            items.append(f"- Kl {kl}: " + " · ".join(ab[:8]))
    if not items:
        return ""
    return "\n## Anwendungsbereiche (Themen-Ideen für die Kernfragen)\n" + "\n".join(items) + "\n"


def build():
    outdir = RUNS_DIR / "ingest"
    (outdir / GEN_SUBDIR).mkdir(parents=True, exist_ok=True)
    recipes = "\n".join(f"  - `{gid}` — {hint}" for gid, hint in GENERATION_RECIPES.items())
    manifest = []
    for code, subject, anchor, practical, target_language in SUBJECTS:
        model = ls.get_subject_model(subject, STUFE)
        comps_text, anchor_field = _competence_block(subject, anchor)
        dims = "\n".join(f"- `{d.id}` — {d.label}" for d in model.dimensions)
        kinds = ", ".join(sorted(CORE_TASK_KINDS | set(model.task_kind_extensions)))
        lang_clause = ""
        if target_language:
            modality_note = (f"Sprech-/Hör-Aufgaben dürfen `modality` \"oral\" sein, schriftliche "
                             f"\"printable\". Beschreibe alles in Worten (keine Audiodateien).")
            lang_clause = (
                f"\n## Sprache (WICHTIG)\nDas **Sprachmaterial** (Texte, Dialoge, Wortschatz, "
                f"Beispielsätze, die die Schüler:innen bearbeiten) ist in **{target_language}**. "
                f"Arbeitsanweisungen dürfen Deutsch oder {target_language} sein (Unterstufe: oft Deutsch "
                f"als Gerüst, später mehr {target_language}). Die **Lehrkraft-Ebene** "
                f"(throughline/talking_points/extensions) und `watch_outs` bleiben **Deutsch**. "
                f"`answer_key` in {target_language} (Modelllösung), bei Bedarf mit kurzer deutscher Notiz.\n")
        elif practical:
            modality_note = ("Praktisches Fach: nutze `modality` \"enactive\" (Tun/Üben) oder \"oral\" "
                             "wo passend, sonst \"printable\". Beschreibe Tätigkeiten in Worten.")
        else:
            modality_note = "Reiner Text (modality \"printable\")."
        data_brief = ds.format_available_datasets(ds.relevant_datasets(subject=code))
        data_block = ("\n" + data_brief + "\n") if data_brief else ""
        prompt = _TEMPLATE.format(
            subject=subject, n=N_KERNFRAGEN, competences=comps_text, dims=dims, kinds=kinds,
            ab_block=_ab_block(subject), anchor_rule=(_ANCHOR_KB if anchor == "kb" else _ANCHOR_GRADE),
            modality_note=modality_note, lang_clause=lang_clause, gendir=GEN_SUBDIR,
            code=code, anchor_field=anchor_field, dim0=model.dimensions[0].id, recipes=recipes,
            data_block=data_block, stufe_label=STUFE,
            klasse_hint=f"{KLASSEN[0]}-{KLASSEN[-1]}",
        )
        (outdir / f"prompt_{code}.md").write_text(prompt, encoding="utf-8")
        manifest.append({"code": code, "subject": subject, "anchor": anchor,
                         "target_language": target_language})
        n_comp = len({c.id for kl in _klassen(subject) for c in ls.competences_for(subject, kl, STUFE)})
        print(f"{code}: {n_comp} competences, {target_language or 'Deutsch'} -> prompt_{code}.md")
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                          encoding="utf-8")


if __name__ == "__main__":
    build()
