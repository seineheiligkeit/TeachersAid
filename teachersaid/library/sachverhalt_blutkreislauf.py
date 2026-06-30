"""Curated Sachverhalt 'Der Blutkreislauf' (Biologie 2./3. Kl.) — the Phase-2 flagship.

Proves the Sachverhalt container **generalises beyond History** (design Phase 2;
`Documents/sachverhalt-content-layer-design.md`). Where the GPB flagship carried a dated
`timeline`, a biological topic carries an undated **`process`/cycle** — the new Phase-2
fact-type — which derives a `matplotlib:process_flow` figure and a process-ordering task.
Everything else (the cause→effect Wirkungsgefüge, the Begriff-Zuordnung, the content/structure
tasks, the Standpunkt) is subject-agnostic and reused unchanged.

The discipline is identical (invariants.md §3): the structured facts (the process steps, the
structures, the cause→effect links, the Begriffe) are *selected/sourced*; the `darstellung` is
*authored over the frozen fact-set*, entity-lint guarded. **The SME fact-checks the biology and
the German at the gate.** Bio has no dates, so the year-guarantee is vacuously satisfied — the
proof here is that the container, derivation, lint, figures, and HITL all hold for a non-history
subject with a cyclic process instead of a timeline.

Anchoring follows the science-model convention: a *content* module serves **W** (Wissen
aneignen/anwenden — the Sachkompetenz analogue) for its Sachkompetenz tasks and **S** (Standpunkte
begründen — here Gesundheit) for the judgment task; **E** (Erkenntnisgewinnung/Experimente) is not
exercised by a Darstellung. The Bio competences resolve with empty dims (like GPB), so the
dimension hints are load-bearing.
"""

from __future__ import annotations

from ..schema.provenance import ProvenanceSource
from ..schema.sachverhalt import (
    Actor,
    CausalLink,
    Concept,
    DarstellungSection,
    ProcessStep,
    Sachverhalt,
)

# role="facts": consulted for information only (no expression obligation). A plain article URL —
# the exact-revision permalink can be pinned via tools/fetch_wikipedia.py at the review gate; we do
# NOT fabricate an oldid (a fake-verified citation is worse than none).
_WP_FACTS = ProvenanceSource(
    title="Blutkreislauf",
    url="https://de.wikipedia.org/wiki/Blutkreislauf",
    publisher="Wikipedia (de)",
    licence="CC-BY-SA-4.0",
    licence_url="https://creativecommons.org/licenses/by-sa/4.0/",
    retrieved="2026-06-30",
    role="facts",
)


