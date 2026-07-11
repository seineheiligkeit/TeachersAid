"""Finanzführerschein engine — the finance twin of `pipeline/chemistry.py`.

Same contract as `pipeline/parametrize.py` / `pipeline/chemistry.py`: each recipe OWNS
sampling + solving and returns an `Instance` (slot values + the DERIVED answer + a worked
Rechenweg), registered into the *shared* `_RECIPES` registry (`@_recipe`), so
`make_variants` / templates / `compose_variants` drive the Finanz recipes exactly as they
drive maths. The numbers are **computed from the curated legal tables** (`grounding/finanz.py`)
and the **cited VPI dataset** (`grounding/data/statistik_austria_vpi.json`) — *select, never
author*; every variant is correct by construction.

Three recipes:
- `lohnzettel`         — Brutto → SV (18,07 %) → Steuerbemessung → Lohnsteuer (Tarif 2026)
                         → Netto. The Rechenweg IS the chain; the difficulty band is the top
                         Grenzsteuersatz the wage reaches (20/30/40 % → 1/2/3).
- `inflation_vpi`      — real VPI index arithmetic from the cited dataset ("was 1995 X
                         kostete …"); values + citation selected from the dataset, never authored.
- `handyvertrag_vergleich` — 2–3 CONSTRUCTED tariffs (no real provider/price); 24-Monats-
                         Gesamtkosten computed; the internal-consistency discipline of the
                         Realien (every number in the answer is shown in the task).

**Zinseszins is deliberately NOT re-implemented here** — compound growth is already the
`exponential_model` recipe (its evaluate branch K·q^t is exactly the Sparbuch/Zinseszins case;
template `mat-fa-exponentialmodell`, anchored `MAT.OS.6.REE.10`). The Finanz pack ties into
that machinery rather than duplicating it.

`build_worksheet(sheet_id, n=…)` wraps N variants into an assemble-ready `WorksheetContent`
with the **strongest honest anchor** per sheet (Lohnzettel → ÜT 13 Wirtschafts-, Finanz- und
Verbraucher/innenbildung, a pure computation beyond the GWB competence *descriptors*;
Inflation → competence GWB.US.3.ENT.09, which names Inflation verbatim; Handytarife →
competence GWB.US.3.ENT.04, "Preise von … Dienstleistungen vergleichen") and the deliberate
didactic simplification stated ON the sheet.
"""

from __future__ import annotations

import random
from decimal import Decimal

from ..grounding.finanz import (
    SV_DIENSTNEHMER_RATE_2026, SV_HOECHSTBEITRAGSGRUNDLAGE_MONAT_2026, TAX_YEAR,
    euro, lohnsteuer_breakdown, lohnsteuer_jahr, prozent, sv_dienstnehmer, top_grenzsteuersatz,
    _cent,
)
from ..schema.blocks import SolutionStep
from ..schema.parametric import Instance
from .parametrize import Unsuitable, _recipe

SUBJECT = "Geographie und wirtschaftliche Bildung"
VPI_DATASET_ID = "statistik_austria_vpi"

_HBGL = SV_HOECHSTBEITRAGSGRUNDLAGE_MONAT_2026


# --- lohnzettel -------------------------------------------------------------
# Monthly gross wages grouped by the top Grenzsteuersatz the yearly Bemessungsgrundlage
# reaches (band 1 = 20 %, 2 = 30 %, 3 = 40 %) — the honest, computed difficulty ladder.
_BRUTTO_BANDS: dict[int, list[int]] = {
    1: [1400, 1600, 1800, 2000, 2200],
    2: [2400, 2600, 2800, 3000, 3200, 3400],
    3: [3800, 4200, 4600, 5000, 5500, 6000],
}
_ALL_BRUTTO = [b for pool in _BRUTTO_BANDS.values() for b in pool]
_RATE_TO_BAND = {Decimal("0.20"): 1, Decimal("0.30"): 2}   # 0.40/0.48/0.50 → band 3


def _lohn_chain(brutto_m: Decimal) -> dict:
    """The whole Brutto→Netto chain (monthly), each money value on Cent (Decimal, exact)."""
    sv_m = sv_dienstnehmer(brutto_m, cap=_HBGL)
    bemess_m = brutto_m - sv_m
    bemess_year = _cent(bemess_m * 12)
    lst_year = lohnsteuer_jahr(bemess_year)
    lst_m = _cent(lst_year / 12)
    netto_m = brutto_m - sv_m - lst_m
    return {"brutto_m": brutto_m, "sv_m": sv_m, "bemess_m": bemess_m,
            "bemess_year": bemess_year, "lst_year": lst_year, "lst_m": lst_m,
            "netto_m": netto_m}


