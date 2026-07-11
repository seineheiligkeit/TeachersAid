"""Curated historical image sources (Bildquellen asset class)."""

from __future__ import annotations

from ..schema.blocks import Serves
from ..schema.image_sources import (
    ImageAnnotation,
    ImageSource,
    ImageSourceRef,
    ReproductionRights,
    WorkRights,
)

_COMMONS_TITLE = (
    "File:Afgevaardigden op het Congres van Wenen, 1814-1815 Der Wiener Congress "
    "1815. Sitzung der Bevollmächtigten der acht an dem Tractate von Paris "
    "betheiligten Mächte (titel op object), RP-P-OB-87.274.jpg"
)
_DESCRIPTION_URL = (
    "https://commons.wikimedia.org/wiki/File:Afgevaardigden_op_het_Congres_van_"
    "Wenen,_1814-1815_Der_Wiener_Congress_1815._Sitzung_der_Bevollm%C3%A4chtigten_"
    "der_acht_an_dem_Tractate_von_Paris_betheiligten_M%C3%A4chte_(titel_op_object),_"
    "RP-P-OB-87.274.jpg"
)
_FILE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/9/91/Afgevaardigden_op_het_"
    "Congres_van_Wenen%2C_1814-1815_Der_Wiener_Congress_1815._Sitzung_der_"
    "Bevollm%C3%A4chtigten_der_acht_an_dem_Tractate_von_Paris_betheiligten_M%C3%A4chte_"
    "%28titel_op_object%29%2C_RP-P-OB-87.274.jpg"
)


ISABEY_WIENER_KONGRESS = ImageSource(
    id="gpb-isabey-wiener-kongress",
    title="Der Wiener Kongress im Bild",
    klasse=3,
    image_asset_id="gpb-isabey-wiener-kongress-image",
    source=ImageSourceRef(
        creator="Bernhard J. Dondorf (Lithograf), nach Jean Baptiste Isabey",
        title=(
            "Afgevaardigden op het Congres van Wenen, 1814-1815 / "
            "Der Wiener Congress 1815"
        ),
        work_date="1833-1872",
        repository="Rijksmuseum Amsterdam / Wikimedia Commons",
        description_url=_DESCRIPTION_URL,
        file_url=_FILE_URL,
        retrieved="2026-07-11",
        attribution=(
            "Bernhard J. Dondorf, nach Jean Baptiste Isabey, „Der Wiener Congress "
            "1815“ (1833-1872), Rijksmuseum Amsterdam, RP-P-OB-87.274; "
            "Digitalisat via Wikimedia Commons, CC0."
        ),
        mime="image/jpeg",
        width=6474,
        height=5356,
        sha1="305042160df70540a974b9f6efe4b6ede3979bab",
        work_rights=WorkRights(
            basis="public_domain_pma",
            creator="Bernhard J. Dondorf (1809-1902), nach Jean Baptiste Isabey (1767-1855)",
            creator_death_year=1902,
            evidence=(
                "Rijksmuseum object RP-P-OB-87.274 records the print as public domain; "
                "the latest named creator, Bernhard J. Dondorf, died in 1902, more than "
                "70 years ago in Austria."
            ),
        ),
        reproduction_rights=ReproductionRights(
            basis="cc0",
            licence="Creative Commons Zero, Public Domain Dedication (CC0 1.0)",
            licence_url="https://creativecommons.org/publicdomain/zero/1.0/",
            attribution_required=False,
            evidence=(
                "Wikimedia Commons imageinfo/extmetadata reports LicenseShortName=CC0, "
                "UsageTerms=Creative Commons Zero, Public Domain Dedication, "
                "License=cc0 and AttributionRequired=false for this exact file."
            ),
        ),
        rights_metadata={
            "commons_title": _COMMONS_TITLE,
            "pageid": "84921882",
            "LicenseShortName": "CC0",
            "UsageTerms": "Creative Commons Zero, Public Domain Dedication",
            "LicenseUrl": "http://creativecommons.org/publicdomain/zero/1.0/deed.en",
            "License": "cc0",
            "AttributionRequired": False,
            "Copyrighted": True,
            "Credit": "http://hdl.handle.net/10934/RM0001.COLLECT.519284",
        },
    ),
    serves=[Serves(competence_id="GPB.US.3.ALL.02", relation="exercises")],
    keywords=[
        "Wiener Kongress",
        "Bildquelle",
        "Quellenkritik",
        "Diplomatie",
        "Restauration",
        "Isabey",
    ],
    related_sachverhalt_id="sv-wiener-kongress",
    related_text_id="deu-anno-lehrertag-1871",
    annotations=[
        ImageAnnotation(
            kind="beschreibung",
            question=(
                "Beschreibe die Bildquelle ohne Deutung: Welche Personen, Gegenstände und "
                "räumlichen Anordnungen sind zu sehen? Formuliere mindestens vier Beobachtungen."
            ),
            answer=(
                "Zu sehen ist ein großer Innenraum mit vielen Männern in formeller Kleidung. "
                "Die Personen stehen oder sitzen in Gruppen um einen Tisch; Stühle, ein Tisch "
                "und eine Büste gehören zur Ausstattung. Manche Personen wenden sich einander "
                "zu, andere sind zum Bildbetrachter ausgerichtet."
            ),
            focus="sichtbare Personen, Gegenstände und Gruppierung",
            cognitive_level="understand",
            dimensions=["HME"],
        ),
        ImageAnnotation(
            kind="analyse",
            question=(
                "Analysiere die Gestaltung: Wie erzeugen Raum, Gruppierung und Blickrichtungen "
                "den Eindruck einer geordneten politischen Versammlung? Belege am Bild."
            ),
            answer=(
                "Der repräsentative Innenraum und die sorgfältige Gruppierung machen aus den "
                "Delegierten ein geschlossenes politisches Ensemble. Tisch und Sitzordnung "
                "strukturieren die Szene; die gestaffelten Figuren und unterschiedlichen "
                "Blickrichtungen lassen zugleich Gespräch und Rangordnung erkennen. Die "
                "detailreiche, inszenierte Darstellung betont Würde und Bedeutung der Beteiligten."
            ),
            focus="Komposition, Raumwirkung und Inszenierung",
            cognitive_level="analyze",
            dimensions=["HME", "HSA"],
        ),
        ImageAnnotation(
            kind="interpretation",
            question=(
                "Interpretiere die Perspektive der Bildquelle: Welches Bild von Politik und "
                "Macht vermittelt sie? Was kann man aus dieser Druckgrafik nicht zuverlässig "
                "über die tatsächlichen Verhandlungen ableiten?"
            ),
            answer=(
                "Die Bildquelle präsentiert Politik als Angelegenheit weniger, vornehm "
                "gekleideter männlicher Eliten in einem repräsentativen Raum. Sie hebt Ordnung, "
                "Rang und persönliche Diplomatie hervor; breitere Bevölkerungsgruppen bleiben "
                "unsichtbar. Nicht zuverlässig ableitbar sind der genaue Gesprächsverlauf, "
                "Konflikte, Motive oder der tatsächliche Einfluss einzelner Personen. Die Grafik "
                "entstand nach dem Ereignis und ist eine gestaltete Deutung, kein fotografischer "
                "Mitschnitt."
            ),
            focus="Perspektivität, Reichweite und Grenzen der Quelle",
            cognitive_level="evaluate",
            dimensions=["HME", "HOR"],
        ),
    ],
)

IMAGE_SOURCES = [ISABEY_WIENER_KONGRESS]


def find_image_source(image_id: str) -> ImageSource | None:
    return next((image for image in IMAGE_SOURCES if image.id == image_id), None)
