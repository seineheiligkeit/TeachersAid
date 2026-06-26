"""Build fully-grounded Lernarrangement-generation briefs (one per subject).

The v0.5 analogue of `breadth_prompt.py`. Each `runs/ingest/arr/prompt_<CODE>.md` is a
self-contained brief: a subagent reads it, designs ONE arrangement (a debate / Planspiel
/ jigsaw / mystery / stations) for a chosen grade + theme, and writes one wrapper JSON to
`runs/ingest/gen_arr/<CODE>.json`. Grounding (verbatim competences grouped by KB+grade,
allowed dims/kinds, the JSON shape) lives here so agents can't invent it. Run with the venv:

    python tools/arrangement_prompt.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.schema.enums import CORE_TASK_KINDS

GEN_SUBDIR = "gen_arr"

# code, subject, suggested format, target_language — subjects whose oral/social/enactive
# competences a worksheet can't reach, so an arrangement genuinely extends coverage.
SUBJECTS = [
    ("GPB", "Geschichte und politische Bildung", "role_debate", None),
    ("DEU", "Deutsch", "role_debate", None),
    ("GWB", "Geographie und wirtschaftliche Bildung", "jigsaw", None),
    ("FS1", "Englisch", "simulation_game", "Englisch"),
]

_TEMPLATE = """# Lernarrangement-Generierung: {subject}

Entwirf **ein** Lernarrangement für die **AHS-Unterstufe** (österreichischer Lehrplan). Ein
Lernarrangement ist eine Gruppen-/Interaktionsform (Rollendebatte, Planspiel, Gruppenpuzzle,
Mystery, Stationen), die **mehrere Arbeitsblätter enthält** — eines pro Rolle. Der Sinn: es
erreicht **mündliche/soziale/handelnde** Kompetenzen, die ein einzelnes Arbeitsblatt NICHT
erreichen kann (über die Interaktion, den Debrief, das gemeinsame Produkt).
**Vorgeschlagenes Format:** `{fmt}` (du darfst ein anderes aus der Liste wählen, wenn es besser passt:
role_debate · simulation_game · jigsaw · mystery · stations). Sprache der Anweisungen: **Deutsch**.

## Kompetenzen (verbatim — JEDE `competence_id` MUSS eine dieser IDs sein), gruppiert nach Klasse + Kompetenzbereich
{competences}

## Erlaubte Dimensionen (`dimensions` / Anker-`dimension` — Teilmenge dieser Codes)
{dims}

## Erlaubte Aufgaben-`kind`-Werte (für die Rollen-Arbeitsblätter)
{kinds}
{ab_block}
## Aufbau & Regeln
- Wähle **eine Klasse** und **ein Thema**, das sich für Interaktion eignet (Konflikt, Entscheidung,
  Mehrperspektivität). Alle IDs müssen zu Kompetenzen DIESER Klasse gehören.
- **3–4 Rollen.** Jede Rolle hat ein eigenes Arbeitsblatt (`material`) = ein echtes Arbeitsblatt mit
  1–2 Aufgaben (role "task"), die die Rolle auf die Interaktion vorbereiten (Orientierung/Urteil auf
  Papier). Jede Aufgabe `serves` eine echte Kompetenz-ID; `dimensions` ⊆ erlaubte Codes; `kind` ∈ erlaubte
  kinds; realistische `est_minutes`; `answer_key` + `watch_outs`.
- **`competence_anchors` (das Herzstück, 1–3):** die Kompetenzen, die durch das **Arrangement selbst**
  erreicht werden — über `served_by` ∈ `interaction` (Debatte/Aushandlung) · `debrief` (Reflexion) ·
  `shared_product` (gemeinsames Ergebnis). Diese sollen die **mündlich/sozial/handelnden** Kompetenzen
  sein (oft Urteils-/Handlungskompetenz), die **kein** Rollen-Arbeitsblatt allein abdeckt — wähle dafür
  möglichst IDs, die NICHT schon von einer Rollenaufgabe `serves` werden. Jede mit `dimension` (ein Code).
- **`phases`:** 4–6 Phasen mit `grouping` ∈ `individual` · `role_group` · `home_group` · `plenary`,
  realistischen `minutes` (Summe ~50–100 min = Doppelstunde/Block) und `what_happens` (1 Satz, Lehrkraft-Sicht).
- **`common_material`:** 1–3 Info-Blöcke (role "info", kind "prose"/"key_fact"/"procedure") = der Fall +
  Spielregeln, die ALLE Rollen bekommen. **`debrief`:** 1–2 Info-Blöcke = die Reflexionsfragen (aus den
  Rollen heraustreten). Beides nur Info-Blöcke (keine "task").
- **`shared_product`:** das gemeinsame Ergebnis (`description`) + eine `rubric`
  (Liste `{{"criterion":"...","levels":["niedrig","...","hoch"]}}`, englische Schlüssel).
- **Korrektheit by construction**; Fehlvorstellungen in `watch_outs`. **Kein** Bild/Diffusion, keine
  `data_interpretation`-Payload, keine `response.mode` ∈ {{diagram, drawing, artifact}} (reiner Text).
