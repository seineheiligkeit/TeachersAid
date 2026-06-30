# Realie-Autorierung: „a bus timetable" (French, Zweite lebende Fremdsprache, 4. Klasse, A2)

Du schreibst **eine** `Realie` — ein **erfundenes, alltagsnahes** Lesedokument in **French**
(a bus timetable), das als **Sprechanlass** dient. Eine Realie ist **kein** Sachtext: die „Fakten" (Zeiten,
Preise, Namen) sind **frei erfunden, aber in sich stimmig** — niemand wird durch einen erfundenen
Fahrplan getäuscht. **Tragend ist die SPRACHE**, nicht die Fakten: korrektes, niveaugerechtes
French und ein **kommunikativer** Aufgabenteil. *„Erfinde den Fahrplan, prüfe das French."*

**Szene / Kommunikationsanlass:** Les horaires de bus — plan a trip against a deadline and ask the driver.

**Kurator-Hinweis:** Un horaire de bus: heures de départ + destinations. The deadline lives in the task prompt (so the answer may cite it). Correct A2 French.

## Das tragende Prinzip — *purpose-appropriate rigor*
- **Erfinde die Fakten kohärent.** Diese Realie braucht keine Preise. Erfinde keine realen Behauptungen über die Welt;
  es ist bewusst Fiktion (pädagogisch erkennbar, `origin: "constructed"`, **keine Quelle**).
- **Interne Konsistenz (hart):** Jede Uhrzeit/jeden Preis, den eine **Aufgaben-Antwort** nennt, muss
  im Realie-**Text** oder in `facts` (oder im Aufgaben-Prompt selbst) vorkommen. Eine gezeigte **Summe**
  („£2.00 + £3.00 = £5.00") ist erlaubt (Rechnung über die Karte).
- **Das French muss korrekt und auf A2-Niveau sein** — das prüft die Lehrkraft am Gate.

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
   in **French** verfassen; `answer` = ein kurzer Modelltext.
4. **1 Sprechkarte** (`roleplay`, dim SPR, apply): `roles` = **genau zwei** Karten (A und B) in
   **French**; mündlich, kein Schreibfeld. `answer` = erwartete Wendungen (Deutsch ok).

## Kompetenzen (Zweite lebende Fremdsprache, 4. Klasse — `serves`/`dimensions` MÜSSEN echte IDs/Codes nutzen)
- `FS2.US.4.HOR.01` [dim HOR]: Anweisungen, Fragen und Auskünfte verstehen.
- `FS2.US.4.HOR.02` [dim HOR]: einfache kurze Gespräche und Texte über vertraute Themen verstehen.
- `FS2.US.4.LES.01` [dim LES]: kurze einfache Geschichten, Briefe, E-Mails oder bebilderte Sachtexte verstehen.
- `FS2.US.4.LES.02` [dim LES]: kurzen vertrauten Alltagstexten wichtige Informationen entnehmen.
- `FS2.US.4.SPR.01` [dim SPR]: kurze Gespräche über vertraute Themen führen.
- `FS2.US.4.SPR.02` [dim SPR]: in Alltagssituationen einfache Informationen geben, Fragen stellen und Vereinbarungen treffen.
- `FS2.US.4.SPR.03` [dim SPR]: über vertraute Themen (ua. Dinge, Orte, Personen) sprechen und dabei auch Gefühle, Vorlieben, Stärken und Meinungen auf einfache Weise ausdrücken.
- `FS2.US.4.SCH.01` [dim SCH]: Aspekte des persönlichen Lebensumfeldes beschreiben (ua. Personen, Orte, Pläne, Wünsche).
- `FS2.US.4.SCH.02` [dim SCH]: die eigene Meinung ausdrücken und begründen.
- `FS2.US.4.SCH.03` [dim SCH]: einfache Geschichten und Gebrauchstexte (ua. E-Mails, Mitteilungen) schreiben und dabei auch über vergangene und zukünftige Ereignisse berichten.

Nimm in `serves` **je eine** Kompetenz für Lesen (LES), Schreiben (SCH) und Sprechen (SPR) dieser Klasse.
`dimensions` einer Aufgabe ⊆ {HOR, LES, SPR, SCH} (Scan→LES, Schreiben→SCH, Sprechkarte→SPR).

## Sprache
**Material** (Text, Sprechkarten, Modelltext-`answer`) in **French**. Vokabel-Glossen + die
Lehrer-Hinweise in `answer` dürfen **Deutsch** sein (Gerüst). Niemals Kompetenz-IDs im Schülertext.

## Ausgabe
Schreibe **genau eine** Datei nach `runs/ingest/realien/bus.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune), genau in dieser Form:

```json
{
  "id": "fs-realie-bus",
  "title": "<prägnanter L2-Titel>",
  "subject": "Zweite lebende Fremdsprache",
  "klasse": 4,
  "genre": "a bus timetable",
  "textsorte": "Realie",
  "cefr": "A2",
  "origin": "constructed",
  "scene": "Les horaires de bus",
  "text": "<das ERFUNDENE Realie-Dokument in French, mit Zeilenumbrüchen; inkl. etwas atmosphärischem 'Fluff'>",
  "facts": [
    {
      "label": "<Posten/Zeile>",
      "value": "<Preis oder Gleis/Detail>"
    }
  ],
  "serves": [
    {
      "competence_id": "<LES-ID>",
      "relation": "exercises"
    },
    {
      "competence_id": "<SCH-ID>",
      "relation": "exercises"
    },
    {
      "competence_id": "<SPR-ID>",
      "relation": "exercises"
    }
  ],
  "keywords": [
    "Realie",
    "a bus timetable",
    "A2",
    "French"
  ],
  "annotations": [
    {
      "kind": "vocab",
      "label": "<L2-Wort>",
      "answer": "<deutsche Bedeutung>"
    },
    {
      "kind": "comprehension",
      "dimensions": [
        "LES"
      ],
      "cognitive_level": "understand",
      "label": "<scan question in French>",
      "answer": "<short answer>"
    },
    {
      "kind": "comprehension",
      "dimensions": [
        "LES"
      ],
      "cognitive_level": "analyze",
      "label": "<decide-under-constraint question>",
      "answer": "<answer; show a sum if adding prices>"
    },
    {
      "kind": "communicative",
      "dimensions": [
        "SCH"
      ],
      "cognitive_level": "apply",
      "label": "<write-a-reply / order task in French>",
      "answer": "Modelltext: „<short French model text>“ (kurze, korrekte Sätze)."
    },
    {
      "kind": "roleplay",
      "dimensions": [
        "SPR"
      ],
      "cognitive_level": "apply",
      "label": "<role-play instruction>",
      "roles": [
        "<cue for partner A, in French>",
        "<cue for partner B, in French>"
      ],
      "answer": "Erwartet: <nützliche Wendungen / erwartete Züge> (Deutsch ok)."
    }
  ]
}
```
