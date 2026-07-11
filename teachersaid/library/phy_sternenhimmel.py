"""Hand-authored Physik 'Sternenhimmel über Wien' (4. Kl.) — the FIRST real Horizont flagship.

This worksheet is the worked example for the third anchoring tier (`Documents/anchoring-modes.md`):
**Horizont** — teacher-choice enrichment that reaches *beyond* the Lehrplan and says so
honestly. It carries `anchor_mode="horizont"`; **no task claims a competence** (`serves: []`
everywhere, enforced by verify); `derive_nachweis` renders the honest statement — *„kein
Lehrplan-Kompetenzbezug behauptet"* — instead of a coverage table. The Lehrplan does not
require constellation-finding; a class that has caught fire on the Mondphasen sheet
(PHY.US.2.SEH.04, the competence-anchored companion) deserves a real star chart, and Horizont
is how the corpus offers one without faking an anchor.

Every figure is COMPUTED, not decorative: `matplotlib:star_chart` (`pipeline/astro`) selects the
bright-star positions from the curated catalog (`grounding/astro`, a cited fact layer) and
computes the visible sky for a date/time/place by plain spherical astronomy (sidereal time →
alt-az → azimuthal projection with a horizon ring N/O/S/W). The riddle chart uses the MASKING
invariant — a highlighted constellation with its name switched OFF — so „Welches Sternbild ist
das?" never prints its own answer. The observation task (t5) is deliberately an *inquiry frame*
(students investigate their OWN sky): we never assert unvetted local facts.

Build-for-joy, literally: a computed evening sky on a worksheet.
"""
from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..schema.assets import Asset
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.enums import AnchorMode
from ..schema.worksheet import Baustein, BundleRequest, WorksheetContent, WorksheetMeta

SUBJECT = "Physik"
KLASSE = 4

# A fixed winter evening and a summer late-evening over Wien — the two skies the sheet compares.
_WINTER = {"date": "2026-01-15", "time": "21:00"}
_SUMMER = {"date": "2026-07-15", "time": "23:00"}


def build_request() -> BundleRequest:
    return BundleRequest(subject=SUBJECT, klasse=KLASSE,
                         topic_raw="Sternenhimmel über Wien", envelope="doppelstunde",
                         anchor_mode=AnchorMode.HORIZONT)


def build_assets() -> list[Asset]:
    return [
        # the labelled reference sky (winter) — the intro chart students read from
        Asset(id="sky-winter", role="figure", generator="matplotlib:star_chart",
              spec={**_WINTER, "show_constellation_labels": True, "mag_limit": 4.2}),
        # the riddle: the Große Wagen highlighted, its NAME masked (the masking invariant)
        Asset(id="sky-raetsel", role="figure", generator="matplotlib:star_chart",
              spec={**_WINTER, "highlight": "UMa", "show_moon": False, "mag_limit": 4.0,
                    "title": "Welches Sternbild ist hervorgehoben?"}),
        # the summer sky (labelled) — for the winter/summer comparison
        Asset(id="sky-summer", role="figure", generator="matplotlib:star_chart",
              spec={**_SUMMER, "show_constellation_labels": True, "mag_limit": 4.2}),
    ]


def _intro() -> list:
    return [
        InfoBlock(
            id="sk.i1", kind="prose",
            content=(
                "Der Lehrplan verlangt keine Sternbildkunde – dieses Blatt ist ein "
                "Horizont: freiwillige Vertiefung, weil ein klarer Sternenhimmel eine "
                "der schönsten Physikstunden überhaupt ist. Die Karte unten ist keine "
                "Zeichnung, sondern für Wien BERECHNET: für ein bestimmtes Datum und "
                "eine bestimmte Uhrzeit ist ausgerechnet, welcher Stern gerade wo über "
                "dem Horizont steht."
            ),
        ),
        InfoBlock(
            id="sk.i2", kind="key_fact",
            content=(
                "So liest du die Karte: Der Kreisrand ist der Horizont ringsum, die "
                "Randbuchstaben sind die Himmelsrichtungen (N = Norden, O = Osten, "
                "S = Süden, W = Westen). Die Mitte ist der Punkt genau über dir (der "
                "Zenit). Ein Stern nahe der Mitte steht hoch am Himmel, ein Stern nahe "
                "dem Rand tief über dem Horizont. Größere Punkte sind hellere Sterne."
            ),
        ),
        InfoBlock(
            id="sk.i3", kind="figure", asset_refs=["sky-winter"],
            content=(
                "Der Winterhimmel über Wien, Mitte Jänner gegen 21 Uhr. Halte die Karte "
                "beim Beobachten über den Kopf und drehe sie so, dass die Richtung, in "
                "die du schaust, unten steht."
            ),
            watch_outs=[
                "Beim Blick nach oben sind Ost und West vertauscht gegenüber einer "
                "Landkarte – deshalb steht auf der Sternkarte O links und W rechts. Das "
                "verwirrt zuerst; über den Kopf gehalten stimmt es.",
            ],
        ),
    ]


