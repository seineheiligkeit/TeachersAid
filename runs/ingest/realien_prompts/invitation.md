# Realie-Autorierung: „a birthday-party invitation" (English, Erste lebende Fremdsprache, 1. Klasse, A1)

Du schreibst **eine** `Realie` — ein **erfundenes, alltagsnahes** Lesedokument in **English**
(a birthday-party invitation), das als **Sprechanlass** dient. Eine Realie ist **kein** Sachtext: die „Fakten" (Zeiten,
Preise, Namen) sind **frei erfunden, aber in sich stimmig** — niemand wird durch einen erfundenen
Fahrplan getäuscht. **Tragend ist die SPRACHE**, nicht die Fakten: korrektes, niveaugerechtes
English und ein **kommunikativer** Aufgabenteil. *„Erfinde den Fahrplan, prüfe das English."*

**Szene / Kommunikationsanlass:** Eine Einladung — understand an invitation and reply (accept / say you can come).

**Kurator-Hinweis:** A printed party invitation: who, what, the date, the time, the place. Keep it A1-simple.

## Das tragende Prinzip — *purpose-appropriate rigor*
- **Erfinde die Fakten kohärent.** Diese Realie braucht keine Preise. Erfinde keine realen Behauptungen über die Welt;
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

## Kompetenzen (Erste lebende Fremdsprache, 1. Klasse — `serves`/`dimensions` MÜSSEN echte IDs/Codes nutzen)
- `FS1.US.1.HOR.01` [dim HOR]: in kurzen Dialogen oder Monologen einfache Fragen und Sätze, die sich auf sie selbst und ihr persönliches Umfeld beziehen, verstehen.
- `FS1.US.1.HOR.02` [dim HOR]: einfache alltägliche Kommunikation im Unterricht verstehen.
- `FS1.US.1.LES.01` [dim LES]: einfache Arbeitsanweisungen und Mitteilungen verstehen.
- `FS1.US.1.LES.02` [dim LES]: sehr einfache Texte über vertraute Themen verstehen.
- `FS1.US.1.SPR.01` [dim SPR]: an Gesprächen teilnehmen und sich mit Hilfe des Gesprächspartners auf einfache Art verständigen.
- `FS1.US.1.SPR.02` [dim SPR]: einfache Fragen stellen und beantworten.
- `FS1.US.1.SPR.03` [dim SPR]: beim zusammenhängenden Sprechen in einfachen Sätzen über vertraute Themen (ua. Familie, Freunde, Tagesablauf, Hobbys, Schule) sprechen.
- `FS1.US.1.SCH.01` [dim SCH]: über sich selbst und vertraute Themen (ua. Familie, Freunde, Tagesablauf, Hobbys, Schule) in einfachen Sätzen schreiben.
- `FS1.US.1.SCH.02` [dim SCH]: Informationen in geschriebener Form weitergeben (persönliche Mitteilungen).

Nimm in `serves` **je eine** Kompetenz für Lesen (LES), Schreiben (SCH) und Sprechen (SPR) dieser Klasse.
`dimensions` einer Aufgabe ⊆ {HOR, LES, SPR, SCH} (Scan→LES, Schreiben→SCH, Sprechkarte→SPR).

## Sprache
**Material** (Text, Sprechkarten, Modelltext-`answer`) in **English**. Vokabel-Glossen + die
Lehrer-Hinweise in `answer` dürfen **Deutsch** sein (Gerüst). Niemals Kompetenz-IDs im Schülertext.

## Ausgabe
Schreibe **genau eine** Datei nach `runs/ingest/realien/invitation.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune), genau in dieser Form:

```json
{
  "id": "fs-realie-invitation",
  "title": "<prägnanter L2-Titel>",
  "subject": "Erste lebende Fremdsprache",
  "klasse": 1,
  "genre": "a birthday-party invitation",
  "textsorte": "Realie",
  "cefr": "A1",
  "origin": "constructed",
  "scene": "Eine Einladung",
  "text": "<das ERFUNDENE Realie-Dokument in English, mit Zeilenumbrüchen; inkl. etwas atmosphärischem 'Fluff'>",
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
    "a birthday-party invitation",
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
      "answer": "<answer; show a sum if adding prices>"
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
