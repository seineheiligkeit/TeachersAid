"""Referenced-only GPB Quellenarbeit #2: the official voice (ANNO/ÖNB, Wiener Zeitung 1873).

The counterpart to ``gpb_anno_quellenarbeit`` (the oppositional 1871 Leitmeritzer
Leitartikel): here the class reads the CELEBRATORY official register — the Wiener
Zeitung's report on the opening of the 1873 Weltausstellung, printing the Vienna
mayor's address to the emperor in full.  Same discipline: the historical newspaper
expression is NOT embedded; students open the stable IIIF canvas, work with scan + raw
OCR, and analyse whose achievement "progress" is made to be.  Source metadata comes from
``tools/fetch_anno.py``'s record (runs/ingest/texts_src/anno-weltausstellung-1873.json);
expected answers state criteria or quote only OCR strings recorded there.
"""
from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

SUBJECT = "Geschichte und politische Bildung"
KLASSE = 3
ANNO_PAGE = "https://iiif.onb.ac.at/presentation/ANNO/wrz18730502/canvas/00000003"
ISSUE = "Wiener Zeitung, 2. Mai 1873, Seite 3"
ARTICLE = "Eröffnungsfeier der Weltausstellung: Ansprache des Bürgermeisters"


def build_content() -> WorksheetContent:
    meta = WorksheetMeta(
        title="Fortschritt als Festrede: Quellenarbeit in ANNO",
        subtitle="Die Wiener Zeitung berichtet von der Eröffnung der Weltausstellung 1873",
        subject=SUBJECT, stufe="Unterstufe", klasse=KLASSE,
        kernfrage="Wessen Verdienst ist der Fortschritt — und wer sagt das hier?",
        fassung=store.get_fassung(),
        lehrplan_label="Geschichte und politische Bildung · 3. Klasse · Quellenarbeit",
    )
    intro = [
        InfoBlock(
            id="anno2.hinweis", kind="callout", callout_role="note",
            content=(f"Öffne die historische Zeitungsseite: {ANNO_PAGE} — {ISSUE}, "
                     f"„{ARTICLE}“. Arbeite immer mit dem Seitenbild UND der maschinellen "
                     "OCR. Die OCR ist ungeprüft: Übernimm keinen korrigierten Wortlaut, "
                     "ohne ihn am Scan zu kontrollieren; unlesbare Stellen markierst du "
                     "ehrlich mit [?]."),
        ),
        InfoBlock(
            id="anno2.methode", kind="procedure",
            content=("Vier Schritte: 1. Quelle bestimmen (Wer? Wann? Wo? Welche Textsorte?). "
                     "2. Seitenbild und OCR vergleichen. 3. Wortwahl und Sprecher-Standort "
                     "belegen. 4. Ein begründetes Quellenurteil formulieren."),
        ),
    ]
    tasks = [
        TaskBlock(
            id="anno2.t1", kind="source_analysis",
            prompt=("Bestimme die Quelle: Notiere Zeitungstitel, Datum und Seite. Um welche "
                    "Textsorte handelt es sich (was druckt die Zeitung hier ab)? Erkläre "
                    "anschließend, warum die Seite eine Quelle und keine spätere "
                    "Darstellung ist."),
            response={"mode": "lines", "n": 5}, cognitive_level="understand",
            dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"},
                    {"competence_id": "GPB.US.3.ALL.07", "relation": "exercises"}],
            est_minutes=8,
            answer_key=("Wiener Zeitung; 2. Mai 1873; Seite 3. Abgedruckt ist die feierliche "
                        "Ansprache (Festrede) des Bürgermeisters von Wien bei der Eröffnung "
                        "der Weltausstellung. Quelle: Die Seite entstand 1873, zur Zeit des "
                        "Ereignisses selbst — sie ist ein zeitgenössisches Zeugnis, keine "
                        "spätere Darstellung."),
        ),
        TaskBlock(
            id="anno2.t2", kind="source_analysis",
            prompt=("OCR-Prüfung: Finde drei Stellen, an denen die OCR nicht sicher zum "
                    "Seitenbild passt. Notiere jeweils (a) den OCR-Wortlaut, (b) deine "
                    "Lesung am Scan und (c) wie sicher du bist. Verwende [?], wenn die "
                    "Stelle offen bleibt."),
            response={"mode": "table", "columns": ["OCR", "Lesung am Scan", "Sicherheit"],
                      "rows": 3},
            cognitive_level="analyze", dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"}],
            est_minutes=10,
            answer_key=("Erwartet: drei nachvollziehbare Vergleiche direkt am Scan, z. B. "
                        "OCR „Bald find es fünfundzwanzig Jahre“ → Lesung „sind“; OCR "
                        "„wahrhast kaiserlichen Schutze“ → Lesung „wahrhaft“; OCR „stimmten "
                        "begeistert em“ → Lesung „ein“. Korrekt ist nur eine Lesung, die "
                        "das Seitenbild trägt; Unsicherheit darf und soll mit [?] markiert "
                        "werden."),
            watch_outs=["Keine stillen OCR-Korrekturen akzeptieren: Scanbeleg oder [?]."],
        ),
        TaskBlock(
            id="anno2.t3", kind="source_analysis",
            prompt=("Untersuche den Standort des Redners: Wer spricht hier, zu wem, bei "
                    "welchem Anlass? Wem schreibt die Rede die Veränderungen Wiens zu? "
                    "Belege mit mindestens zwei Formulierungen aus dem Text und erkläre, "
                    "wie Anlass und Sprecherrolle das Urteil der Rede prägen."),
            response={"mode": "lines", "n": 7}, cognitive_level="analyze",
            dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.09", "relation": "exercises"}],
            est_minutes=10,
            answer_key=("Der Bürgermeister von Wien spricht bei der festlichen Eröffnung "
                        "direkt zum Kaiser. Alle Veränderungen erscheinen als dessen "
                        "persönliches Verdienst: seine „erleuchtete Entschließung“, seine "
                        "„hochherzige Fürsorge und Munificenz“, die Stadt „treu ergeben“. "
                        "Standortgebundenheit: Eine loyale Stadtspitze bei einem Festakt "
                        "vor dem Herrscher lobt — Kritik oder Abwägung sind in dieser "
                        "Sprechsituation nicht zu erwarten."),
        ),
        TaskBlock(
            id="anno2.t4", kind="open_response",
            prompt=("Formuliere ein Quellenurteil (8–10 Sätze): Was belegt dieser Auszug "
                    "über die öffentliche Feier von Fortschritt und Kaisertreue im Jahr "
                    "1873 — und was können wir aus dieser einen, festlichen Stimme NICHT "
                    "verlässlich ableiten? Belege zweimal am Wortlaut oder Seitenbild."),
            response={"mode": "box", "min_height_mm": 60}, cognitive_level="evaluate",
            dimensions=["HME", "HOR"],
            serves=[{"competence_id": "GPB.US.3.ALL.03", "relation": "exercises"},
                    {"competence_id": "GPB.US.3.ALL.09", "relation": "exercises"}],
            est_minutes=14,
            acceptable_reasoning=("Erwartet: Die Quelle belegt, WIE Fortschritt öffentlich "
                                  "inszeniert wurde — als kaiserliche Wohltat und "
                                  "Friedenswerk („der Fortschritt Gemeingut werde“, „Gott "
                                  "segne, Gott schütze, Gott erhalte“). Sie belegt NICHT, "
                                  "wie die Bevölkerung dachte, was das Unternehmen kostete "
                                  "oder ob alle die Begeisterung teilten. Zwei konkrete "
                                  "Belege + klare Reichweitenbegrenzung."),
        ),
    ]
    return WorksheetContent(
        meta=meta, subject_model=store.get_subject_model(SUBJECT), intro=intro,
        sections=[Baustein(
            id="anno2.quelle", title="Die offizielle Stimme lesen",
            teacher_overview={
                "throughline": ("Die Gegenstimme zur 1871er-Leitartikel-Quellenarbeit: hier "
                                "spricht der feierliche, loyale Amtston. Die Quelle belegt "
                                "die Inszenierung von Fortschritt und Kaisertreue — nicht "
                                "die Stimmung der Stadt. Standort erkennen, Reichweite "
                                "begrenzen."),
                "talking_points": [
                    "OCR-Fehler sind Methode, kein Defekt: Sie erzwingen den Blick auf den Scan.",
                    "Eine Festrede lobt — das ist keine Schwäche der Quelle, sondern ihre "
                    "Eigenschaft: Sie zeigt, wie öffentliche Loyalität klingen sollte.",
                    "Stark im Paar mit dem oppositionellen Leitartikel von 1871: gleiche "
                    "Epoche, entgegengesetzter Standort.",
                ],
                "timing_notes": ("Einzel- bis Doppelstunde; Internetzugang für das "
                                 "ANNO-Digitalisat nötig."),
            },
            blocks=tasks,
        )],
    )
