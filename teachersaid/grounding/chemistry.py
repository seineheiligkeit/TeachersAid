"""Chemistry grounding — the periodic facts the quantitative engine computes from.

The chemistry analogue of `lehrplan_store` (competences) and `data_store` (datasets):
the **facts** here are the IUPAC standard atomic weights. Discipline is identical —
*select, never author*: the masses come from a single cited source (IUPAC), the engine
*reads* them, the LLM never invents a number. A molar mass, a balanced equation, a
stoichiometric result is then **correct by construction** (computed from these masses +
conservation), exactly like the sympy maths recipes.

`parse_formula` is the load-bearing primitive: it turns a formula string (`"Ca(OH)2"`,
`"Al2(SO4)3"`) into an element→count map, used by molar mass, balancing and stoichiometry.
"""

from __future__ import annotations

import re

from ..schema.datasets import SourceRef

# --- provenance -------------------------------------------------------------
# Standard atomic weights, IUPAC 2021 (conventional values for elements with a
# range; abridged to the precision a school worksheet uses). Public, citable —
# the data twin of a FassungRef. We *select* these; we never author a mass.
SOURCE = SourceRef(
    publisher="IUPAC",
    title="Standard Atomic Weights 2021 (Commission on Isotopic Abundances and Atomic Weights)",
    url="https://iupac.org/what-we-do/periodic-table-of-elements/",
    licence="CC BY 4.0",
    redistributable=True,
    attribution="Atomgewichte: IUPAC (2021), Standard Atomic Weights",
    stand="2021",
)

# Symbol → standard atomic weight in g/mol. Covers the elements that appear in
# AHS chemistry; extend by adding a row (one cited fact per row).
ATOMIC_MASSES: dict[str, float] = {
    "H": 1.008, "He": 4.0026, "Li": 6.94, "Be": 9.0122, "B": 10.81, "C": 12.011,
    "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180, "Na": 22.990, "Mg": 24.305,
    "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45, "Ar": 39.95,
    "K": 39.098, "Ca": 40.078, "Sc": 44.956, "Ti": 47.867, "V": 50.942, "Cr": 51.996,
    "Mn": 54.938, "Fe": 55.845, "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38,
    "Ga": 69.723, "Ge": 72.630, "As": 74.922, "Se": 78.971, "Br": 79.904, "Kr": 83.798,
    "Rb": 85.468, "Sr": 87.62, "Y": 88.906, "Zr": 91.224, "Nb": 92.906, "Mo": 95.95,
    "Ag": 107.868, "Cd": 112.414, "In": 114.818, "Sn": 118.710, "Sb": 121.760,
    "Te": 127.60, "I": 126.904, "Xe": 131.293, "Cs": 132.905, "Ba": 137.327,
    "Pt": 195.084, "Au": 196.967, "Hg": 200.592, "Tl": 204.38, "Pb": 207.2,
    "Bi": 208.980, "W": 183.84, "U": 238.029,
}

# German element names (for the worked Rechenweg; display only).
ELEMENT_NAMES: dict[str, str] = {
    "H": "Wasserstoff", "C": "Kohlenstoff", "N": "Stickstoff", "O": "Sauerstoff",
    "Na": "Natrium", "Mg": "Magnesium", "Al": "Aluminium", "S": "Schwefel",
    "Cl": "Chlor", "K": "Kalium", "Ca": "Calcium", "Fe": "Eisen", "Cu": "Kupfer",
    "Zn": "Zink", "Ag": "Silber", "Pb": "Blei", "Sn": "Zinn", "Br": "Brom",
    "Ba": "Barium", "Mn": "Mangan",
}

# Unicode subscript digits — the renderer typesets these correctly (CO₂, H₂O).
_SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*)|(\()|(\))(\d*)")


class FormulaError(ValueError):
    """An unparseable formula or an unknown element symbol."""


