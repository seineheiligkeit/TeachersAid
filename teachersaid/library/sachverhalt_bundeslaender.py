"""Curated Sachverhalt 'Bevölkerung in Österreichs Bundesländern' (GWB 4. Kl.) — the third-
subject flagship (Geography), and the first one with a MAP.

Proves the Sachverhalt container generalises to a spatial subject (design Phase 2; the map-figure
extension). Where History carried a dated `timeline` and Biology an undated `process`, Geography
carries a **`Region`** spatial fact set → a **choropleth map** (`matplotlib:choropleth_map`) + a
rank-by-value task. Both axes of the map are FACTS, not authored:

* **boundaries** — a sourced CC-BY GeoJSON (`grounding/geo/at_bundeslaender`, fetched by
  `tools/fetch_geo_boundaries.py`; Statistik Austria / Flooh Perlot), loaded by `geo_id`;
* **values** — the cited Bundesländer population dataset (`region_dataset`/`region_series`), pulled
  at derivation and filled at assemble (`ground_data`), so *select-never-author* holds for the
  numbers. The map renders both citations.

The `Region` notes are curated; the Darstellung is authored over the frozen fact-set (no dates, so
the year-guarantee is vacuous — the map's "Stand 2024" rides the citation). **The SME fact-checks
the geography and the German at the gate.** GWB serves OK (Orientierungs-/Kartenkompetenz) for the
Sachkompetenz tasks and UK (Urteilskompetenz) for the Standpunkt.
"""

from __future__ import annotations

from ..schema.provenance import ProvenanceSource
from ..schema.sachverhalt import CausalLink, Concept, DarstellungSection, Region, Sachverhalt

# role="facts": a real Darstellung consulted for the qualitative claims; the numbers + boundaries
# are separately cited on the map. The SME fact-checks at the gate.
_WP_FACTS = ProvenanceSource(
    title="Land (Österreich) — Bundesländer",
    url="https://de.wikipedia.org/wiki/Land_(%C3%96sterreich)",
    publisher="Wikipedia (de)",
    licence="CC-BY-SA-4.0",
    licence_url="https://creativecommons.org/licenses/by-sa/4.0/",
    retrieved="2026-06-30",
    role="facts",
)


