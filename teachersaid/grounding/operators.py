"""Standardized SRDP *Operatoren* — the controlled task-verb vocabulary (grounding).

Austria's *standardisierte kompetenzorientierte Reife- und Diplomprüfung* (SRDP) uses
published sets of **Operatoren** (task verbs). Anchoring generated task prompts to these
standardized verbs makes our tasks read as genuinely *Matura-oriented* and gives the
abstract ``cognitive_level`` a concrete, recognisable surface form a teacher trusts.

**This is GROUNDING, not an asset class.** Like the competence catalog or the ÜT legend,
it is a controlled vocabulary *injected into the generation brief*
(``llm/prompts.build_system``) — selected, never authored. The Matura shapes *what our
tasks ask*; it is not stored as content.

**The catalogs are subject-specific AND structurally different** — the SRDP publishes one
per subject (group), and they do not share a shape, so we store each faithfully rather than
forcing one mould:

- **Deutsch** — operators banded by **Anforderungsbereich (AFB)** with definitions:
  AFB 1 Reproduktion · AFB 2 Reorganisation und Transfer · AFB 3 Reflexion und Problemlösung.
- **Naturwissenschaften (Biologie/Physik/Chemie)** — operators dual-tagged by AFB
  (Rp/Tr/Rf) **and** by the science competence model **W/E/S** (Fachwissen · Erkenntnis­
  gewinnung · Standpunkte) — the exact model our science ``SubjectCompetenceModel`` uses.
- **Mathematik / Angewandte Mathematik** — a **flat list, NOT AFB-banded** in the official
  source; each operator instead carries a preferred **Antwortformat** (offen/halboffen/
  Konstruktion/MC/Zuordnung/Lückentext), which maps onto our ``kind``/``ResponseSpec``.

A subject without a curated catalog falls back to a clearly-flagged generic palette.

This banding ties into the depth ladder we already use: ``CognitiveLevel`` maps to an AFB
(see ``pipeline/difficulty.py``; a test locks the two identical). Two official fidelity
notes are honoured: (1) an operator is **not strictly 1:1 with one AFB** — the same verb
sits in different bands depending on the task (so an operator may appear under more than one
band, and the brief calls this out); (2) the AFB hierarchy is rising **Eigenständigkeit, not
difficulty** — which is exactly why our AFB→``difficulty`` mapping is an overridable default,
not a measurement.

Sources (all CC BY via IWG 2022, published by BMBWF/IQS / AECC):
- Deutsch: *"Typen sprachlichen Handelns (Operatoren) in der SRDP Deutsch"* (U. Abraham &
  A. Saxalber, Stand Okt. 2016).
- Mathematik/AMT: *"Operatorenliste für die SRP Mathematik und die SRDP Angewandte
  Mathematik"* (IQS, Stand 13.3.2023).
- Naturwissenschaften: *"Operatoren in der mündlichen und schriftlichen kompetenz­
  orientierten Reifeprüfung Biologie & Umweltkunde"* (A. Reichstädter & B. Müllner,
  AECC-Biologie, Univ. Wien, Stand Juni 2018, V3) — the W/E/S tags are read verbatim from
  the catalog's grid. Used as the shared *Naturwissenschaften* base for BIO/PHY/CHE
  (shared W/E/S); PHY/CHE may later refine with their own subject specifics.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schema.enums import COGNITIVE_RANK, CognitiveLevel

AFB_LABEL: dict[int, str] = {
    1: "Reproduktion",
    2: "Reorganisation und Transfer",
    3: "Reflexion und Problemlösung",
}

# Mathematik Antwortformat codes → human labels (for the brief legend).
ANSWER_FORMAT_LABEL: dict[str, str] = {
    "o": "offen", "ho": "halboffen", "k": "Konstruktion",
    "mc": "Multiple-Choice", "z": "Zuordnung", "l": "Lückentext",
}

# cognitive rank (0..5) → AFB band (1..3). Kept IDENTICAL to
# ``pipeline.difficulty._RANK_TO_BAND`` so operators and difficulty speak one ladder
# (a test locks this invariant).
_RANK_TO_AFB: dict[int, int] = {0: 1, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3}


@dataclass(frozen=True)
class Operator:
    """A task verb (with its published equivalent forms) and the action it demands.

    ``afb`` is the AFB band(s) 1/2/3 the source assigns (empty for catalogs that are not
    AFB-banded, e.g. Mathematik). ``wes`` is the science competence area(s) W/E/S
    (Naturwissenschaften only). ``answer_format`` is the Mathematik preferred Antwortformat.
    """
    forms: str
    definition: str = ""
    afb: tuple[int, ...] = ()
    wes: tuple[str, ...] = ()
    answer_format: str = ""

    def __str__(self) -> str:
        return self.forms


# --- Deutsch — AUTHORITATIVE (BIFIE/IQS, Stand Okt. 2016) -----------------------------
DEUTSCH: list[Operator] = [
    Operator("(be)nennen", "Informationen, Aspekte eines Sachverhalts, Fakten, Begriffe "
             "ohne nähere Erläuterungen und Wertungen knapp und strukturiert aufführen",
             afb=(1,)),
    Operator("beschreiben", "Sachverhalte, Situationen, Vorgänge, äußere Merkmale von "
             "Personen bzw. Figuren strukturiert und genau darlegen", afb=(1,)),
    Operator("wiedergeben", "Inhalte, Aussagen, Zusammenhänge in eigenen Worten sachlich "
             "darlegen", afb=(1,)),
    Operator("zusammenfassen", "Inhalte, Aussagen, Zusammenhänge komprimiert und in "
             "sinnvoller Anordnung darlegen", afb=(1,)),
    Operator("analysieren / untersuchen", "unter Bezugnahme auf spezifische "
             "Fragestellungen Elemente, Strukturmerkmale, Zusammenhänge eines Textes "
             "herausarbeiten, belegen und strukturiert fachsprachlich darlegen", afb=(2,)),
    Operator("bestimmen / einordnen / zuordnen", "Aussagen, Texte, Sachverhalte unter "
             "Verwendung von Kontextwissen Kategorien oder Aspekten zuweisen und diese "
             "Zuordnungen nachvollziehbar begründen", afb=(2,)),
    Operator("charakterisieren", "die jeweilige Eigenart von Figuren, Sachverhalten "
             "erfassen und treffend formulieren", afb=(2,)),
    Operator("erklären", "Verhaltensweisen und Sachverhalte auf Ursachen zurückführen und "
             "verständlich und differenziert darlegen", afb=(2,)),
    Operator("erläutern", "komplexe Sachverhalte durch zusätzliche Informationen und/oder "
             "Beispiele veranschaulichen, verdeutlichen", afb=(2,)),
    Operator("erschließen", "etwas nicht explizit Formuliertes aus einem Text ermitteln "
             "und darlegen", afb=(2,)),
    Operator("in Beziehung setzen", "Zusammenhänge unter vorgegebenen oder selbst "
             "gewählten Gesichtspunkten herstellen und darlegen", afb=(2,)),
    Operator("vergleichen / einander gegenüberstellen", "nach Gesichtspunkten "
             "Gemeinsamkeiten, Ähnlichkeiten und Unterschiede herausarbeiten, abwägen und "
             "strukturiert formulieren", afb=(2,)),
    Operator("appellieren", "an eine Einzelperson, ein Publikum, eine Institution mit "
             "einer begründeten Bitte/Aufforderung schriftlich herantreten", afb=(3,)),
    Operator("begründen / Gründe angeben", "Analyseergebnisse, Urteile, Wertungen fachlich "
             "und sachlich absichern (durch Argumente, Belege, Beispiele)", afb=(3,)),
    Operator("beurteilen", "hinsichtlich von Texten, Aussagen, Sachverhalten zu einem "
             "selbstständigen Urteil gelangen und dieses argumentativ stützen", afb=(3,)),
    Operator("bewerten", "wie „beurteilen“, jedoch verbunden mit der Offenlegung "
             "begründeter eigener Wertmaßstäbe", afb=(3,)),
    Operator("deuten / interpretieren", "auf der Grundlage einer Analyse Sinnzusammenhänge "
             "eines Textes herausarbeiten und unter Einbeziehung von Inhalt, Form und "
             "Sprache eine schlüssige Deutung formulieren", afb=(3,)),
    Operator("diskutieren / erörtern / sich auseinandersetzen mit", "Aussagen, Thesen, "
             "Problemstellungen anhand von Pro- und Kontraargumenten abwägen und eine "
             "begründete eigene Stellungnahme verfassen", afb=(3,)),
    Operator("entwerfen", "ein Konzept, ein Szenario, einen Plan nachvollziehbar in groben "
             "Zügen darlegen", afb=(3,)),
    Operator("kommentieren / Stellung nehmen", "die Einschätzung einer Problemstellung, "
             "Wertung, eines Sachverhalts nach kritischer Prüfung formulieren", afb=(3,)),
    Operator("(über)prüfen", "Aussagen, Thesen, Argumentationen kritisch hinterfragen und "
             "ihre Gültigkeit kriterienorientiert und begründet einschätzen", afb=(3,)),
    Operator("vorschlagen / Vorschläge machen", "Ideen für den Umgang mit Problemen oder "
             "Vorgehensweisen in einer Situation formulieren", afb=(3,)),
]

# --- Naturwissenschaften (BIO/PHY/CHE) — AECC-Bio, Stand Juni 2018 --------------------
# afb (Rp/Tr/Rf) and wes (W/E/S) read verbatim from the catalog's grid.
NATURWISSENSCHAFTEN: list[Operator] = [
    Operator("analysieren / untersuchen", "Texte, Daten, Diagramme systematisch auf "
             "Zusammenhänge oder Strukturmerkmale untersuchen und strukturiert darstellen",
             afb=(2,), wes=("E",)),
    Operator("argumentieren", "Behauptungen, Einschätzungen oder Wertungen durch "
             "naturwissenschaftlich fundierte Belege, Beispiele oder Vergleiche stützen",
             afb=(2, 3), wes=("S",)),
    Operator("begründen", "einen Sachverhalt, ein Analyseergebnis, ein Urteil auf kausale "
             "Zusammenhänge zurückführen", afb=(2, 3), wes=("E", "S")),
    Operator("benennen", "konkreten Elementen einen Namen bzw. eine Bezeichnung zuordnen",
             afb=(2,), wes=("W",)),
    Operator("beschreiben", "Prozesse, Sachverhalte, Zusammenhänge strukturiert und präzise "
             "unter Verwendung der Fachsprache darlegen", afb=(1, 2), wes=("W",)),
    Operator("beschriften", "Elementen in einer Skizze, Zeichnung oder Abbildung einen "
             "Namen zuordnen", afb=(2,), wes=("W",)),
    Operator("beurteilen", "zu einem Sachverhalt ein selbstständiges Urteil unter "
             "Verwendung von Fachwissen und Fachmethoden formulieren und argumentativ "
             "stützen", afb=(2, 3), wes=("S",)),
    Operator("darstellen", "Zusammenhänge, Sachverhalte in eine bildliche Darstellungsform "
             "übertragen", afb=(2,), wes=("W",)),
    Operator("definieren", "charakteristische, abgrenzende Merkmale eines Begriffes "
             "herausarbeiten", afb=(1,), wes=("W",)),
    Operator("diskutieren", "Pro- und Kontra-Argumente zu einer Aussage, Problemstellung "
             "oder These gegenüberstellen", afb=(2, 3), wes=("S",)),
    Operator("entwickeln", "Strategien, Hypothesen, Konzepte oder ein Schema zur Lösung "
             "einer Problemstellung erarbeiten", afb=(2, 3), wes=("E",)),
    Operator("erklären", "einen Sachverhalt auf Regeln und Gesetzmäßigkeiten zurückführen "
             "und ihn nachvollziehbar darlegen", afb=(1, 2), wes=("W",)),
    Operator("erläutern", "einen Sachverhalt auf Regeln und Gesetzmäßigkeiten zurückführen "
             "und ihn durch zusätzliche Informationen verständlich darlegen", afb=(1, 2),
             wes=("W",)),
    Operator("erörtern", "Pro- und Kontra-Argumente abwägen und auf dieser Grundlage eine "
             "Schlussfolgerung bzw. eigene Stellungnahme widerspruchsfrei darlegen",
             afb=(3,), wes=("S",)),
    Operator("interpretieren", "Erklärungsmöglichkeiten von Sachverhalten, Zusammenhängen "
             "und Analyseergebnissen herausarbeiten", afb=(2,), wes=("E",)),
    Operator("kritisch Stellung nehmen", "nach kritischer Prüfung zu einer strittigen "
             "Problemstellung, Wertung, Aussage ein eigenes Urteil widerspruchsfrei "
             "darlegen", afb=(2, 3), wes=("S",)),
    Operator("nennen", "Sachverhalte, Begriffe, Daten und Fakten ohne nähere Erläuterung "
             "und Wertung anführen", afb=(1, 2), wes=("W",)),
    Operator("vergleichen", "Gemeinsamkeiten, Ähnlichkeiten und Unterschiede von "
             "Sachverhalten, Lebewesen und Vorgängen herausarbeiten und strukturiert "
             "gegenüberstellen", afb=(2,), wes=("W", "E", "S")),
    Operator("zeichnen", "beobachtbare oder gegebene Strukturen skizzenhaft darstellen",
             afb=(1, 2), wes=("W",)),
    Operator("zusammenfassen", "Inhalte eines Textes, Aussagen, Zusammenhänge und "
             "Ergebnisse von Untersuchungen in konzentrierter Form darlegen", afb=(1, 2),
             wes=("W",)),
]

# --- Mathematik / Angewandte Mathematik — IQS, Stand 13.3.2023 ------------------------
# Flat list (the official source is NOT AFB-banded); each carries a preferred Antwortformat.
MATHEMATIK: list[Operator] = [
    Operator("ablesen", answer_format="ho/o"),
    Operator("(ab)schätzen", answer_format="ho/o"),
    Operator("angeben", answer_format="ho/o"),
    Operator("ankreuzen", answer_format="mc"),
    Operator("argumentieren", answer_format="o"),
    Operator("aufstellen", answer_format="ho/o"),
    Operator("begründen / erklären", answer_format="o"),
    Operator("berechnen / ermitteln", answer_format="o/ho"),
    Operator("beschreiben", answer_format="o"),
    Operator("beschriften", answer_format="k/ho"),
    Operator("eintragen", answer_format="ho"),
    Operator("einzeichnen", answer_format="k"),
    Operator("ergänzen", answer_format="l"),
    Operator("erstellen", answer_format="ho/o"),
    Operator("interpretieren / Bedeutung beschreiben", answer_format="o"),
    Operator("kennzeichnen / markieren", answer_format="k"),
    Operator("nachweisen / zeigen", answer_format="o"),
    Operator("skizzieren", answer_format="k"),
    Operator("überprüfen", answer_format="o"),
    Operator("umformen", answer_format="ho"),
    Operator("veranschaulichen", answer_format="k"),
    Operator("vervollständigen", answer_format="ho"),
    Operator("zuordnen", answer_format="z"),
]

# --- Generic fallback — PROVISIONAL (no subject catalog curated yet) ------------------
# Common German task verbs that span subjects; replace per subject as official catalogs
# are curated (remaining: GWB, Fremdsprachen, Latein, Geometrisches Zeichnen, …).
DEFAULT: list[Operator] = [
    Operator("nennen", afb=(1,)), Operator("benennen", afb=(1,)),
    Operator("beschreiben", afb=(1,)), Operator("angeben", afb=(1,)),
    Operator("darstellen", afb=(1,)), Operator("wiedergeben", afb=(1,)),
    Operator("zusammenfassen", afb=(1,)), Operator("skizzieren", afb=(1,)),
    Operator("erklären", afb=(2,)), Operator("erläutern", afb=(2,)),
    Operator("vergleichen", afb=(2,)), Operator("analysieren", afb=(2,)),
    Operator("einordnen", afb=(2,)), Operator("anwenden", afb=(2,)),
    Operator("berechnen", afb=(2,)), Operator("ermitteln", afb=(2,)),
    Operator("charakterisieren", afb=(2,)),
    Operator("begründen", afb=(3,)), Operator("beurteilen", afb=(3,)),
    Operator("bewerten", afb=(3,)), Operator("Stellung nehmen", afb=(3,)),
    Operator("diskutieren", afb=(3,)), Operator("erörtern", afb=(3,)),
    Operator("überprüfen", afb=(3,)), Operator("interpretieren", afb=(3,)),
    Operator("entwickeln", afb=(3,)),
]

# subject name → authoritative catalog. Subjects absent here use DEFAULT.
# BIO/PHY/CHE share the Naturwissenschaften catalog (shared W/E/S model); PHY/CHE may
# later get their own refinements (SME to confirm).
SUBJECT_OPERATORS: dict[str, list[Operator]] = {
    "Deutsch": DEUTSCH,
    "Mathematik": MATHEMATIK,
    "Biologie": NATURWISSENSCHAFTEN,
    "Physik": NATURWISSENSCHAFTEN,
    "Chemie": NATURWISSENSCHAFTEN,
}


def operator_set(subject: str | None) -> list[Operator]:
    """The operator catalog for a subject — its authoritative list if curated, else the
    generic fallback."""
    return SUBJECT_OPERATORS.get(subject or "", DEFAULT)


def is_authoritative(subject: str | None) -> bool:
    return (subject or "") in SUBJECT_OPERATORS


def is_banded(catalog: list[Operator]) -> bool:
    """True if the catalog assigns AFB bands (Deutsch/Naturwissenschaften), False for a
    flat list (Mathematik)."""
    return any(o.afb for o in catalog)


def afb_for_level(cognitive_level: str) -> int:
    """The Anforderungsbereich band (1..3) of a ``cognitive_level`` string."""
    rank = COGNITIVE_RANK.get(cognitive_level, 1)
    return _RANK_TO_AFB.get(rank, 2)


def operators_for_level(cognitive_level: str, subject: str | None = None) -> list[Operator]:
    """The standardized operators that fit a ``cognitive_level`` for a subject. For a
    banded catalog: operators whose AFB band-set includes the level's band. For a flat
    catalog (Mathematik): the whole list (the source carries no band)."""
    catalog = operator_set(subject)
    if not is_banded(catalog):
        return catalog
    band = afb_for_level(cognitive_level)
    return [o for o in catalog if band in o.afb]


def format_operators_brief(subject: str | None = None) -> str:
    """A compact palette for the generation system prompt, in the shape that fits the
    subject's catalog (AFB-banded, or flat with answer formats)."""
    catalog = operator_set(subject)
    tag = subject if is_authoritative(subject) else "generic — subject catalog pending"

    if not is_banded(catalog):  # Mathematik: flat list + Antwortformat
        legend = ", ".join(f"{k}={v}" for k, v in ANSWER_FORMAT_LABEL.items())
        verbs = ", ".join(f"{o.forms} ({o.answer_format})" for o in catalog)
        return (
            f"Standardized SRDP Operatoren ({tag}) — the official list is not AFB-banded; "
            f"each carries a preferred answer format ({legend}). Use an apt operator per "
            f"task:\n  {verbs}"
        )

    lines = [
        f"Standardized SRDP Operatoren ({tag}) by Anforderungsbereich — phrase each task's "
        "prompt with an apt operator for its cognitive_level (these are the typical homes, "
        "not a strict 1:1 mapping):"
    ]
    for band in (1, 2, 3):
        levels = [cl.value for cl in CognitiveLevel
                  if _RANK_TO_AFB[COGNITIVE_RANK[cl]] == band]
        verbs = ", ".join(o.forms for o in catalog if band in o.afb)
        lines.append(
            f"  - AFB {band} ({AFB_LABEL[band]}) [{', '.join(levels)}]: {verbs}"
        )
    return "\n".join(lines)