def _tasks() -> list[TaskBlock]:
    t1 = TaskBlock(  # E · apply — read the azimuthal chart + horizon ring
        id="sk.t1", kind="open_response",
        prompt=(
            "Arbeite mit der Karte des Winterhimmels (oben). (a) In welcher "
            "Himmelsrichtung steht das Sternbild Orion, und steht es hoch oder tief? "
            "(b) Welches helle Gestirn steht fast senkrecht über Wien (nahe der Mitte)? "
            "(c) Nenne ein Sternbild, das gerade im Osten aufgeht."
        ),
        asset_refs=["sky-winter"],
        response={"mode": "lines", "n": 4},
        cognitive_level="apply", dimensions=["E"], serves=[], est_minutes=9,
        answer_key=(
            "(a) Orion steht im Süden (unten auf der Karte) und ziemlich hoch. "
            "(b) Nahe dem Zenit steht die Capella (im Fuhrmann). "
            "(c) Im Osten (links) steigt der Löwe herauf – Regulus steht knapp über dem "
            "Osthorizont. Jede am linken (Ost-)Rand aufsteigende Figur wird akzeptiert; "
            "die genaue Antwort hängt von Datum und Uhrzeit der Karte ab (hier 21 Uhr)."
        ),
        watch_outs=[
            "Ziel: die azimutale Karte lesen – Rand = Horizont, Mitte = Zenit, O links / "
            "W rechts. Genaue Antworten hängen von Datum/Uhrzeit der Karte ab; auf die "
            "Richtung und die Höhe achten, nicht auf den exakten Stern.",
        ],
    )
    t2 = TaskBlock(  # E · apply — the riddle (the masking invariant in action)
        id="sk.t2", kind="open_response",
        prompt=(
            "Auf dieser Karte ist ein Sternbild rot hervorgehoben, aber nicht benannt. "
            "(a) Zeichne die Verbindungslinien mit dem Lineal nach. (b) Wie heißt das "
            "Sternbild? (c) Woran hast du es erkannt, und wie hilft es dir, die "
            "Nordrichtung zu finden?"
        ),
        asset_refs=["sky-raetsel"],
        response={"mode": "lines", "n": 4},
        cognitive_level="apply", dimensions=["E"], serves=[], est_minutes=9,
        answer_key=(
            "(a)/(b) Es ist der Große Wagen (Teil des Großen Bären) – vier Sterne bilden "
            "den Kasten, drei die Deichsel. (c) An der markanten Wagen-/Kastenform. "
            "Verlängert man die hintere Kastenkante (Merak → Dubhe) um etwa das Fünffache, "
            "trifft man den Polarstern – und der steht fast genau im Norden."
        ),
        watch_outs=[
            "Die Karte VERRÄT den Namen nicht (Maskierung) – die Lösung steht nur hier. "
            "Der Polarstern-Trick (hintere Kastenkante fünffach verlängern) ist der "
            "eigentliche Gewinn: aus dem Wagen die Nordrichtung finden.",
        ],
    )
    t3 = TaskBlock(  # W · understand — why the sky changes across the year (Earth's orbit)
        id="sk.t3", kind="open_response",
        prompt=(
            "Vergleiche den Winterhimmel (oben) mit dem Sommerhimmel über Wien (Karte "
            "rechts/unten). (a) Nenne je ein auffälliges Sternbild bzw. helles Gestirn, "
            "das du im Winter, aber nicht im Sommer siehst – und umgekehrt. (b) Erkläre "
            "mit der Bewegung der Erde um die Sonne, warum sich der Anblick des Nachthimmels "
            "im Laufe eines Jahres ändert."
        ),
        asset_refs=["sky-summer"],
        response={"mode": "lines", "n": 6},
        cognitive_level="understand", dimensions=["W"], serves=[], est_minutes=11,
        answer_key=(
            "(a) Winter: Orion, Stier, Großer Hund (Sirius). Sommer: das Sommerdreieck "
            "aus Wega (Leier), Deneb (Schwan) und Atair (Adler), dazu Skorpion/Schütze "
            "tief im Süden. (b) Nachts schauen wir von der Erde weg von der Sonne ins "
            "All. Weil die Erde in einem Jahr einmal um die Sonne läuft, zeigt diese "
            "Nachtseite im Winter in eine andere Richtung des Weltraums als im Sommer – "
            "also sehen wir andere Sternbilder. Die Sterne selbst wandern nicht; unser "
            "Blickwinkel ändert sich."
        ),
        watch_outs=[
            "Kernidee: nicht die Sterne ziehen um, die ERDE wechselt im Jahreslauf die "
            "Seite. Sommerdreieck (Wega/Deneb/Atair) vs. Orion ist der plakative "
            "Gegensatz. (Zirkumpolare wie der Große Wagen sind das ganze Jahr da.)",
        ],
    )
    t4 = TaskBlock(  # E · analyze — nightly rotation + the (nearly) fixed Pole Star
        id="sk.t4", kind="open_response",
        prompt=(
            "Die Karte gilt für 21 Uhr. Um Mitternacht sieht der Himmel gedreht aus. "
            "(a) Erkläre mit der Drehung der Erde, warum die Sterne im Osten aufgehen "
            "und im Westen untergehen. (b) Ein einziger heller Stern bleibt die ganze "
            "Nacht fast an derselben Stelle. Welcher ist das, und warum bewegt er sich "
            "kaum?"
        ),
        response={"mode": "lines", "n": 5},
        cognitive_level="analyze", dimensions=["E"], serves=[], est_minutes=10,
        answer_key=(
            "(a) Die Erde dreht sich in etwa 24 Stunden einmal um ihre Achse (von West "
            "nach Ost). Für uns sieht es deshalb so aus, als würde sich der ganze "
            "Himmel in die Gegenrichtung drehen: die Gestirne gehen im Osten auf und im "
            "Westen unter – genau wie die Sonne tagsüber. (b) Der Polarstern. Er liegt "
            "fast genau in der Verlängerung der Erdachse (über dem Nordpol), deshalb "
            "steht er scheinbar still, und alle anderen Sterne scheinen um ihn zu kreisen."
        ),
        watch_outs=[
            "Dieselbe Ursache wie Tag/Nacht auf dem Mondphasen-Blatt: die Erddrehung. "
            "Der Polarstern steht nahe der Himmelsachse – nicht, weil er besonders wäre, "
            "sondern wegen seiner Lage fast in der verlängerten Erdachse.",
        ],
    )
    t5 = TaskBlock(  # S · create — the inquiry-frame observation (own sky, no asserted facts)
        id="sk.t5", kind="create_produce",
        prompt=(
            "Beobachtungsauftrag für einen klaren Abend (möglichst weg von hellen "
            "Straßenlampen): (a) Finde mit der Karte zwei Sternbilder und den hellsten "
            "Stern, den du siehst. (b) Steht der Mond am Himmel? Skizziere seine Phase "
            "und notiere, auf welcher Seite er beleuchtet ist. (c) Schreibe drei Sätze "
            "darüber, was dich überrascht hat. Es gibt keine falsche Beobachtung."
        ),
        response={"mode": "box", "min_height_mm": 60},
        cognitive_level="create", dimensions=["S"], serves=[], est_minutes=8,
        acceptable_reasoning=(
            "Kein fester Erwartungshorizont – es ist eine echte eigene Beobachtung. "
            "Gewürdigt wird: die Karte wurde benutzt (zwei benannte Sternbilder + der "
            "hellste gesehene Stern), die Mondphase ist skizziert und die beleuchtete "
            "Seite benannt (Anschluss ans Mondphasen-Blatt), und die drei Sätze zeigen "
            "eigenes Hinschauen. Bewölkung ist eine gültige Beobachtung – dann an einem "
            "anderen Abend."
        ),
        watch_outs=[
            "Bewusst als eigener Beobachtungsauftrag gehalten (Forschungshaltung): keine "
            "Vorgabe, WAS am Himmel steht – die Klasse untersucht ihren eigenen Himmel. "
            "Verbindet Sternkarte und Mondphasen zu einem echten Blick nach oben.",
        ],
    )
    return [t1, t2, t3, t4, t5]


