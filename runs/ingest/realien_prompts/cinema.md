# Realie-Autorierung: „a cinema film listing" (English, Erste lebende Fremdsprache, 3. Klasse, A2)

Du schreibst **eine** `Realie` — ein **erfundenes, alltagsnahes** Lesedokument in **English**
(a cinema film listing), das als **Sprechanlass** dient. Eine Realie ist **kein** Sachtext: die „Fakten" (Zeiten,
Preise, Namen) sind **frei erfunden, aber in sich stimmig** — niemand wird durch einen erfundenen
Fahrplan getäuscht. **Tragend ist die SPRACHE**, nicht die Fakten: korrektes, niveaugerechtes
English und ein **kommunikativer** Aufgabenteil. *„Erfinde den Fahrplan, prüfe das English."*

**Szene / Kommunikationsanlass:** Im Kino — choose a film that fits a time + budget, then buy tickets.

**Kurator-Hinweis:** A cinema board: 3–4 films with start times and ticket prices. The decide-task should use a time OR budget constraint stated in the task prompt.

## Das tragende Prinzip — *purpose-appropriate rigor*
- **Erfinde die Fakten kohärent.** Preise in **£** (z. B. £3.50). Erfinde keine realen Behauptungen über die Welt;
  es ist bewusst Fiktion (pädagogisch erkennbar, `origin: "constructed"`, **keine Quelle**).
- **Interne Konsistenz (hart):** Jede Uhrzeit/jeden Preis, den eine **Aufgaben-Antwort** nennt, muss
  im Realie-**Text** oder in `facts` (oder im Aufgaben-Prompt selbst) vorkommen. Eine gezeigte **Summe**
  („£2.00 + £3.00 = £5.00") ist erlaubt (Rechnung über die Karte).
- **Das English muss korrekt und auf A2-Niveau sein** — das prüft die Lehrkraft am Gate.

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

## Kompetenzen (Erste lebende Fremdsprache, 3. Klasse — `serves`/`dimensions` MÜSSEN echte IDs/Codes nutzen)
- `FS1.US.3.HOR.01` [dim HOR]: einfache Gespräche, Erzählungen und kurze Medienbeiträge verstehen.
- `FS1.US.3.LES.01` [dim LES]: einfache und konkrete Artikel in Magazinen und Jugendzeitschriften, altersadäquate Kinder- und Jugendbücher, Geschichten und Sachtexte sowie persönliche Texte, die sich auf altersgerechte Aspekte der zielsprachlichen Kultur(en) beziehen, verstehen.
- `FS1.US.3.LES.02` [dim LES]: in einfachen Texten Wünsche und Gefühle verstehen.
- `FS1.US.3.SPR.01` [dim SPR]: ein Gespräch beginnen, weiterführen und beenden sowie einfache Sprecherwechsel durchführen.
- `FS1.US.3.SPR.02` [dim SPR]: Vereinbarungen treffen, Ratschläge erbitten und geben, einfache Begründungen, Meinungen und Gefühle ausdrücken und darauf reagieren.
- `FS1.US.3.SPR.03` [dim SPR]: über vertraute Themenbereiche erzählen und einfache (Buch-)Präsentationen halten.
- `FS1.US.3.SCH.01` [dim SCH]: kurze zusammenhängende Texte über alltägliche Aspekte des eigenen Umfelds sowie des Lebensalltags von Jugendlichen in verschiedenen Ländern schreiben.
- `FS1.US.3.SCH.02` [dim SCH]: kurze Beschreibungen von Ereignissen, vergangenen und zukünftigen Handlungen und persönlichen Erfahrungen verfassen und dabei auch Meinungen und Gefühle ausdrücken.
- `FS1.US.3.SCH.03` [dim SCH]: kurz über ihre Eindrücke und Meinungen zu altersadäquaten Geschichten sowie zu Kinder- und Jugendliteratur schreiben.

Nimm in `serves` **je eine** Kompetenz für Lesen (LES), Schreiben (SCH) und Sprechen (SPR) dieser Klasse.
`dimensions` einer Aufgabe ⊆ {HOR, LES, SPR, SCH} (Scan→LES, Schreiben→SCH, Sprechkarte→SPR).

## Sprache
**Material** (Text, Sprechkarten, Modelltext-`answer`) in **English**. Vokabel-Glossen + die
Lehrer-Hinweise in `answer` dürfen **Deutsch** sein (Gerüst). Niemals Kompetenz-IDs im Schülertext.

## Ausgabe
Schreibe **genau eine** Datei nach `runs/ingest/realien/cinema.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune), genau in dieser Form:

```json
{
  "id": "fs-realie-cinema",
  "title": "<prägnanter L2-Titel>",
  "subject": "Erste lebende Fremdsprache",
  "klasse": 3,
  "genre": "a cinema film listing",
  "textsorte": "Realie",
  "cefr": "A2",
  "origin": "constructed",
  "scene": "Im Kino",
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
    "a cinema film listing",
    "A2",
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