def parse_formula(formula: str) -> dict[str, int]:
    """A chemical formula → {element: atom count}. Handles nested parentheses and
    hydrate dots (`CuSO4·5H2O`). Raises FormulaError on a bad token / unknown element."""
    # Hydrate notation: split on the centre dot / bullet and sum the parts.
    f = formula.replace(" ", "")
    for dot in ("·", "*", "•", "."):
        if dot in f:
            total: dict[str, int] = {}
            for part in f.split(dot):
                part = part.strip()
                if not part:
                    continue
                mult, body = re.match(r"(\d*)(.*)", part).groups()
                k = int(mult) if mult else 1
                for el, n in parse_formula(body).items():
                    total[el] = total.get(el, 0) + n * k
            return total

    counts: dict[str, int] = {}
    stack: list[dict[str, int]] = [counts]
    pos = 0
    while pos < len(f):
        m = _TOKEN.match(f, pos)
        if m is None or m.end() == pos:
            raise FormulaError(f"cannot parse {formula!r} at {f[pos:]!r}")
        pos = m.end()
        el, n, lparen, rparen, rmult = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        if el:
            if el not in ATOMIC_MASSES:
                raise FormulaError(f"unknown element {el!r} in {formula!r}")
            stack[-1][el] = stack[-1].get(el, 0) + (int(n) if n else 1)
        elif lparen:
            stack.append({})
        elif rparen:
            if len(stack) < 2:
                raise FormulaError(f"unbalanced ')' in {formula!r}")
            group = stack.pop()
            k = int(rmult) if rmult else 1
            for e, c in group.items():
                stack[-1][e] = stack[-1].get(e, 0) + c * k
    if len(stack) != 1:
        raise FormulaError(f"unbalanced '(' in {formula!r}")
    return counts


def atomic_mass(symbol: str) -> float:
    if symbol not in ATOMIC_MASSES:
        raise FormulaError(f"unknown element {symbol!r}")
    return ATOMIC_MASSES[symbol]


def molar_mass(formula: str) -> float:
    """Molar mass in g/mol = Σ (count · atomic weight). Correct by construction."""
    return sum(ATOMIC_MASSES[el] * n for el, n in parse_formula(formula).items())


def mass_breakdown(formula: str) -> list[tuple[str, int, float]]:
    """Per-element (symbol, count, count·atomic_mass) — the rows of the Rechenweg."""
    return [(el, n, ATOMIC_MASSES[el] * n) for el, n in parse_formula(formula).items()]


_COUNT_DIGITS = re.compile(r"(?<=[A-Za-z)])(\d+)")


def subscript(formula: str) -> str:
    """Render a formula with proper subscripts (H2O → H₂O) for display. Only a COUNT
    subscripts — a digit run following an element letter or a ')'. Coefficients and
    hydrate multipliers (after a space, '·' or at the start: "2 H2O", "CuSO4·5H2O")
    stay normal-size digits."""
    return _COUNT_DIGITS.sub(lambda m: m.group(1).translate(_SUBSCRIPTS), formula)


# --- qualitative reference tables (curated truth — select, never author) ------
# The Unterstufe (4. Kl.) chemistry is qualitative; these are the curated *facts* the
# qualitative recipes read. Same discipline as the data layer: the engine selects an
# entry, the answer IS the curated truth — the model never invents a classification.
# (Display strings carry proper subscripts so the renderer typesets them directly.)

# Reinstoffe vs. Gemische: Element / Verbindung (Reinstoffe) · Gemisch.
SUBSTANCE_CLASSES: list[tuple[str, str]] = [
    ("Sauerstoff (O₂)", "Element"), ("Eisen (Fe)", "Element"),
    ("Kupfer (Cu)", "Element"), ("Gold (Au)", "Element"),
    ("Wasserstoff (H₂)", "Element"), ("Schwefel (S)", "Element"),
    ("Helium (He)", "Element"), ("Stickstoff (N₂)", "Element"),
    ("Wasser (H₂O)", "Verbindung"), ("Kochsalz (NaCl)", "Verbindung"),
    ("Kohlenstoffdioxid (CO₂)", "Verbindung"), ("Traubenzucker (C₆H₁₂O₆)", "Verbindung"),
    ("Ammoniak (NH₃)", "Verbindung"), ("Kalk (CaCO₃)", "Verbindung"),
    ("Magnesiumoxid (MgO)", "Verbindung"),
    ("Luft", "Gemisch"), ("Salzwasser", "Gemisch"), ("Messing", "Gemisch"),
    ("Granit", "Gemisch"), ("Mineralwasser", "Gemisch"), ("Milch", "Gemisch"),
    ("Edelstahl", "Gemisch"), ("Tee", "Gemisch"),
]

# Trennverfahren: a mixture → the technique that separates it (its physical-property basis).
SEPARATION_METHODS: list[tuple[str, str]] = [
    ("Sand und Wasser", "Filtrieren"),
    ("Salz in Wasser gelöst", "Eindampfen (Verdampfen des Wassers)"),
    ("Eisenspäne und Sand", "Magnetscheidung (mit einem Magneten)"),
    ("Alkohol und Wasser", "Destillation"),
    ("Sand und Kies (verschiedene Korngrößen)", "Sieben"),
    ("Öl und Wasser", "Dekantieren / Scheidetrichter"),
    ("Farbstoffe in Tinte", "Chromatografie"),
    ("Feststoff in einer Flüssigkeit (fein verteilt)", "Zentrifugieren"),
]

