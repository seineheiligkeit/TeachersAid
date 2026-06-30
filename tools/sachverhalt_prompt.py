"""Build fully-grounded Sachverhalt-authoring briefs from the catalog (one per topic).

The content-layer twin of `tools/breadth_prompt.py`. Where the breadth brief asks a
subagent for a *worksheet of tasks*, this one asks for a `Sachverhalt` — a curated module
of structured, SOURCED facts (timeline / process / actors / causes / concepts) plus a
Darstellung authored *over that frozen fact-set*. The subagent never invents a worksheet:
`pipeline/sachverhalt.py` derives the three projections (learn-text + figures + computed
Sachkompetenz tasks) deterministically. So the brief's whole job is to ground the FACTS
(real competence ids, the fact-type the subject needs, the load-bearing rules) and pin the
JSON shape. Run with the venv:

    python tools/sachverhalt_prompt.py

Each `runs/ingest/sv_prompts/<id>.md` is self-contained: a subagent reads it and writes one
`runs/ingest/sv/<id>.json`, then `tools/ingest_sachverhalte.py --dry-run` validates it.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import lehrplan_store as ls


@dataclass
class Topic:
    """One assigned Sachverhalt: a content-rich, non-sensitive topic + the grade it anchors."""
    id: str                 # the file slug (sv-<id>.json) + the Sachverhalt id
    topic: str              # the display title
    klasse: int             # the anchor grade (must carry the subject's competences)
    leitfrage: str          # an orienting question (the curator's; the subagent may sharpen)
    note: str = ""          # a curator hint on scope/angle


@dataclass
class SubjectBrief:
    """A subject's grounding for the content layer: which competence strand is Sachkompetenz,
    which is the Urteils strand, the fact-type the subject's content wants, and its topics.

    `sach_dimension`/`urteil_dimension`/`urteil_competence` are LOAD-BEARING, not cosmetic:
    GPB.US.* and BIO.US.* competences resolve with EMPTY dimensions, so the derivation falls
    back to these hints (see `pipeline/sachverhalt.py`)."""
    code: str
    subject: str
    fact_type: str          # "timeline" (dated history) | "process" (undated cycle/sequence)
    sach_dimension: str     # the Sachkompetenz dimension code (e.g. GPB "HSA", BIO "W")
    urteil_dimension: str   # the judgment task's dimension (e.g. GPB "HOR", BIO "S")
    actor_label: str        # the structure_overview noun ("Akteure" | "Strukturen" | …)
    urteil_competence: str | None = None  # the id the Urteils-task serves (where ids encode strand)
    process_cyclic: bool = False           # a process that loops back (Kreislauf) vs a linear sequence
    topics: list[Topic] = field(default_factory=list)


# The Phase-3 proof batch — content-rich, well-documented, NON-sensitive topics across the two
# robust fact-types (timeline=History, process=Biology). Regions (Geography) need a sourced
# boundary set + a cited dataset, so they stay curated by hand (the Bundesländer flagship); this
# batch proves the breadth seam on the fact-types that need only sourced facts + a Darstellung.
SUBJECTS: list[SubjectBrief] = [
    SubjectBrief(
        code="GPB", subject="Geschichte und politische Bildung", fact_type="timeline",
        sach_dimension="HSA", urteil_dimension="HOR", actor_label="Akteure",
        topics=[
            Topic("franzoesische-revolution", "Die Französische Revolution", 3,
                  "Wie stürzt das Volk eine jahrhundertealte Ordnung — und was setzt es an ihre Stelle?",
                  "1789–1799. Klare Eckdaten (Bastille 1789, Erklärung der Menschen- und Bürgerrechte, "
                  "Hinrichtung Ludwigs XVI. 1793, Napoleon 1799). Ursache→Folge ist sehr reich."),
            Topic("industrialisierung", "Die Industrialisierung", 3,
                  "Wie verändert die Maschine Arbeit, Stadt und Gesellschaft?",
                  "Spätes 18./19. Jh. Dampfmaschine, Fabrik, Eisenbahn, Urbanisierung, soziale Frage. "
                  "Datier die echten Eckpunkte; vermeide erfundene Jahreszahlen."),
        ],
    ),
    SubjectBrief(
        code="BIO", subject="Biologie und Umweltbildung", fact_type="process",
        sach_dimension="W", urteil_dimension="S", urteil_competence="BIO.US.x.STA.02",
        actor_label="Strukturen", process_cyclic=False,
        topics=[
            Topic("photosynthese", "Die Photosynthese", 3,
                  "Wie macht eine Pflanze aus Licht, Wasser und Luft ihre Nahrung?",
                  "Linearer Prozess (Licht → Wasser+CO₂ → Traubenzucker+Sauerstoff). Begriffe: "
                  "Chlorophyll, Spaltöffnungen, Glucose. Kein Datum — die Schrittfolge IST die Ordnung."),
            Topic("verdauung", "Die Verdauung des Menschen", 2,
                  "Welchen Weg nimmt das Essen — und was passiert auf jeder Station?",
                  "Linearer Prozess (Mund → Speiseröhre → Magen → Dünndarm → Dickdarm). Begriffe: "
                  "Enzym, Nährstoff, Resorption. Die Stationen sind die Prozess-Schritte."),
        ],
    ),
]

SV_PROMPT_SUBDIR = "sv_prompts"
SV_SUBDIR = "sv"


_FACT_TYPE_BLOCK = {
    "timeline": """## Faktentyp: **Zeitleiste** (datierte Ereignisse)
