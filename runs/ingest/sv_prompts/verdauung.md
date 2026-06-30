# Sachverhalt-Autorierung: „Die Verdauung des Menschen" (Biologie und Umweltbildung, 2. Klasse)

Du schreibst **einen** `Sachverhalt` — ein kuratiertes Modul aus **strukturierten, BELEGTEN
Fakten** plus einer **Darstellung**, die du *über diesem festen Faktensatz* formulierst. Du
schreibst **kein** Arbeitsblatt: das System leitet daraus deterministisch drei Projektionen ab
(Lerntext + Abbildungen + berechnete Sachkompetenz-Aufgaben). Deine Aufgabe ist also: **die
Fakten sauber recherchieren und belegen**, und die Darstellung **nur aus ihnen** formulieren.

**Leitfrage (Vorschlag):** Welchen Weg nimmt das Essen — und was passiert auf jeder Station?

**Kurator-Hinweis:** Linearer Prozess (Mund → Speiseröhre → Magen → Dünndarm → Dickdarm). Begriffe: Enzym, Nährstoff, Resorption. Die Stationen sind die Prozess-Schritte.

## Das tragende Prinzip — *Wähle die Fakten, formuliere den Ausdruck*
- **Fakten sind belegt, nicht erfunden.** Daten, Akteur:innen-Rollen, Ursache→Folge, Begriffe:
  recherchiert aus einer echten Quelle (Wikipedia ist ok) und in `sources` mit `role:"facts"`
  vermerkt. Die Lehrkraft prüft sie am Review-Gate — also keine ausgedachten „Fakten".
- **Die Darstellung ist eine Projektion über dem Faktensatz** — formuliere frei und didaktisch
  schön, aber führe **nichts** ein, was nicht im Faktensatz steht. Ein deterministischer
  *Entity-Lint* prüft das (jede Jahreszahl muss im Faktensatz vorkommen).
- **Mehrperspektivität / Wertung NUR in `urteilsfrage`** — niemals in der sachlichen Darstellung.

## Faktentyp: **Prozess / Ablauf** (ungeordnete Schritte → richtige Reihenfolge)
Dieser Sachverhalt trägt einen `process`: **5–7 Schritte in der RICHTIGEN Reihenfolge** (die
Listenreihenfolge IST die Lösung der Reihenfolge-Aufgabe — das System berechnet sie daraus).
Setze `process_name` (z. B. „Der Weg der Nahrung") und `process_cyclic` (false). Jeder Schritt:
`{"name":"...","text":"<eine erklärende Zeile>"}`. Es gibt **kein Datum** — die Schrittfolge ist
die Ordnung. `timeline`/`regions` bleiben leer. (Vermeide trotzdem erfundene Jahreszahlen in der
Prosa — der Entity-Lint prüft jede 3–4-stellige Zahl gegen den Faktensatz.)

## Kompetenzen (Biologie und Umweltbildung, 2. Klasse — verbatim; `competences` MUSS aus diesen IDs wählen)

### Erkenntnisse gewinnen (E)
- `BIO.US.x.ERK.01` [dims —]: Lebewesen und biologische Phänomene betrachten, beobachten, bestimmen, kriteriengeleitet vergleichen und ordnen, mikroskopieren, zeichnen und messen.
- `BIO.US.x.ERK.02` [dims —]: zu biologischen Vorgängen und Phänomenen naturwissenschaftliche Fragen stellen sowie Hypothesen entwickeln und formulieren.
- `BIO.US.x.ERK.03` [dims —]: Beobachtungen, Versuche, Untersuchungen und Experimente zu naturwissenschaftlichen Fragestellungen planen, durchführen und protokollieren.
- `BIO.US.x.ERK.04` [dims —]: Daten und Ergebnisse von Untersuchungen, Beobachtungen und Experimenten darstellen, analysieren und interpretieren.

### Standpunkte begründen und reflektiert handeln (S)
- `BIO.US.x.STA.01` [dims —]: naturwissenschaftliche von nicht naturwissenschaftlichen Argumentationen unterscheiden, fachlich korrekt und folgerichtig argumentieren.
- `BIO.US.x.STA.02` [dims —]: Fragestellungen im Bereich Bioethik, Sexualität, Gesundheit, Umweltschutz und Nachhaltigkeit unter Einbeziehung kontroverser Gesichtspunkte erörtern und den eigenen Standpunkt fachlich fundiert begründen.
- `BIO.US.x.STA.03` [dims —]: Handlungsempfehlungen fachlich fundiert erstellen und begründen, verantwortungsbewusst und individuell sowie gesellschaftlich nachhaltig handeln.

### Wissen aneignen, anwenden und kommunizieren (W)
- `BIO.US.x.WIS.01` [dims —]: Lebewesen, Lebensräume, biologische Phänomene und Prinzipien benennen, beschreiben, erläutern und in Beziehung setzen.
- `BIO.US.x.WIS.02` [dims —]: Informationen aus unterschiedlichen Medien und Quellen fachbezogen erschließen, zusammenfassen, vergleichen und in verschiedenen Formen (Grafik, Foto, Video, Tabelle, Diagramm, ...) adressaten- und situationsgerecht darstellen und kommunizieren.
- `BIO.US.x.WIS.03` [dims —]: Modelle zur Beschreibung und Erklärung biologischer Sachverhalte/Vorgänge/Beziehungen verwenden, erstellen und deren Gültigkeitsbereiche und Grenzen diskutieren.

### Dimensions-Hinweise (WICHTIG — diese Felder MUSST du setzen)
Die obigen Kompetenzen lösen mit **leeren** Dimensionen auf, darum trägt der Sachverhalt die
Dimension explizit:
- `"sach_dimension": "W"` — die Sachkompetenz-Dimension (für Sach-Aufgaben).
- `"urteil_dimension": "S"` — die Dimension der Urteils-Aufgabe.
- `"urteil_competence": "BIO.US.x.STA.02"` — die Kompetenz, der die Urteils-Aufgabe dient.
- `"actor_label": "Strukturen"` — das Substantiv für die Struktur-Aufgabe.

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
Darstellung und Begriffe auf **2. Klasse AHS** — klar, konkret, anschaulich, ohne Fachjargon-Überladung.
Niemals Kompetenz-IDs, Dimensionen oder das Wort „Lehrplan" im Schülertext.

## Ausgabe
Schreibe **genau eine** Datei nach `runs/ingest/sv/verdauung.json` — **ausschließlich** dieses JSON
(kein Fließtext, keine ``` Zäune), exakt in dieser Form:

```json
{
  "id": "sv-verdauung",
  "subject": "Biologie und Umweltbildung",
  "klasse_range": [
    2,
    2
  ],
  "topic": "Die Verdauung des Menschen",
  "leitfrage": "Welchen Weg nimmt das Essen — und was passiert auf jeder Station?",
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
      "title": "Die Verdauung des Menschen",
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
  "sach_dimension": "W",
  "urteil_dimension": "S",
  "actor_label": "Strukturen",
  "darstellung": [
    {
      "heading": "<Abschnitt>",
      "body": "<2–4 Sätze, nur aus dem Faktensatz>",
      "grounded_by": [
        "<Fakt-Schlüssel>"
      ]
    }
  ],
  "urteil_competence": "BIO.US.x.STA.02",
  "process_name": "<Name des Ablaufs>",
  "process_cyclic": false,
  "process": [
    {
      "name": "<Schritt 1>",
      "text": "<eine Zeile>"
    },
    {
      "name": "<Schritt 2>",
      "text": "<eine Zeile>"
    }
  ]
}
```
