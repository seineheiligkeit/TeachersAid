"""Build fully-grounded breadth-generation briefs from the catalog (one per subject).

Each `runs/ingest/prompt_<CODE>.md` is a self-contained brief: a subagent reads it,
picks N distinct Kernfragen spanning the subject's themes, and writes one wrapper JSON
per Kernfrage to `runs/ingest/<gen-dir>/<CODE>_<n>.json`. The deterministic grounding
(verbatim competences grouped by Kompetenzbereich + grade, allowed dims/kinds, the JSON
shape) lives here so agents can't invent it, plus a **Korpus-Kontext** section — the
worksheets already in the review store for that (subject, stufe), so agents pick NEW
angles rather than duplicate. Run in the venv:

    python tools/breadth_prompt.py --stufe Unterstufe                 # all US subjects, 2 each
    python tools/breadth_prompt.py --stufe Oberstufe --subjects MAT,PHY --n 3 --gen-dir gen_os_3

A pass should always write to a FRESH --gen-dir: review items are created, not upserted,
so re-ingesting an old dir would duplicate. See Documents/content-campaign-workflow.md.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import data_store as ds
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.pipeline.assets import GENERATION_RECIPES
from teachersaid.schema.enums import CORE_TASK_KINDS

DEFAULT_N = 2  # Kernfragen (worksheets) per subject

# Per-stufe subject registry: (code, subject-name, anchor, practical, target_language).
#   anchor "kb"    — the worksheet targets ONE content/skill Kompetenzbereich (-> kompetenzbereich)
#          "grade" — strand/process competences, topic supplied by content (-> scope_label)
#   Derived once from each subject's KB structure (>=2 KBs -> kb); every current AHS
#   Pflichtgegenstand is kb-anchored. practical -> enactive/oral modality allowed;
#   target_language -> the language the *material* is written in (teacher layer stays German).
SUBJECT_SETS: dict[str, list[tuple]] = {
    "Oberstufe": [
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
    ],
    "Unterstufe": [
        ("MAT", "Mathematik", "kb", False, None),
        ("PHY", "Physik", "kb", False, None),
        ("CHE", "Chemie", "kb", False, None),
        ("BIO", "Biologie und Umweltbildung", "kb", False, None),
        ("DEU", "Deutsch", "kb", False, None),
        ("GWB", "Geographie und wirtschaftliche Bildung", "kb", False, None),
        ("GPB", "Geschichte und politische Bildung", "kb", False, None),
        ("DGB", "Digitale Grundbildung", "kb", False, None),
        ("GEZ", "Geometrisches Zeichnen", "kb", False, None),
        ("FS1", "Erste lebende Fremdsprache", "kb", False, "Englisch"),
        ("FS2", "Zweite lebende Fremdsprache", "kb", False, "Französisch"),
        ("LAT", "Latein", "kb", False, "Latein"),
        ("MUS", "Musik", "kb", True, None),
        ("KUG", "Kunst und Gestaltung", "kb", True, None),
        ("TED", "Technik und Design", "kb", True, None),
        ("BUS", "Bewegung und Sport", "kb", True, None),
    ],
}

# Prior manual batches (kept for reproducibility):
#   Unterstufe gen/ (2026-06-25): MINT PHY/CHE/BIO/MAT · German DEU/GWB/GPB/DGB/GEZ +
#     practical MUS/KUG/TED/BUS · Language FS1/FS2/LAT (gen_lang/)
#   Oberstufe gen_os/ (2026-06-28), gen_os_2/ (2026-07-14): the 14 academic subjects above

# Age/level framing per stufe (the target_language subjects override the *material* language
# via the Sprache clause; this is the German register + Schulstufe).
_NIVEAU = {
    "Oberstufe": "Sprache: **Deutsch**, AHS-Niveau (anspruchsvoll, Sek II).",
    "Unterstufe": ("Sprache: **Deutsch**, altersgerecht für die Unterstufe (Sek I, ~10-14 J.) — "
                   "klar und konkret, aber nie trivial (der Blackboard-Test gilt trotzdem)."),
}

_TEMPLATE = """# Breiten-Generierung: {subject} — {n} Kernfragen

