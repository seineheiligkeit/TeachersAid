"""Curated annotated authentic texts (the Deutsch asset library).

Hand-curated flagship `AnnotatedText`s — a real, rights-cleared text + a vetted annotation
layer from which `pipeline/text_tasks` derives a worksheet. The seed pair shows both core
Lehrplan angles: a literary text (Lesen · Stilmittel · Interpretation) and a media text
(Medienkompetenz · how a text persuades). Texts are *selected* from real public-domain
sources (cited), never authored; answers live in the annotations (correct by curation).
"""

from __future__ import annotations

from ..schema.blocks import Serves
from ..schema.texts import AnnotatedText, Annotation, TextSourceRef

# --- literary flagship: Heine, "Die Lore-Ley" (Heine d. 1856 → PD) -----------
_LORELEY = """Ich weiß nicht, was soll es bedeuten,
Dass ich so traurig bin;
Ein Märchen aus alten Zeiten,
Das kommt mir nicht aus dem Sinn.

Die Luft ist kühl und es dunkelt,
Und ruhig fließt der Rhein;
Der Gipfel des Berges funkelt
Im Abendsonnenschein.

Die schönste Jungfrau sitzet
Dort oben wunderbar;
Ihr goldnes Geschmeide blitzet,
Sie kämmt ihr goldenes Haar.

Sie kämmt es mit goldenem Kamme
Und singt ein Lied dabei;
Das hat eine wundersame,
Gewaltige Melodei.

Den Schiffer im kleinen Schiffe
Ergreift es mit wildem Weh;
Er schaut nicht die Felsenriffe,
Er schaut nur hinauf in die Höh.

Ich glaube, die Wellen verschlingen
Am Ende Schiffer und Kahn;
Und das hat mit ihrem Singen
Die Lore-Ley getan."""

