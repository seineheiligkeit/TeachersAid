"""Fermi-Werkstatt grounding — the curated anchors + problems.

The estimation twin of `grounding/finanz.py` (curated legal tables) and `grounding/data/`
(cited datasets): a small, SME-vetted registry of **`FermiAnchor`**s (each quantity with its
value, honest `[low, high]` band, unit and provenance) and **`FermiProblem`**s (each a
question + an ordered arithmetic decomposition chain over those anchors). *Select the facts,
author the expression* (invariants §3): the anchor values are either selected from a cited
dataset, cited from an external source, or explicitly flagged as an **authored-then-vetted
estimate** with a plausibility rationale — never a bare invented fact.

**Anchor provenance at a glance** (the SME fact-checks the estimate rationales):
- `einwohner_wien`, `lebenserwartung_at` → **dataset** (our curated `grounding/data/` catalog).
- `personen_pro_haushalt` → **cited** (Statistik Austria household statistics).
- everything else → **vetted estimate** (no dataset exists for it), incl. the exact
  definitional conversions (`minuten_pro_tag`, `tage_pro_jahr`, `schultage_woche`) which carry
  `low == high` and a rationale saying so.

**Refresh discipline** (like the datasets/finanz tables): if a cited/dataset figure moves,
edit the anchor here and re-verify; `tests/test_fermi.py` locks the dataset-backed anchors
against the live dataset (anti-rot) and every anchor's `low <= value <= high`.
"""

from __future__ import annotations

from decimal import Decimal

from ..schema.datasets import SourceRef
from ..schema.fermi import (
    ChainStep,
    FermiAnchor,
    FermiCitation,
    FermiDatasetRef,
    FermiEstimate,
    FermiProblem,
)


def _D(x: str) -> Decimal:
    return Decimal(x)


# --- cited external sources --------------------------------------------------
# The average size of an Austrian Privathaushalt (~2.2 persons) is a published Statistik
# Austria figure; we SELECT it (fact), the student ESTIMATES it (skill). Verified 2026-07.
HAUSHALT_SOURCE = SourceRef(
    publisher="Statistik Austria",
    title="Haushalte und Familien — durchschnittliche Privathaushaltsgröße Österreich",
    url="https://www.statistik.at/statistiken/bevoelkerung-und-soziales/"
        "haushalte-familien-lebensformen",
    redistributable=True,
    attribution="Durchschnittliche Haushaltsgröße Österreich: Statistik Austria",
    stand="2024",
)


