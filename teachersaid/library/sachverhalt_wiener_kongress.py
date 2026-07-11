"""Curated Sachverhalt 'Der Wiener Kongress' (GPB 3./4. Kl.) — the content-layer flagship.

The worked example for the **Sachverhalt content/exposition layer** (the third
grounding/provenance sibling; `Documents/sachverhalt-content-layer-design.md`). It rebuilds
*Der Wiener Kongress* **content-first** — a real Darstellung (Ausgangslage → Kongress →
Leitprinzipien → Ergebnis → Bedeutung → Gegenwartsbezug), a DERIVED timeline + Wirkungsgefüge,
and several correct-by-construction Sachkompetenz tasks — **alongside** (not replacing) the
method/Quellenkritik flagship `gpb_wiener_kongress.py` (Quelle ≠ Darstellung).

The discipline (invariants.md §3): the structured facts are *selected/sourced* (Wikipedia as a
`role="facts"` record — a permalink to the exact revision, fetched once via
`tools/fetch_wikipedia.py`, copyright protects expression not facts); the `darstellung` prose is
*authored over the frozen fact-set*, and the entity-lint (`pipeline/sachverhalt_lint.py`)
guarantees every year in it appears in the fact-set. **The SME fact-checks the history at the
gate** — do not assert an uncited claim; every date here is in the timeline.
"""

from __future__ import annotations

from ..schema.provenance import ProvenanceSource
from ..schema.sachverhalt import (
    Actor,
    CausalLink,
    Concept,
    DarstellungSection,
    HistEvent,
    Sachverhalt,
)

# The Wikipedia FACTS record — a snapshot permalink (the live article changes; the citation is
# stable). role="facts": consulted for information only, no expression obligation (the same
# record the method flagship uses).
_WP_FACTS = ProvenanceSource(
    title="Wiener Kongress",
    url="https://de.wikipedia.org/w/index.php?title=Wiener_Kongress&oldid=267935028",
    publisher="Wikipedia (de)",
    licence="CC-BY-SA-4.0",
    licence_url="https://creativecommons.org/licenses/by-sa/4.0/",
    retrieved="2026-06-30",
    role="facts",
)