Du erzeugst **{n} verschiedene** Arbeitsblatt-Inhalte (je eine eigene **Kernfrage**) für die
**AHS-{stufe_label}** auf österreichischem Lehrplan-Niveau. {niveau_note}
Wähle **{n} klar unterschiedliche Themen/Bereiche** (Breite!), nicht Varianten desselben Themas.

{korpus_kontext}
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


def _klassen(subject: str, stufe: str, klassen: tuple[int, ...]) -> list[int]:
    """Grades that actually carry competences (robust to None-KB competences, which
    grade_map drops)."""
    return [k for k in klassen if ls.competences_for(subject, k, stufe)]


def _competence_block(subject: str, anchor: str, stufe: str,
                      klassen: tuple[int, ...]) -> tuple[str, str]:
    """Returns (competences_grouped_text, anchor_field_template)."""
    by_kb: dict[str, list] = defaultdict(list)
    for kl in _klassen(subject, stufe, klassen):
        for c in ls.competences_for(subject, kl, stufe):
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


def _ab_block(subject: str, stufe: str, klassen: tuple[int, ...]) -> str:
    items = []
    for kl in _klassen(subject, stufe, klassen):
        ab = ls.anwendungsbereiche_for(subject, kl, stufe)
        if ab:
            items.append(f"- Kl {kl}: " + " · ".join(ab[:8]))
    if not items:
        return ""
    return "\n## Anwendungsbereiche (Themen-Ideen für die Kernfragen)\n" + "\n".join(items) + "\n"


def _korpus_kontext(subject: str, stufe: str, n: int, cov_subject: dict | None,
                    existing: list[tuple]) -> str:
    """The 'was es schon gibt' section: the worksheets already in the review store for this
    (subject, stufe) so the agent picks NEW angles, plus a one-line coverage summary.
    `existing` is a list of (klasse, title, kernfrage)."""
    if existing:
        rows = "\n".join(f"- [Kl {kl}] {title} — {kf}" for kl, title, kf in sorted(existing))
        head = (f"Für **{subject}** ({stufe}) gibt es im Korpus schon **{len(existing)}** "
                f"Arbeitsblätter. Wähle {n} **neue** Kernfragen, die sich davon klar unterscheiden "
                f"(keine Dubletten, keine bloßen Varianten):")
    else:
        rows = "- (noch keine)"
        head = (f"Für **{subject}** ({stufe}) gibt es im Korpus noch **keine** Arbeitsblätter — "
                f"freie Themenwahl über die Breite des Fachs.")
    cov = ""
    if cov_subject:
        cov = (f"\n\n_Abdeckung (Kompetenzbereich-Zellen): {cov_subject['gruen']} grün · "
               f"{cov_subject['teil']} teilweise · {cov_subject['leer']} leer "
               f"von {cov_subject['cells_total']}._")
    return f"## Korpus-Kontext — was es schon gibt\n{head}\n{rows}{cov}\n"