def build_sachverhalt() -> Sachverhalt:
    return Sachverhalt(
        id="sv-blutkreislauf",
        subject="Biologie",
        klasse_range=(2, 3),
        topic="Der Blutkreislauf",
        leitfrage="Wie versorgt der Blutkreislauf jede Zelle des Körpers — und welche Rolle "
                  "spielen Herz und Blutgefäße dabei?",
        kompetenzbereiche=["Wissen aneignen, anwenden und kommunizieren (W)"],
        competences=["BIO.US.x.WIS.01", "BIO.US.x.WIS.02", "BIO.US.x.WIS.03"],
        keywords=["Blutkreislauf", "Herz", "Lunge", "Sauerstoff", "Arterie", "Vene",
                  "Kapillare", "Kreislauf", "Gefäße"],
        sach_dimension="W",                  # Wissen aneignen, anwenden und kommunizieren
        urteil_dimension="S",                # Standpunkte begründen (Gesundheit)
        urteil_competence="BIO.US.x.STA.02",  # Fragestellungen u. a. im Bereich Gesundheit
        actor_label="Strukturen",            # not "Akteure" — these are organs/vessels
        sources=[_WP_FACTS],
        # --- the process / CYCLE (the Phase-2 fact-type, the undated sibling of timeline) ----
        process_name="Der Weg des Blutes (Doppelkreislauf)",
        process_cyclic=True,
        process=[
            ProcessStep(name="Rechtes Herz: Blut zur Lunge"),
            ProcessStep(name="Lunge: Sauerstoff aufnehmen"),
            ProcessStep(name="Zum linken Herzen"),
            ProcessStep(name="Linkes Herz: Blut in den Körper"),
            ProcessStep(name="Im Körper: Sauerstoff abgeben"),
            ProcessStep(name="Zurück zum rechten Herzen"),
        ],
        # --- structures (the science analogue of actors) ----------------------
        actors=[
            Actor(name="Herz", role="der kräftige Muskel, der das Blut durch den Körper pumpt "
                                    "(zwei Hälften, vier Kammern)"),
            Actor(name="Arterien", role="Blutgefäße, die das Blut vom Herzen wegführen"),
            Actor(name="Venen", role="Blutgefäße, die das Blut zum Herzen zurückführen"),
            Actor(name="Kapillaren", role="feinste Blutgefäße, in denen der Stoffaustausch mit "
                                          "den Zellen stattfindet"),
            Actor(name="Lunge", role="Organ, in dem das Blut Sauerstoff aufnimmt und "
                                     "Kohlendioxid abgibt"),
        ],
        # --- cause -> effect (the Wirkungsgefüge) -----------------------------
        causes=[
            CausalLink(cause="Der Herzmuskel zieht sich zusammen",
                       effect="Blut wird in den Kreislauf gepumpt", kind="ursache"),
            CausalLink(cause="Das Blut transportiert Sauerstoff",
                       effect="die Zellen können Energie gewinnen", kind="folge"),
            CausalLink(cause="Die Kapillarwände sind sehr dünn",
                       effect="Sauerstoff und Nährstoffe gelangen in die Zellen", kind="folge"),
            CausalLink(cause="Bei Anstrengung schlägt das Herz schneller",
                       effect="die Muskeln bekommen mehr Sauerstoff", kind="wirkung"),
        ],
        # --- Begriffe (complement the structures) -----------------------------
        concepts=[
            Concept(term="Körperkreislauf",
                    definition="der Weg des Blutes vom linken Herzen durch den Körper und "
                               "zurück zum rechten Herzen"),
            Concept(term="Lungenkreislauf",
                    definition="der Weg des Blutes vom rechten Herzen durch die Lunge und "
                               "zurück zum linken Herzen"),
            Concept(term="Doppelkreislauf",
                    definition="das Zusammenspiel von Lungen- und Körperkreislauf — das Blut "
                               "durchläuft das Herz zweimal pro Runde"),
            Concept(term="Puls",
                    definition="das fühlbare Pochen der Arterien im Takt des Herzschlags"),
        ],
        bedeutung="Der Blutkreislauf versorgt jede einzelne Zelle des Körpers mit Sauerstoff und "
                  "Nährstoffen und transportiert Abfallstoffe wie Kohlendioxid ab. Ohne diesen "
                  "ständigen Transport könnten die Organe nicht arbeiten — der Kreislauf ist die "
                  "Lebensader des Körpers.",
        gegenwartsbezug="Wer sich viel bewegt, hält Herz und Gefäße fit. Bewegungsmangel, Rauchen "
                        "und einseitige Ernährung können die Gefäße dagegen schädigen — "
                        "Herz-Kreislauf-Erkrankungen gehören zu den häufigsten Krankheiten. Den "
                        "eigenen Puls zu messen ist ein einfacher Blick auf die eigene Gesundheit.",
        urteilsfrage="„Für ein gesundes Herz ist Bewegung wichtiger als alles andere.“ Nimm zu "
                     "dieser Aussage Stellung: Welche Rolle spielen Bewegung, Ernährung und "
                     "Nichtrauchen für einen gesunden Blutkreislauf? Begründe, was du selbst tun "
                     "kannst.",
        # --- the Darstellung (authored over the facts; no dates → year-check vacuous) ---------
        darstellung=[
            DarstellungSection(
                heading="Warum wir einen Kreislauf brauchen",
                body="Jede einzelne Zelle deines Körpers braucht ständig Sauerstoff und "
                     "Nährstoffe und muss Abfallstoffe loswerden. Damit das überall gelingt, "
                     "pumpt das Herz das Blut in einem geschlossenen Kreislauf durch den ganzen "
                     "Körper.",
                grounded_by=["Herz", "Doppelkreislauf"]),
            DarstellungSection(
                heading="Der Weg des Blutes",
                body="Das Blut läuft in zwei Runden. Im Lungenkreislauf pumpt die rechte "
                     "Herzhälfte das sauerstoffarme Blut in die Lunge, wo es Sauerstoff aufnimmt "
                     "und Kohlendioxid abgibt. Im Körperkreislauf pumpt die linke Herzhälfte das "
                     "sauerstoffreiche Blut durch den ganzen Körper, bevor es zum Herzen "
                     "zurückkehrt.",
                grounded_by=["Lungenkreislauf", "Körperkreislauf", "Lunge"]),
            DarstellungSection(
                heading="Die Blutgefäße",
                body="Den Transport übernehmen drei verschiedene Gefäße. Die Arterien führen das "
                     "Blut vom Herzen weg, die Venen führen es zurück. Dazwischen liegen die "
                     "feinen Kapillaren: an ihren hauchdünnen Wänden tauschen Blut und Zellen "
                     "Sauerstoff, Nährstoffe und Abfallstoffe aus.",
                grounded_by=["Arterien", "Venen", "Kapillaren"]),
            DarstellungSection(
                heading="Das Herz als Pumpe",
                body="Das Herz ist ein kräftiger Muskel mit zwei Hälften. Es zieht sich "
                     "rhythmisch zusammen und presst dabei das Blut in die Arterien — dieses "
                     "Pochen kannst du als Puls fühlen. Bei Anstrengung schlägt das Herz "
                     "schneller, damit die Muskeln mehr Sauerstoff bekommen.",
                grounded_by=["Herz", "Puls"]),
        ],
    )


def build_content():
    """The derived WorksheetContent (for tests / the offline demo)."""
    from ..pipeline.sachverhalt import build_worksheet

    content, _ = build_worksheet(build_sachverhalt())
    return content
