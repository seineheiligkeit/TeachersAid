# Sachverhalt-Autorierung: „Die Französische Revolution" (Geschichte und politische Bildung, 3. Klasse)

Du schreibst **einen** `Sachverhalt` — ein kuratiertes Modul aus **strukturierten, BELEGTEN
Fakten** plus einer **Darstellung**, die du *über diesem festen Faktensatz* formulierst. Du
schreibst **kein** Arbeitsblatt: das System leitet daraus deterministisch drei Projektionen ab
(Lerntext + Abbildungen + berechnete Sachkompetenz-Aufgaben). Deine Aufgabe ist also: **die
Fakten sauber recherchieren und belegen**, und die Darstellung **nur aus ihnen** formulieren.

**Leitfrage (Vorschlag):** Wie stürzt das Volk eine jahrhundertealte Ordnung — und was setzt es an ihre Stelle?

**Kurator-Hinweis:** 1789–1799. Klare Eckdaten (Bastille 1789, Erklärung der Menschen- und Bürgerrechte, Hinrichtung Ludwigs XVI. 1793, Napoleon 1799). Ursache→Folge ist sehr reich.

## Das tragende Prinzip — *Wähle die Fakten, formuliere den Ausdruck*
- **Fakten sind belegt, nicht erfunden.** Daten, Akteur:innen-Rollen, Ursache→Folge, Begriffe:
  recherchiert aus einer echten Quelle (Wikipedia ist ok) und in `sources` mit `role:"facts"`
  vermerkt. Die Lehrkraft prüft sie am Review-Gate — also keine ausgedachten „Fakten".
- **Die Darstellung ist eine Projektion über dem Faktensatz** — formuliere frei und didaktisch
  schön, aber führe **nichts** ein, was nicht im Faktensatz steht. Ein deterministischer
  *Entity-Lint* prüft das (jede Jahreszahl muss im Faktensatz vorkommen).
- **Mehrperspektivität / Wertung NUR in `urteilsfrage`** — niemals in der sachlichen Darstellung.

## Faktentyp: **Zeitleiste** (datierte Ereignisse)
Dieser Sachverhalt trägt eine `timeline` aus **5–7 echten, datierten Ereignissen** (Feld `at`:
eine Jahreszahl als Zahl, oder ein String wie „um 1500"). Sie treibt die Zeitleisten-Abbildung
**und** die Chronologie-Aufgabe (die Lösung = sortiert nach `at`, vom System berechnet).
**HARTE Regel (Entity-Lint):** *Jede* 3–4-stellige Jahreszahl, die in der `darstellung`-Prosa
vorkommt, MUSS als Ereignis in der `timeline` stehen. Erfinde keine Jahreszahl; nimm nur belegte.
`process`/`regions` bleiben leer.

## Kompetenzen (Geschichte und politische Bildung, 3. Klasse — verbatim; `competences` MUSS aus diesen IDs wählen)

### —
- `GPB.US.3.ALL.01` [dims —]: Darstellungen beschreiben, unterscheiden, analysieren und hinterfragen (Schulbücher, TV-Dokumentationen, Internetangebote etc.) – Schwerpunkt: Erzählstrukturen von Darstellungen analysieren (Zielgruppenausrichtung, inhaltliche Schwerpunktsetzung, Emotionalisierung etc.).
- `GPB.US.3.ALL.02` [dims —]: Quellen beschreiben, unterscheiden, analysieren und interpretieren (Schriften, Bilder, Gegenstände etc.).
- `GPB.US.3.ALL.03` [dims —]: eigene Erzählungen über die Vergangenheit auf der Grundlage von Quellen und Darstellungen erstellen.
- `GPB.US.3.ALL.04` [dims —]: unterschiedliche Darstellungen zum selben Thema vergleichen und Gründe für die Unterschiedlichkeit analysieren.
- `GPB.US.3.ALL.05` [dims —]: Fragen zu Kontinuität und Wandel an die Vergangenheit stellen (Schülerinnen und Schüler stellen Fragen wie ua.: Wie entwickelten sich Geschlechterrollen seit dem 19. Jahrhundert in Mitteleuropa? Waren Wanderungen und Migration immer schon Bestandteil von Gesellschaften?).
- `GPB.US.3.ALL.06` [dims —]: unterschiedliche Orientierungsangebote in Darstellungen zum selben Thema analysieren (ua. Bedeutungszuweisungen/Stellenwert von historischen Ereignissen und Persönlichkeiten für Gegenwart/Zukunft, Handlungsempfehlungen für die Gegenwart/Zukunft).
- `GPB.US.3.ALL.07` [dims —]: fachspezifische Konzepte anwenden, reflektieren und weiterentwickeln (ua. „Darstellung“ und „Quelle“ unterscheiden; Gattungsmerkmale von Darstellungen erkennen; „Epoche“ als Form der Zeiteinteilung reflektieren; verschiedene Formen von „Perspektivität“ in Quellen und Darstellungen herausarbeiten); „Herrschaft“ und „Revolution“ in unterschiedlichen Zeiten vergleichen und mit den eigenen Vorstellungen in Verbindung setzen).
- `GPB.US.3.ALL.08` [dims —]: politische Manifestationen (Formen der digitalen Kommunikation, Demonstrationsbanner, Flugzettel, aktionistische Formen, etc.) beschreiben, analysieren und hinterfragen sowie selbstständig erstellen.
- `GPB.US.3.ALL.09` [dims —]: Interessen- und Standortgebundenheit von eigenen und fremden politischen Urteilen analysieren.
- `GPB.US.3.ALL.10` [dims —]: Formen von politischer Mitbestimmung und Vertretung nutzen und demokratische Mittel anwenden.

