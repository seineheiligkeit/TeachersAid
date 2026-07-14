"""Self-contained GPB Quellenarbeit #1: the oppositional 1871 Leitmeritzer Leitartikel.

The historical newspaper expression is EMBEDDED here (not merely referenced): the line-numbered
OCR excerpt as a ``source_text`` block and a scan crop of the matching page region as a sourced
raster.  So the OCR-Prüfung (compare the machine text against the Fraktur scan) and the reading
work happen entirely on the sheet — external ANNO navigation is enrichment, never a dependency
(*referenced-only is a rights fallback, not a didactic mode*).  Both are Public Domain Mark (the
ÖNB-Labs subset), so embedding is fully rights-clear; the same OCR text is redistributed in the
staged DEU twin ``deu-anno-lehrertag-1871``.

``OCR_EXCERPT`` is byte-locked against ``runs/ingest/texts_src/anno-lehrertag-1871.json`` (the
verbatim ``alto_to_text`` output, OCR errors and all) by ``tests/test_gpb_anno_quellenarbeit.py``.
The scan crop is ``runs/anno/gpb-anno-lehrertag-1871-crop.json`` (region 66,1397,1001,837 of the
2819×3788 page); its binary is rebuilt with ``tools/fetch_anno.py --rehydrate``.
"""
from __future__ import annotations

from . import anno_common as anno
from ..grounding import lehrplan_store as store
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

SUBJECT = "Geschichte und politische Bildung"
KLASSE = 3
CROP_ID = "gpb-anno-lehrertag-1871-crop"
CROP_SHA1 = "ccde3559184e453d10ec9b1d624f84e313eb2891"
RETRIEVED = "2026-07-11"                                  # OCR fetch (texts_src record)
# The human ANNO viewer page (HTML, unlike the IIIF canvas which returns JSON):
ANNO_VIEWER = anno.viewer_url("lmz", "18710902", 1)

# Verbatim OCR excerpt (physical lines 41–87 of page 1), byte-locked against the tracked source
# record.  OCR errors are preserved on purpose — they are the object of the OCR-Prüfung.
OCR_EXCERPT = """Zum zweiten deutsch-böhmischen Lehrer
tage in Leitmeritz.
Führwahr in ! einer verzweifelten Lage be-
finde» sich die Liberalen Oesterreichs. Von allen
Seiten wilder denn je angegriffen, müssen sie mit
dem Aufgebot aller ihrer Kräfte den "andrängenden
Feinden festen Widerstand M leisten suchen; mit
vereinten Kräften müssen sie ihre Rechte nnd Frei
heiten vor den heraustürmenden Fluten der Reaktion
zu retten suchen.' Nicht genng daran, daß der
Föderalismus das Band, welches alle Völker
Oesterreichs bis jetzt zn einem großen Ganzen
umschlang, freventlich zerreißt, die Einheit der
Monarchie in winzige Theile zerlegt, das Werk, zu
dessen Vollendung die Deutscheu ein Jahrtausend
hindurch dem Kaiser und . Reich zu Liebe ihre
besten Kräfte eingesetzt haben, zum Spielball na
tionaler i Launeu macht/ das stolze Schiff Oester
reich, dem selbst die gewaltigen Stürme des 19.

Jahrhunderts nichts anzuhaben veimochten, ziim
mast- und ruderlosen Wrak gestaltet, das gar
leicht vou einer kleinen Welle auf dem Meere
der politischen EreignM an ten Fels der Ver
nichtung geschlendert werden kann, — nicht gcnng
an allen dem sucht auch noch derUltiamontan'smn's
mit der Gier des nach Nahrung lüsternen Geiers
seine Krallen in den Leib des armen vielgeqnälten
Oesterreichs einzuhacken, sucht auch der auf
allen Punkten geschlagene JesnitismnS Oesterreich
znm letzten Bollwerk seiner Vertheidigung5Iinie zu
machen.
' - Und doch 'wollen wir nicht verzagen!
Mit dem Muthe der Männer,^ die ihr Hei
ligstes bis auf den Tod zu vertheidigen wissen,
wollen wir in den Kamps gegen diese Feinde des
Reiches ziehen, — wollen ihnen zeigen,, daß
der Geist der Freiheit und des Lichts, der zugleich
der Geist unseres Jahrhunderts ist, sich nicht nn-
gestrast verhöhnen läßt, daß der Liberalismus eiu
Segen für seine Jünger, eine »ubcnmherzige Pcilsche
für seine Gegner ist, daß im Geiste 'des Fort
schrittes und der Bildung eine Titanenkraft
liegt, die die Finsterlinge auf Nimmerwiederans-
steheii zu zerschmettern vermag. Groß ist die
Arbeit, groß aber auch t er "Sieg, den keine
Macht der Welt nnS entreißen kann."""