# Säuren / Basen / Neutral: everyday substances → pH-Charakter.
ACID_BASE: list[tuple[str, str]] = [
    ("Zitronensaft", "sauer"), ("Essig", "sauer"), ("Magensaft", "sauer"),
    ("Salzsäure", "sauer"), ("Cola", "sauer"),
    ("Seifenlauge", "basisch"), ("Natronlauge", "basisch"),
    ("Rohrreiniger", "basisch"), ("Backpulver-Lösung", "basisch"),
    ("reines Wasser", "neutral"), ("Kochsalzlösung", "neutral"), ("Zuckerlösung", "neutral"),
]

# Reaktionstypen: an (unambiguous) reaction skeleton → its type. The engine balances it;
# the *type* is the curated truth (reactions chosen so the type is unambiguous).
REACTION_TYPES: list[tuple[list[str], list[str], str]] = [
    (["Fe", "S"], ["FeS"], "Synthese (Vereinigung)"),
    (["N2", "H2"], ["NH3"], "Synthese (Vereinigung)"),
    (["H2O"], ["H2", "O2"], "Analyse (Zersetzung)"),
    (["CaCO3"], ["CaO", "CO2"], "Analyse (Zersetzung)"),
    (["HgO"], ["Hg", "O2"], "Analyse (Zersetzung)"),
    (["CH4", "O2"], ["CO2", "H2O"], "Verbrennung (Oxidation)"),
    (["C", "O2"], ["CO2"], "Verbrennung (Oxidation)"),
    (["HCl", "NaOH"], ["NaCl", "H2O"], "Säure-Base-Reaktion (Neutralisation)"),
    (["H2SO4", "NaOH"], ["Na2SO4", "H2O"], "Säure-Base-Reaktion (Neutralisation)"),
]

REACTION_TYPE_REASON: dict[str, str] = {
    "Synthese (Vereinigung)": "Aus mehreren Edukten entsteht ein einziges Produkt.",
    "Analyse (Zersetzung)": "Aus einem Edukt entstehen mehrere Produkte.",
    "Verbrennung (Oxidation)": "Ein Stoff reagiert mit Sauerstoff (O₂) unter Energiefreisetzung.",
    "Säure-Base-Reaktion (Neutralisation)": "Säure und Base reagieren zu Salz und Wasser.",
}


# --- curated context frames (Übungsreihe upgrade — the blackboard test) --------
# One vetted, plain, DIGIT-FREE German sentence per drawn item: where the substance /
# reaction occurs in the real world. Same discipline as every curated table above —
# the engine *selects* the sentence keyed to the drawn item; it never authors one at
# task time, and a context never asserts a number (all digits are computed by the
# recipe; `schema/parametric.Instance` enforces digit-freeness). SME vets at the gate.

