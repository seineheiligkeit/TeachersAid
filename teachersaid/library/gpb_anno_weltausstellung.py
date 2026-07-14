"""Self-contained GPB Quellenarbeit #2: the official voice (Wiener Zeitung, 1873).

The counterpart to ``gpb_anno_quellenarbeit`` (the oppositional 1871 Leitmeritzer Leitartikel):
here the class reads the CELEBRATORY official register — the Wiener Zeitung's report on the
opening of the 1873 Weltausstellung, printing the Vienna mayor's address to the emperor.  Same
discipline, now SELF-CONTAINED: the line-numbered OCR excerpt is embedded as a ``source_text``
block and a scan crop of the matching page region as a sourced raster, so the OCR-Prüfung and the
source determination happen on the sheet.  External ANNO navigation is enrichment, never a task
dependency (*referenced-only is a rights fallback, not a didactic mode*).  Both are Public Domain
Mark (ÖNB-Labs subset); the same OCR text is redistributed in the DEU twin
``deu-anno-weltausstellung-1873``.

Aufgabe 1 no longer restates the intro (the SME's „copy-paste“ note): page 3 carries no masthead,
so t1 shifts fully onto the student's OWN determination FROM the source (speaker/addressee via the
salutation in Zeile 4–5; Quelle vs. Darstellung), and the intro no longer names who speaks.

``OCR_EXCERPT`` is byte-locked against ``runs/ingest/texts_src/anno-weltausstellung-1873.json``.
The scan crop is ``runs/anno/gpb-anno-weltausstellung-1873-crop.json`` (region 60,1869,1089,1012
of the 3104×4534 page); the binary is rebuilt with ``tools/fetch_anno.py --rehydrate``.
"""
from __future__ import annotations

from . import anno_common as anno
from ..grounding import lehrplan_store as store
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

SUBJECT = "Geschichte und politische Bildung"
KLASSE = 3
CROP_ID = "gpb-anno-weltausstellung-1873-crop"
CROP_SHA1 = "f5e4e01ebc6fd6cbd3bcb22b0753e18ac365aaa8"
RETRIEVED = "2026-07-12"                                  # OCR fetch (texts_src record)
# The human ANNO viewer page (HTML, unlike the IIIF canvas which returns JSON):
ANNO_VIEWER = anno.viewer_url("wrz", "18730502", 3)

# Verbatim OCR excerpt (physical lines 34–81 of page 3), byte-locked against the tracked source
# record.  OCR errors preserved on purpose — e.g. „Bald find es“ (Z. 6) for „sind“, the object
# of the OCR-Prüfung.
OCR_EXCERPT = """Die gleiche Danksagung sprach der Bürgermeister
von Wien im Namen der Reichshaupt- und Residenz
stadt folgendermaßen aus:
„Eu. Majestät!
Allergnädigster Herr!
„Bald find es fünfundzwanzig Jahre, daß Eu.
k. und k. Majestät auf dem angestammten Throne
Ihrer erlauchten Ahnen das Scepter über die
Völker Oesterreichs führen.
Dankbar verzeichnen es die Annalen, daß in
diesem Zeitlaufe die Gemeindeautonomie erhalten,
daß unter der Regierung Eu. Majestät Wien im
raschen, zuvor nie geahnten Aufschwünge zur Welt
stadt geworden.
Es war erleuchtete Entschließung Eu. Majestät,
die die Stadtwälle fallen ließ, es war Eu. Maje
stät hochherzige Fürsorge und Munificenz, durch
welche großartige Werke ins Leben gerufen wurden,
die der öffentlichen Wohlfahrt, dem Gedeihen des
Gemeinwesens in allen Richtungen gewidmet,
Zeugen der thatkräftigen Bestrebungen der Gegen
wart sind und für kommende Jahrhunderte ehrende
Denkmale bleiben werden des segensreichen Waltens
Eu. Majestät.
In dieser feierlichen Stunde verleihen Eu. Ma
jestät die höchste Weihe einem Unternehmen, das
die edle Bestimmung hat, in diesen Räumen zusam
mengefaßt zu zeigen, was menschlicher Geist, was
menschliche Kraft, was Wissenschaft und Kunst unter
allen Himmelsstrichen zu schaffen vermag, auf daß
der Fortschritt Gemeingut werde, sich nähre und
fördere durch das Zusammenwirken Aller, durch den
Wettkampf der Erfindung und Fertigkeit, durch die
Segnungen des Völkerfriedens.
Die erhabene Schöpfung Eu. Majestät wird die
Culturgeschichte Oesterreichs verewigen.
Zu allen Zeiten treu ergeben festhaltend an
Dynastie und Reich, fühlt sich Wien, dem es be-
schieden ist, Besucher aus allen Welttheilen inner
halb seines Weichbildes gastlich willkommen zu.
heißen, heute stolzer und gehobener denn je, unter
dem huldvollen, wahrhast kaiserlichen Schutze Eu.
Majestät, und dankbewegt tönt ans Aller Herzen:

Gott segne, Gott schütze, Gott erhalte Eu. Ma
jestät! Unser Kaiser Franz Joseph hoch! hoch!
hoch!"
Die Anwesenden stimmten begeistert em."""