### Dimensions-Hinweise (WICHTIG — diese Felder MUSST du setzen)
Die obigen Kompetenzen lösen mit **leeren** Dimensionen auf, darum trägt der Sachverhalt die
Dimension explizit:
- `"sach_dimension": "HSA"` — die Sachkompetenz-Dimension (für Sach-Aufgaben).
- `"urteil_dimension": "HOR"` — die Dimension der Urteils-Aufgabe.
- `"actor_label": "Akteure"` — das Substantiv für die Struktur-Aufgabe.

## Pflicht-Inhalte (der Faktensatz)
- `sources`: **mindestens eine** `role:"facts"`-Quelle mit echtem Permalink (Wikipedia: nimm einen
  `oldid`-Permalink auf die konkrete Version), `licence:"CC-BY-SA-4.0"`, `retrieved:"2026-06-30"`.
- `actors` (3–6): Name + `role` (eine erklärende Zeile). Bei Bio/Prozess = **Strukturen/Bestandteile**.
- `causes` (4–6): `{"cause":"...","effect":"...","kind":"<voraussetzung|ursache|verlauf|folge|wirkung>"}`
  → die Wirkungsgefüge-Abbildung **und** die Ursache→Folge-Zuordnungsaufgabe (Lösung = die Paare).
- `concepts` (4–6): `{"term":"...","definition":"..."}` → die Begriff-Zuordnungsaufgabe (Lösung = die Paare).
- `bedeutung` (1–3 Sätze): Bedeutung/Nachwirkung. `gegenwartsbezug` (1–2 Sätze): der Gegenwartsbezug.
- `urteilsfrage`: **eine** abwägende Frage (pro/contra, eigenes Urteil) → die hochstufige Urteils-Aufgabe.
- `darstellung`: **3–5 Abschnitte** `{"heading":"...","body":"<2–4 Sätze>","grounded_by":["<Fakt-Schlüssel>"]}`.
  `grounded_by` listet die Fakt-Schlüssel (Ereignis-`label` / Begriff-`term` / Akteur-`name` / Schritt-`name`),
  auf denen der Absatz fußt. **Setze KEINE `provenance`** an den Abschnitten — die Ableitung hängt sie
  automatisch an (sonst doppelt).

## Schüler-Niveau
Darstellung und Begriffe auf **3. Klasse AHS** — klar, konkret, anschaulich, ohne Fachjargon-Überladung.
Niemals Kompetenz-IDs, Dimensionen oder das Wort „Lehrplan" im Schülertext.

## Ausgabe
Schreibe **genau eine** Datei nach `runs/ingest/sv/franzoesische-revolution.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune), exakt in dieser Form:

```json
{
  "id": "sv-franzoesische-revolution",
  "subject": "Geschichte und politische Bildung",
  "klasse_range": [
    3,
    3
  ],
  "topic": "Die Französische Revolution",
  "leitfrage": "Wie stürzt das Volk eine jahrhundertealte Ordnung — und was setzt es an ihre Stelle?",
  "competences": [
    "<ID aus der Liste>",
    "<weitere ID>"
  ],
  "keywords": [
    "<Schlagwort>",
    "<Schlagwort>"
  ],
  "sources": [
    {
      "title": "Die Französische Revolution",
      "url": "https://de.wikipedia.org/w/index.php?title=…&oldid=…",
      "publisher": "Wikipedia (de)",
      "licence": "CC-BY-SA-4.0",
      "licence_url": "https://creativecommons.org/licenses/by-sa/4.0/",
      "retrieved": "2026-06-30",
      "role": "facts"
    }
  ],
  "actors": [
    {
      "name": "<Name/Struktur>",
      "role": "<eine erklärende Zeile>"
    }
  ],
  "causes": [
    {
      "cause": "<Ursache>",
      "effect": "<Folge>",
      "kind": "ursache"
    },
    {
      "cause": "<…>",
      "effect": "<…>",
      "kind": "folge"
    }
  ],
  "concepts": [
    {
      "term": "<Begriff>",
      "definition": "<kindgerechte Definition>"
    }
  ],
  "bedeutung": "<Bedeutung/Nachwirkung in 1–3 Sätzen>",
  "gegenwartsbezug": "<der Gegenwartsbezug in 1–2 Sätzen>",
  "urteilsfrage": "<eine abwägende Frage mit eigenem Urteil>",
  "sach_dimension": "HSA",
  "urteil_dimension": "HOR",
  "actor_label": "Akteure",
  "darstellung": [
    {
      "heading": "<Abschnitt>",
      "body": "<2–4 Sätze, nur aus dem Faktensatz>",
      "grounded_by": [
        "<Fakt-Schlüssel>"
      ]
    }
  ],
  "timeline": [
    {
      "at": 1789,
      "label": "<datiertes Ereignis>"
    },
    {
      "at": 1793,
      "label": "<datiertes Ereignis>"
    }
  ]
}
```