# Formula → context sentence. Covers the molar-mass and atom-count pools.
COMPOUND_CONTEXTS: dict[str, str] = {
    "H2O": "Wasser ist das wichtigste Lösungsmittel — im Labor wie im Alltag.",
    "CO2": "Kohlenstoffdioxid entsteht bei jeder vollständigen Verbrennung und lässt "
           "Mineralwasser sprudeln.",
    "NaCl": "Kochsalz würzt unser Essen und dient im Winter als Streusalz.",
    "H2SO4": "Schwefelsäure steckt in Autobatterien und ist eine der wichtigsten "
             "Industriechemikalien.",
    "CaCO3": "Calciumcarbonat bildet Kalkstein und Marmor; beim Kalkbrennen wird es zu "
             "Branntkalk zersetzt.",
    "NaOH": "Natriumhydroxid ist der Wirkstoff vieler Abflussreiniger.",
    "KOH": "Kaliumhydroxid steckt in Schmierseife und in Alkali-Batterien.",
    "HCl": "Chlorwasserstoff ergibt in Wasser gelöst die Salzsäure — sie arbeitet auch "
           "in unserem Magen.",
    "NH3": "Ammoniak ist der Ausgangsstoff für Kunstdünger und riecht stechend.",
    "CH4": "Methan ist der Hauptbestandteil von Erdgas und brennt im Gasherd.",
    "C6H12O6": "Traubenzucker ist der schnelle Energielieferant unseres Körpers und "
               "entsteht bei der Photosynthese.",
    "Ca(OH)2": "Gelöschter Kalk wird seit der Antike zum Mauern und Verputzen verwendet.",
    "MgO": "Magnesiumoxid bleibt als weißes Pulver zurück, wenn Magnesium hell "
           "aufleuchtend verbrennt.",
    "Fe2O3": "Eisenoxid kennt jeder als Rost — und als rotes Pigment in Farben.",
    "Al2O3": "Aluminiumoxid bildet die schützende Schicht auf jedem Aluminiumteil; als "
             "Korund schleift es Werkzeuge.",
    "CuSO4": "Kupfersulfat bildet auffällig blaue Kristalle und wird im Weinbau als "
             "Pflanzenschutzmittel eingesetzt.",
    "KMnO4": "Kaliumpermanganat färbt Lösungen tiefviolett und wirkt stark oxidierend — "
             "ein klassisches Desinfektionsmittel.",
    "HNO3": "Salpetersäure braucht man zur Herstellung von Düngemitteln und Sprengstoffen.",
    "Na2CO3": "Soda wird seit Jahrtausenden zum Waschen und für die Glasherstellung genutzt.",
    "C2H5OH": "Ethanol ist der Alkohol in Wein und Bier — und ein wichtiges "
              "Desinfektionsmittel.",
    "CaCl2": "Calciumchlorid bindet Wasser so gut, dass es als Trockenmittel und "
             "Auftausalz dient.",
    "ZnO": "Zinkoxid ist das weiße Pigment in Sonnencremes und Wundsalben.",
    "Mg(OH)2": "Magnesiumhydroxid neutralisiert als Mittel gegen Sodbrennen überschüssige "
               "Magensäure.",
    "Al2(SO4)3": "Aluminiumsulfat klärt Trinkwasser, indem es Schwebstoffe ausflockt.",
    "Ba(NO3)2": "Bariumnitrat färbt Feuerwerksflammen grün.",
    "(NH4)2SO4": "Ammoniumsulfat ist ein verbreiteter Stickstoffdünger.",
    "CuSO4·5H2O": "Kupfersulfat bindet Wasser in seine blauen Kristalle ein — wasserfrei "
                  "ist es fast farblos.",
}


def reaction_key(reactants: list[str], products: list[str]) -> str:
    """Canonical key for a reaction skeleton — joins the raw formula lists, so the
    context lookup is independent of coefficients and display subscripts."""
    return " + ".join(reactants) + " → " + " + ".join(products)


# Skeleton key (see `reaction_key`) → context sentence. Covers the balancing /
# stoichiometry reaction pool in `pipeline/chemistry.py`.
REACTION_CONTEXTS: dict[str, str] = {
    "H2 + O2 → H2O": "Die Knallgasreaktion: Wasserstoff verbrennt mit Sauerstoff zu "
                     "Wasser — sie treibt auch Brennstoffzellen an.",
    "N2 + H2 → NH3": "Die Ammoniaksynthese nach Haber und Bosch macht aus Luftstickstoff "
                     "Dünger für die halbe Welt.",
    "Fe + O2 → Fe2O3": "Eisen reagiert mit Sauerstoff — langsam als Rost, schnell als "
                       "Funkenregen einer Wunderkerze.",
    "CH4 + O2 → CO2 + H2O": "Diese Verbrennung läuft in jedem Gasherd ab: Erdgas besteht "
                            "überwiegend aus Methan.",
    "Al + O2 → Al2O3": "Frisches Aluminium überzieht sich sofort mit einer schützenden "
                       "Oxidschicht.",
    "Na + Cl2 → NaCl": "Aus einem weichen Metall und einem giftigen Gas entsteht "
                       "harmloses Kochsalz.",
    "C3H8 + O2 → CO2 + H2O": "Propan verbrennt im Campingkocher und im Gasgriller.",
    "H2 + Cl2 → HCl": "Die Chlorknallgasreaktion startet schon durch Licht — das Produkt "
                      "ergibt gelöst die Salzsäure.",
    "Mg + O2 → MgO": "Magnesium verbrennt mit grellweißer Flamme — früher das Blitzlicht "
                     "der Fotografen.",
    "C2H6 + O2 → CO2 + H2O": "Ethan ist ein Bestandteil des Erdgases und verbrennt wie "
                             "Methan.",
    "Fe + Cl2 → FeCl3": "Eisen reagiert mit Chlorgas zu Eisenchlorid, einem "
                        "Flockungsmittel der Abwasserreinigung.",
    "NaN3 → Na + N2": "Im Airbag zersetzt sich Natriumazid schlagartig — der freigesetzte "
                      "Stickstoff bläst das Luftkissen auf.",
    "CO2 + H2O → C6H12O6 + O2": "Die Photosynthese: Pflanzen bauen aus Kohlenstoffdioxid "
                                "und Wasser Traubenzucker auf und geben Sauerstoff ab.",
}
