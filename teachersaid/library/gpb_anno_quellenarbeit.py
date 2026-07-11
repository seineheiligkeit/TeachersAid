"""Referenced-only GPB Quellenarbeit with one exact ÖNB-Labs/ANNO issue page.

The historical newspaper expression is NOT embedded here.  Students open the stable IIIF
canvas, inspect the scan and its raw OCR, and build their own source analysis.  This is the
grounded-facts layer's (b2) path: point at the archive with a precise reference, but do not
redistribute the source.  The source metadata comes from ``tools/fetch_anno.py``'s recorded
manifest/page; expected answers state criteria or quote only OCR strings in that record.
"""
from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

SUBJECT = "Geschichte und politische Bildung"
KLASSE = 3
ANNO_PAGE = "https://iiif.onb.ac.at/presentation/ANNO/lmz18710902/canvas/00000001"
ISSUE = "Leitmeritzer Zeitung, 2. September 1871, Seite 1"


def build_content() -> WorksheetContent:
    meta = WorksheetMeta(
        title="Zeitung als politische Waffe? Quellenarbeit in ANNO",
        subtitle="Seitenbild, OCR und Perspektive eines Leitartikels von 1871",
        subject=SUBJECT, stufe="Unterstufe", klasse=KLASSE,
        kernfrage="Wie macht politische Sprache aus einer Meinung einen dringenden Aufruf?",
        fassung=store.get_fassung(),
        lehrplan_label="Geschichte und politische Bildung · 3. Klasse · Quellenarbeit",
    )
    intro = [
        InfoBlock(
            id="anno.hinweis", kind="callout", callout_role="note",
            content=(f"Öffne die historische Zeitungsseite: {ANNO_PAGE} — {ISSUE}. "
                     "Arbeite immer mit dem Seitenbild UND der maschinellen OCR. Die OCR ist "
                     "ungeprüft: Übernimm keinen korrigierten Wortlaut, ohne ihn am Scan zu "
                     "kontrollieren; unlesbare Stellen markierst du ehrlich mit [?]."),
        ),
        InfoBlock(
            id="anno.methode", kind="procedure",
            content=("Vier Schritte: 1. Quelle bestimmen (Wer? Wann? Wo?). 2. Seitenbild und OCR "
                     "vergleichen. 3. Wortwahl und Perspektive belegen. 4. Ein begründetes "
                     "Quellenurteil formulieren."),
        ),
    ]
    tasks = [
        TaskBlock(
            id="anno.t1", kind="source_analysis",
            prompt=("Bestimme die Quelle: Notiere Zeitungstitel, Datum, Seite und die Überschrift "
                    "des Artikels. Erkläre anschließend, warum die Seite eine Quelle und keine "
                    "spätere Darstellung ist."),
            response={"mode": "lines", "n": 5}, cognitive_level="understand",
            dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"}],
            est_minutes=8,
            answer_key=("Leitmeritzer Zeitung; 2. September 1871; Seite 1; „Zum zweiten "
                        "deutsch-böhmischen Lehrertage in Leitmeritz“. Quelle: Die Zeitung "
                        "entstand 1871 und ist damit ein zeitgenössisches Medienzeugnis."),
        ),
        TaskBlock(
            id="anno.t2", kind="source_analysis",
            prompt=("OCR-Prüfung: Finde drei Stellen, an denen die OCR nicht sicher zum Seitenbild "
                    "passt. Notiere jeweils (a) den OCR-Wortlaut, (b) deine Lesung am Scan und "
                    "(c) wie sicher du bist. Verwende [?], wenn die Stelle offen bleibt."),
            response={"mode": "table", "columns": ["OCR", "Lesung am Scan", "Sicherheit"],
                      "rows": 3},
            cognitive_level="analyze", dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"}],
            est_minutes=10,
            answer_key=("Erwartet: drei nachvollziehbare Vergleiche direkt am Scan. Korrekt ist nur "
                        "eine Lesung, die das Seitenbild trägt; Unsicherheit darf und soll mit [?] "
                        "markiert werden. Nicht die moderne Rechtschreibung, sondern der gedruckte "
                        "Wortlaut ist maßgeblich."),
            watch_outs=["Keine stillen OCR-Korrekturen akzeptieren: Scanbeleg oder [?]."],
        ),
        TaskBlock(
            id="anno.t3", kind="source_analysis",
            prompt=("Untersuche zwei Bildfelder des Artikels: (a) Österreich als „stolzes Schiff“, "
                    "das zum „mast- und ruderlosen Wrak“ werde; (b) die politischen Gegner als "
                    "„nach Nahrung lüsterner Geier“. Was bewirken diese Bilder?"),
            response={"mode": "lines", "n": 6}, cognitive_level="analyze",
            dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.07", "relation": "exercises"}],
            est_minutes=10,
            answer_key=("Schiff/Wrack: dramatisiert staatlichen Zerfall und fehlende Steuerung. "
                        "Geier/Krallen: entmenschlicht politische Gegner und stellt sie als "
                        "räuberische Bedrohung dar. Beide Bilder emotionalisieren und mobilisieren."),
        ),
        TaskBlock(
            id="anno.t4", kind="open_response",
            prompt=("Formuliere ein Quellenurteil (8–10 Sätze): Was erfahren wir aus dem Artikel "
                    "über politische Kommunikation im Jahr 1871 — und was können wir aus dieser "
                    "einzelnen, parteilichen Stimme NICHT verlässlich ableiten? Belege zweimal am "
                    "Wortlaut oder Seitenbild."),
            response={"mode": "box", "min_height_mm": 60}, cognitive_level="evaluate",
            dimensions=["HME", "HOR"],
            serves=[{"competence_id": "GPB.US.3.ALL.03", "relation": "exercises"},
                    {"competence_id": "GPB.US.3.ALL.07", "relation": "exercises"}],
            est_minutes=14,
            acceptable_reasoning=("Erwartet: Die Quelle zeigt eine stark wertende liberale "
                                  "Perspektive und politische Mobilisierung durch Metaphern/Wir-Form. "
                                  "Sie belegt nicht, wie alle Menschen dachten oder wie die politische "
                                  "Lage objektiv war. Zwei konkrete Belege + Reichweitenbegrenzung."),
        ),
    ]
    return WorksheetContent(
        meta=meta, subject_model=store.get_subject_model(SUBJECT), intro=intro,
        sections=[Baustein(
            id="anno.quelle", title="Vom Digitalisat zum Quellenurteil",
            teacher_overview={
                "throughline": ("Nicht die OCR glauben und nicht die Quelle verwerfen: Scan und "
                                "Maschinentext gegeneinander prüfen, Perspektive belegen, Reichweite "
                                "des Quellenurteils begrenzen."),
                "talking_points": [
                    "OCR-Fehler sind hier Methode, kein Defekt: Sie zwingen zum Blick auf die Quelle.",
                    "Perspektivität ist keine Widerlegung; sie ist eine Eigenschaft, die untersucht wird.",
                ],
                "timing_notes": "Einzel- bis Doppelstunde; Internetzugang für das ANNO-Digitalisat nötig.",
            },
            blocks=tasks,
        )],
    )