@_recipe("lohnzettel")
def _lohnzettel(rng: random.Random, difficulty: int | None = None) -> Instance:
    """Vom Brutto zum Netto (Standardfall Angestellte, Tarif {TAX_YEAR}).

    Difficulty knob: the monthly gross is drawn from the band whose yearly
    Steuerbemessungsgrundlage tops out in the 20/30/40 %-Tarifstufe. The stamped band is
    the DELIVERED one (from `top_grenzsteuersatz`), never the requested value."""
    pool = _BRUTTO_BANDS.get(difficulty, _ALL_BRUTTO)
    brutto_m = Decimal(rng.choice(pool))
    c = _lohn_chain(brutto_m)
    band = _RATE_TO_BAND.get(top_grenzsteuersatz(c["bemess_year"]), 3)

    steps = [
        SolutionStep(text=f"Bruttolohn im Monat: {euro(c['brutto_m'])}."),
        SolutionStep(text=f"Sozialversicherung (Dienstnehmeranteil, {prozent(SV_DIENSTNEHMER_RATE_2026)}): "
                          f"{euro(c['brutto_m'])} · {prozent(SV_DIENSTNEHMER_RATE_2026)} = {euro(c['sv_m'])}."),
        SolutionStep(text=f"Steuerbemessungsgrundlage im Monat = Brutto − SV = "
                          f"{euro(c['brutto_m'])} − {euro(c['sv_m'])} = {euro(c['bemess_m'])}."),
        SolutionStep(text=f"Auf das Jahr hochgerechnet (12 Monate, ohne 13./14. Gehalt): "
                          f"{euro(c['bemess_m'])} · 12 = {euro(c['bemess_year'])}."),
    ]
    for row in lohnsteuer_breakdown(c["bemess_year"]):
        steps.append(SolutionStep(
            text=f"Tarifstufe {prozent(row['satz'])}: ({euro(row['bis'])} − {euro(row['von'])}) "
                 f"· {prozent(row['satz'])} = {euro(row['steuer'])}."))
    steps.append(SolutionStep(
        text=f"Jahres-Lohnsteuer (Summe der Stufen) = {euro(c['lst_year'])}; "
             f"pro Monat: {euro(c['lst_year'])} : 12 = {euro(c['lst_m'])}."))
    steps.append(SolutionStep(
        text=f"Nettolohn im Monat = Brutto − SV − Lohnsteuer = {euro(c['brutto_m'])} − "
             f"{euro(c['sv_m'])} − {euro(c['lst_m'])} = {euro(c['netto_m'])}."))

    return Instance(
        params={"brutto": euro(c["brutto_m"])},
        answer=f"Nettolohn ≈ {euro(c['netto_m'])} pro Monat "
               f"(SV {euro(c['sv_m'])}, Lohnsteuer {euro(c['lst_m'])}).",
        steps=steps, difficulty=band)


# --- inflation (real VPI index arithmetic, cited) ---------------------------
_THEN_YEARS = [1980, 1985, 1990, 1995, 2000, 2005]
_NOW_YEARS = [2020, 2022, 2023, 2024, 2025]
_PREISE = [5, 8, 10, 12, 15, 20, 25, 50, 100]


def _vpi_index() -> tuple[dict[int, float], str, str]:
    """{year: Jahresindex}, attribution, Stand — from the cited grounded dataset."""
    from ..grounding import data_store
    ds = data_store.get_dataset(VPI_DATASET_ID)
    if ds is None:
        raise RuntimeError(
            f"VPI-Datensatz '{VPI_DATASET_ID}' fehlt — bitte "
            "`python -m tools.fetch_statistik_austria_vpi` ausführen.")
    s = ds.series["jahresindex"]
    return dict(zip(s["years"], s["index"])), ds.source.attribution, ds.source.stand or ""


def _de(value: float, dp: int = 2) -> str:
    """German decimal (comma), fixed dp, no thousands separator (for index points/percent)."""
    return f"{value:.{dp}f}".replace(".", ",")


