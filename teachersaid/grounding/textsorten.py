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


# Source note for the curated genre facts (struktur/register distilled from the corpus).
QUELLE = (
    "Textsortenkatalog zur SRDP in der Unterrichtssprache (Stand Sept. 2020) sowie die "
    "SRDP-Korrekturhefte Deutsch (Haupttermine 2015–2026, 33 Klausuren). "
    "Datenquelle: Bundesministerium für Bildung; CC BY (IWG 2022)."
)


@dataclass(frozen=True)
class Textsorte:
    id: str
    name: str
    definition: str
    schreibhandlungen: tuple[str, ...]          # ids into SCHREIBHANDLUNGEN
    struktur: tuple[tuple[str, str], ...]       # ordered (Bauteil, Funktion) — the Aufbau
    typical_operators: tuple[str, ...]          # operators.DEUTSCH forms (verbatim, banded)
    umfang: tuple[tuple[int, int], ...]         # allowed word-count bands (die Wortanzahl)
    sprachregister: str                         # register/Stil notes (Standardsprache, Präsens …)
    situativer_kontext: bool                    # needs a role/occasion beyond the exam
    textbasis: str                              # literarisch | nicht-fiktional | pragmatisch
    scope: str                                  # kurz | lang | variabel
    artikel: str = "eine"                       # accusative article: „Verfasse {artikel} {name}“
    schueler_definition: str = ""               # authored-then-vetted SIMPLE wording for the
    # student learn-text (kept grade-readable — the Wiener-Sachtextformel lint checks it);
    # the formal `definition` stays source-faithful to the SRDP Textsortenkatalog and serves
    # the teacher layer. Empty → the scaffold falls back to `definition`.
    verwandt: tuple[str, ...] = field(default_factory=tuple)
    quelle: str = QUELLE


_ALL = ("argumentation", "deskription", "evaluation", "explikation", "narration",
        "rekapitulation")