# --- the curated anchor registry --------------------------------------------
# Each FermiAnchor: value + honest [low, high] band + unit + provenance. Estimate rationales
# are the SME-critical part (they justify the range a teacher grades against).
_ANCHOR_LIST: list[FermiAnchor] = [
    # -- dataset-backed (selected from grounding/data/, cited via the dataset SourceRef) --
    FermiAnchor(
        id="einwohner_wien", label="Einwohner:innen von Wien",
        value=_D("2005760"), low=_D("2005760"), high=_D("2005760"), unit="Personen",
        provenance=FermiDatasetRef(
            dataset_id="statistik_austria_bundeslaender_2024", series="bevoelkerung",
            note="Bevölkerungsstand Wien, 1.1.2024 (exakte Zählung — als gegeben behandelt).")),
    FermiAnchor(
        id="lebenserwartung_at", label="Lebenserwartung bei Geburt in Österreich",
        value=_D("82"), low=_D("79"), high=_D("85"), unit="Jahre",
        provenance=FermiDatasetRef(
            dataset_id="statistik_austria_lebenserwartung_2002_2024", series="vergleich_aktuell",
            note="gerundetes Mittel aus m 79,8 / w 84,3 Jahre (2024); Band deckt beide "
                 "Geschlechter ab.")),

    # -- cited external source --------------------------------------------------
    FermiAnchor(
        id="personen_pro_haushalt", label="Personen pro Haushalt (Österreich)",
        value=_D("2.2"), low=_D("2.0"), high=_D("2.5"), unit="Personen",
        provenance=FermiCitation(source=HAUSHALT_SOURCE)),

    # -- exact definitional conversions (vetted estimate, low == high) ----------
    FermiAnchor(
        id="minuten_pro_tag", label="Minuten pro Tag",
        value=_D("1440"), low=_D("1440"), high=_D("1440"), unit="min",
        provenance=FermiEstimate(rationale="24 h · 60 min = 1440 min (exakte Umrechnung).")),
    FermiAnchor(
        id="tage_pro_jahr", label="Tage pro Jahr",
        value=_D("365"), low=_D("365"), high=_D("365"), unit="Tage",
        provenance=FermiEstimate(rationale="1 Jahr ≈ 365 Tage (ohne Schaltjahr; exakt genug).")),
    FermiAnchor(
        id="schultage_woche", label="Schultage pro Woche",
        value=_D("5"), low=_D("5"), high=_D("5"), unit="Tage",
        provenance=FermiEstimate(rationale="Schulwoche Mo–Fr = 5 Tage (exakt).")),

    # -- authored-then-vetted plausibility estimates (no dataset exists) --------
    FermiAnchor(
        id="wasser_pro_person_schultag",
        label="Wasserverbrauch pro Person und Schultag (in der Schule)",
        value=_D("15"), low=_D("10"), high=_D("25"), unit="L",
        provenance=FermiEstimate(rationale=(
            "In der Schule v.a. WC-Spülung (~6–9 L je Spülgang), Händewaschen und Trinkwasser. "
            "Deutlich unter dem Haushaltswert von ~130 L/Person/Tag, weil man nur einen Teil "
            "des Tages in der Schule ist. Plausibel 10–25 L."))),
    FermiAnchor(
        id="personen_schule", label="Personen an der Schule (Schüler:innen + Personal)",
        value=_D("600"), low=_D("400"), high=_D("900"), unit="Personen",
        provenance=FermiEstimate(rationale=(
            "Mittelgroße AHS: ~500–700 Schüler:innen plus ~50–90 Lehrpersonen und weiteres "
            "Personal. Als Szenario gegeben (die eigene Schule kann eingesetzt werden)."))),
    FermiAnchor(
        id="schueler_schule", label="Schüler:innen an der Schule",
        value=_D("500"), low=_D("350"), high=_D("800"), unit="Schüler:innen",
        provenance=FermiEstimate(rationale=(
            "Schüler:innenzahl einer mittelgroßen AHS. Als Szenario gegeben."))),
    FermiAnchor(
        id="schultage_jahr", label="Schultage pro Jahr",
        value=_D("180"), low=_D("170"), high=_D("190"), unit="Tage",
        provenance=FermiEstimate(rationale=(
            "Österreichisches Schuljahr: ~38–40 Unterrichtswochen · 5 Tage minus Feiertage "
            "und schulfreie Tage ≈ 180 Schultage."))),
    FermiAnchor(
        id="blatt_pro_schueler_tag", label="Blätter Papier pro Schüler:in und Schultag",
        value=_D("4"), low=_D("2"), high=_D("8"), unit="Blätter",
        provenance=FermiEstimate(rationale=(
            "Arbeitsblätter, Hefteinträge, Tests, Kopien: grob 2–8 Blätter pro Schüler:in "
            "und Schultag; Mittel ~4."))),
    FermiAnchor(
        id="klavier_anteil", label="Anteil der Haushalte mit stimmbarem Klavier",
        value=_D("0.02"), low=_D("0.01"), high=_D("0.04"), unit="",
        provenance=FermiEstimate(rationale=(
            "Anteil der Haushalte mit einem regelmäßig gespielten, stimmbaren Klavier: grob "
            "1–4 % (Klaviere sind seltener als Keyboards/Digitalpianos, die nicht gestimmt "
            "werden)."))),
    FermiAnchor(
        id="stimmung_pro_klavier_jahr", label="Stimmungen pro Klavier und Jahr",
        value=_D("1"), low=_D("0.5"), high=_D("2"), unit="",
        provenance=FermiEstimate(rationale=(
            "Ein regelmäßig gespieltes Klavier wird etwa 1× pro Jahr gestimmt (Wenigspieler "
            "seltener, Profis öfter): 0,5–2 pro Jahr."))),
    FermiAnchor(
        id="stimmung_pro_stimmer_tag", label="Stimmungen pro Klavierstimmer:in und Arbeitstag",
        value=_D("3"), low=_D("2"), high=_D("4"), unit="",
        provenance=FermiEstimate(rationale=(
            "Eine Stimmung dauert ~1,5–2 h; inklusive Anfahrt schafft eine Klavierstimmer:in "
            "etwa 2–4 pro Arbeitstag."))),
    FermiAnchor(
        id="arbeitstage_jahr", label="Arbeitstage pro Jahr",
        value=_D("220"), low=_D("200"), high=_D("230"), unit="Tage",
        provenance=FermiEstimate(rationale=(
            "365 minus ~104 Wochenendtage, ~13 Feiertage und ~25 Urlaubstage ≈ 220 "
            "Arbeitstage."))),
    FermiAnchor(
        id="km_pro_schueler_tag", label="Schulweg pro Schüler:in und Tag (hin und zurück)",
        value=_D("4"), low=_D("2"), high=_D("8"), unit="km",
        provenance=FermiEstimate(rationale=(
            "Viele Schulwege 1–3 km einfach, manche deutlich länger (Bus/Bahn). Hin und "
            "zurück grob 4 km im Mittel (Band 2–8)."))),
    FermiAnchor(
        id="puls_ruhe", label="Ruhepuls (Herzschläge pro Minute)",
        value=_D("70"), low=_D("60"), high=_D("90"), unit="Schläge/min",
        provenance=FermiEstimate(rationale=(
            "Ruhepuls eines Jugendlichen/Erwachsenen ~60–80/min; über ein ganzes Leben liegt "
            "der Durchschnittspuls etwas höher (Aktivität), daher Band 60–90."))),
    FermiAnchor(
        id="raum_laenge", label="Länge des Klassenzimmers",
        value=_D("8"), low=_D("7"), high=_D("10"), unit="m",
        provenance=FermiEstimate(rationale="Typisches Klassenzimmer ~7–10 m lang.")),
    FermiAnchor(
        id="raum_breite", label="Breite des Klassenzimmers",
        value=_D("7"), low=_D("6"), high=_D("8"), unit="m",
        provenance=FermiEstimate(rationale="Typisches Klassenzimmer ~6–8 m breit.")),
    FermiAnchor(
        id="raum_hoehe", label="Höhe des Klassenzimmers",
        value=_D("3"), low=_D("2.7"), high=_D("3.5"), unit="m",
        provenance=FermiEstimate(rationale="Raumhöhe (Neubau ~2,7 m, Altbau bis ~3,5 m).")),
    FermiAnchor(
        id="ballon_volumen", label="Rauminhalt eines aufgeblasenen Luftballons",
        value=_D("0.005"), low=_D("0.004"), high=_D("0.007"), unit="m³",
        provenance=FermiEstimate(rationale=(
            "Ein aufgeblasener Luftballon fasst ~4–7 L = 0,004–0,007 m³ (Kugel mit ~20–24 cm "
            "Durchmesser)."))),
]