- **Schülertext ist für Schüler:innen** — niemals Kompetenz-IDs/„Lehrplan" im `prompt`/Intro/`what_happens`.
- **Scope-Grenze:** wir erzeugen das Material + eine Lehrkraft-Anleitung. Wir steuern NICHT den Raum
  (keine Live-Gruppierung/Zeitnahme/Schüler-Tracking) — `what_happens` beschreibt, was passiert, knapp.
{lang_clause}
## Ausgabe
Schreibe **eine** Datei nach `runs/ingest/{gendir}/{code}.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune):

```json
{{
  "subject": "{subject}", "klasse": <1-4>, "format": "{fmt}",
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {{
    "common_material": [ {{"role":"info","id":"case","kind":"prose","content":"Der Fall + Spielregeln ..."}} ],
    "roles": [
      {{ "id":"r1","label":"<Rollenname>","material": {{
          "intro": [ {{"role":"info","id":"r1i","kind":"prose","content":"Deine Rolle ..."}} ],
          "assets": [],
          "sections": [ {{ "id":"r1s","title":"Rollenarbeit","throughline":"...","talking_points":["..."],"extensions":["..."],
            "blocks": [ {{"role":"task","id":"r1t1","kind":"open_response","prompt":"...","payload":null,
              "response":{{"mode":"lines","n":3}},"cognitive_level":"understand","dimensions":["{dim0}"],
              "serves":[{{"competence_id":"<ID>","relation":"exercises"}}],"est_minutes":7,"asset_refs":[],
              "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]}} ] }} ] }} }}
      /* … 3–4 Rollen … */
    ],
    "phases": [ {{"id":"p1","label":"Fall & Regeln","grouping":"plenary","minutes":10,"what_happens":"..."}} ],
    "shared_product": {{ "description":"...","rubric":[{{"criterion":"...","levels":["...","..."]}}] }},
    "debrief": [ {{"role":"info","id":"db","kind":"prose","content":"Reflexion: ..."}} ],
    "competence_anchors": [ {{"competence_id":"<ID>","dimension":"<dim>","served_by":"interaction"}} ]
  }}
}}
```
"""


def _klassen(subject: str) -> list[int]:
    return [k for k in (1, 2, 3, 4) if ls.competences_for(subject, k)]


def _competence_block(subject: str) -> str:
    by_grade_kb: dict[int, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for kl in _klassen(subject):
        for c in ls.competences_for(subject, kl):
            by_grade_kb[kl][c.kompetenzbereich].append(c)
    lines = []
    for kl in sorted(by_grade_kb):
        lines.append(f"\n### Klasse {kl}")
        for kb in sorted(by_grade_kb[kl], key=lambda x: x or ""):
            lines.append(f"**{kb}**")
            seen = set()
            for c in by_grade_kb[kl][kb]:
                if c.id in seen:
                    continue
                seen.add(c.id)
                dims = ",".join(c.dimensions) if c.dimensions else "—"
                lines.append(f"- `{c.id}` [dims {dims}]: {c.text.strip()}")
    return "\n".join(lines)


def _ab_block(subject: str) -> str:
    items = []
    for kl in _klassen(subject):
        ab = ls.anwendungsbereiche_for(subject, kl)
        if ab:
            items.append(f"- Kl {kl}: " + " · ".join(ab[:8]))
    return ("\n## Anwendungsbereiche (Themen-Ideen)\n" + "\n".join(items) + "\n") if items else ""


def build():
    outdir = RUNS_DIR / "ingest"
    (outdir / GEN_SUBDIR).mkdir(parents=True, exist_ok=True)
    manifest = []
    for code, subject, fmt, target_language in SUBJECTS:
        model = ls.get_subject_model(subject)
        if model is None:
            print(f"{code}: SKIP — no subject model for {subject!r}")
            continue
        dims = "\n".join(f"- `{d.id}` — {d.label}" for d in model.dimensions)
        kinds = ", ".join(sorted(CORE_TASK_KINDS | set(model.task_kind_extensions)))
        lang_clause = ""
        if target_language:
            lang_clause = (
                f"\n## Sprache (WICHTIG)\nDas **Sprachmaterial** der Rollen (Dialoge, Wortschatz, "
                f"Sätze, die die Schüler:innen sprechen/bearbeiten) ist in **{target_language}**; "
                f"Anweisungen dürfen Deutsch sein. Die Lehrkraft-Ebene (throughline/talking_points/"
                f"extensions), `watch_outs` und `what_happens` bleiben **Deutsch**. Sprech-Aufgaben "
                f"dürfen `modality` \"oral\" sein.\n")
        prompt = _TEMPLATE.format(
            subject=subject, fmt=fmt, competences=_competence_block(subject), dims=dims,
            kinds=kinds, ab_block=_ab_block(subject), lang_clause=lang_clause,
            gendir=GEN_SUBDIR, code=code, dim0=model.dimensions[0].id,
        )
        (outdir / f"prompt_arr_{code}.md").write_text(prompt, encoding="utf-8")
        manifest.append({"code": code, "subject": subject, "format": fmt,
                         "target_language": target_language})
        n = len({c.id for kl in _klassen(subject) for c in ls.competences_for(subject, kl)})
        print(f"{code}: {n} competences ({target_language or 'Deutsch'}) -> prompt_arr_{code}.md")
    (outdir / "arr_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    build()
