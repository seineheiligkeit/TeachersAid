"""Hand-authored GWB Lernarrangement hero (schema v0.5): a Gemeinderat-Planspiel.

Format: simulation_game. The class becomes the Gemeinderat of the (fictional)
Gemeinde Auerbach and must decide whether a logistics distribution centre may be
built on a green-field site — and under what conditions. Four Fraktionen each get a
real worksheet (Orientierung/Urteil on paper); the **debate, the council decision,
and the debrief** reach the competences a worksheet can't: ENT.05 (Akteure &
Interessenskonflikte *analysieren*) via the interaction, ENT.01 (Standort­entscheidung
& Folgen *erörtern*) via the shared Gemeinderatsbeschluss.

Grounded in GWB grade-3 (Fassung BGBl. II 204/2024). The role sheets exercise
ENT.03/06/07 + ZEN.03; ENT.05 + ENT.01 are arrangement-level anchors. SME to
fact-check the German and the GWB framing.
"""

from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..schema.arrangement import (
    ArrangementMeta,
    ArrangementPhase,
    ArrangementRole,
    CompetenceAnchor,
    Lernarrangement,
    SharedProduct,
)
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

SUBJECT = "Geographie und wirtschaftliche Bildung"
KLASSE = 3
KERNFRAGE = ("Soll in unserer Gemeinde ein großes Verteilzentrum gebaut werden — "
             "und wenn ja, unter welchen Bedingungen?")
_LABEL = "Geographie u. wirtschaftliche Bildung · 3. Kl. · Wirtschaftsstandort & Raumplanung"


def _material(role_id: str, title: str, subtitle: str, intro: str,
              tasks: list[TaskBlock]) -> WorksheetContent:
    model = store.get_subject_model(SUBJECT)
    return WorksheetContent(
        meta=WorksheetMeta(
            title=title, subtitle=subtitle, subject=SUBJECT, stufe="Unterstufe",
            klasse=KLASSE, kernfrage=KERNFRAGE, fassung=store.get_fassung(),
            lehrplan_label=_LABEL,
        ),
        subject_model=model,
        intro=[InfoBlock(id=f"{role_id}.i", kind="prose", content=intro)],
        sections=[Baustein(id=f"{role_id}.kern", title="Eure Fraktionsarbeit", blocks=tasks)],
    )