def build_content() -> WorksheetContent:
    model = store.get_subject_model(SUBJECT, "Unterstufe")
    fassung = store.get_fassung()
    meta = WorksheetMeta(
        title="Sternenhimmel über Wien",
        subtitle="Eine berechnete Sternkarte lesen – Sternbilder, Himmelsrichtungen und "
                 "der Lauf der Nacht",
        subject=SUBJECT, stufe="Unterstufe", klasse=KLASSE,
        kernfrage="Wie findet man sich am nächtlichen Sternenhimmel zurecht?",
        fassung=fassung,
        lehrplan_label="Physik · 4. Klasse · Horizont (freiwillige Vertiefung über den "
                       "Lehrplan hinaus)",
    )
    section = Baustein(
        id="sk.kern",
        title="Eine Karte des Himmels lesen",
        teacher_overview={
            "throughline": (
                "Eine berechnete Sternkarte macht den Nachthimmel lesbar: "
                "Himmelsrichtungen und Höhe am Horizontring, Sternbilder als Wegweiser, "
                "und der ganze Anblick dreht sich – nächtlich durch die Erddrehung, übers "
                "Jahr durch den Erdumlauf."
            ),
            "talking_points": [
                "Zuerst das Kartenlesen sichern (i2): Rand = Horizont, Mitte = Zenit, "
                "O links / W rechts (weil man nach OBEN schaut).",
                "Das Rätsel (t2) ist der Aha-Moment: Großer Wagen erkennen und daraus "
                "über die hintere Kastenkante den Polarstern (Norden!) finden.",
                "Winter vs. Sommer (t3): nicht die Sterne ziehen um – die Erde wechselt "
                "im Jahreslauf die Nachtseite.",
                "Nächtliche Drehung + Polarstern (t4) knüpfen an Tag/Nacht vom "
                "Mondphasen-Blatt an: immer wieder die Erddrehung.",
            ],
            "extensions": [
                "Planeten sind auf der Sternkarte NICHT eingezeichnet (sie wandern) – wer "
                "einen sehr hellen „Stern“ sieht, der nicht auf der Karte steht, hat "
                "vielleicht einen Planeten gefunden.",
                "Warum funkeln Sterne, Planeten aber kaum? (Luftunruhe; Sterne sind "
                "Punktquellen, Planeten kleine Scheibchen.)",
                "Mit der Mondphasen-Einheit verknüpfen: den heutigen Mond auf der Karte "
                "suchen und seine Phase bestimmen.",
            ],
            "differentiation": (
                "Basis: t1/t2 (Karte lesen, ein Sternbild finden) reichen für einen "
                "gelungenen Einstieg. Weiterführend: t3/t4 verlangen das Modell hinter "
                "dem Anblick (Erdumlauf, Erddrehung, Himmelsachse). t5 ist für alle."
            ),
            "timing_notes": (
                "Doppelstunde; t5 ist ein Beobachtungsauftrag für zu Hause. Am schönsten "
                "mit einem echten Abendtermin oder einem Planetariumsbesuch verbinden."
            ),
        },
        blocks=_tasks(),
    )
    return WorksheetContent(
        meta=meta, subject_model=model, intro=_intro(), sections=[section],
        assets=build_assets(), anchor_mode=AnchorMode.HORIZONT,
    )
