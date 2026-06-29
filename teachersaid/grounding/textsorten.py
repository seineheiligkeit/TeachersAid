"""SRDP Deutsch **Textsorten** + **Schreibhandlungen** — the German genre layer (grounding).

The Maths analogue of "missing parametric recipes" for German is the **genre/scaffold layer**:
the Matura demands students *produce* a Textsorte (Erörterung, Kommentar, …) by performing
operator-driven Arbeitsaufträge on a source text, and it assumes the genre is already
mastered. *Matura-backward design* (see `Documents/matura-deutsch-coverage.md`): we teach that
genre richly and earlier. This catalog is the durable grounding for it.

Two levels, mirroring the official model:
- **Schreibhandlung** (writing-act) — the basic Vertextungsmuster (Deskription, Narration,
  Explikation, Argumentation, Rekapitulation, Evaluation). Context-independent, learnable,
  the *building blocks*.
- **Textsorte** — a recognisable, situated text pattern realised by combining Schreibhandlungen
  (a Kommentar is dominated by Argumentation, a Zusammenfassung by Rekapitulation, …).

This is **GROUNDING, select-never-author**: transcribed from the official *Textsortenkatalog
zur SRDP in der Unterrichtssprache* (Arbeitsgruppe SRDP Deutsch; M. Rheindorf, Univ. Wien;
Stand Sept. 2020), CC BY via IWG 2022. Three Schreibhandlungen-Unterformen the katalog names
(Appell ⊂ Argumentation, Illustration ⊂ Explikation, Integration ⊂ Rekapitulation) are noted
but not split out. The `SCHREIBHANDLUNG_OPERATORS` cross-walk to our Deutsch operator catalog
is *our* curated linkage (grounded in the definitions), not from the katalog verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Schreibhandlung:
    id: str
    name: str
    definition: str
    ziel: str  # the communicative goal (the katalog's distinguishing axis)


# The six Schreibhandlungen the katalog uses in the Textsorte profiles.
SCHREIBHANDLUNGEN: dict[str, Schreibhandlung] = {
    "deskription": Schreibhandlung(
        "deskription", "Deskription",
        "Zustände, Personen, Gegenstände, Orte, Ereignisse aus neutraler Perspektive "
        "strukturiert darstellen, ohne explizit logische Zusammenhänge herzustellen.",
        "Informationen vermitteln"),
    "narration": Schreibhandlung(
        "narration", "Narration",
        "Zustände und Ereignisse aus spezifischer Perspektive zeitlich (z. T. ursächlich) "
        "bezogen und gestaltend schildern (Bericht/Erzählung).",
        "Vergegenwärtigung der Vergangenheit"),
    "explikation": Schreibhandlung(
        "explikation", "Explikation",
        "Zusammenhänge (Warum/Wie; Ursache–Wirkung, Grund–Folge, Zweck–Mittel) "
        "identifizieren und verständlich machen.",
        "Verständnis vermitteln"),
    "argumentation": Schreibhandlung(
        "argumentation", "Argumentation",
        "Sachverhalte in einem argumentativen Rahmen (These/Frage/Problem → Schluss) in "
        "Gegensatz, Stützung oder Einschränkung zueinander setzen.",
        "Überzeugung"),
    "rekapitulation": Schreibhandlung(
        "rekapitulation", "Rekapitulation",
        "Eine Quelle aus neutraler Perspektive (ganz oder selektiv) wiedergeben, ohne die "
        "rekapitulierende Beziehung zur Quelle aufzugeben.",
        "Wiedergabe"),
    "evaluation": Schreibhandlung(
        "evaluation", "Evaluation",
        "Einen Sachverhalt aus einer Perspektive bewerten (Erfassung + Bewertung, evtl. "
        "Kriterien und Reflexion).",
        "Bewertung"),
}

# Curated cross-walk Schreibhandlung → realising Deutsch operators (forms in
# operators.DEUTSCH). Our linkage, grounded in the definitions — a test checks the targets
# are real catalog operators. Narration has no single operator (it is a mode of schildern).
SCHREIBHANDLUNG_OPERATORS: dict[str, tuple[str, ...]] = {
    "deskription": ("beschreiben", "wiedergeben"),
    "narration": (),
    "explikation": ("erklären", "erläutern", "erschließen"),
    "argumentation": ("begründen / Gründe angeben", "kommentieren / Stellung nehmen",
                      "diskutieren / erörtern / sich auseinandersetzen mit", "appellieren"),
    "rekapitulation": ("zusammenfassen", "wiedergeben"),
    "evaluation": ("beurteilen", "bewerten"),
}


@dataclass(frozen=True)
class Textsorte:
    id: str
    name: str
    definition: str
    schreibhandlungen: tuple[str, ...]          # ids into SCHREIBHANDLUNGEN
    umfang: tuple[tuple[int, int], ...]         # allowed word-count bands
    situativer_kontext: bool                    # needs a role/occasion beyond the exam
    textbasis: str                              # literarisch | nicht-fiktional | pragmatisch
    scope: str                                  # kurz | lang | variabel
    verwandt: tuple[str, ...] = field(default_factory=tuple)


_ALL = ("argumentation", "deskription", "evaluation", "explikation", "narration",
        "rekapitulation")

TEXTSORTEN: dict[str, Textsorte] = {
    "eroerterung": Textsorte(
        "eroerterung", "Erörterung",
        "Schriftliche Auseinandersetzung mit einem strittigen Thema; multiperspektivische "
        "Behandlung anhand der Textbeilage(n) und der eigenen Position.",
        _ALL, ((405, 495), (540, 660)), False, "pragmatisch", "lang",
        ("kommentar", "leserbrief")),
    "kommentar": Textsorte(
        "kommentar", "Kommentar",
        "Journalistische Textsorte, die auf die Meinungsbildung der Leser/innen abzielt; "
        "die/der Verfasser/in äußert einen Standpunkt zu einem öffentlich diskutierten Thema.",
        _ALL, ((270, 330), (405, 495), (540, 660)), True, "pragmatisch", "variabel",
        ("leserbrief", "eroerterung")),
    "leserbrief": Textsorte(
        "leserbrief", "Leserbrief",
        "Kompakte schriftliche Darstellung der persönlichen Meinung in einem (Print-)Medium, "
        "als Reaktion auf publizierte Berichte oder Äußerungen.",
        _ALL, ((270, 330),), True, "pragmatisch", "kurz",
        ("kommentar", "eroerterung")),
    "meinungsrede": Textsorte(
        "meinungsrede", "Meinungsrede",
        "Druckfassung einer Rede, die ein bestimmtes Publikum von der eigenen Position "
        "überzeugen will; bedient sich vorwiegend der Argumentation.",
        ("argumentation", "deskription", "explikation", "narration", "rekapitulation"),
        ((405, 495), (540, 660)), True, "pragmatisch", "lang"),
    "textanalyse": Textsorte(
        "textanalyse", "Textanalyse",
        "Sachliche Beschreibung eines nicht-fiktionalen Textes anhand von Analyseaspekten "
        "(Inhalt, Form, Sprache, Funktion).",
        ("deskription", "explikation", "narration", "rekapitulation"),
        ((405, 495), (540, 660)), False, "nicht-fiktional", "lang",
        ("textinterpretation",)),
    "textinterpretation": Textsorte(
        "textinterpretation", "Textinterpretation",
        "Deutung eines literarischen Textes auf Grundlage der Untersuchung von Textmerkmalen; "
        "setzt fort, wo die Textanalyse endet.",
        ("argumentation", "deskription", "explikation", "narration", "rekapitulation"),
        ((540, 660),), False, "literarisch", "lang", ("textanalyse",)),
    "zusammenfassung": Textsorte(
        "zusammenfassung", "Zusammenfassung",
        "Komprimierung einer (oder mehrerer) Quelle(n) entlang ihrer logisch-sachlichen "
        "Struktur unter vorgegebenen Gesichtspunkten.",
        ("deskription", "narration", "rekapitulation"),
        ((270, 330),), True, "pragmatisch", "kurz"),
}


def get_textsorte(name_or_id: str) -> Textsorte | None:
    """Resolve a Textsorte by id or display name (case-insensitive)."""
    key = (name_or_id or "").strip().lower()
    if key in TEXTSORTEN:
        return TEXTSORTEN[key]
    for ts in TEXTSORTEN.values():
        if ts.name.lower() == key:
            return ts
    return None


def schreibhandlungen_for(textsorte: str) -> list[Schreibhandlung]:
    ts = get_textsorte(textsorte)
    return [SCHREIBHANDLUNGEN[s] for s in ts.schreibhandlungen] if ts else []


def by_scope(scope: str) -> list[Textsorte]:
    return [t for t in TEXTSORTEN.values() if t.scope == scope]


def format_textsorte_brief(textsorte: str) -> str:
    """A compact brief for building a worksheet that teaches/scaffolds a target Textsorte."""
    ts = get_textsorte(textsorte)
    if ts is None:
        return ""
    bands = " / ".join(f"{lo}–{hi}" for lo, hi in ts.umfang)
    sh = ", ".join(SCHREIBHANDLUNGEN[s].name for s in ts.schreibhandlungen)
    ctx = "ja (Rolle/Anlass angeben)" if ts.situativer_kontext else "nein"
    return (
        f"Textsorte: {ts.name} — {ts.definition}\n"
        f"  Schreibhandlungen: {sh}\n"
        f"  Umfang (Wörter): {bands} · Textbasis: {ts.textbasis} · "
        f"situativer Kontext: {ctx}"
    )
