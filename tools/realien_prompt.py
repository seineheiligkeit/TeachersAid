"""Build grounded Realien-authoring briefs — the modern-FS breadth seam (Realien Phase 3).

The languages twin of `tools/sachverhalt_prompt.py`. A Realie is a CONSTRUCTED, CEFR-leveled
everyday text (a Sprechanlass, not a world-claim): the subagent INVENTS the facts coherently and
authors correct, level-appropriate L2 over them, with a communicative-first task layer. So the
brief grounds what the agent must NOT get wrong — the real FS competences for the grade, the
genre/scene/level/currency, the load-bearing rules (correct L2 · internal consistency · atmosphere
without touching task data · a reasoning task ladder) — and pins the JSON shape. Run with the venv:

    python tools/realien_prompt.py

Each `runs/ingest/realien_prompts/<id>.md` is self-contained: a subagent reads it and writes one
`runs/ingest/realien/<id>.json`, then `tools/ingest_realien.py --dry-run` validates it. The SME
fact-checks the L2 and the level — the one thing no lint can.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import lehrplan_store as ls


@dataclass
class Realie:
    """One assigned Realie: a genre + scene at a target language and CEFR level."""
    id: str
    subject: str            # "Erste lebende Fremdsprache" (FS1) | "Zweite lebende Fremdsprache" (FS2)
    code: str               # FS1 | FS2 (for the filename anchor)
    language: str           # the L2 the *material* is written in (English | French)
    klasse: int
    cefr: str               # A1 | A2
    genre: str              # the textsorte ("invitation", "film listing", "boulangerie", …)
    scene: str              # the German scene label ("Im Kino", "À la boulangerie" stays L2 ok)
    currency: str           # "£" | "€" | "" (none) — drives the price tasks
    goal: str               # the communicative goal (what the talk is FOR)
    hint: str = ""          # a curator note on content/angle


# The Phase-3 breadth batch — diverse genres across EN (FS1) + FR (FS2), A1 + A2. Distinct from
# the two flagships (station, café). Constructed fiction; the SME vets the L2 + level at the gate.
REALIEN: list[Realie] = [
    Realie("invitation", "Erste lebende Fremdsprache", "FS1", "English", 1, "A1",
           "a birthday-party invitation", "Eine Einladung", "",
           "understand an invitation and reply (accept / say you can come)",
           "A printed party invitation: who, what, the date, the time, the place. Keep it A1-simple."),
    Realie("zoo", "Erste lebende Fremdsprache", "FS1", "English", 2, "A1",
           "a zoo information sign", "Im Zoo", "£",
           "find opening times + ticket prices and plan a visit",
           "A zoo entrance sign: opening hours, ticket prices (adult/child), feeding times. Times "
           "as HH:MM so the consistency lint has something to check."),
    Realie("cinema", "Erste lebende Fremdsprache", "FS1", "English", 3, "A2",
           "a cinema film listing", "Im Kino", "£",
           "choose a film that fits a time + budget, then buy tickets",
           "A cinema board: 3–4 films with start times and ticket prices. The decide-task should "
           "use a time OR budget constraint stated in the task prompt."),
    Realie("weather", "Erste lebende Fremdsprache", "FS1", "English", 3, "A2",
           "a weekly weather forecast", "Das Wetter", "",
           "read the forecast and decide what to wear / what to do",
           "A 5-day forecast: day · weather · temperature (e.g. 18°C). Temperatures are not "
           "lint-checked (no £/time) — the value is the reasoning + speaking."),
    Realie("boulangerie", "Zweite lebende Fremdsprache", "FS2", "French", 3, "A1",
           "a bakery price list", "À la boulangerie", "€",
           "order at the bakery and work out the price",
           "Une carte de boulangerie: croissant, baguette, pain au chocolat … with € prices. "
           "Correct, simple A1 French. The price-total task must SHOW the sum (lint-exempt)."),
    Realie("bus", "Zweite lebende Fremdsprache", "FS2", "French", 4, "A2",
           "a bus timetable", "Les horaires de bus", "",
           "plan a trip against a deadline and ask the driver",
           "Un horaire de bus: heures de départ + destinations. The deadline lives in the task "
           "prompt (so the answer may cite it). Correct A2 French."),
]

REALIEN_PROMPT_SUBDIR = "realien_prompts"
REALIEN_SUBDIR = "realien"


_TEMPLATE = """# Realie-Autorierung: „{title_hint}" ({language}, {subject}, {klasse}. Klasse, {cefr})