LORELEY = AnnotatedText(
    id="deu-loreley", title="Die Lore-Ley", subject="Deutsch", klasse=3,
    genre="Gedicht (Ballade)", textsorte="Gedicht", text=_LORELEY,
    source=TextSourceRef(
        author="Heinrich Heine", title="Die Lore-Ley", year="1824",
        author_death_year=1856, rights_basis="public_domain_pma",
        repository="Wikisource", url="https://de.wikisource.org/wiki/Die_Lorelei",
        attribution="Heinrich Heine, „Die Lore-Ley“ (1824); gemeinfrei (Wikisource)."),
    serves=[Serves(competence_id="DEU.US.3.LES.02", relation="exercises"),
            Serves(competence_id="DEU.US.3.LES.01", relation="exercises"),
            Serves(competence_id="DEU.US.3.SCH.01", relation="exercises")],
    keywords=["Gedicht", "Ballade", "Stilmittel", "Interpretation", "Heine", "Loreley", "Rhein"],
    annotations=[
        Annotation(kind="vocab", label="Geschmeide", answer="(wertvoller) Schmuck"),
        Annotation(kind="vocab", label="Felsenriffe", answer="gefährliche Felsen im/unter Wasser"),
        Annotation(kind="vocab", label="Kahn", answer="kleines (Ruder-)Boot"),
        Annotation(kind="vocab", label="Melodei", answer="ältere Form von „Melodie“"),
        Annotation(kind="comprehension", zeile="1-4",
                   label="Wie fühlt sich das lyrische Ich am Anfang, und was lässt es nicht los?",
                   answer="Es ist traurig/schwermütig und weiß nicht genau warum; ein „Märchen "
                          "aus alten Zeiten“ geht ihm nicht aus dem Sinn.",
                   cognitive_level="understand"),
        Annotation(kind="comprehension", zeile="9-16",
                   label="Wer sitzt oben auf dem Berg, und was tut sie?",
                   answer="Die schönste Jungfrau (die Lore-Ley); sie kämmt ihr goldenes Haar "
                          "und singt dabei ein wundersames, gewaltiges Lied.",
                   cognitive_level="understand"),
        Annotation(kind="comprehension", zeile="17-24",
                   label="Was geschieht am Ende mit dem Schiffer – und wodurch?",
                   answer="Er achtet nicht auf die Felsen, sondern blickt nur nach oben; die "
                          "Wellen verschlingen Schiffer und Kahn. Schuld ist der Gesang der Lore-Ley.",
                   cognitive_level="understand"),
        Annotation(kind="stilmittel", zeile="11-13", span="goldnes … goldenes … goldenem",
                   label="Wiederholung des Wortes „golden“",
                   answer="Das wiederholte „golden“ (Leitwort) hebt die kostbare, betörende "
                          "Schönheit der Lore-Ley hervor und macht sie unwiderstehlich.",
                   cognitive_level="analyze", dimensions=["SPR"]),
        Annotation(kind="stilmittel", zeile="15-16", span="wundersame, / Gewaltige Melodei",
                   label="Steigernde Adjektive („wundersam“, „gewaltig“)",
                   answer="Die Adjektive steigern die unheimliche Macht des Liedes – seine Wirkung "
                          "ist nicht nur schön, sondern überwältigend und gefährlich.",
                   cognitive_level="analyze", dimensions=["SPR"]),
        Annotation(kind="erwartungshorizont", zeile="17-24",
                   label="Deute, warum der Schiffer untergeht. Welche Rolle spielt die Lore-Ley?",
                   answer="Der Schiffer wird vom Gesang und der Schönheit der Lore-Ley so gefesselt, "
                          "dass er die Gefahr (die Felsen) nicht mehr beachtet. Die Lore-Ley steht für "
                          "eine verführerische, todbringende Schönheit; das Märchenhafte (Z. 3) deutet "
                          "ihre unheimliche Macht von Beginn an an.",
                   cognitive_level="evaluate", dimensions=["LES"]),
        Annotation(kind="erwartungshorizont",
                   label="Schreibe einen kurzen Tagebucheintrag (8–10 Sätze) aus der Sicht des "
                         "Schiffers, kurz bevor sein Boot kentert.",
                   answer="Erwartet: durchgehende Ich-Perspektive; die Faszination durch Gesang/Anblick; "
                          "das Verdrängen der Gefahr; stimmige, bildhafte Sprache; Tagebuch-Merkmale "
                          "(Anrede/Datum, Gefühle).",
                   cognitive_level="create", dimensions=["SCH"]),
    ],
)

# --- media/persuasion flagship: Lessing, "Der Rabe und der Fuchs" (d. 1781 → PD) ---
# A fable whose *content is persuasion itself* (the fox flatters to manipulate) — the
# Unterstufe bridge to Medienkompetenz. A real newspaper/advert text needs the ANNO
# fetch tool (OCR/scans); this proves the media_technique/argument annotations now.
_RABE_FUCHS = """Ein Rabe trug ein Stück vergiftetes Fleisch,
das der erzürnte Gärtner für die Katzen seines Nachbars hingeworfen hatte,
in seinen Klauen fort.
Und eben wollte er es auf einer alten Eiche verzehren,
als sich ein Fuchs herbeischlich und ihm zurief:
Sei mir gesegnet, Vogel des Jupiter!

Der Rabe erstaunte und freute sich innig, für einen Adler gehalten zu werden.
Ich muß, dachte er, den Fuchs aus diesem Irrthume nicht bringen.
Großmüthig dumm ließ er ihm also seinen Raub herabfallen und flog stolz davon.

Der Fuchs fing das Fleisch lachend auf und fraß es mit boshafter Freude.
Doch bald verkehrte sich die Freude in ein schmerzhaftes Gefühl;
das Gift fing an zu wirken, und er verreckte.

Möchtet Ihr Euch nie etwas Anderes als Gift erloben, verdammte Schmeichler!"""