def _roles() -> list[ArrangementRole]:
    gemeinde = _material(
        "gem", "Rollenblatt: Gemeindeführung",
        "Bürgermeister:in & Gemeindeamt — ihr leitet die Sitzung und tragt für alle Verantwortung",
        "Ihr führt die Gemeinde Auerbach und leitet die Gemeinderatssitzung. Ihr "
        "müsst das Gesamtwohl im Blick haben: Arbeitsplätze und Einnahmen genauso wie "
        "Lebensqualität und Umwelt. Am Ende moderiert ihr die Entscheidung.",
        [
            TaskBlock(
                id="gem.t1", kind="open_response",
                prompt=("Welche Einnahmen brächte das Verteilzentrum der Gemeinde "
                        "(z. B. Kommunalsteuer, Arbeitsplätze für Auerbacher:innen) — "
                        "und welche Folgekosten entstünden ihr (z. B. Straßen, "
                        "Kinderbetreuung, Instandhaltung)? Stellt Einnahmen und Kosten "
                        "gegenüber."),
                response={"mode": "lines", "n": 4},
                cognitive_level="understand", dimensions=["OK"],
                serves=[{"competence_id": "GWB.US.3.ENT.06", "relation": "exercises"}],
                est_minutes=8,
                answer_key=("Einnahmen: Kommunalsteuer auf Löhne, evtl. Aufträge für "
                            "lokale Betriebe, Kaufkraft. Folgekosten: Straßenausbau/"
                            "Erhaltung, Infrastruktur, evtl. mehr Bedarf an Wohnraum & "
                            "Betreuung. Steuern finanzieren öffentliche Leistungen — "
                            "Einnahmen und Folgekosten gehören zusammen gedacht."),
            ),
            TaskBlock(
                id="gem.t2", kind="open_response",
                prompt=("Bereitet drei Fragen vor, die ihr als Vorsitz an die anderen "
                        "Fraktionen stellt, damit am Ende eine faire, gut begründete "
                        "Entscheidung möglich ist."),
                response={"mode": "lines", "n": 3},
                cognitive_level="evaluate", dimensions=["UK", "OK"],
                serves=[{"competence_id": "GWB.US.3.ENT.03", "relation": "exercises"}],
                est_minutes=7,
                acceptable_reasoning=("Gute Fragen zielen auf Folgen und Bedingungen: "
                                      "z. B. nach Lärmschutz, LKW-Route, Ausgleichsflächen, "
                                      "Zahl/Sicherheit der Arbeitsplätze — sie machen "
                                      "Interessen und mögliche Kompromisse sichtbar."),
            ),
        ],
    )
    betrieb = _material(
        "btr", "Rollenblatt: Das Unternehmen",
        "Projektwerber — ihr wollt das Verteilzentrum bauen",
        "Euer Versandhandels-Unternehmen will am Ortsrand von Auerbach ein "
        "Verteilzentrum bauen. Euer Ziel in der Sitzung: überzeugend darlegen, warum "
        "das gut für die Region ist — sachlich, nicht beschönigend.",
        [
            TaskBlock(
                id="btr.t1", kind="open_response",
                prompt=("Stellt dar, welche Bedeutung euer Betrieb für die Region hätte: "
                        "Arbeitsplätze, Aufträge für lokale Firmen, Kaufkraft, "
                        "Anbindung. Warum ist gerade dieser Standort für euch attraktiv?"),
                response={"mode": "lines", "n": 4},
                cognitive_level="understand", dimensions=["OK"],
                serves=[{"competence_id": "GWB.US.3.ENT.07", "relation": "exercises"}],
                est_minutes=8,
                answer_key=("Bedeutung: ~250 Arbeitsplätze, Aufträge an lokale Handwerks-/"
                            "Dienstleistungsbetriebe, Kaufkraft. Standortvorteile: "
                            "Autobahnauffahrt, große ebene Fläche, verfügbare Arbeitskräfte. "
                            "Unternehmen tragen zum Wirtschaftsstandort bei — aber der "
                            "Nutzen ist gegen die Folgen abzuwägen."),
            ),
            TaskBlock(
                id="btr.t2", kind="open_response",
                prompt=("Welche Bedenken erwartet ihr von Anrainer:innen und der "
                        "Umweltgruppe? Wählt zwei und bereitet je eine sachliche, ehrliche "
                        "Antwort vor (kein Schönreden)."),
                response={"mode": "lines", "n": 3},
                cognitive_level="evaluate", dimensions=["UK"],
                serves=[{"competence_id": "GWB.US.3.ENT.03", "relation": "exercises"}],
                est_minutes=7,
                acceptable_reasoning=("Erwartbare Bedenken: LKW-Verkehr/Lärm, Boden­"
                                      "versiegelung, Verlust von Grünland. Gute Antworten "
                                      "räumen die Folge ein und nennen eine Maßnahme "
                                      "(Lärmschutzwall, Nacht-LKW-Verbot, Dachbegrünung) — "
                                      "Interessen ernst nehmen statt abwiegeln."),
            ),
        ],
    )
    anrainer = _material(
        "anr", "Rollenblatt: Anrainer:innen",
        "Bürgerinitiative — ihr wohnt direkt neben der geplanten Fläche",
        "Ihr wohnt direkt neben der geplanten Fläche. Euch geht es um Verkehr, Lärm, "
        "Lebensqualität und den Wert eurer Häuser — aber auch ihr wisst, dass "
        "Arbeitsplätze wichtig sind.",
        [
            TaskBlock(
                id="anr.t1", kind="open_response",
                prompt=("Welche Veränderungen im Alltag erwartet ihr durch Bau und "
                        "Betrieb (LKW-Verkehr, Lärm, Licht, Erholungsflächen)? "
                        "Vergleicht die heutige Nutzung der Fläche mit der künftigen."),
                response={"mode": "lines", "n": 4},
                cognitive_level="understand", dimensions=["OK"],
                serves=[{"competence_id": "GWB.US.3.ZEN.03", "relation": "exercises"}],
                est_minutes=8,
                answer_key=("Heute: Acker/Wiese, ruhig, Naherholung. Künftig: LKW-Verkehr "
                            "(auch früh/nachts), Lärm, Lichtemissionen, mehr Verkehr auf "
                            "der Ortsdurchfahrt. Nutzungskonflikt Wohnen ↔ Gewerbe/Verkehr."),
            ),
            TaskBlock(
                id="anr.t2", kind="open_response",
                prompt=("Formuliert eure Position: lehnt ihr ab — oder stimmt ihr unter "
                        "Bedingungen zu? Nennt zwei konkrete Bedingungen, mit denen ihr "
                        "leben könntet."),
                response={"mode": "lines", "n": 3},
                cognitive_level="evaluate", dimensions=["UK"],
                serves=[{"competence_id": "GWB.US.3.ENT.03", "relation": "exercises"}],
                est_minutes=7,
                acceptable_reasoning=("Tragfähige Bedingungen: eigene LKW-Zufahrt abseits "
                                      "der Wohnstraßen, Nacht-Fahrverbot, Lärmschutzwall, "
                                      "Grünstreifen. Position sachlich begründen, nicht nur "
                                      "'dagegen'."),
            ),
        ],
    )
    umwelt = _material(
        "umw", "Rollenblatt: Umwelt- & Naturschutzgruppe",
        "ihr vertretet Boden, Wasser, Klima und Natur",
        "Ihr vertretet die Interessen von Boden, Wasser, Klima und Natur — die in der "
        "Sitzung sonst niemand vertritt. Eure Aufgabe: die ökologischen Folgen sichtbar "
        "machen und gangbare Alternativen vorschlagen.",
        [
            TaskBlock(
                id="umw.t1", kind="open_response",
                prompt=("Was geht durch das Versiegeln von rund 8 Hektar Grünfläche "
                        "verloren? Denkt an Boden, Versickerung von Regen/Hochwasserschutz, "
                        "Lebensraum und Acker für Lebensmittel."),
                response={"mode": "lines", "n": 4},
                cognitive_level="understand", dimensions=["OK"],
                serves=[{"competence_id": "GWB.US.3.ZEN.03", "relation": "exercises"}],
                est_minutes=8,
                answer_key=("Versiegelung: Boden ist nicht erneuerbar; Regen versickert "
                            "nicht mehr → höhere Hochwassergefahr; Verlust von Lebensraum "
                            "und Ackerfläche; lokal wärmer. Fläche ist eine knappe Ressource "
                            "mit konkurrierenden Nutzungen."),
            ),
            TaskBlock(
                id="umw.t2", kind="open_response",
                prompt=("Schlagt Alternativen oder Auflagen vor, die die ökologischen "
                        "Folgen verringern (z. B. Bau auf einer bereits versiegelten Brache, "
                        "Dachbegrünung, Photovoltaik, Ausgleichsflächen)."),
                response={"mode": "lines", "n": 3},
                cognitive_level="evaluate", dimensions=["UK"],
                serves=[{"competence_id": "GWB.US.3.ENT.03", "relation": "exercises"}],
                est_minutes=7,
                acceptable_reasoning=("Sinnvolle Auflagen: Vorrang für Brachflächen/"
                                      "Leerstand, Entsiegelung an anderer Stelle als "
                                      "Ausgleich, Dachbegrünung + PV, Regenrückhaltung. "
                                      "Nachhaltigkeit heißt Folgen für kommende Generationen "
                                      "mitdenken."),
            ),
        ],
    )
    return [
        ArrangementRole(id="gem", label="Gemeindeführung", material=gemeinde),
        ArrangementRole(id="btr", label="Das Unternehmen", material=betrieb),
        ArrangementRole(id="anr", label="Anrainer:innen", material=anrainer),
        ArrangementRole(id="umw", label="Umwelt- & Naturschutzgruppe", material=umwelt),
    ]


