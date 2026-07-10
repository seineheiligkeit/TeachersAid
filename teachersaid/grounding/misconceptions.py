"""Misconception catalog — the curated error-analysis layer for MC distractors.

The grounding twin of `grounding/chemistry.py` / `grounding/physics.py`, but the curated
*facts* here are documented **student misconceptions** — the systematic wrong procedures
error-analysis research has catalogued. Each entry is a stable id + a German display name
+ a one-line German description (this text reaches the *teacher guide*, so it is written
in Austrian school register) + the domain scope it applies to + a literature source note
(the curation provenance — an honest bibliographic reference to the error-analysis work we
draw the pattern from, NOT a URL to fabricate).

The point of the whole engine (roadmap A3): a multiple-choice distractor is
*correct-by-construction* when it is **computed** by applying one of these documented
misconceptions to the SAME drawn numbers the correct answer used. The teacher guide can
then say exactly which error each distractor probes ("B prüft den Vorzeichenfehler"). This
is `intentionally_flawed`, generalised into a theory: a wrong option built on purpose, from
a named cause, and never "fixed".

`grounding/` imports only `schema/` — this module is a pure data catalog + a tiny resolver
(no engine logic; the transforms that *compute* the wrong value live in
`pipeline/misconceive.py`, the way the balancing logic lives in `pipeline/chemistry.py`,
not in the chemistry grounding).

The sources actually drawn on:
  * **Radatz (1979/1980)** — the classic taxonomy of arithmetic error classes (sign
    handling, operation confusion, place-value / carry). We cite it for the arithmetic and
    transposition patterns.
  * **Malle (1993)** — the standard German-language analysis of the systematic errors of
    elementary algebra (equation rearrangement, inverse-operation slips). We cite it for the
    equation patterns.
  * **Padberg & Wartha (2017)** — the reference on fraction didactics and the persistent
    fraction misconceptions. We cite it for the "add across" fraction error.
  * The physics "plug into the un-rearranged formula" and "parallel resistors added like a
    series" errors are documented staples of physics-education research (the misconceptions
    literature around Ohm's law and simple circuits); we cite them descriptively rather than
    over-claim a single canonical page.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Misconception(BaseModel):
    """One catalogued student error. `id` is the stable key transforms register against;
    `name`/`short` are the teacher-guide German strings; `scope` lists the recipe/domain
    tags it applies to (documentation + the catalog-integrity test); `source` is the
    curation provenance (a real bibliographic note — never a fabricated URL)."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    name: str                 # German display name (teacher guide) — Austrian school register
    short: str                # one-line German description of the error (teacher guide)
    scope: tuple[str, ...]    # domain/recipe tags this misconception applies to
    source: str               # error-analysis literature note (curation provenance)