RABE_FUCHS = AnnotatedText(
    id="deu-rabe-fuchs", title="Der Rabe und der Fuchs", subject="Deutsch", klasse=2,
    genre="Fabel", textsorte="Fabel", text=_RABE_FUCHS,
    source=TextSourceRef(
        author="Gotthold Ephraim Lessing", title="Der Rabe und der Fuchs (Fabeln, 2. Buch)",
        year="1759", author_death_year=1781, rights_basis="public_domain_pma",
        repository="Projekt Gutenberg-DE / Zeno.org",
        url="https://www.projekt-gutenberg.org/lessing/fragfabe/",
        attribution="G. E. Lessing, „Der Rabe und der Fuchs“ (Fabeln, 1759); gemeinfrei."),
    serves=[Serves(competence_id="DEU.US.2.LES.03", relation="exercises"),
            Serves(competence_id="DEU.US.2.LES.01", relation="exercises"),
            Serves(competence_id="DEU.US.2.SCH.03", relation="exercises")],
    keywords=["Fabel", "Lessing", "Schmeichelei", "Manipulation", "Medienkompetenz",
              "Werbung", "Überzeugen", "Moral"],
    annotations=[
        Annotation(kind="vocab", label="erzürnt", answer="sehr wütend"),
        Annotation(kind="vocab", label="verzehren", answer="(auf)essen"),
        Annotation(kind="vocab", label="herbeischlich", answer="kam heimlich/leise näher"),
        Annotation(kind="vocab", label="Schmeichler",
                   answer="jemand, der übertrieben lobt, um etwas zu erreichen"),
        Annotation(kind="comprehension", zeile="5-9",
                   label="Warum nennt der Fuchs den Raben „Vogel des Jupiter“ und behandelt ihn "
                         "wie einen Adler?",
                   answer="Er schmeichelt dem Raben, macht ihn stolz – damit der Rabe sich "
                          "geschmeichelt fühlt und das Fleisch fallen lässt.",
                   cognitive_level="understand"),
        Annotation(kind="comprehension", zeile="10-13",
                   label="Wie endet Lessings Fabel anders, als man es erwartet?",
                   answer="Das Fleisch war vergiftet: Der Fuchs frisst es und stirbt. Der "
                          "Schmeichler selbst kommt zu Schaden.",
                   cognitive_level="understand"),
        Annotation(kind="media_technique", zeile="6", span="Sei mir gesegnet, Vogel des Jupiter!",
                   label="Schmeichelei / übertriebenes Lob",
                   answer="Der Fuchs lobt den Raben maßlos (macht ihn zum Götter-Vogel/Adler), um "
                          "ihn zu manipulieren. Genau so schmeichelt Werbung den Käufer:innen "
                          "(„Nur für echte Kenner!“), um sie zu lenken.",
                   cognitive_level="evaluate", dimensions=["LES"]),
        Annotation(kind="argument_move", zeile="13",
                   label="Die Lehre (Moral) der Fabel",
                   answer="Hütet euch vor Schmeichlern: Wer auf übertriebenes Lob hereinfällt, "
                          "kann betrogen werden. Lessing verschärft die bekannte Fabel – nicht nur "
                          "der eitle Rabe, sondern der Schmeichler selbst wird bestraft.",
                   cognitive_level="analyze", dimensions=["LES"]),
        Annotation(kind="erwartungshorizont",
                   label="Wo begegnet dir Schmeichelei in Werbung oder sozialen Medien? Beschreibe "
                         "ein Beispiel (4–6 Sätze) und erkläre, wie es dich beeinflussen soll.",
                   answer="Erwartet: ein konkretes Beispiel (Werbeslogan, Influencer-Lob, „du hast "
                          "es dir verdient“); Benennen der Schmeichelei; Erklärung der "
                          "manipulativen Absicht (Kauf/Klick auslösen).",
                   cognitive_level="create", dimensions=["SCH"]),
    ],
)

ANNOTATED_TEXTS: list[AnnotatedText] = [LORELEY, RABE_FUCHS]


def find_text(text_id: str) -> AnnotatedText | None:
    return next((t for t in ANNOTATED_TEXTS if t.id == text_id), None)