def build_content() -> WorksheetContent:
    meta = WorksheetMeta(
        title="Fortschritt als Festrede: Quellenarbeit in ANNO",
        subtitle="Eine Wiener Zeitungsseite vom Mai 1873 als Quelle lesen",
        subject=SUBJECT, stufe="Unterstufe", klasse=KLASSE,
        kernfrage="Wessen Verdienst ist der Fortschritt — und wer sagt das hier?",
        fassung=store.get_fassung(),
        lehrplan_label="Geschichte und politische Bildung · 3. Klasse · Quellenarbeit",
    )
    intro = [anno.ocr_callout(), anno.procedure_block()]

    source_blocks = [
        InfoBlock(
            id="anno2.scan", kind="figure",
            content=("1873 wurde in Wien die Weltausstellung eröffnet — ein großes Fest des "
                     "technischen Fortschritts. Oben der Originalscan der Zeitungsseite "
                     "(Ausschnitt), darunter der maschinell erkannte Text (OCR) mit "
                     "Zeilennummern. Der Scan zeigt Zeile 1–15 des Auszugs."),
            asset_refs=[CROP_ID],
        ),
        InfoBlock(
            id="anno2.auszug", kind="source_text", content=OCR_EXCERPT, numbered=True,
            teacher_note=("Maschinelle OCR, ungeprüft (Public Domain Mark, ÖNB Labs/ANNO). Der "
                          "Wortlaut ist unverändert — die Lesefehler (z. B. „find“ statt „sind“, "
                          "Z. 6) sind Absicht und Gegenstand von Aufgabe 2."),
            provenance=anno.excerpt_provenance(
                title="Eröffnung der Weltausstellung: Ansprache des Bürgermeisters",
                publisher=f"Wiener Zeitung, 2. Mai 1873, S. 3 · {anno.REPOSITORY}",
                viewer=ANNO_VIEWER, retrieved=RETRIEVED),
        ),
        anno.digitalisat_block(block_id="anno2.digitalisat", viewer=ANNO_VIEWER,
                               retrieved=RETRIEVED),
    ]

    tasks = [
        TaskBlock(
            id="anno2.t1", kind="source_analysis",
            prompt=("Bestimme die Quelle aus dem Auszug selbst (nicht aus dem Titel des Blattes): "
                    "(a) Wer hält diese Rede, und an wen richtet er sie? Belege mit Zeile 1–5. "
                    "(b) Warum ist dieser Auszug eine Quelle von 1873 und keine spätere "
                    "Darstellung? Nenne zwei Merkmale."),
            response={"mode": "lines", "n": 5}, cognitive_level="understand",
            dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"},
                    {"competence_id": "GPB.US.3.ALL.07", "relation": "exercises"}],
            est_minutes=8,
            answer_key=("(a) Der Bürgermeister von Wien (Zeile 1–2) spricht direkt zum Kaiser — die "
                        "Anrede „Eu. Majestät! Allergnädigster Herr!“ (Zeile 4–5) zeigt es. "
                        "(b) Quelle: 1873, zur Zeit des Ereignisses entstanden; abgedruckt ist der "
                        "zeitgenössische Wortlaut einer feierlichen Ansprache (Festrede), keine "
                        "spätere, einordnende Zusammenfassung."),
            watch_outs=["Die Textsorte steht schon im Titel des Blattes — gewürdigt wird, dass "
                        "die Klasse Sprecher, Adressat und Quelle/Darstellung AM WORTLAUT belegt, "
                        "nicht bloß benennt."],
        ),
        TaskBlock(
            id="anno2.t2", kind="source_analysis",
            prompt=("OCR-Prüfung: Vergleiche Zeile 1–15 des Auszugs (OCR) mit dem Scanausschnitt. "
                    "An einer Stelle hat der Computer sicher falsch gelesen — finde sie und "
                    "notiere (a) den OCR-Wortlaut mit Zeile, (b) was am Scan steht, (c) deine "
                    "Sicherheit. Prüfe außerdem: Stimmen die übrigen Zeilen mit dem Scan überein?"),
            response={"mode": "table", "columns": ["OCR (mit Zeile)", "Lesung am Scan", "Sicherheit"],
                      "rows": 3},
            cognitive_level="analyze", dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"}],
            est_minutes=10,
            answer_key=("Sichere Fehlstelle: „Bald find es“ (Z. 6) → am Scan steht „Bald sind es“ "
                        "(das lange ſ der Fraktur wurde als f gelesen). Die übrigen Zeilen 1–15 "
                        "stimmen weitgehend mit dem Scan überein — wichtig ist, dass geprüft und "
                        "nicht blind übernommen wird. Weitere Fehler stehen später im Auszug (z. B. "
                        "„wahrhast“ Z. 42 → „wahrhaft“; „em“ Z. 47 → „ein“)."),
            watch_outs=["Keine stillen OCR-Korrekturen akzeptieren: Scanbeleg oder [?].",
                        "Dass die meisten Zeilen stimmen, ist ein gültiges Prüfergebnis — die "
                        "Haltung „prüfen statt glauben“ ist das Lernziel."],
        ),
        TaskBlock(
            id="anno2.t3", kind="source_analysis",
            prompt=("Untersuche den Standort des Redners: Wem schreibt die Rede alle "
                    "Veränderungen Wiens zu? Belege mit zwei Wendungen aus dem Text (z. B. "
                    "Zeile 15 und Zeile 17) und erkläre, wie Anlass und Sprecherrolle das Urteil "
                    "der Rede prägen."),
            response={"mode": "lines", "n": 7}, cognitive_level="analyze",
            dimensions=["HME"],
            serves=[{"competence_id": "GPB.US.3.ALL.09", "relation": "exercises"}],
            est_minutes=10,
            answer_key=("Alle Veränderungen erscheinen als persönliches Verdienst des Kaisers: "
                        "seine „erleuchtete Entschließung“ (Z. 15), seine „hochherzige Fürsorge "
                        "und Munificenz“ (Z. 17); Wien ist ihm „treu ergeben“ (Z. 37). "
                        "Standortgebundenheit: Eine loyale Stadtspitze bei einem Festakt vor dem "
                        "Herrscher lobt — Kritik oder Abwägung sind in dieser Sprechsituation "
                        "nicht zu erwarten."),
        ),
        TaskBlock(
            id="anno2.t4", kind="open_response",
            prompt=("Formuliere ein Quellenurteil (8–10 Sätze): Was belegt dieser Auszug über die "
                    "öffentliche Feier von Fortschritt und Kaisertreue im Jahr 1873 — und was "
                    "können wir aus dieser einen, festlichen Stimme NICHT verlässlich ableiten? "
                    "Belege zweimal am Wortlaut (mit Zeilennummer) oder am Scan."),
            response={"mode": "box", "min_height_mm": 60}, cognitive_level="evaluate",
            dimensions=["HME", "HOR"],
            serves=[{"competence_id": "GPB.US.3.ALL.03", "relation": "exercises"},
                    {"competence_id": "GPB.US.3.ALL.09", "relation": "exercises"}],
            est_minutes=14,
            acceptable_reasoning=("Erwartet: Die Quelle belegt, WIE Fortschritt öffentlich "
                                  "inszeniert wurde — als kaiserliche Wohltat und Friedenswerk "
                                  "(„der Fortschritt Gemeingut werde“, Z. 31; „Gott segne, Gott "
                                  "schütze, Gott erhalte“, Z. 44). Sie belegt NICHT, wie die "
                                  "Bevölkerung dachte, was das Unternehmen kostete oder ob alle "
                                  "die Begeisterung teilten. Zwei konkrete Belege + klare "
                                  "Reichweitenbegrenzung."),
        ),
    ]

    return WorksheetContent(
        meta=meta, subject_model=store.get_subject_model(SUBJECT), intro=intro,
        sections=[Baustein(
            id="anno2.quelle", title="Die offizielle Stimme lesen",
            teacher_overview={
                "throughline": ("Die Gegenstimme zur 1871er-Leitartikel-Quellenarbeit: hier "
                                "spricht der feierliche, loyale Amtston. Die Quelle belegt die "
                                "Inszenierung von Fortschritt und Kaisertreue — nicht die Stimmung "
                                "der Stadt. Standort erkennen, Reichweite begrenzen."),
                "talking_points": [
                    "OCR-Fehler sind Methode, kein Defekt: Sie erzwingen den Blick auf den Scan "
                    "(„find“ statt „sind“, Z. 6).",
                    "Eine Festrede lobt — das ist keine Schwäche der Quelle, sondern ihre "
                    "Eigenschaft: Sie zeigt, wie öffentliche Loyalität klingen sollte.",
                    "Stark im Paar mit dem oppositionellen Leitartikel von 1871: gleiche Epoche, "
                    "entgegengesetzter Standort. Alles Nötige ist auf dem Blatt; der ANNO-Link ist "
                    "freiwillige Weiterführung.",
                ],
                "timing_notes": "Einzel- bis Doppelstunde; kein Internetzugang nötig.",
            },
            blocks=source_blocks + tasks,
        )],
        assets=[anno.scan_crop_asset(
            crop_id=CROP_ID, sha1=CROP_SHA1,
            caption="Wiener Zeitung, 2. Mai 1873, S. 3 — Scanausschnitt (Zeile 1–15)",
            viewer=ANNO_VIEWER,
            depicts="Anrede und Zeile 1–15 der Ansprache")],
    )