def build_content() -> WorksheetContent:
    meta = WorksheetMeta(
        title="Zeitung als politische Waffe? Quellenarbeit in ANNO",
        subtitle="Seitenbild, OCR und Perspektive eines Leitartikels von 1871",
        subject=SUBJECT, stufe="Unterstufe", klasse=KLASSE,
        kernfrage="Wie macht politische Sprache aus einer Meinung einen dringenden Aufruf?",
        fassung=store.get_fassung(),
        lehrplan_label="Geschichte und politische Bildung · 3. Klasse · Quellenarbeit",
    )
    intro = [anno.ocr_callout(), anno.procedure_block()]

    source_blocks = [
        InfoBlock(
            id="anno.scan", kind="figure",
            content=("Oben der Originalscan der Zeitungsseite (Ausschnitt), darunter der "
                     "maschinell erkannte Text (OCR) mit Zeilennummern. Der Scan zeigt Zeile "
                     "1–15 des Auszugs."),
            asset_refs=[CROP_ID],
        ),
        InfoBlock(
            id="anno.auszug", kind="source_text", content=OCR_EXCERPT, numbered=True,
            teacher_note=("Maschinelle OCR, ungeprüft (Public Domain Mark, ÖNB Labs/ANNO). Der "
                          "Wortlaut ist unverändert — die Lesefehler sind Absicht und der "
                          "Gegenstand von Aufgabe 2. Historische Rechtschreibung bleibt erhalten."),
            provenance=anno.excerpt_provenance(
                title="Zum zweiten deutsch-böhmischen Lehrertage in Leitmeritz",
                publisher=f"Leitmeritzer Zeitung, 2. September 1871, S. 1 · {anno.REPOSITORY}",
                viewer=ANNO_VIEWER, retrieved=RETRIEVED),
        ),
        anno.digitalisat_block(block_id="anno.digitalisat", viewer=ANNO_VIEWER,
                               retrieved=RETRIEVED),
    ]

    tasks = [
        TaskBlock(
            id="anno.t1", kind="source_analysis",
            prompt=("Arbeite am Scanausschnitt (nicht an der OCR): (a) Lies die Überschrift des "
                    "Artikels in der Frakturschrift und schreibe sie in heutiger Schrift ab. "
                    "(b) Der Auszug ist eine Quelle, keine spätere Darstellung. Begründe das mit "
                    "zwei Merkmalen (denke an das Erscheinungsjahr und daran, wer hier schreibt)."),
            response={"mode": "lines", "n": 5}, cognitive_level="understand",
            dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"}],
            est_minutes=8,
            answer_key=("(a) „Zum zweiten deutsch-böhmischen Lehrertage in Leitmeritz.“ "
                        "(b) Quelle: Der Text entstand 1871, also zur Zeit selbst (zeitgenössisches "
                        "Zeugnis); er ist ein Leitartikel — eine wertende Stimme von damals, keine "
                        "spätere, einordnende Zusammenfassung wie ein Schulbuchtext."),
            watch_outs=["Kern ist das Fraktur-Lesen am Scan + die Unterscheidung Quelle/"
                        "Darstellung — nicht das Abschreiben der Quellenangabe (die steht schon "
                        "unter dem Auszug)."],
        ),
        TaskBlock(
            id="anno.t2", kind="source_analysis",
            prompt=("OCR-Prüfung: Vergleiche Zeile 1–15 des Auszugs (OCR) mit dem Scanausschnitt. "
                    "Finde drei Stellen, an denen die OCR falsch gelesen hat. Notiere je (a) den "
                    "OCR-Wortlaut mit Zeilennummer, (b) was am Scan wirklich steht, (c) wie sicher "
                    "du bist. Verwende [?], wenn eine Stelle offen bleibt."),
            response={"mode": "table", "columns": ["OCR (mit Zeile)", "Lesung am Scan", "Sicherheit"],
                      "rows": 3},
            cognitive_level="analyze", dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"}],
            est_minutes=10,
            answer_key=("Klare Beispiele in Zeile 1–15: „nnd“ (Z. 8) → „und“; „genng“ (Z. 10) → "
                        "„genug“; „zn“ (Z. 12) → „zu“; „finde»“ (Z. 4) → „finden“; „Deutscheu“ "
                        "(Z. 15) → „Deutschen“. Korrekt ist nur eine Lesung, die das Seitenbild "
                        "trägt; Unsicherheit darf und soll mit [?] markiert werden. Maßgeblich ist "
                        "der gedruckte Wortlaut, nicht die moderne Rechtschreibung."),
            watch_outs=["Keine stillen OCR-Korrekturen akzeptieren: Scanbeleg oder [?].",
                        "Die Fraktur nutzt ein langes ſ, das die OCR oft als f verliest — ein "
                        "guter Prüf-Reflex."],
        ),
        TaskBlock(
            id="anno.t3", kind="source_analysis",
            prompt=("Untersuche zwei Bildfelder des Leitartikels im gedruckten Auszug: "
                    "(a) Österreich als „stolze Schiff“ (Zeile 18), das zum „mast- und ruderlosen "
                    "Wrak“ (Zeile 21) werde; (b) die politischen Gegner als „nach Nahrung "
                    "lüsternen Geiers“ mit „Krallen“ (Zeile 26). Was bewirken diese Bilder bei "
                    "den Leserinnen und Lesern?"),
            response={"mode": "lines", "n": 6}, cognitive_level="analyze",
            dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.07", "relation": "exercises"}],
            est_minutes=10,
            answer_key=("Schiff/Wrack: dramatisiert den staatlichen Zerfall und die fehlende "
                        "Steuerung (aus dem stolzen Schiff wird ein steuerloses Wrack). "
                        "Geier/Krallen: entmenschlicht die politischen Gegner und stellt sie als "
                        "räuberische Bedrohung dar. Beide Bilder emotionalisieren und mobilisieren "
                        "— aus einer Meinung wird ein dringender Aufruf."),
        ),
        TaskBlock(
            id="anno.t4", kind="open_response",
            prompt=("Formuliere ein Quellenurteil (8–10 Sätze): Was erfahren wir aus diesem "
                    "Artikel über politische Kommunikation im Jahr 1871 — und was können wir aus "
                    "dieser einen, parteilichen Stimme NICHT verlässlich ableiten? Belege zweimal "
                    "am Wortlaut (mit Zeilennummer) oder am Scan."),
            response={"mode": "box", "min_height_mm": 60}, cognitive_level="evaluate",
            dimensions=["HME", "HOR"],
            serves=[{"competence_id": "GPB.US.3.ALL.03", "relation": "exercises"},
                    {"competence_id": "GPB.US.3.ALL.07", "relation": "exercises"}],
            est_minutes=14,
            acceptable_reasoning=("Erwartet: Die Quelle zeigt eine stark wertende liberale "
                                  "Perspektive und politische Mobilisierung durch Metaphern und "
                                  "Wir-Form. Sie belegt NICHT, wie alle Menschen dachten oder wie "
                                  "die politische Lage objektiv war. Zwei konkrete Belege (Zeile "
                                  "oder Scan) + eine klare Reichweitenbegrenzung."),
        ),
    ]

    return WorksheetContent(
        meta=meta, subject_model=store.get_subject_model(SUBJECT), intro=intro,
        sections=[Baustein(
            id="anno.quelle", title="Vom Seitenbild zum Quellenurteil",
            teacher_overview={
                "throughline": ("Nicht der OCR glauben und die Quelle nicht verwerfen: Scan und "
                                "Maschinentext gegeneinander prüfen, die Perspektive am Wortlaut "
                                "belegen, die Reichweite des Quellenurteils begrenzen."),
                "talking_points": [
                    "OCR-Fehler sind hier Methode, kein Defekt: Sie zwingen zum Blick auf den Scan "
                    "(das lange ſ der Fraktur → oft als f verlesen).",
                    "Perspektivität ist keine Widerlegung; sie ist eine Eigenschaft, die man "
                    "untersucht — hier über die Schiff-/Wrack- und Geier-Metaphern.",
                    "Alles, was die Klasse braucht, ist auf dem Blatt: der Scanausschnitt und der "
                    "vollständige OCR-Auszug. Der ANNO-Link ist freiwillige Weiterführung.",
                ],
                "timing_notes": "Einzel- bis Doppelstunde; kein Internetzugang nötig.",
            },
            blocks=source_blocks + tasks,
        )],
        assets=[anno.scan_crop_asset(
            crop_id=CROP_ID, sha1=CROP_SHA1,
            caption="Leitmeritzer Zeitung, 2. September 1871, S. 1 — Scanausschnitt (Zeile 1–15)",
            viewer=ANNO_VIEWER,
            depicts="Überschrift und Zeile 1–15 des Leitartikels")],
    )