Dieser Sachverhalt trägt eine `timeline` aus **5–7 echten, datierten Ereignissen** (Feld `at`:
eine Jahreszahl als Zahl, oder ein String wie „um 1500"). Sie treibt die Zeitleisten-Abbildung
**und** die Chronologie-Aufgabe (die Lösung = sortiert nach `at`, vom System berechnet).
**HARTE Regel (Entity-Lint):** *Jede* 3–4-stellige Jahreszahl, die in der `darstellung`-Prosa
vorkommt, MUSS als Ereignis in der `timeline` stehen. Erfinde keine Jahreszahl; nimm nur belegte.
`process`/`regions` bleiben leer.""",
    "process": """## Faktentyp: **Prozess / Ablauf** (ungeordnete Schritte → richtige Reihenfolge)
Dieser Sachverhalt trägt einen `process`: **5–7 Schritte in der RICHTIGEN Reihenfolge** (die
Listenreihenfolge IST die Lösung der Reihenfolge-Aufgabe — das System berechnet sie daraus).
Setze `process_name` (z. B. „Der Weg der Nahrung") und `process_cyclic` ({cyclic}). Jeder Schritt:
`{{"name":"...","text":"<eine erklärende Zeile>"}}`. Es gibt **kein Datum** — die Schrittfolge ist
die Ordnung. `timeline`/`regions` bleiben leer. (Vermeide trotzdem erfundene Jahreszahlen in der
Prosa — der Entity-Lint prüft jede 3–4-stellige Zahl gegen den Faktensatz.)""",
}


_TEMPLATE = """# Sachverhalt-Autorierung: „{topic}" ({subject}, {klasse}. Klasse)

Du schreibst **einen** `Sachverhalt` — ein kuratiertes Modul aus **strukturierten, BELEGTEN
Fakten** plus einer **Darstellung**, die du *über diesem festen Faktensatz* formulierst. Du
schreibst **kein** Arbeitsblatt: das System leitet daraus deterministisch drei Projektionen ab
(Lerntext + Abbildungen + berechnete Sachkompetenz-Aufgaben). Deine Aufgabe ist also: **die
Fakten sauber recherchieren und belegen**, und die Darstellung **nur aus ihnen** formulieren.

**Leitfrage (Vorschlag):** {leitfrage}
{note_block}
## Das tragende Prinzip — *Wähle die Fakten, formuliere den Ausdruck*
- **Fakten sind belegt, nicht erfunden.** Daten, Akteur:innen-Rollen, Ursache→Folge, Begriffe:
  recherchiert aus einer echten Quelle (Wikipedia ist ok) und in `sources` mit `role:"facts"`
  vermerkt. Die Lehrkraft prüft sie am Review-Gate — also keine ausgedachten „Fakten".
- **Die Darstellung ist eine Projektion über dem Faktensatz** — formuliere frei und didaktisch
  schön, aber führe **nichts** ein, was nicht im Faktensatz steht. Ein deterministischer
  *Entity-Lint* prüft das (jede Jahreszahl muss im Faktensatz vorkommen).
- **Mehrperspektivität / Wertung NUR in `urteilsfrage`** — niemals in der sachlichen Darstellung.

{fact_type_block}

## Kompetenzen ({subject}, {klasse}. Klasse — verbatim; `competences` MUSS aus diesen IDs wählen)
{competences}

### Dimensions-Hinweise (WICHTIG — diese Felder MUSST du setzen)
Die obigen Kompetenzen lösen mit **leeren** Dimensionen auf, darum trägt der Sachverhalt die
Dimension explizit:
- `"sach_dimension": "{sach_dimension}"` — die Sachkompetenz-Dimension (für Sach-Aufgaben).
- `"urteil_dimension": "{urteil_dimension}"` — die Dimension der Urteils-Aufgabe.{urteil_comp_line}
- `"actor_label": "{actor_label}"` — das Substantiv für die Struktur-Aufgabe.

## Pflicht-Inhalte (der Faktensatz)
- `sources`: **mindestens eine** `role:"facts"`-Quelle mit echtem Permalink (Wikipedia: nimm einen
  `oldid`-Permalink auf die konkrete Version), `licence:"CC-BY-SA-4.0"`, `retrieved:"2026-06-30"`.
- `actors` (3–6): Name + `role` (eine erklärende Zeile). Bei Bio/Prozess = **Strukturen/Bestandteile**.
- `causes` (4–6): `{{"cause":"...","effect":"...","kind":"<voraussetzung|ursache|verlauf|folge|wirkung>"}}`
  → die Wirkungsgefüge-Abbildung **und** die Ursache→Folge-Zuordnungsaufgabe (Lösung = die Paare).
- `concepts` (4–6): `{{"term":"...","definition":"..."}}` → die Begriff-Zuordnungsaufgabe (Lösung = die Paare).
- `bedeutung` (1–3 Sätze): Bedeutung/Nachwirkung. `gegenwartsbezug` (1–2 Sätze): der Gegenwartsbezug.
- `urteilsfrage`: **eine** abwägende Frage (pro/contra, eigenes Urteil) → die hochstufige Urteils-Aufgabe.
- `darstellung`: **3–5 Abschnitte** `{{"heading":"...","body":"<2–4 Sätze>","grounded_by":["<Fakt-Schlüssel>"]}}`.
  `grounded_by` listet die Fakt-Schlüssel (Ereignis-`label` / Begriff-`term` / Akteur-`name` / Schritt-`name`),
  auf denen der Absatz fußt. **Setze KEINE `provenance`** an den Abschnitten — die Ableitung hängt sie
  automatisch an (sonst doppelt).

## Schüler-Niveau
Darstellung und Begriffe auf **{klasse}. Klasse AHS** — klar, konkret, anschaulich, ohne Fachjargon-Überladung.
Niemals Kompetenz-IDs, Dimensionen oder das Wort „Lehrplan" im Schülertext.

## Ausgabe
Schreibe **genau eine** Datei nach `runs/ingest/{sv_subdir}/{id}.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune), exakt in dieser Form:

```json
{example}
```
"""


def _competence_block(subject: str, klasse: int) -> str:
    by_kb: dict[str, list] = defaultdict(list)
    for c in ls.competences_for(subject, klasse):
        by_kb[c.kompetenzbereich or "—"].append(c)
    lines = []
    for kb in sorted(by_kb, key=lambda x: x or ""):
        lines.append(f"\n### {kb}")
        for c in by_kb[kb]:
            dims = ",".join(c.dimensions) if c.dimensions else "—"
            lines.append(f"- `{c.id}` [dims {dims}]: {c.text.strip()}")
    return "\n".join(lines)


def _example(b: SubjectBrief, t: Topic) -> str:
    """A fully-shaped worked example for this topic's fact-type (so the agent copies the shape,
    not invents it). Facts are placeholders — the agent researches the real ones."""
    common = {
        "id": f"sv-{t.id}",
        "subject": b.subject,
        "klasse_range": [t.klasse, t.klasse],
        "topic": t.topic,
        "leitfrage": t.leitfrage,
        "competences": ["<ID aus der Liste>", "<weitere ID>"],
        "keywords": ["<Schlagwort>", "<Schlagwort>"],
        "sources": [{
            "title": f"{t.topic}", "url": "https://de.wikipedia.org/w/index.php?title=…&oldid=…",
            "publisher": "Wikipedia (de)", "licence": "CC-BY-SA-4.0",
            "licence_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "retrieved": "2026-06-30", "role": "facts",
        }],
        "actors": [{"name": "<Name/Struktur>", "role": "<eine erklärende Zeile>"}],
        "causes": [
            {"cause": "<Ursache>", "effect": "<Folge>", "kind": "ursache"},
            {"cause": "<…>", "effect": "<…>", "kind": "folge"},
        ],
        "concepts": [{"term": "<Begriff>", "definition": "<kindgerechte Definition>"}],
        "bedeutung": "<Bedeutung/Nachwirkung in 1–3 Sätzen>",
        "gegenwartsbezug": "<der Gegenwartsbezug in 1–2 Sätzen>",
        "urteilsfrage": "<eine abwägende Frage mit eigenem Urteil>",
        "sach_dimension": b.sach_dimension,
        "urteil_dimension": b.urteil_dimension,
        "actor_label": b.actor_label,
        "darstellung": [
            {"heading": "<Abschnitt>", "body": "<2–4 Sätze, nur aus dem Faktensatz>",
             "grounded_by": ["<Fakt-Schlüssel>"]},
        ],
    }
    if b.urteil_competence:
        common["urteil_competence"] = b.urteil_competence
    if b.fact_type == "timeline":
        common["timeline"] = [
            {"at": 1789, "label": "<datiertes Ereignis>"},
            {"at": 1793, "label": "<datiertes Ereignis>"},
        ]
    else:
        common["process_name"] = "<Name des Ablaufs>"
        common["process_cyclic"] = b.process_cyclic
        common["process"] = [
            {"name": "<Schritt 1>", "text": "<eine Zeile>"},
            {"name": "<Schritt 2>", "text": "<eine Zeile>"},
        ]
    return json.dumps(common, ensure_ascii=False, indent=2)


def build() -> None:
    outdir = RUNS_DIR / "ingest"
    (outdir / SV_PROMPT_SUBDIR).mkdir(parents=True, exist_ok=True)
    (outdir / SV_SUBDIR).mkdir(parents=True, exist_ok=True)
    manifest = []
    for b in SUBJECTS:
        fact_block = _FACT_TYPE_BLOCK[b.fact_type].format(
            cyclic="true" if b.process_cyclic else "false")
        for t in b.topics:
            comps = _competence_block(b.subject, t.klasse)
            urteil_comp_line = (f"\n- `\"urteil_competence\": \"{b.urteil_competence}\"` — die "
                                f"Kompetenz, der die Urteils-Aufgabe dient." if b.urteil_competence else "")
            note_block = f"\n**Kurator-Hinweis:** {t.note}\n" if t.note else ""
            prompt = _TEMPLATE.format(
                topic=t.topic, subject=b.subject, klasse=t.klasse, leitfrage=t.leitfrage,
                note_block=note_block, fact_type_block=fact_block, competences=comps,
                sach_dimension=b.sach_dimension, urteil_dimension=b.urteil_dimension,
                urteil_comp_line=urteil_comp_line, actor_label=b.actor_label,
                sv_subdir=SV_SUBDIR, id=t.id, example=_example(b, t),
            )
            (outdir / SV_PROMPT_SUBDIR / f"{t.id}.md").write_text(prompt, encoding="utf-8")
            manifest.append({"id": t.id, "code": b.code, "subject": b.subject,
                             "klasse": t.klasse, "fact_type": b.fact_type, "topic": t.topic})
            print(f"{b.code}/{t.id}: {b.fact_type}, kl{t.klasse} -> {SV_PROMPT_SUBDIR}/{t.id}.md")
    (outdir / "sv_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n== {len(manifest)} Sachverhalt-Briefs in {outdir / SV_PROMPT_SUBDIR} ==")


if __name__ == "__main__":
    build()
