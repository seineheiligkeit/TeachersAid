# Realie-Autorierung: „a zoo information sign" (English, Erste lebende Fremdsprache, 2. Klasse, A1)

Du schreibst **eine** `Realie` — ein **erfundenes, alltagsnahes** Lesedokument in **English**
(a zoo information sign), das als **Sprechanlass** dient. Eine Realie ist **kein** Sachtext: die „Fakten" (Zeiten,
Preise, Namen) sind **frei erfunden, aber in sich stimmig** — niemand wird durch einen erfundenen
Fahrplan getäuscht. **Tragend ist die SPRACHE**, nicht die Fakten: korrektes, niveaugerechtes
English und ein **kommunikativer** Aufgabenteil. *„Erfinde den Fahrplan, prüfe das English."*

**Szene / Kommunikationsanlass:** Im Zoo — find opening times + ticket prices and plan a visit.

**Kurator-Hinweis:** A zoo entrance sign: opening hours, ticket prices (adult/child), feeding times. Times as HH:MM so the consistency lint has something to check.

## Das tragende Prinzip — *purpose-appropriate rigor*
- **Erfinde die Fakten kohärent.** Preise in **£** (z. B. £3.50). Erfinde keine realen Behauptungen über die Welt;
  es ist bewusst Fiktion (pädagogisch erkennbar, `origin: "constructed"`, **keine Quelle**).
- **Interne Konsistenz (hart):** Jede Uhrzeit/jeden Preis, den eine **Aufgaben-Antwort** nennt, muss
  im Realie-**Text** oder in `facts` (oder im Aufgaben-Prompt selbst) vorkommen. Eine gezeigte **Summe**
  („£2.00 + £3.00 = £5.00") ist erlaubt (Rechnung über die Karte).
- **Das English muss korrekt und auf A1-Niveau sein** — das prüft die Lehrkraft am Gate.

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
   in **English** verfassen; `answer` = ein kurzer Modelltext.
4. **1 Sprechkarte** (`roleplay`, dim SPR, apply): `roles` = **genau zwei** Karten (A und B) in
   **English**; mündlich, kein Schreibfeld. `answer` = erwartete Wendungen (Deutsch ok).

## Kompetenzen (Erste lebende Fremdsprache, 2. Klasse — `serves`/`dimensions` MÜSSEN echte IDs/Codes nutzen)
- `FS1.US.2.HOR.01` [dim HOR]: Anweisungen, Fragen und Auskünfte verstehen.
- `FS1.US.2.HOR.02` [dim HOR]: kurze einfache Gespräche und Texte über vertraute Themen verstehen.
- `FS1.US.2.LES.01` [dim LES]: kurze einfache Geschichten, Briefe, E-Mails oder bebilderte Sachtexte verstehen.
- `FS1.US.2.LES.02` [dim LES]: kurzen vertrauten Alltagstexten wichtige Informationen entnehmen.
- `FS1.US.2.SPR.01` [dim SPR]: kurze Gespräche über vertraute Themen führen.
- `FS1.US.2.SPR.02` [dim SPR]: in Alltagssituationen einfache Informationen geben, Fragen stellen und Vereinbarungen treffen.
- `FS1.US.2.SPR.03` [dim SPR]: über vertraute Themen (ua. Dinge, Orte, Personen) sprechen und dabei auch Gefühle, Vorlieben, Stärken und Meinungen auf einfache Weise ausdrücken.
- `FS1.US.2.SCH.01` [dim SCH]: Aspekte des persönlichen Lebensumfeldes beschreiben (ua. Personen, Orte, Pläne, Wünsche).
- `FS1.US.2.SCH.02` [dim SCH]: die eigene Meinung ausdrücken und begründen.
- `FS1.US.2.SCH.03` [dim SCH]: einfache Geschichten und Gebrauchstexte (ua. E-Mails, Mitteilungen) schreiben und dabei auch über vergangene und zukünftige Ereignisse berichten.

Nimm in `serves` **je eine** Kompetenz für Lesen (LES), Schreiben (SCH) und Sprechen (SPR) dieser Klasse.
`dimensions` einer Aufgabe ⊆ {HOR, LES, SPR, SCH} (Scan→LES, Schreiben→SCH, Sprechkarte→SPR).

## Sprache
**Material** (Text, Sprechkarten, Modelltext-`answer`) in **English**. Vokabel-Glossen + die
Lehrer-Hinweise in `answer` dürfen **Deutsch** sein (Gerüst). Niemals Kompetenz-IDs im Schülertext.

## Ausgabe
Schreibe **genau eine** Datei nach `runs/ingest/realien/zoo.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune), genau in dieser Form:

```json
{
  "id": "fs-realie-zoo",
  "title": "<prägnanter L2-Titel>",
  "subject": "Erste lebende Fremdsprache",
  "klasse": 2,
  "genre": "a zoo information sign",
  "textsorte": "Realie",
  "cefr": "A1",
  "origin": "constructed",
  "scene": "Im Zoo",
  "text": "<das ERFUNDENE Realie-Dokument in English, mit Zeilenumbrüchen; inkl. etwas atmosphärischem 'Fluff'>",
  "facts": [
    {
      "label": "<Posten/Zeile>",
      "value": "<£Preis oder Gleis/Detail>"
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
    "a zoo information sign",
    "A1",
    "English"
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
      "label": "<scan question in English>",
      "answer": "<short answer>"
    },
    {
      "kind": "comprehension",
      "dimensions": [
        "LES"
      ],
      "cognitive_level": "analyze",
      "label": "<decide-under-constraint question>",
      "answer": "<answer; show a sum if adding £>"
    },
    {
      "kind": "communicative",
      "dimensions": [
        "SCH"
      ],
      "cognitive_level": "apply",
      "label": "<write-a-reply / order task in English>",
      "answer": "Modelltext: „<short English model text>“ (kurze, korrekte Sätze)."
    },
    {
      "kind": "roleplay",
      "dimensions": [
        "SPR"
      ],
      "cognitive_level": "apply",
      "label": "<role-play instruction>",
      "roles": [
        "<cue for partner A, in English>",
        "<cue for partner B, in English>"
      ],
      "answer": "Erwartet: <nützliche Wendungen / erwartete Züge> (Deutsch ok)."
    }
  ]
}
```