@_recipe("inflation_vpi")
def _inflation_vpi(rng: random.Random) -> Instance:
    """Kaufkraft/Teuerung über den echten Verbraucherpreisindex (Statistik Austria, zitiert).

    Zwei Fragerichtungen: den mit dem VPI mitgewachsenen Preis vorwärts rechnen, oder den
    Geldwert von heute in die Preise eines früheren Jahres zurückrechnen. Die Indexwerte sind
    echte, zitierte Fakten aus dem Datensatz; der Ausgangsbetrag ist ein angenommener Wert."""
    idx, attribution, stand = _vpi_index()
    thens = [y for y in _THEN_YEARS if y in idx]
    nows = [y for y in _NOW_YEARS if y in idx]
    then, now = rng.choice(thens), rng.choice(nows)
    price = Decimal(rng.choice(_PREISE))
    i_then, i_now = Decimal(str(idx[then])), Decimal(str(idx[now]))
    ask = rng.choice(["teuerung", "ruecklauf"])
    quelle = f"Quelle: {attribution}" + (f", Stand {stand}." if stand else ".")
    basis = SolutionStep(text=f"Verbraucherpreisindex (Basis 1966 = 100): {then} = "
                              f"{_de(idx[then], 1)}, {now} = {_de(idx[now], 1)}. {quelle}")

    if ask == "teuerung":
        result = _cent(price * i_now / i_then)
        steigerung = ((i_now / i_then - 1) * 100)
        aufgabe = (f"Eine Ware kostete im Jahr {then} {euro(price, cents=False)}. Wie viel "
                   f"kostet dieselbe Ware im Jahr {now}, wenn ihr Preis genau mit dem "
                   f"Verbraucherpreisindex gestiegen ist? Wie viel Prozent Teuerung ist das?")
        steps = [
            basis,
            SolutionStep(text=f"Der Preis wächst im Verhältnis der Indexwerte: "
                              f"{euro(price, cents=False)} · {_de(idx[now], 1)} / {_de(idx[then], 1)} "
                              f"= {euro(result)}."),
            SolutionStep(text=f"Teuerung = ({_de(idx[now], 1)} / {_de(idx[then], 1)} − 1) · 100 "
                              f"≈ {_de(float(steigerung), 1)} %."),
        ]
        answer = (f"≈ {euro(result)} im Jahr {now} "
                  f"(Teuerung ≈ {_de(float(steigerung), 1)} % gegenüber {then}).")
    else:
        result = _cent(price * i_then / i_now)
        aufgabe = (f"Wie viel war die Kaufkraft von {euro(price, cents=False)} aus dem Jahr "
                   f"{now} in Preisen des Jahres {then}? (Rechne den Geldwert mit dem "
                   f"Verbraucherpreisindex zurück.)")
        steps = [
            basis,
            SolutionStep(text=f"Zurückgerechnet im Verhältnis der Indexwerte: "
                              f"{euro(price, cents=False)} · {_de(idx[then], 1)} / {_de(idx[now], 1)} "
                              f"= {euro(result)}."),
        ]
        answer = f"≈ {euro(result)} in Preisen von {then}."

    return Instance(params={"aufgabe": aufgabe}, answer=answer, steps=steps)


# --- Handytarife vergleichen (constructed; internal-consistency discipline) --
# Brand-neutral colour names — NO real provider or real price (Realien discipline: the
# tariffs are invented-coherent, the comparison SKILL is what's exercised).
_TARIF_NAMES = ["Tarif Blau", "Tarif Grün", "Tarif Orange", "Tarif Rot", "Tarif Gelb"]
_GRUND = [8, 10, 12, 15, 18, 20, 25, 30]          # Grundgebühr €/Monat
_DATEN = [5, 10, 15, 20, 30, 40]                   # inkludiertes Datenvolumen (GB)
_AKTIV = [0, 10, 20, 30, 40]                       # einmalige Aktivierungskosten €
_MONATE = 24


def _tarif(rng: random.Random, name: str, *, with_aktiv: bool) -> dict:
    g = rng.choice(_GRUND)
    d = rng.choice(_DATEN)
    a = rng.choice([x for x in _AKTIV if x > 0]) if with_aktiv else 0
    total = Decimal(g) * _MONATE + Decimal(a)
    return {"name": name, "grund": g, "daten": d, "aktiv": a, "total": total}