def build_sachverhalt() -> Sachverhalt:
    return Sachverhalt(
        id="sv-bundeslaender-bevoelkerung",
        subject="Geographie und wirtschaftliche Bildung",
        klasse_range=(4, 4),
        topic="Bevölkerung in Österreichs Bundesländern",
        leitfrage="Wie ungleich verteilt sich die Bevölkerung auf Österreichs Bundesländer — "
                  "und warum?",
        kompetenzbereiche=["Entwicklungen in einer globalisierten Welt"],
        competences=["GWB.US.4.ENT2.01", "GWB.US.4.ENT2.02"],
        keywords=["Bevölkerung", "Verteilung", "Bundesländer", "Ballungsraum", "Stadt",
                  "Verstädterung", "Bevölkerungsdichte", "Österreich"],
        sach_dimension="OK",                  # Orientierungskompetenz (Karten-/Raumkompetenz)
        urteil_dimension="UK",                # Urteilskompetenz
        urteil_competence="GWB.US.4.ENT2.04",  # nachhaltige räumliche/wirtschaftliche Entwicklung
        actor_label="Bundesländer",
        sources=[_WP_FACTS],
        # --- the spatial fact set (the Phase-2 Geography fact-type) -----------
        geo_id="at_bundeslaender",
        region_dataset="statistik_austria_bundeslaender_2024",
        region_series="bevoelkerung",
        region_value_label="Einwohner:innen (1.1.2024)",
        regions=[
            Region(name="Wien", note="Bundeshauptstadt und größter Ballungsraum; flächenklein, "
                                     "aber am dichtesten besiedelt"),
            Region(name="Niederösterreich", note="flächengrößtes Bundesland, umschließt Wien; "
                                                 "dicht besiedelter Großraum im Norden"),
            Region(name="Oberösterreich", note="bevölkerungsstark, Industrie- und Agrarland um Linz"),
            Region(name="Steiermark", note="zweitgrößte Fläche; Ballungsraum Graz, sonst viel "
                                           "Gebirge"),
            Region(name="Tirol", note="alpin geprägt; Menschen leben v. a. in den Tälern"),
            Region(name="Kärnten", note="südlich der Alpen, dünner besiedelt"),
            Region(name="Salzburg", note="Stadt Salzburg als Zentrum, dazu Gebirgsregionen"),
            Region(name="Vorarlberg", note="kleinstes Flächenland im Westen, dicht im Rheintal"),
            Region(name="Burgenland", note="östlichstes und einwohnerschwächstes Bundesland, "
                                           "überwiegend ländlich"),
        ],
        # --- cause -> effect (why the distribution is uneven) -----------------
        causes=[
            CausalLink(cause="Ballungsräume bieten Arbeit, Bildung und Infrastruktur",
                       effect="viele Menschen leben dort dicht zusammen", kind="ursache"),
            CausalLink(cause="Die Alpen bedecken weite Teile West- und Südösterreichs",
                       effect="in den Gebirgsregionen leben weniger Menschen", kind="folge"),
            CausalLink(cause="Wien ist Hauptstadt und Wirtschaftszentrum",
                       effect="der Großraum Wien wächst am stärksten", kind="folge"),
            CausalLink(cause="Ländliche Randregionen verlieren junge Menschen",
                       effect="dort sinkt die Bevölkerung (Abwanderung)", kind="wirkung"),
        ],
        # --- Begriffe ---------------------------------------------------------
        concepts=[
            Concept(term="Ballungsraum",
                    definition="ein dicht besiedeltes Gebiet rund um eine oder mehrere Großstädte"),
            Concept(term="Bevölkerungsdichte",
                    definition="die Zahl der Einwohner:innen je Quadratkilometer"),
            Concept(term="Peripherie",
                    definition="ein dünn besiedeltes Randgebiet, oft fernab der großen Städte"),
            Concept(term="Verstädterung",
                    definition="das Wachstum der Städte und die Zuwanderung vom Land in die Stadt"),
        ],
        bedeutung="Wo Menschen leben, entscheidet darüber, wo Wohnungen, Schulen, Verkehr und "
                  "Arbeitsplätze gebraucht werden. Die sehr ungleiche Verteilung der Bevölkerung "
                  "in Österreich — dicht im Großraum Wien und in den Tälern, dünn im Gebirge — "
                  "prägt die Planung des ganzen Landes.",
        gegenwartsbezug="Wachsen die Ballungsräume weiter, steigen dort Mieten und Verkehr, "
                        "während ländliche Regionen mit Abwanderung kämpfen. Wie man Wohnraum "
                        "schafft, ohne immer mehr Boden zu verbrauchen, ist eine der großen "
                        "Fragen der Raumplanung.",
        urteilsfrage="„Neue Wohnungen sollen vor allem in den großen Ballungsräumen entstehen.“ "
                     "Nimm zu dieser Aussage Stellung: Welche Vor- und Nachteile hat es, wenn sich "
                     "Menschen in wenigen Ballungsräumen konzentrieren — für die Menschen, die "
                     "Umwelt und die ländlichen Regionen? Begründe dein Urteil.",
        # --- the Darstellung (authored over the facts; no dates) --------------
        darstellung=[
            DarstellungSection(
                heading="Ein Land, sehr ungleich besiedelt",
                body="Die Menschen verteilen sich in Österreich sehr ungleich über das Land. Im "
                     "Großraum Wien und in den großen Tälern leben viele Menschen dicht "
                     "beieinander, während in den Gebirgsregionen nur wenige wohnen.",
                grounded_by=["Wien", "Ballungsraum"]),
            DarstellungSection(
                heading="Warum die Verteilung so ungleich ist",
                body="Wo es Arbeit, Bildung und gute Verbindungen gibt, ziehen Menschen hin — das "
                     "sind vor allem die Ballungsräume rund um die großen Städte. Die Alpen "
                     "dagegen bedecken weite Teile West- und Südösterreichs; dort ist das Leben "
                     "schwieriger und es wohnen weniger Menschen.",
                grounded_by=["Ballungsraum"]),
            DarstellungSection(
                heading="Die Bundesländer im Vergleich",
                body="Die Karte zeigt die Bevölkerung je Bundesland. Wien und Niederösterreich "
                     "sind am stärksten besiedelt, das Burgenland und Vorarlberg am schwächsten. "
                     "Vergleicht man die Zahlen mit der Fläche, zeigt sich: Wien ist klein, aber "
                     "am dichtesten bevölkert.",
                grounded_by=["Wien", "Niederösterreich", "Burgenland", "Vorarlberg"]),
        ],
    )


def build_content():
    """The derived WorksheetContent (for tests / the offline demo)."""
    from ..pipeline.sachverhalt import build_worksheet

    content, _ = build_worksheet(build_sachverhalt())
    return content