TEXTSORTEN: dict[str, Textsorte] = {
    "eroerterung": Textsorte(
        id="eroerterung", name="Erörterung",
        definition="Schriftliche Auseinandersetzung mit einem strittigen Thema; "
        "multiperspektivische Behandlung anhand der Textbeilage(n) und der eigenen Position.",
        schreibhandlungen=_ALL,
        struktur=(
            ("Einleitung", "Zum strittigen Thema hinführen und die Leitfrage benennen."),
            ("Hauptteil", "Argumente und Gegenargumente abwägend gegenüberstellen und jeweils "
             "mit Belegen aus der/den Textbeilage(n) stützen."),
            ("Schluss", "Die Abwägung zu einem begründeten eigenen Urteil zusammenführen."),
        ),
        typical_operators=("diskutieren / erörtern / sich auseinandersetzen mit",
                           "begründen / Gründe angeben", "beurteilen"),
        umfang=((405, 495), (540, 660)),
        sprachregister="Sachlich-argumentativ und standardsprachlich; abwägende Konnektoren "
        "(einerseits/andererseits, dennoch); das eigene Urteil erst im Schluss.",
        situativer_kontext=False, textbasis="pragmatisch", scope="lang", artikel="eine",
        verwandt=("kommentar", "leserbrief")),
    "kommentar": Textsorte(
        id="kommentar", name="Kommentar",
        definition="Journalistische Textsorte, die auf die Meinungsbildung der Leser/innen "
        "abzielt; die/der Verfasser/in äußert einen Standpunkt zu einem öffentlich "
        "diskutierten Thema.",
        schueler_definition="In einem Kommentar sagst du deutlich, was du zu einem Thema "
        "meinst. Deine Meinung stützt du mit guten Gründen.",
        schreibhandlungen=_ALL,
        struktur=(
            ("Titel", "Eine zugespitzte Überschrift, die neugierig macht und den Standpunkt "
             "andeutet."),
            ("Einleitung", "Den aktuellen Anlass nennen, zum strittigen Thema hinführen und "
             "die eigene These andeuten."),
            ("Hauptteil", "Den eigenen Standpunkt mit Argumenten und Belegen begründen; "
             "Gegenargumente aufgreifen und entkräften."),
            ("Schluss", "Die Position zuspitzen und mit einem Fazit oder einem Appell an die "
             "Leserinnen und Leser enden."),
        ),
        typical_operators=("kommentieren / Stellung nehmen", "begründen / Gründe angeben",
                           "appellieren"),
        umfang=((270, 330), (405, 495), (540, 660)),
        sprachregister="Standardsprachlich, meinungsbetont und pointiert; klar erkennbare "
        "Ich-Position; direkte Leseransprache und rhetorische Mittel sind erlaubt.",
        situativer_kontext=True, textbasis="pragmatisch", scope="variabel", artikel="einen",
        verwandt=("leserbrief", "eroerterung")),
    "leserbrief": Textsorte(
        id="leserbrief", name="Leserbrief",
        definition="Kompakte schriftliche Darstellung der persönlichen Meinung in einem "
        "(Print-)Medium, als Reaktion auf publizierte Berichte oder Äußerungen.",
        schreibhandlungen=_ALL,
        struktur=(
            ("Bezug", "Auf den auslösenden Artikel (Titel, Medium, Datum) Bezug nehmen."),
            ("Anrede", "Eine passende Anrede an die Redaktion."),
            ("Hauptteil", "Die eigene Meinung zum Beitrag knapp und begründet darlegen; "
             "zustimmen oder widersprechen."),
            ("Schluss und Grußformel", "Ein pointiertes Schlusswort, eine Grußformel und die "
             "Unterschrift."),
        ),
        typical_operators=("kommentieren / Stellung nehmen", "begründen / Gründe angeben",
                           "appellieren"),
        umfang=((270, 330),),
        sprachregister="Standardsprachlich, höflich, aber meinungsstark; Briefkonventionen "
        "(Anrede, Grußformel); klarer Bezug auf den Ausgangsartikel.",
        situativer_kontext=True, textbasis="pragmatisch", scope="kurz", artikel="einen",
        verwandt=("kommentar", "eroerterung")),
    "meinungsrede": Textsorte(
        id="meinungsrede", name="Meinungsrede",
        definition="Druckfassung einer Rede, die ein bestimmtes Publikum von der eigenen "
        "Position überzeugen will; bedient sich vorwiegend der Argumentation.",
        schreibhandlungen=("argumentation", "deskription", "explikation", "narration",
                           "rekapitulation"),
        struktur=(
            ("Begrüßung und Hinführung", "Das Publikum ansprechen und zum Thema hinführen."),
            ("Hauptteil", "Die eigene Position mit Argumenten entfalten und das Publikum durch "
             "rhetorische Mittel überzeugen."),
            ("Appell und Schluss", "Mit einem eindringlichen Appell und einem einprägsamen "
             "Schlusssatz enden."),
        ),
        typical_operators=("appellieren", "begründen / Gründe angeben",
                           "kommentieren / Stellung nehmen"),
        umfang=((405, 495), (540, 660)),
        sprachregister="Gesprochene, wirkungsvolle Standardsprache; direkte Publikumsansprache; "
        "rhetorische Mittel (Frage, Wiederholung, Dreierfigur); mündlicher Duktus.",
        situativer_kontext=True, textbasis="pragmatisch", scope="lang", artikel="eine"),
    "textanalyse": Textsorte(
        id="textanalyse", name="Textanalyse",
        definition="Sachliche Beschreibung eines nicht-fiktionalen Textes anhand von "
        "Analyseaspekten (Inhalt, Form, Sprache, Funktion).",
        schreibhandlungen=("deskription", "explikation", "narration", "rekapitulation"),
        struktur=(
            ("Einleitung", "Autor/in, Titel, Textsorte, Quelle/Datum und Thema nennen."),
            ("Hauptteil", "Inhalt, Aufbau, sprachlich-formale Mittel und die Funktion/Wirkung "
             "des Textes systematisch untersuchen und am Text belegen."),
            ("Schluss", "Die Analyseergebnisse zusammenfassen und die Aussageabsicht bündeln."),
        ),
        typical_operators=("analysieren / untersuchen", "beschreiben", "erschließen"),
        umfang=((405, 495), (540, 660)),
        sprachregister="Fachsprachlich, sachlich und distanziert; durchgehend Präsens; jede "
        "Aussage am Text belegt; keine eigene Wertung.",
        situativer_kontext=False, textbasis="nicht-fiktional", scope="lang", artikel="eine",
        verwandt=("textinterpretation",)),
    "textinterpretation": Textsorte(
        id="textinterpretation", name="Textinterpretation",
        definition="Deutung eines literarischen Textes auf Grundlage der Untersuchung von "
        "Textmerkmalen; setzt fort, wo die Textanalyse endet.",
        schueler_definition="In einer Textinterpretation deutest du einen literarischen "
        "Text. Du zeigst am Text, wie er gemacht ist und was er bedeuten kann.",
        schreibhandlungen=("argumentation", "deskription", "explikation", "narration",
                           "rekapitulation"),
        struktur=(
            ("Einleitung", "Autor/in, Titel, Textsorte, Erscheinungsjahr und Thema nennen "
             "sowie eine Deutungshypothese aufstellen."),
            ("Hauptteil – Analyse", "Inhalt, Aufbau und sprachlich-formale Gestaltung "
             "(z. B. Bilder, Reim, Rhythmus) untersuchen und am Text belegen."),
            ("Hauptteil – Deutung", "Aus der Analyse eine schlüssige Gesamtdeutung entwickeln "
             "und die Deutungshypothese prüfen."),
            ("Schluss", "Die Deutung bündeln; gegebenenfalls eine begründete Stellungnahme."),
        ),
        typical_operators=("deuten / interpretieren", "analysieren / untersuchen", "beschreiben"),
        umfang=((540, 660),),
        sprachregister="Fachsprachlich und sachlich; durchgehend Präsens; jede Deutung am Text "
        "belegt (Zeilenverweis/Zitat); keine bloße Nacherzählung.",
        situativer_kontext=False, textbasis="literarisch", scope="lang", artikel="eine",
        verwandt=("textanalyse",)),
    "zusammenfassung": Textsorte(
        id="zusammenfassung", name="Zusammenfassung",
        definition="Komprimierung einer (oder mehrerer) Quelle(n) entlang ihrer "
        "logisch-sachlichen Struktur unter vorgegebenen Gesichtspunkten.",
        schueler_definition="In einer Zusammenfassung gibst du das Wichtigste eines Textes "
        "kurz und sachlich wieder. Du bleibst dabei bei der Sache und ordnest klar.",
        schreibhandlungen=("deskription", "narration", "rekapitulation"),
        struktur=(
            ("Basissatz", "Autor/in, Titel, Textsorte und Kernaussage des Ausgangstextes in "
             "einem Satz nennen."),
            ("Hauptteil", "Die wichtigsten Gedanken des Textes in eigenen Worten, in "
             "sinnvoller Reihenfolge und ohne Beispiele oder Zitate wiedergeben."),
            ("Sachlicher Abschluss", "Das Ergebnis knapp bündeln — ohne eigene Meinung oder "
             "Wertung."),
        ),
        typical_operators=("zusammenfassen", "wiedergeben", "beschreiben"),
        umfang=((270, 330),),
        sprachregister="Sachlich und distanziert; durchgehend Präsens; indirekte Rede für "
        "fremde Aussagen; keine eigene Wertung und keine wörtlichen Zitate.",
        situativer_kontext=True, textbasis="pragmatisch", scope="kurz", artikel="eine"),
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


def struktur_teile(textsorte: str) -> list[str]:
    """The Bauteil names of a Textsorte's Aufbau, in order."""
    ts = get_textsorte(textsorte)
    return [teil for teil, _ in ts.struktur] if ts else []


def format_textsorte_brief(textsorte: str) -> str:
    """A compact brief for building a worksheet that teaches/scaffolds a target Textsorte."""
    ts = get_textsorte(textsorte)
    if ts is None:
        return ""
    bands = " / ".join(f"{lo}–{hi}" for lo, hi in ts.umfang)
    sh = ", ".join(SCHREIBHANDLUNGEN[s].name for s in ts.schreibhandlungen)
    aufbau = " → ".join(teil for teil, _ in ts.struktur)
    ops = ", ".join(ts.typical_operators)
    ctx = "ja (Rolle/Anlass angeben)" if ts.situativer_kontext else "nein"
    return (
        f"Textsorte: {ts.name} — {ts.definition}\n"
        f"  Schreibhandlungen: {sh}\n"
        f"  Aufbau: {aufbau}\n"
        f"  Typische Operatoren: {ops}\n"
        f"  Umfang (Wörter): {bands} · Textbasis: {ts.textbasis} · "
        f"situativer Kontext: {ctx}\n"
        f"  Sprachregister: {ts.sprachregister}"
    )