# The curated set — only entries a transform in pipeline/misconceive.py genuinely
# implements. No padding: the catalog-integrity test asserts every entry is used by at
# least one transform (or is explicitly marked planned; none are, currently).
_ENTRIES: tuple[Misconception, ...] = (
    Misconception(
        id="sign_error",
        name="Vorzeichenfehler",
        short="Beim Umstellen wird das Vorzeichen eines Terms nicht gewechselt "
              "(der konstante Term wird addiert statt subtrahiert).",
        scope=("algebra", "linear_equation"),
        source="Radatz (1980), Fehleranalysen im Mathematikunterricht; "
               "Malle (1993), Didaktische Probleme der elementaren Algebra.",
    ),
    Misconception(
        id="inverse_operation",
        name="Umkehroperation verwechselt",
        short="Statt durch den Koeffizienten zu dividieren, wird mit ihm multipliziert "
              "(die Umkehroperation wird verwechselt).",
        scope=("algebra", "linear_equation"),
        source="Malle (1993), Didaktische Probleme der elementaren Algebra "
               "(systematische Fehler beim Gleichungslösen).",
    ),
    Misconception(
        id="percent_base_confusion",
        name="Prozentbasis verwechselt",
        short="Der Prozentsatz wird auf die falsche Bezugsgröße bezogen — statt "
              "Grundwert · Prozentsatz wird durch den Prozentsatz dividiert.",
        scope=("percentage", "percentage_rate"),
        source="Radatz (1980), Fehleranalysen im Mathematikunterricht "
               "(Fehlvorstellungen zum Grundwert in der Prozentrechnung).",
    ),
    Misconception(
        id="fraction_add_across",
        name="Brüche: Zähler+Zähler / Nenner+Nenner",
        short="Brüche werden fälschlich addiert, indem Zähler und Nenner getrennt "
              "addiert werden (statt auf einen gemeinsamen Nenner zu erweitern).",
        scope=("fraction_add",),
        source="Padberg & Wartha (2017), Didaktik der Bruchrechnung "
               "(die hartnäckigste Bruch-Fehlvorstellung).",
    ),
    Misconception(
        id="fraction_keep_numerators",
        name="Zähler nicht miterweitert",
        short="Der gemeinsame Nenner wird richtig gebildet, aber die Zähler werden nicht "
              "mit erweitert — die ursprünglichen Zähler werden über den neuen Nenner "
              "addiert.",
        scope=("fraction_add",),
        source="Padberg & Wartha (2017), Didaktik der Bruchrechnung "
               "(unvollständige Erweiterung beim Addieren).",
    ),
    Misconception(
        id="unit_power_ten",
        name="Einheitenfehler (Zehnerpotenz)",
        short="Beim Umrechnen der Einheit wird um eine Zehnerpotenz danebengegriffen "
              "(Faktor 10 zu viel oder zu wenig).",
        scope=("percentage", "density", "molar_mass", "ohm", "uniform_motion", "resistors"),
        source="Radatz (1980), Fehleranalysen im Mathematikunterricht "
               "(Stellenwert- und Einheitenfehler).",
    ),
    Misconception(
        id="formula_not_rearranged",
        name="Formel nicht umgestellt",
        short="Die gesuchte Größe wird berechnet, ohne die Formel umzustellen — es wird "
              "multipliziert, wo hätte dividiert werden müssen (z. B. s = v·t für t).",
        scope=("physics", "ohm", "uniform_motion"),
        source="Physikdidaktik (Fehlvorstellungen zum Umgang mit Formeln — Einsetzen in "
               "die nicht umgestellte Gleichung).",
    ),
    Misconception(
        id="parallel_as_series",
        name="Kehrwert vergessen (parallel wie Reihe)",
        short="Bei der Parallelschaltung werden die Widerstände einfach addiert wie in "
              "der Reihenschaltung — die Kehrwertaddition wird vergessen.",
        scope=("physics", "resistors"),
        source="Physikdidaktik (Fehlvorstellungen zu einfachen Stromkreisen — Parallel- "
               "vs. Reihenschaltung).",
    ),
    Misconception(
        id="subscript_ignored",
        name="Indexzahl ignoriert",
        short="Die tiefgestellte Anzahl in der Summenformel wird übersehen — jedes "
              "Element wird nur einfach gezählt (H₂O als H·O statt H₂·O).",
        scope=("chemistry", "molar_mass"),
        source="Chemiedidaktik (Fehlvorstellungen zur Formelsprache — Verwechslung von "
               "Index und Koeffizient).",
    ),
)

CATALOG: dict[str, Misconception] = {m.id: m for m in _ENTRIES}

# Entries with no transform yet, kept as an explicit allow-list for the integrity test so a
# planned-but-unimplemented pattern is honest rather than a silent orphan. Currently none.
PLANNED: frozenset[str] = frozenset()


def get(mid: str) -> Misconception:
    """The catalogued misconception for `mid`, or raise (a transform must name a real id)."""
    try:
        return CATALOG[mid]
    except KeyError:
        raise KeyError(f"unknown misconception id {mid!r} (not in the curated catalog)")


def label(mid: str) -> str:
    """The teacher-guide German name (for the 'B prüft: …' line)."""
    return get(mid).name