ANCHORS: dict[str, FermiAnchor] = {a.id: a for a in _ANCHOR_LIST}


# --- the curated problem registry -------------------------------------------
# The dimension is always MOD (Modellieren und Problemlösen — a Fermi problem is the
# archetype of a modelling task); the served competence is the content competence whose
# quantities the chain computes (ZAH "Zahlen und Maße" for arithmetic/Größen, FIG for the
# volume problem). All verified verbatim in lehrplan/MAT.json.
_PROBLEM_LIST: list[FermiProblem] = [
    FermiProblem(
        id="schulwasser",
        title="Trinkwasser der Schule",
        question="Wie viel Wasser verbraucht unsere Schule in einem ganzen Schuljahr?",
        chain=[
            ChainStep(anchor_id="wasser_pro_person_schultag", op="multiply"),
            ChainStep(anchor_id="personen_schule", op="multiply", given=True),
            ChainStep(anchor_id="schultage_jahr", op="multiply"),
        ],
        result_unit="L", result_label="Liter Wasser pro Schuljahr",
        klasse=3, competence_id="MAT.US.3.ZAH.01", kompetenzbereich="Zahlen und Maße",
        context_note="Nimm eine mittelgroße Schule mit rund 600 Personen an "
                     "(oder setze die Zahl eurer eigenen Schule ein)."),
    FermiProblem(
        id="schulpapier",
        title="Papierverbrauch der Schule",
        question="Wie viele Blätter Papier verbraucht unsere Schule in einem Schuljahr?",
        chain=[
            ChainStep(anchor_id="blatt_pro_schueler_tag", op="multiply"),
            ChainStep(anchor_id="schueler_schule", op="multiply", given=True),
            ChainStep(anchor_id="schultage_jahr", op="multiply"),
        ],
        result_unit="Blätter", result_label="Blätter Papier pro Schuljahr",
        klasse=2, competence_id="MAT.US.2.ZAH.04", kompetenzbereich="Zahlen und Maße",
        context_note="Nimm eine Schule mit rund 500 Schüler:innen an."),
    FermiProblem(
        id="klavierstimmer_wien",
        title="Klavierstimmer:innen in Wien",
        question="Wie viele Klavierstimmer:innen arbeiten (ungefähr) in Wien?",
        chain=[
            ChainStep(anchor_id="einwohner_wien", op="multiply", given=True),
            ChainStep(anchor_id="personen_pro_haushalt", op="divide"),
            ChainStep(anchor_id="klavier_anteil", op="multiply"),
            ChainStep(anchor_id="stimmung_pro_klavier_jahr", op="multiply"),
            ChainStep(anchor_id="stimmung_pro_stimmer_tag", op="divide"),
            ChainStep(anchor_id="arbeitstage_jahr", op="divide"),
        ],
        result_unit="Klavierstimmer:innen", result_label="Klavierstimmer:innen in Wien",
        klasse=4, competence_id="MAT.US.4.ZAH.01", kompetenzbereich="Zahlen und Maße",
        context_note="Die berühmte Fermi-Frage: niemand kennt die Zahl genau — aber man kann "
                     "sie erstaunlich gut schätzen. Gegeben ist nur die Einwohnerzahl Wiens."),
    FermiProblem(
        id="schulweg_woche",
        title="Schulweg-Kilometer pro Woche",
        question="Wie viele Kilometer legen alle Schüler:innen unserer Schule an einem "
                 "Schulweg-Tag zusammen zurück — und wie viele in einer ganzen Schulwoche?",
        chain=[
            ChainStep(anchor_id="km_pro_schueler_tag", op="multiply"),
            ChainStep(anchor_id="schueler_schule", op="multiply", given=True),
            ChainStep(anchor_id="schultage_woche", op="multiply", given=True),
        ],
        result_unit="km", result_label="Schulweg-Kilometer pro Woche",
        klasse=3, competence_id="MAT.US.3.ZAH.01", kompetenzbereich="Zahlen und Maße",
        context_note="„Schulweg pro Tag“ heißt hin UND zurück. Nimm rund 500 Schüler:innen "
                     "und 5 Schultage pro Woche an."),
    FermiProblem(
        id="herzschlaege_leben",
        title="Herzschläge in einem Leben",
        question="Wie oft schlägt das Herz eines Menschen in einem ganzen Leben?",
        chain=[
            ChainStep(anchor_id="puls_ruhe", op="multiply"),
            ChainStep(anchor_id="minuten_pro_tag", op="multiply", given=True),
            ChainStep(anchor_id="tage_pro_jahr", op="multiply", given=True),
            ChainStep(anchor_id="lebenserwartung_at", op="multiply", given=True),
        ],
        result_unit="Schläge", result_label="Herzschläge in einem Leben",
        klasse=3, competence_id="MAT.US.3.ZAH.01", kompetenzbereich="Zahlen und Maße",
        context_note="Gegeben sind die Umrechnungen (1440 min pro Tag, 365 Tage pro Jahr) und "
                     "die Lebenserwartung (~82 Jahre, Statistik Austria). Schätzen musst du "
                     "nur den Ruhepuls."),
    FermiProblem(
        id="klassenzimmer_ballons",
        title="Luftballons im Klassenzimmer",
        question="Wie viele aufgeblasene Luftballons braucht man, um euer Klassenzimmer "
                 "vollständig zu füllen?",
        chain=[
            ChainStep(anchor_id="raum_laenge", op="multiply"),
            ChainStep(anchor_id="raum_breite", op="multiply"),
            ChainStep(anchor_id="raum_hoehe", op="multiply"),
            ChainStep(anchor_id="ballon_volumen", op="divide"),
        ],
        result_unit="Luftballons", result_label="Luftballons für das Klassenzimmer",
        klasse=3, competence_id="MAT.US.3.FIG.03", kompetenzbereich="Figuren und Körper",
        context_note="Das Klassenzimmer ist (fast) ein Quader: Rauminhalt = Länge · Breite · "
                     "Höhe. Messt es aus oder schätzt die drei Maße."),
]

PROBLEMS: dict[str, FermiProblem] = {p.id: p for p in _PROBLEM_LIST}


# --- accessors --------------------------------------------------------------
def get_anchor(anchor_id: str) -> FermiAnchor:
    a = ANCHORS.get(anchor_id)
    if a is None:
        raise KeyError(f"unknown Fermi anchor '{anchor_id}'")
    return a


def get_problem(problem_id: str) -> FermiProblem:
    p = PROBLEMS.get(problem_id)
    if p is None:
        raise KeyError(f"unknown Fermi problem '{problem_id}'")
    return p


def list_problems() -> list[FermiProblem]:
    return list(_PROBLEM_LIST)