def build_sachverhalt() -> Sachverhalt:
    return Sachverhalt(
        id="sv-wiener-kongress",
        subject="Geschichte und politische Bildung",
        klasse_range=(3, 4),
        topic="Der Wiener Kongress",
        leitfrage="Wie ordnet der Wiener Kongress Europa neu — und warum hält diese Ordnung "
                  "Jahrzehnte?",
        kompetenzbereiche=["Historische und politische Sachkompetenz"],
        competences=[
            "GPB.US.3.ALL.05", "GPB.US.3.ALL.04", "GPB.US.3.ALL.03",
            "GPB.US.3.ALL.06", "GPB.US.3.ALL.01", "GPB.US.3.ALL.02",
        ],
        keywords=["Restauration", "Gleichgewicht der Mächte", "Deutscher Bund", "Metternich",
                  "Napoleon", "Europa", "Neuordnung"],
        sach_dimension="HSA",          # Historische und politische Sachkompetenz
        urteil_dimension="HOR",        # Historische Orientierungskompetenz (the Urteils-task)
        sources=[_WP_FACTS],
        # --- structured facts (selected/sourced) ---------------------------------
        # timeline events + actors carry an optional entity_id into the entity registry
        # (grounding/entities); the corpus lint checks each linked year against the registry.
        timeline=[
            HistEvent(at=1806, label="Auflösung des Heiligen Römischen Reichs",
                      entity_id="aufloesung-hrr"),
            HistEvent(at=1813, label="Völkerschlacht bei Leipzig – Wende gegen Napoleon",
                      entity_id="voelkerschlacht-leipzig"),
            HistEvent(at=1814, label="Beginn des Wiener Kongresses", entity_id="wiener-kongress"),
            HistEvent(at=1815, label="Deutsche Bundesakte – Gründung des Deutschen Bundes",
                      entity_id="deutscher-bund"),
            HistEvent(at=1848, label="Revolution – Ende der Restaurationsepoche",
                      entity_id="revolution-1848"),
        ],
        actors=[
            Actor(name="Klemens von Metternich", entity_id="metternich",
                  role="österreichischer Außenminister; Gastgeber und prägende Figur des "
                       "Kongresses, Verfechter von Restauration und Gleichgewicht"),
            Actor(name="Charles-Maurice de Talleyrand", entity_id="talleyrand",
                  role="Gesandter Frankreichs; erreichte mit dem Prinzip der Legitimität, dass "
                       "das besiegte Frankreich mitverhandeln durfte"),
            Actor(name="Zar Alexander I.", entity_id="alexander-i-russland",
                  role="Kaiser von Russland, eine der vier siegreichen Großmächte"),
            Actor(name="Viscount Castlereagh", entity_id="castlereagh",
                  role="britischer Außenminister; trieb die Gleichgewichtspolitik voran"),
            Actor(name="Karl August von Hardenberg", entity_id="hardenberg",
                  role="preußischer Staatskanzler, verhandelte für Preußen"),
        ],
        causes=[
            CausalLink(cause="Niederlage Napoleons",
                       effect="Europa wird auf dem Kongress neu geordnet", kind="ursache"),
            CausalLink(cause="Prinzip des Gleichgewichts der Mächte",
                       effect="kein Staat soll je wieder ganz Europa beherrschen", kind="folge"),
            CausalLink(cause="Prinzip der Restauration",
                       effect="verdrängte Fürsten kehren an die Macht zurück", kind="folge"),
            CausalLink(cause="Auflösung des Heiligen Römischen Reichs",
                       effect="Gründung des Deutschen Bundes als lockerer Staatenbund",
                       kind="folge"),
            CausalLink(cause="Unterdrückung liberaler und nationaler Wünsche",
                       effect="Spannungen, die zur Revolution von 1848 führen", kind="wirkung"),
        ],
        concepts=[
            Concept(term="Restauration",
                    definition="die Wiederherstellung der politischen Ordnung von vor der "
                               "Französischen Revolution und Napoleon"),
            Concept(term="Legitimität",
                    definition="der Grundsatz, dass die alten, „rechtmäßigen“ Herrscherhäuser "
                               "wieder eingesetzt werden"),
            Concept(term="Gleichgewicht der Mächte",
                    definition="eine Ordnung, in der kein Staat so stark wird, dass er die "
                               "anderen beherrscht"),
            Concept(term="Deutscher Bund",
                    definition="ein lockerer Zusammenschluss (Staatenbund) deutscher Staaten, "
                               "der den früheren Reichsverband ersetzte"),
        ],
        bedeutung="Die Wiener Ordnung sicherte den Großmächten über Jahrzehnte den Frieden und "
                  "prägte die europäische Politik. Zugleich unterdrückte sie liberale und "
                  "nationale Bewegungen — Stabilität für die Herrschenden, Rückschritt für die "
                  "Mitbestimmung.",
        gegenwartsbezug="Die Idee, durch ein Gleichgewicht und gemeinsame Regeln zwischen "
                        "Staaten Kriege zu verhindern, wirkt bis heute nach — von späteren "
                        "Friedensordnungen bis zu internationalen Organisationen. Wer dabei "
                        "mitbestimmen darf, blieb umstritten.",
        urteilsfrage="„Der Wiener Kongress brachte vor allem Stabilität.“ Nimm zu dieser Aussage "
                     "Stellung: Was spricht dafür, was dagegen? Denke an die zurückgekehrten "
                     "Fürsten und an die Menschen, die sich mehr Mitbestimmung wünschten, und "
                     "begründe am Ende dein eigenes Urteil.",
        # --- the Darstellung (authored over the facts; every year is in the timeline) -----
        darstellung=[
            DarstellungSection(
                heading="Ausgangslage",
                body="Napoleon hatte Europa über Jahre beherrscht und seine Grenzen immer "
                     "wieder verschoben. Schon 1806 war das Heilige Römische Reich untergegangen. "
                     "Nach der Völkerschlacht bei Leipzig 1813 und seiner Niederlage standen die "
                     "europäischen Großmächte vor der Frage, wie der Kontinent neu zu ordnen sei.",
                grounded_by=["Auflösung des Heiligen Römischen Reichs",
                             "Völkerschlacht bei Leipzig – Wende gegen Napoleon"]),
            DarstellungSection(
                heading="Der Kongress in Wien",
                body="Ab 1814 verhandelten die Großmächte — Österreich, Russland, Preußen, "
                     "Großbritannien und das besiegte Frankreich — in Wien über die Neuordnung "
                     "Europas. Den Vorsitz führte der österreichische Außenminister Klemens von "
                     "Metternich. Geschickt erreichte der französische Gesandte Talleyrand, dass "
                     "auch Frankreich mitverhandeln durfte.",
                grounded_by=["Beginn des Wiener Kongresses", "Klemens von Metternich",
                             "Charles-Maurice de Talleyrand"]),
            DarstellungSection(
                heading="Die Leitprinzipien",
                body="Drei Grundsätze bestimmten die Verhandlungen. Das Gleichgewicht der Mächte "
                     "sollte verhindern, dass je wieder ein einzelner Staat ganz Europa "
                     "beherrscht. Die Legitimität setzte die alten Herrscherhäuser wieder in ihre "
                     "Rechte ein. Und die Restauration stellte die Ordnung von vor der Revolution "
                     "möglichst wieder her — viele verdrängte Fürsten kehrten an die Macht zurück.",
                grounded_by=["Gleichgewicht der Mächte", "Legitimität", "Restauration"]),
            DarstellungSection(
                heading="Das Ergebnis",
                body="An die Stelle des untergegangenen Reichs trat kein neuer Gesamtstaat, "
                     "sondern ein lockerer Staatenbund: der Deutsche Bund, 1815 durch die "
                     "Deutsche Bundesakte gegründet. Die in Wien geschaffene Ordnung prägte "
                     "Europa über Jahrzehnte und gilt als Beginn der Epoche der Restauration.",
                grounded_by=["Deutsche Bundesakte – Gründung des Deutschen Bundes",
                             "Deutscher Bund"]),
        ],
    )


def build_content():
    """The derived WorksheetContent (for tests / the offline demo)."""
    from ..pipeline.sachverhalt import build_worksheet

    content, _ = build_worksheet(build_sachverhalt())
    return content