def _common_material() -> list[InfoBlock]:
    return [
        InfoBlock(
            id="case", kind="prose",
            content=("Die Gemeinde Auerbach (rund 4 000 Einwohner:innen, an einer "
                     "Autobahnauffahrt) hat eine Anfrage: Ein Versandhandels-Unternehmen "
                     "möchte am Ortsrand auf einer rund 8 Hektar großen Wiese ein "
                     "Verteilzentrum bauen. Der Gemeinderat muss entscheiden."),
        ),
        InfoBlock(
            id="facts", kind="key_fact",
            content=("Auf dem Tisch liegen: rund 250 Arbeitsplätze · zusätzliche "
                     "LKW-Fahrten täglich · Versiegelung von 8 ha Grünland · "
                     "Kommunalsteuer-Einnahmen für die Gemeinde · die Fläche ist heute "
                     "Acker/Wiese am Ortsrand."),
        ),
        InfoBlock(
            id="rules", kind="procedure",
            content=("Ablauf der Sitzung: (1) Jede Fraktion bereitet ihre Position vor. "
                     "(2) Jede Fraktion hat 2 Minuten für ihr Eingangsstatement. "
                     "(3) Offene Debatte mit Fragen und Repliken. (4) Der Gemeinderat "
                     "fasst einen begründeten Beschluss."),
        ),
    ]