@_recipe("handyvertrag_vergleich")
def _handyvertrag_vergleich(rng: random.Random, difficulty: int | None = None) -> Instance:
    """Handytarife über 24 Monate vergleichen — Gesamtkosten = Grundgebühr · 24 + Aktivierung.

    Difficulty knob: 1 = zwei Tarife ohne Aktivierungskosten · 2 = drei Tarife · 3 = drei
    Tarife mit Aktivierungskosten (die einmaligen Kosten kippen den Vergleich). Konstruiert,
    intern konsistent: jede Zahl der Antwort steht in der Angabe."""
    n = 2 if difficulty == 1 else 3
    with_aktiv = difficulty != 1 and (difficulty == 3 or rng.random() < 0.5)
    names = rng.sample(_TARIF_NAMES, n)
    tarife = [_tarif(rng, nm, with_aktiv=with_aktiv) for nm in names]
    totals = [t["total"] for t in tarife]
    if len(set(totals)) != n:
        raise Unsuitable                                # eindeutig günstigster Tarif verlangt
    best = min(tarife, key=lambda t: t["total"])
    band = 1 if n == 2 else (3 if with_aktiv else 2)

    def _describe(t: dict) -> str:
        akt = f", {t['aktiv']} € Aktivierung" if t["aktiv"] else ", keine Aktivierungskosten"
        return f"{t['name']}: {t['grund']} €/Monat, {t['daten']} GB{akt}"

    angabe = "; ".join(_describe(t) for t in tarife) + "."
    steps = [
        SolutionStep(text=f"{t['name']}: {t['grund']} €/Monat · {_MONATE} Monate"
                          + (f" + {t['aktiv']} € Aktivierung" if t["aktiv"] else "")
                          + f" = {euro(t['total'])}.")
        for t in tarife
    ]
    steps.append(SolutionStep(
        text=f"Günstigster Tarif über {_MONATE} Monate: {best['name']} mit {euro(best['total'])}."))
    return Instance(
        params={"tarife": angabe},
        answer=f"{best['name']} ist über {_MONATE} Monate am günstigsten "
               f"({euro(best['total'])} gesamt).",
        steps=steps, difficulty=band)


# ---------------------------------------------------------------------------
#  Worksheet builder — the strongest honest anchor per sheet (see module docstring)
# ---------------------------------------------------------------------------
_LOHN_SIMPL = (
    f"Vereinfachte Modellrechnung (Finanzführerschein, Stand {TAX_YEAR}). Wir rechnen den "
    "Standardfall: eine angestellte Person, nur der laufende Monatslohn — kein 13./14. Gehalt "
    "und keine Sonderzahlungen, keine Pendlerpauschale, kein Alleinverdiener-/Alleinerzieher"
    "absetzbetrag und keine weiteren Absetz- oder Freibeträge außer der steuerfreien Grundstufe "
    f"(0 % bis 13.539 €). Der Sozialversicherungs-Dienstnehmeranteil wird pauschal mit "
    f"{prozent(SV_DIENSTNEHMER_RATE_2026)} angesetzt (Angestellte, außerhalb Wiens; in Wien "
    "18,32 %), die Lohnsteuer nach dem Einkommensteuertarif 2026. So bleibt die Kette Brutto → "
    "Sozialversicherung → Steuerbemessung → Lohnsteuer → Netto klar erkennbar — es geht um das "
    "Verstehen dieser Kette, nicht um jede Sonderregel des Steuerrechts."
)
_HANDY_SIMPL = (
    "Die Tarife auf diesem Blatt sind frei erfunden (keine echten Anbieter, keine echten "
    "Preise) — geübt wird der Vergleich: die Gesamtkosten über die ganze Vertragsdauer statt "
    "nur der monatlichen Grundgebühr, einmalige Kosten eingerechnet."
)


