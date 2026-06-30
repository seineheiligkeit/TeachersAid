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

# --- Latein flagship: Phaedrus, "Vulpes et Corvus" (d. ~50 n. Chr. → PD) ------
# The same fox-and-flattery fable as RABE_FUCHS, in Latin — shows the annotated-text
# engine carrying Latin: vocab, Übersetzung, Formen/Konstruktion, Inhalt/Kultur.
_VULPES = """Qui se laudari gaudet verbis subdolis,
Fere dat poenas turpi paenitentia.
Cum de fenestra corvus raptum caseum
Comesse vellet, celsa residens arbore,
Vulpes hunc vidit, deinde sic coepit loqui:
O qui tuarum, corve, pennarum est nitor!
Quantum decoris corpore et vultu geris!
Si vocem haberes, nulla prior ales foret.
At ille stultus, dum vult vocem ostendere,
Emisit ore caseum, quem celeriter
Dolosa vulpes avidis rapuit dentibus.
Tunc demum ingemuit corvi deceptus stupor.
Hac re probatur quantum ingenium valet;
Virtute semper praevalet sapientia."""

VULPES_CORVUS = AnnotatedText(
    id="lat-vulpes-corvus", title="Vulpes et Corvus", subject="Latein", klasse=4,
    genre="Fabel (Versfabel)", textsorte="Fabel", text=_VULPES,
    source=TextSourceRef(
        author="Phaedrus", title="Fabulae Aesopiae I,13 (Vulpes et Corvus)", year="~40 n. Chr.",
        author_death_year=50, rights_basis="public_domain_pma",
        repository="Perseus Digital Library (ed. L. Mueller, 1876)",
        url="https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.02.0118:book=1:poem=13",
        attribution="Phaedrus, Fabulae I,13; gemeinfrei (Perseus Digital Library)."),
    serves=[Serves(competence_id="LAT.US.4.SPR.06", relation="exercises"),   # Übersetzen/Wiedergabe
            Serves(competence_id="LAT.US.4.SPR.01", relation="exercises"),   # Kernwortschatz
            Serves(competence_id="LAT.US.4.SPR.02", relation="exercises"),   # formale Analyse
            Serves(competence_id="LAT.US.4.INH.01", relation="exercises")],  # Inhalt/Kultur
    keywords=["Fabel", "Phaedrus", "Übersetzung", "Schmeichelei", "Aesop", "Latein", "Sentenz"],
    annotations=[
        Annotation(kind="vocab", label="caseus, -i (m)", answer="der Käse"),
        Annotation(kind="vocab", label="subdolus, -a, -um", answer="hinterlistig, arglistig"),
        Annotation(kind="vocab", label="nitor, -oris (m)", answer="der Glanz"),
        Annotation(kind="vocab", label="dolosus, -a, -um", answer="listig, trügerisch"),
        Annotation(kind="vocab", label="ingenium, -i (n)", answer="die Klugheit, der Verstand"),
        Annotation(kind="translation", zeile="3-5",
                   answer="Als ein Rabe einen vom Fenster geraubten Käse verzehren wollte, während "
                          "er hoch oben auf einem Baum saß, erblickte ihn ein Fuchs und begann dann "
                          "so zu sprechen:", label="", cognitive_level="apply", dimensions=["SPR"]),
        Annotation(kind="translation", zeile="6-8",
                   answer="„O welch ein Glanz deines Gefieders, Rabe! Wie viel Schönheit trägst du "
                          "an Körper und Gesicht! Wenn du eine Stimme hättest, wäre kein Vogel dir "
                          "überlegen.“", label="", cognitive_level="apply", dimensions=["SPR"]),
        Annotation(kind="grammar", zeile="8", span="haberes",
                   label="Bestimme die Verbform „haberes“ (Z. 8) und erkläre, warum dieser Modus steht.",
                   answer="haberes: 2. Person Singular Konjunktiv Imperfekt Aktiv (von habere). "
                          "Konjunktiv im Irrealis der Gegenwart („wenn du eine Stimme hättest …“).",
                   cognitive_level="analyze", dimensions=["SPR"]),
        Annotation(kind="grammar", zeile="11", span="avidis … dentibus",
                   label="In welchem Kasus steht „avidis dentibus“ (Z. 11) und welche Funktion hat er?",
                   answer="Ablativ Plural; Ablativus instrumenti: „mit gierigen Zähnen“.",
                   cognitive_level="analyze", dimensions=["SPR"]),
        Annotation(kind="culture", zeile="6-8",
                   label="Wie überredet der Fuchs den Raben? Vergleiche mit der Schmeichelei in der "
                         "Werbung.",
                   answer="Durch maßloses Lob (Schmeichelei): Er preist Gefieder und Aussehen und "
                          "behauptet, nur die Stimme fehle zur Vollkommenheit – so verleitet er den "
                          "eitlen Raben zum Singen, und der Käse fällt. Dieselbe Technik nutzt Werbung, "
                          "wenn sie den Käufer:innen schmeichelt.",
                   cognitive_level="evaluate", dimensions=["INH"]),
        Annotation(kind="culture", zeile="1-2",
                   label="Die Fabel wird von einer Sentenz gerahmt (Z. 1–2 und Z. 13–14). Welche Lehre "
                         "zieht Phaedrus?",
                   answer="Z. 1–2: Wer sich gern mit hinterlistigen Worten loben lässt, büßt meist mit "
                          "schimpflicher Reue. Z. 13–14: Klugheit/Weisheit ist mehr wert als (eitle) "
                          "Vorzüge. Botschaft: Hüte dich vor Schmeichelei.",
                   cognitive_level="evaluate", dimensions=["INH"]),
    ],
)