def _debrief() -> list[InfoBlock]:
    return [
        InfoBlock(
            id="db.intro", kind="prose",
            content=("Tretet aus euren Rollen heraus. Jetzt zählt eure eigene Meinung, "
                     "nicht die eurer Fraktion."),
        ),
        InfoBlock(
            id="db.q", kind="prose",
            content=("Reflexion im Plenum: Welcher Interessenkonflikt war am schwersten "
                     "aufzulösen? Wo war ein Kompromiss möglich, wo nicht — und warum? "
                     "War die getroffene Entscheidung aus deiner Sicht fair? Wie ist es, "
                     "in einer Demokratie zwischen widersprüchlichen Interessen zu "
                     "entscheiden?"),
        ),
    ]


def _phases() -> list[ArrangementPhase]:
    return [
        ArrangementPhase(id="p1", label="Fall & Spielregeln", grouping="plenary",
                         minutes=10,
                         what_happens=("Lehrkraft stellt Fall und Kernfrage vor, klärt die "
                                       "Spielregeln und teilt die vier Fraktionen zu.")),
        ArrangementPhase(id="p2", label="Fraktionsarbeit", grouping="role_group",
                         minutes=20,
                         what_happens=("Jede Fraktion liest ihr Rollenblatt, klärt ihre "
                                       "Interessen und bereitet Position und Argumente vor.")),
        ArrangementPhase(id="p3", label="Gemeinderatssitzung (Debatte)", grouping="plenary",
                         minutes=25,
                         what_happens=("Eingangsstatements (je 2 Min), dann offene, "
                                       "moderierte Debatte mit Fragen und Repliken zwischen "
                                       "den Fraktionen.")),
        ArrangementPhase(id="p4", label="Abstimmung & Beschluss", grouping="plenary",
                         minutes=10,
                         what_happens=("Der Gemeinderat formuliert einen Beschluss "
                                       "(Bau / kein Bau / Bau mit Auflagen) samt Begründung.")),
        ArrangementPhase(id="p5", label="Reflexion (Rollen verlassen)", grouping="plenary",
                         minutes=15,
                         what_happens=("Aus den Rollen heraustreten und den Prozess "
                                       "reflektieren — siehe Debrief.")),
    ]


def build_arrangement() -> Lernarrangement:
    return Lernarrangement(
        meta=ArrangementMeta(
            title="Wohin mit dem neuen Verteilzentrum?",
            subtitle="Ein Gemeinderat-Planspiel zu Standortentscheidung und Raumnutzung",
            subject=SUBJECT, stufe="Unterstufe", klasse=KLASSE, kernfrage=KERNFRAGE,
            fassung=store.get_fassung(), format="simulation_game", lehrplan_label=_LABEL,
        ),
        common_material=_common_material(),
        roles=_roles(),
        phases=_phases(),
        shared_product=SharedProduct(
            description=("Gemeinderatsbeschluss: Haltet schriftlich fest, ob (und wo) das "
                         "Verteilzentrum gebaut werden darf, die drei wichtigsten "
                         "Begründungen und — falls ja — welche Auflagen gelten."),
            rubric=[
                {"criterion": "Mehrperspektivität",
                 "levels": ["nur eine Sicht berücksichtigt",
                            "einige Interessen berücksichtigt",
                            "alle vier Interessen abgewogen"]},
                {"criterion": "Begründung",
                 "levels": ["Behauptung ohne Begründung", "teilweise begründet",
                            "sachlich und mehrperspektivisch begründet"]},
                {"criterion": "Umsetzbarkeit der Auflagen",
                 "levels": ["keine / unrealistisch", "vage", "konkret und umsetzbar"]},
            ],
        ),
        debrief=_debrief(),
        competence_anchors=[
            CompetenceAnchor(competence_id="GWB.US.3.ENT.05", dimension="UK",
                             served_by="interaction"),   # Interessenskonflikte analysieren
            CompetenceAnchor(competence_id="GWB.US.3.ENT.01", dimension="UK",
                             served_by="shared_product"),  # Standortentscheidung + Folgen erörtern
        ],
    )