def _sheets():
    """Sheet specs (lazy so the module imports cleanly before the schema is needed)."""
    return {
        "lohnzettel": dict(
            template_id="fin-lohnzettel", klasse=3, uet=13, ramp=True, lines=6,
            title="Finanzführerschein: Vom Brutto zum Netto",
            kernfrage="Wie wird aus dem Bruttolohn das Netto — und wohin geht der Rest?",
            intro=[("callout", "note", _LOHN_SIMPL)],
            throughline=(
                "Die Rechenkette Brutto → Sozialversicherung → Steuerbemessung → Lohnsteuer → "
                "Netto, jede Variante mit vollständigem Rechenweg. Bewusst vereinfachter "
                "Standardfall (auf dem Blatt ausgewiesen); verankert als übergreifendes Thema "
                "13 (Wirtschafts-, Finanz- und Verbraucher/innenbildung), weil die reine "
                "Berechnung über die GWB-Kompetenzbeschreibungen hinausgeht."),
        ),
        "inflation": dict(
            template_id="fin-inflation", klasse=3, uet=None, ramp=False, lines=4,
            kompetenzbereich="Entwicklungen am Wirtschaftsstandort Österreich",
            title="Finanzführerschein: Inflation und Kaufkraft",
            kernfrage="Warum wird dasselbe Geld mit der Zeit weniger wert?",
            intro=[("prose", None,
                    "Der Verbraucherpreisindex (VPI) misst, wie sich die Preise über die Jahre "
                    "verändern. Mit ihm lässt sich ausrechnen, wie viel eine Ware früher im "
                    "Vergleich zu heute gekostet hat. Datenquelle: Statistik Austria "
                    "(data.statistik.gv.at, CC BY 4.0).")],
            throughline=(
                "Inflation greifbar über echte, zitierte VPI-Zahlen (Statistik Austria): den "
                "mitgewachsenen Preis vorwärts, den Geldwert rückwärts rechnen. Verankert an "
                "GWB.US.3.ENT.09, die Inflation ausdrücklich als Kenngröße nennt."),
        ),
        "handyvertrag": dict(
            template_id="fin-handyvertrag", klasse=3, uet=None, ramp=True, lines=5,
            kompetenzbereich="Entwicklungen am Wirtschaftsstandort Österreich",
            title="Finanzführerschein: Handytarife vergleichen",
            kernfrage="Welcher Tarif ist über zwei Jahre wirklich der günstigste?",
            intro=[("callout", "note", _HANDY_SIMPL)],
            throughline=(
                "Preise von Dienstleistungen über die ganze Vertragsdauer vergleichen (nicht "
                "nur die Grundgebühr) — konstruierte, aber realistische Tarife. Verankert an "
                "GWB.US.3.ENT.04, „Preise von … Dienstleistungen vergleichen“."),
        ),
    }


def build_worksheet(sheet_id: str, *, n: int = 6, today=None):
    """Build an assemble-ready `WorksheetContent` for a Finanzführerschein sheet + its
    resolution (mirrors `library.templates.variant_worksheet`, but honours the sheet's
    anchor mode and injects the didactic-simplification note ON the sheet). Returns
    (content, resolution)."""
    from ..grounding import lehrplan_store as ls
    from ..library.templates import find_template
    from ..schema.blocks import InfoBlock
    from ..schema.enums import Role
    from ..schema.response import LinesResponse
    from ..schema.worksheet import (
        Baustein, BundleRequest, TeacherOverview, WorksheetContent, WorksheetMeta,
    )
    from .parametrize import make_variants_with_assets
    from .resolve import resolve, resolve_kompetenzbereich

    spec = _sheets()[sheet_id]
    template = find_template(spec["template_id"])
    if template is None:
        raise KeyError(f"no Finanz template '{spec['template_id']}'")
    klasse = spec["klasse"]
    stufe = ls.stufe_for_klasse(klasse)
    blocks, assets = make_variants_with_assets(template, n, ramp=spec["ramp"])
    # A Rechenweg needs room: give each computation task enough answer lines (the template
    # header stays a pure append — the answer surface is set here, in the new module).
    for blk in blocks:
        if blk.role == Role.TASK:
            blk.response = LinesResponse(n=spec["lines"])

    if spec["uet"]:
        req = BundleRequest(subject=SUBJECT, klasse=klasse, stufe=stufe,
                            topic_raw=spec["title"], anchor_mode="uet", anchor_uet=spec["uet"])
        res = resolve(req, today=today)
        anchor_mode, anchor_uet = "uet", spec["uet"]
        anchor_label = f"ÜT {spec['uet']}"
    else:
        res = resolve_kompetenzbereich(SUBJECT, klasse, spec["kompetenzbereich"], today=today)
        anchor_mode, anchor_uet = "competence", None
        anchor_label = spec["kompetenzbereich"]

    intro = [InfoBlock(id=f"fin.{k}", kind=kind, callout_role=role, content=text)
             for k, (kind, role, text) in zip(("modell", "quelle", "zusatz"), spec["intro"])]

    stamped = [b.difficulty for b in blocks if b.difficulty is not None]
    ramped = len(set(stamped)) > 1
    subtitle = f"Finanzführerschein — {n} Varianten" + (", aufsteigend" if ramped else "")
    meta = WorksheetMeta(
        title=spec["title"], subtitle=subtitle, subject=SUBJECT, stufe=stufe, klasse=klasse,
        kernfrage=spec["kernfrage"], fassung=res.fassung,
        lehrplan_label=f"{SUBJECT} · {klasse}. Kl. · {anchor_label}")
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(SUBJECT, stufe), intro=intro,
        sections=[Baustein(id="uebung", title=spec["title"],
                           teacher_overview=TeacherOverview(throughline=spec["throughline"]),
                           blocks=blocks)],
        assets=assets, anchor_mode=anchor_mode, anchor_uet=anchor_uet)
    return content, res