# --- FS1 (Englisch) audio flagship: a Hörverstehen monologue (A2) -------------
# Audio scripts are AUTHORED-then-vetted (no PD A1/A2 L2 audio to select) — correct by
# curation. The transcript is teacher-only (students listen); the spoken text is rendered
# by the TTS backend (audio:tts) — offline it's pending, the transcript is the fallback.
_MIA = """Hi! My name is Mia. I am twelve years old and I live in Graz, in Austria.
I go to school by bike. It takes about fifteen minutes.
My favourite subject is English, because I like reading stories.
I don't like maths very much — it is too difficult for me.
After school, I play volleyball with my friends on Tuesdays and Thursdays.
In the evening, I do my homework and sometimes I watch a film with my family.
At the weekend, we often visit my grandparents in the countryside.
My grandmother makes the best apple cake in the world!"""

MIA_SCHOOLDAY = AnnotatedText(
    id="fs1-mia-schoolday", title="Mia's school day", subject="Erste lebende Fremdsprache",
    klasse=2, genre="Hörtext (Monolog)", textsorte="Monolog", text=_MIA,
    medium="audio", lang="en",
    source=TextSourceRef(
        author="TeachersAid (Eigenproduktion)", title="Mia's school day (A2 Hörtext)",
        rights_basis="cleared", repository="TeachersAid",
        attribution="Eigenproduktion (TeachersAid); Audio via TTS."),
    serves=[Serves(competence_id="FS1.US.2.HOR.02", relation="exercises"),
            Serves(competence_id="FS1.US.2.HOR.01", relation="exercises"),
            Serves(competence_id="FS1.US.2.SCH.01", relation="exercises")],
    keywords=["Hörverstehen", "listening", "school day", "daily routine", "A2", "Englisch"],
    annotations=[
        Annotation(kind="vocab", label="subject", answer="(Schul-)Fach"),
        Annotation(kind="vocab", label="homework", answer="Hausübung / Hausaufgaben"),
        Annotation(kind="vocab", label="countryside", answer="das Land, die Landschaft"),
        Annotation(kind="vocab", label="apple cake", answer="Apfelkuchen"),
        Annotation(kind="comprehension",
                   label="How does Mia get to school, and how long does it take?",
                   answer="By bike; it takes about fifteen minutes.", cognitive_level="understand"),
        Annotation(kind="comprehension",
                   label="What is Mia's favourite subject, and why?",
                   answer="English, because she likes reading stories.", cognitive_level="understand"),
        Annotation(kind="comprehension",
                   label="Which subject does Mia find difficult?",
                   answer="Maths.", cognitive_level="understand"),
        Annotation(kind="comprehension",
                   label="What does Mia do on Tuesdays and Thursdays?",
                   answer="She plays volleyball with her friends.", cognitive_level="understand"),
        Annotation(kind="comprehension",
                   label="Where does the family go at the weekend?",
                   answer="They visit her grandparents in the countryside.", cognitive_level="understand"),
        Annotation(kind="erwartungshorizont",
                   label="Write four sentences about your own school day: how you get to school, "
                         "your favourite subject, and what you do after school.",
                   answer="Erwartet: simple present, 1. Person; die drei genannten Aspekte (Schulweg, "
                          "Lieblingsfach, Freizeit nach der Schule); einfache, weitgehend korrekte Sätze.",
                   cognitive_level="create", dimensions=["SCH"]),
    ],
)

from .realie_bahnhof import BAHNHOF      # Realien flagship (FS1, A2 — constructed Sprechanlass)

ANNOTATED_TEXTS: list[AnnotatedText] = [LORELEY, RABE_FUCHS, VULPES_CORVUS, MIA_SCHOOLDAY, BAHNHOF]


def find_text(text_id: str) -> AnnotatedText | None:
    return next((t for t in ANNOTATED_TEXTS if t.id == text_id), None)
