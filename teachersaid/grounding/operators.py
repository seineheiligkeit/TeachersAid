"""Standardized SRDP *Operatoren* — the controlled task-verb vocabulary (grounding).

Austria's *standardisierte kompetenzorientierte Reife- und Diplomprüfung* (SRDP) uses
published sets of **Operatoren** (task verbs) sorted by **Anforderungsbereich (AFB)**:

    AFB 1 — Reproduktion
    AFB 2 — Reorganisation und Transfer
    AFB 3 — Reflexion und Problemlösung

This is exactly the depth ladder we already use: ``CognitiveLevel`` maps to an
Anforderungsbereich (see ``pipeline/difficulty.py``). Anchoring generated task prompts to
these standardized verbs makes our tasks read as genuinely *Matura-oriented* and gives the
abstract ``cognitive_level`` a concrete, recognisable surface form a teacher trusts.

**This is GROUNDING, not an asset class.** Like the competence catalog or the ÜT legend,
it is a controlled vocabulary *injected into the generation brief*
(``llm/prompts.build_system``) — selected, never authored. The Matura shapes *what our
tasks ask*; it is not stored as content.

**Operators are subject-specific.** The SRDP publishes one operator catalog per subject
(group): Deutsch, the lebende Fremdsprachen, the sciences, Mathematik, GWB, … each has its
own. Applying Deutsch's text-handling verbs to a physics task would be wrong (it would miss
``berechnen`` / ``skizzieren`` / ``protokollieren``). So the table is keyed by subject, and
a subject without a curated catalog falls back to a generic palette.

Two fidelity notes from the official guidance:
- An operator is **not strictly 1:1 with one AFB** — the same verb sits in different bands
  depending on the concrete task and prior knowledge (``beschreiben`` of a given text is
  AFB 1; ``beschreiben`` of one's own ideas is AFB 3). The banding is the *typical* home,
  offered to the generator as a palette, not a hard rule.
- The AFB hierarchy is an increase in **Eigenständigkeit, not necessarily difficulty** — a
  hard text to summarise (AFB 1) can be harder than a Stellungnahme to a simple question
  (AFB 3). This is exactly why our AFB→``difficulty`` mapping is an honest *default* an SME
  can override (see ``pipeline/difficulty.py``), not a measurement.

Source (Deutsch, authoritative): *"Typen sprachlichen Handelns ('Operatoren') in der SRDP
Deutsch"*, BIFIE/IQS (U. Abraham & A. Saxalber), Stand Oktober 2016 — published on
matura.gv.at, CC BY (IWG 2022). The generic fallback is PROVISIONAL until each subject's
official catalog is curated.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schema.enums import COGNITIVE_RANK, CognitiveLevel

AFB_LABEL: dict[int, str] = {
    1: "Reproduktion",
    2: "Reorganisation und Transfer",
    3: "Reflexion und Problemlösung",
}

# cognitive rank (0..5) → AFB band (1..3). Kept IDENTICAL to
# ``pipeline.difficulty._RANK_TO_BAND`` so operators and difficulty speak one ladder
# (a test locks this invariant).
_RANK_TO_AFB: dict[int, int] = {0: 1, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3}


@dataclass(frozen=True)
class Operator:
    """A task verb (with its published equivalent forms) and the action it demands."""
    forms: str            # e.g. "vergleichen / einander gegenüberstellen"
    definition: str = ""  # the official specification of the demanded action

    def __str__(self) -> str:
        return self.forms


# --- Deutsch — AUTHORITATIVE (BIFIE/IQS, Stand Okt. 2016) -----------------------------
DEUTSCH: dict[int, list[Operator]] = {
    1: [
        Operator("(be)nennen", "Informationen, Aspekte eines Sachverhalts, Fakten, "
                 "Begriffe ohne nähere Erläuterungen und Wertungen knapp und "
                 "strukturiert aufführen"),
        Operator("beschreiben", "Sachverhalte, Situationen, Vorgänge, äußere Merkmale "
                 "von Personen bzw. Figuren strukturiert und genau darlegen"),
        Operator("wiedergeben", "Inhalte, Aussagen, Zusammenhänge in eigenen Worten "
                 "sachlich darlegen"),
        Operator("zusammenfassen", "Inhalte, Aussagen, Zusammenhänge komprimiert und in "
                 "sinnvoller Anordnung darlegen"),
    ],
    2: [
        Operator("analysieren / untersuchen", "unter Bezugnahme auf spezifische "
                 "Fragestellungen Elemente, Strukturmerkmale, Zusammenhänge eines Textes "
                 "herausarbeiten, nach Möglichkeit belegen und die Ergebnisse "
                 "strukturiert und fachsprachlich angemessen darlegen"),
        Operator("bestimmen / einordnen / zuordnen", "Aussagen, Texte, Sachverhalte, "
                 "Merkmale unter Verwendung von Kontextwissen bestimmten Kategorien oder "
                 "Aspekten zuweisen und diese Zuordnungen nachvollziehbar begründen"),
        Operator("charakterisieren", "die jeweilige Eigenart von Figuren, Sachverhalten "
                 "erfassen und treffend formulieren"),
        Operator("erklären", "Verhaltensweisen und Sachverhalte auf real feststellbare "
                 "oder vermutete Ursachen zurückführen und diese verständlich und "
                 "differenziert darlegen"),
        Operator("erläutern", "komplexe Sachverhalte durch zusätzliche Informationen "
                 "und/oder Beispiele veranschaulichen, verdeutlichen"),
        Operator("erschließen", "etwas nicht explizit Formuliertes aus einem Text "
                 "ermitteln und darlegen"),
        Operator("in Beziehung setzen", "Zusammenhänge unter vorgegebenen oder selbst "
                 "gewählten Gesichtspunkten herstellen und darlegen"),
        Operator("vergleichen / einander gegenüberstellen", "nach vorgegebenen oder "
                 "selbst gewählten Gesichtspunkten Gemeinsamkeiten, Ähnlichkeiten und "
                 "Unterschiede herausarbeiten, gegeneinander abwägen und strukturiert "
                 "formulieren"),
    ],
    3: [
        Operator("appellieren", "an eine zuständige Einzelperson, ein Publikum, eine "
                 "Institution mit einer begründeten Bitte/Aufforderung schriftlich "
                 "herantreten"),
        Operator("begründen / Gründe angeben", "Analyseergebnisse, Urteile, "
                 "Einschätzungen, Wertungen fachlich und sachlich absichern (durch "
                 "Argumente, Belege, Beispiele)"),
        Operator("beurteilen", "hinsichtlich von Texten, Aussagen, Sachverhalten, Figuren "
                 "zu einem selbstständigen Urteil gelangen und dieses argumentativ "
                 "stützen"),
        Operator("bewerten", "wie „beurteilen“, jedoch verbunden mit der Offenlegung "
                 "begründeter eigener Wertmaßstäbe"),
        Operator("deuten / interpretieren", "auf der Grundlage einer Analyse "
                 "Sinnzusammenhänge eines Textes herausarbeiten und unter Einbeziehung "
                 "der Wechselwirkung zwischen Inhalt, Form und Sprache eine schlüssige "
                 "Deutung formulieren"),
        Operator("diskutieren / erörtern / sich auseinandersetzen mit", "Aussagen, "
                 "Thesen, Problemstellungen anhand von Pro- und Kontraargumenten abwägen "
                 "und auf dieser Grundlage eine begründete eigene Stellungnahme verfassen"),
        Operator("entwerfen", "ein Konzept, ein Szenario, einen Plan nachvollziehbar in "
                 "groben Zügen darlegen"),
        Operator("kommentieren / Stellung nehmen", "die Einschätzung einer "
                 "Problemstellung, Wertung, eines Sachverhalts nach kritischer Prüfung "
                 "formulieren"),
        Operator("(über)prüfen", "Aussagen, Thesen, Argumentationen auf Grundlage "
                 "fachlicher Kenntnis kritisch hinterfragen und ihre Gültigkeit "
                 "kriterienorientiert und begründet einschätzen"),
        Operator("vorschlagen / Vorschläge machen", "Ideen für den Umgang mit Problemen "
                 "oder Vorgehensweisen in einer Situation formulieren"),
    ],
}

# --- Generic fallback — PROVISIONAL (no subject catalog curated yet) ------------------
# Common German task verbs that span subjects; replace per subject as the official
# operator catalogs are curated (MINT wedge first: Physik/Chemie/Biologie, Mathematik).
DEFAULT: dict[int, list[Operator]] = {
    1: [Operator(v) for v in ("nennen", "benennen", "beschreiben", "angeben",
                              "darstellen", "wiedergeben", "zusammenfassen", "skizzieren")],
    2: [Operator(v) for v in ("erklären", "erläutern", "vergleichen", "analysieren",
                              "einordnen", "anwenden", "berechnen", "ermitteln",
                              "charakterisieren", "ableiten")],
    3: [Operator(v) for v in ("begründen", "beurteilen", "bewerten", "Stellung nehmen",
                              "diskutieren", "erörtern", "überprüfen", "interpretieren",
                              "entwickeln")],
}

# subject name → authoritative catalog. Subjects absent here use DEFAULT.
SUBJECT_OPERATORS: dict[str, dict[int, list[Operator]]] = {
    "Deutsch": DEUTSCH,
}


def operator_set(subject: str | None) -> dict[int, list[Operator]]:
    """The operator table for a subject — its authoritative catalog if curated, else the
    generic fallback."""
    return SUBJECT_OPERATORS.get(subject or "", DEFAULT)


def is_authoritative(subject: str | None) -> bool:
    return (subject or "") in SUBJECT_OPERATORS


def afb_for_level(cognitive_level: str) -> int:
    """The Anforderungsbereich band (1..3) of a ``cognitive_level`` string."""
    rank = COGNITIVE_RANK.get(cognitive_level, 1)
    return _RANK_TO_AFB.get(rank, 2)


def operators_for_level(cognitive_level: str, subject: str | None = None) -> list[Operator]:
    """The standardized operators that fit a ``cognitive_level`` (via its AFB band) for a
    subject."""
    return operator_set(subject)[afb_for_level(cognitive_level)]


def format_operators_brief(subject: str | None = None) -> str:
    """A compact palette for the generation system prompt: AFB band → its cognitive
    levels → its standardized operators, for the given subject."""
    table = operator_set(subject)
    tag = subject if is_authoritative(subject) else "generic — subject catalog pending"
    lines = [
        f"Standardized SRDP Operatoren ({tag}) by Anforderungsbereich — phrase each "
        "task's prompt with an apt operator for its cognitive_level (these are the typical "
        "homes, not a strict 1:1 mapping):"
    ]
    for band in (1, 2, 3):
        levels = [cl.value for cl in CognitiveLevel
                  if _RANK_TO_AFB[COGNITIVE_RANK[cl]] == band]
        verbs = ", ".join(o.forms for o in table[band])
        lines.append(
            f"  - AFB {band} ({AFB_LABEL[band]}) [{', '.join(levels)}]: {verbs}"
        )
    return "\n".join(lines)