Du schreibst **eine** `Realie` — ein **erfundenes, alltagsnahes** Lesedokument in **{language}**
({genre}), das als **Sprechanlass** dient. Eine Realie ist **kein** Sachtext: die „Fakten" (Zeiten,
Preise, Namen) sind **frei erfunden, aber in sich stimmig** — niemand wird durch einen erfundenen
Fahrplan getäuscht. **Tragend ist die SPRACHE**, nicht die Fakten: korrektes, niveaugerechtes
{language} und ein **kommunikativer** Aufgabenteil. *„Erfinde den Fahrplan, prüfe das {language}."*

**Szene / Kommunikationsanlass:** {scene} — {goal}.
{hint_block}
## Das tragende Prinzip — *purpose-appropriate rigor*
- **Erfinde die Fakten kohärent.** {currency_rule} Erfinde keine realen Behauptungen über die Welt;
  es ist bewusst Fiktion (pädagogisch erkennbar, `origin: "constructed"`, **keine Quelle**).
- **Interne Konsistenz (hart):** Jede Uhrzeit/jeden Preis, den eine **Aufgaben-Antwort** nennt, muss
  im Realie-**Text** oder in `facts` (oder im Aufgaben-Prompt selbst) vorkommen. Eine gezeigte **Summe**
  („{cur}2.00 + {cur}3.00 = {cur}5.00") ist erlaubt (Rechnung über die Karte).
- **Das {language} muss korrekt und auf {cefr}-Niveau sein** — das prüft die Lehrkraft am Gate.

## „Leben" geben (wichtig fürs Gefühl)
Mach aus einer nackten Liste ein **echtes** Dokument: ein Motto/Untertitel, Status („on time"),
Geschmacks-/Hinweiszeilen, Öffnungszeiten, freundliche Schlusszeile. **Dieses „Fluff" darf KEINE
Daten enthalten, die eine Aufgabe braucht** (es erweitert nur den Text, nie die Aufgabenlogik).

## Aufgaben: **kommunikativ zuerst, nicht nur Nachschlagen**
Baue eine kleine Niveaustufung (nicht alles „remember"):
1. **1 Scan** (`comprehension`, dim LES) als sanfter Einstieg — eine Info direkt ablesen.
2. **1–2 Denk-/Entscheidungsaufgaben** (`comprehension`, dim LES, `cognitive_level` analyze/evaluate):
   unter einer Bedingung entscheiden (Budget/Uhrzeit/Vorliebe), empfehlen + begründen.
3. **1 Schreibaufgabe** (`communicative`, dim SCH, apply): eine kurze Mitteilung/Antwort/Bestellung
   in **{language}** verfassen; `answer` = ein kurzer Modelltext.
4. **1 Sprechkarte** (`roleplay`, dim SPR, apply): `roles` = **genau zwei** Karten (A und B) in
   **{language}**; mündlich, kein Schreibfeld. `answer` = erwartete Wendungen (Deutsch ok).

## Kompetenzen ({subject}, {klasse}. Klasse — `serves`/`dimensions` MÜSSEN echte IDs/Codes nutzen)
{competences}

Nimm in `serves` **je eine** Kompetenz für Lesen (LES), Schreiben (SCH) und Sprechen (SPR) dieser Klasse.
`dimensions` einer Aufgabe ⊆ {{HOR, LES, SPR, SCH}} (Scan→LES, Schreiben→SCH, Sprechkarte→SPR).

## Sprache
**Material** (Text, Sprechkarten, Modelltext-`answer`) in **{language}**. Vokabel-Glossen + die
Lehrer-Hinweise in `answer` dürfen **Deutsch** sein (Gerüst). Niemals Kompetenz-IDs im Schülertext.

## Ausgabe
Schreibe **genau eine** Datei nach `runs/ingest/{sub}/{id}.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune), genau in dieser Form:

```json
{example}
```
"""


def _competence_block(subject: str, klasse: int) -> str:
    lines = []
    for c in ls.competences_for(subject, klasse):
        dims = ",".join(c.dimensions) if c.dimensions else "—"
        lines.append(f"- `{c.id}` [dim {dims}]: {c.text.strip()}")
    return "\n".join(lines)


def _example(r: Realie) -> str:
    cur = r.currency or ""
    ex = {
        "id": f"fs-realie-{r.id}",
        "title": "<prägnanter L2-Titel>",
        "subject": r.subject,
        "klasse": r.klasse,
        "genre": r.genre, "textsorte": "Realie",
        "cefr": r.cefr, "origin": "constructed", "scene": r.scene,
        "text": "<das ERFUNDENE Realie-Dokument in " + r.language + ", mit Zeilenumbrüchen; "
                "inkl. etwas atmosphärischem 'Fluff'>",
        "facts": [{"label": "<Posten/Zeile>", "value": f"<{cur}Preis oder Gleis/Detail>"}],
        "serves": [{"competence_id": "<LES-ID>", "relation": "exercises"},
                   {"competence_id": "<SCH-ID>", "relation": "exercises"},
                   {"competence_id": "<SPR-ID>", "relation": "exercises"}],
        "keywords": ["Realie", r.genre, r.cefr, r.language],
        "annotations": [
            {"kind": "vocab", "label": "<L2-Wort>", "answer": "<deutsche Bedeutung>"},
            {"kind": "comprehension", "dimensions": ["LES"], "cognitive_level": "understand",
             "label": "<scan question in " + r.language + ">", "answer": "<short answer>"},
            {"kind": "comprehension", "dimensions": ["LES"], "cognitive_level": "analyze",
             "label": "<decide-under-constraint question>", "answer": "<answer; show a sum if adding "
                      + (cur or "prices") + ">"},
            {"kind": "communicative", "dimensions": ["SCH"], "cognitive_level": "apply",
             "label": "<write-a-reply / order task in " + r.language + ">",
             "answer": "Modelltext: „<short " + r.language + " model text>“ (kurze, korrekte Sätze)."},
            {"kind": "roleplay", "dimensions": ["SPR"], "cognitive_level": "apply",
             "label": "<role-play instruction>",
             "roles": ["<cue for partner A, in " + r.language + ">",
                       "<cue for partner B, in " + r.language + ">"],
             "answer": "Erwartet: <nützliche Wendungen / erwartete Züge> (Deutsch ok)."},
        ],
    }
    return json.dumps(ex, ensure_ascii=False, indent=2)


def build() -> None:
    outdir = RUNS_DIR / "ingest"
    (outdir / REALIEN_PROMPT_SUBDIR).mkdir(parents=True, exist_ok=True)
    (outdir / REALIEN_SUBDIR).mkdir(parents=True, exist_ok=True)
    manifest = []
    for r in REALIEN:
        cur = r.currency
        currency_rule = (f"Preise in **{cur}** (z. B. {cur}3.50)." if cur else
                         "Diese Realie braucht keine Preise.")
        prompt = _TEMPLATE.format(
            title_hint=r.genre, language=r.language, subject=r.subject, klasse=r.klasse, cefr=r.cefr,
            genre=r.genre, scene=r.scene, goal=r.goal,
            hint_block=(f"\n**Kurator-Hinweis:** {r.hint}\n" if r.hint else ""),
            currency_rule=currency_rule, cur=cur or "£",
            competences=_competence_block(r.subject, r.klasse),
            sub=REALIEN_SUBDIR, id=r.id, example=_example(r))
        (outdir / REALIEN_PROMPT_SUBDIR / f"{r.id}.md").write_text(prompt, encoding="utf-8")
        manifest.append({"id": r.id, "code": r.code, "subject": r.subject, "language": r.language,
                         "klasse": r.klasse, "cefr": r.cefr, "genre": r.genre})
        print(f"{r.code}/{r.id}: {r.language} {r.cefr} kl{r.klasse} ({r.genre}) -> "
              f"{REALIEN_PROMPT_SUBDIR}/{r.id}.md")
    (outdir / "realien_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n== {len(manifest)} Realie-Briefs in {outdir / REALIEN_PROMPT_SUBDIR} ==")


if __name__ == "__main__":
    build()