def build(stufe: str, subjects: list[tuple], n: int, gen_subdir: str, *, review_store=None):
    """Write one grounded brief per subject to runs/ingest/prompt_<CODE>.md + a manifest."""
    from teachersaid import stats
    from teachersaid.store.repository import ReviewStore

    store = review_store if review_store is not None else ReviewStore()
    klassen = (1, 2, 3, 4) if stufe == "Unterstufe" else (5, 6, 7, 8)
    outdir = RUNS_DIR / "ingest"
    (outdir / gen_subdir).mkdir(parents=True, exist_ok=True)
    recipes = "\n".join(f"  - `{gid}` — {hint}" for gid, hint in GENERATION_RECIPES.items())

    # what the corpus already has, per subject-code, for the Korpus-Kontext dedup section
    existing_by_code: dict[str, list[tuple]] = defaultdict(list)
    for it in store.list():
        c = getattr(it, "content", None)
        if c is None or str(c.meta.stufe) != stufe:
            continue
        ccode = ls._code_for(c.meta.subject, stufe)
        if ccode:
            existing_by_code[ccode].append(
                (c.meta.klasse, (c.meta.title or "").strip(), (c.meta.kernfrage or "").strip()))
    cov_by_code = {s["code"]: s for s in stats.coverage_map()["subjects"] if s["stufe"] == stufe}

    manifest = []
    for code, subject, anchor, practical, target_language in subjects:
        model = ls.get_subject_model(subject, stufe)
        comps_text, anchor_field = _competence_block(subject, anchor, stufe, klassen)
        dims = "\n".join(f"- `{d.id}` — {d.label}" for d in model.dimensions)
        kinds = ", ".join(sorted(CORE_TASK_KINDS | set(model.task_kind_extensions)))
        lang_clause = ""
        if target_language:
            modality_note = ("Sprech-/Hör-Aufgaben dürfen `modality` \"oral\" sein, schriftliche "
                             "\"printable\". Beschreibe alles in Worten (keine Audiodateien).")
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
        korpus = _korpus_kontext(subject, stufe, n, cov_by_code.get(code),
                                 existing_by_code.get(code, []))
        prompt = _TEMPLATE.format(
            subject=subject, n=n, competences=comps_text, dims=dims, kinds=kinds,
            ab_block=_ab_block(subject, stufe, klassen),
            anchor_rule=(_ANCHOR_KB if anchor == "kb" else _ANCHOR_GRADE),
            modality_note=modality_note, lang_clause=lang_clause, gendir=gen_subdir,
            code=code, anchor_field=anchor_field, dim0=model.dimensions[0].id, recipes=recipes,
            data_block=data_block, stufe_label=stufe, niveau_note=_NIVEAU[stufe],
            korpus_kontext=korpus, klasse_hint=f"{klassen[0]}-{klassen[-1]}",
        )
        (outdir / f"prompt_{code}.md").write_text(prompt, encoding="utf-8")
        n_existing = len(existing_by_code.get(code, []))
        manifest.append({"code": code, "subject": subject, "anchor": anchor, "stufe": stufe,
                         "target_language": target_language, "gen_dir": gen_subdir, "n": n,
                         "existing": n_existing})
        n_comp = len({c.id for kl in _klassen(subject, stufe, klassen)
                      for c in ls.competences_for(subject, kl, stufe)})
        print(f"{code}: {n_comp} competences, {n_existing} existing, "
              f"{target_language or 'Deutsch'} -> prompt_{code}.md")
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    print(f"\n== {len(manifest)} briefs for {stufe} -> runs/ingest/prompt_*.md "
          f"(agents write {n} files each to runs/ingest/{gen_subdir}/) ==")


def main():
    ap = argparse.ArgumentParser(description="Build breadth-generation briefs (one per subject).")
    ap.add_argument("--stufe", choices=sorted(SUBJECT_SETS), default="Oberstufe")
    ap.add_argument("--subjects", help="comma-separated codes (default: all for the stufe)")
    ap.add_argument("--n", type=int, default=DEFAULT_N, help="Kernfragen per subject")
    ap.add_argument("--gen-dir", help="output subdir under runs/ingest/ (default: gen_<abbr>)")
    args = ap.parse_args()
    registry = SUBJECT_SETS[args.stufe]
    if args.subjects:
        want = {s.strip().upper() for s in args.subjects.split(",") if s.strip()}
        registry = [r for r in registry if r[0] in want]
        missing = want - {r[0] for r in registry}
        if missing:
            ap.error(f"unknown codes for {args.stufe}: {', '.join(sorted(missing))}")
    gen_dir = args.gen_dir or ("gen_us" if args.stufe == "Unterstufe" else "gen_os")
    build(args.stufe, registry, args.n, gen_dir)


if __name__ == "__main__":
    main()
