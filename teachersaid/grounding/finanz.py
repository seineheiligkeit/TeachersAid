"""Finanz-Grounding — the curated legal tables the Finanzführerschein computes from.

The finance analogue of `grounding/chemistry.py` (atomic masses) and `grounding/data/`
(cited datasets): the **facts** here are the 2026 Austrian *Lohnsteuertarif* brackets and
the *Sozialversicherungs-Dienstnehmeranteil* rate. Discipline is identical —
*select, never author*: every number comes from a cited authority (BMF / § 33 EStG for the
tax tariff; WKO / ÖGK / ASVG for the SV rates), verified online at authoring time (do NOT
trust an LLM's memory of tax law). The engine (`pipeline/finanz.py`) then *computes* a
Lohnzettel — Brutto → SV → Steuerbemessung → Lohnsteuer → Netto — from these tables, so
every variant is **correct by construction**, exactly like a molar mass or a sympy result.

**Deliberate didactic simplification** (stated ON the sheet, see `pipeline/finanz.py`):
the standard employment case only — an *Angestellte/r*, only the running monthly wage, no
13./14. Gehalt / Sonderzahlungen, no Pendlerpauschale, no AVAB/AEAB, no extra
Absetz-/Freibeträge beyond the tax-free Grundstufe (0 % up to 13 539 €). The **learning
object is the CHAIN**, not tax-law completeness.

**Refresh (yearly, like the datasets).** Both tables change every year: the
Einkommensteuertarif is lifted by the annual *Progressionsabgeltung* (kalte-Progression
indexation), the SV rates/Höchstbeitragsgrundlage by the *Aufwertungszahl*. To update: bump
`TAX_YEAR`, replace the bracket bounds and the SV rate, re-verify against BMF (Steuertarif)
and WKO/ÖGK (SV-Werte), and update the two `SourceRef.stand` stamps. `tests/test_finanz.py`
pins hand-computed net wages for fixed gross inputs — keep those green when refreshing.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from ..schema.datasets import SourceRef

TAX_YEAR = 2026

# --- provenance -------------------------------------------------------------
# A tax rate is a *legal fact* (a statute), not a licensed dataset — facts are free
# (invariants §6), so `redistributable=True` with no licence; the citation names the
# authority + the legal basis. Verified online 2026-07 against BMF + two tax advisories.
LOHNSTEUER_SOURCE = SourceRef(
    publisher="Bundesministerium für Finanzen (BMF)",
    title="Einkommensteuertarif 2026 (§ 33 Abs. 1 EStG 1988, inkl. Progressionsabgeltung 2026)",
    url="https://www.bmf.gv.at/themen/steuern/arbeitnehmerveranlagung/"
        "steuertarif-steuerabsetzbetraege/steuertarif-steuerabsetzbetraege.html",
    redistributable=True,
    attribution="Einkommensteuertarif 2026: BMF (§ 33 EStG 1988), Veranlagung 2026",
    stand="2026",
)

SV_SOURCE = SourceRef(
    publisher="Wirtschaftskammer Österreich (WKO) / Österreichische Gesundheitskasse (ÖGK)",
    title="Sozialversicherung — Beitragssätze Dienstnehmer 2026 (ASVG, Angestellte)",
    url="https://www.wko.at/entlohnung/beitragswesen-dienstnehmer-2026",
    redistributable=True,
    attribution="SV-Beitragssätze 2026: WKO / ÖGK (ASVG, Angestellte, Standardfall)",
    stand="2026-01-01",
)

# --- Lohnsteuertarif 2026 (Jahreseinkommen) ---------------------------------
# Progressive brackets: each pair is (untere Grenze, Grenzsteuersatz). The tax on an
# amount x is the sum over brackets of rate·(portion of x that falls in that bracket).
# Verified 2026-07 against the Arbeiterkammer "Steuerwertetabelle 2026" and two independent
# Steuerberatungs-Quellen (identical bounds and the cumulative amounts below).
BRACKETS_2026: list[tuple[Decimal, Decimal]] = [
    (Decimal("0"),       Decimal("0.00")),
    (Decimal("13539"),   Decimal("0.20")),
    (Decimal("21992"),   Decimal("0.30")),
    (Decimal("36458"),   Decimal("0.40")),
    (Decimal("70365"),   Decimal("0.48")),
    (Decimal("104859"),  Decimal("0.50")),
    (Decimal("1000000"), Decimal("0.55")),
]

# --- Sozialversicherung 2026 (Dienstnehmeranteil, Angestellte) --------------
# Standardfall Angestellte/r (außerhalb Wiens). Wien liegt 2026 bei 18,32 % (der
# Wohnbauförderungsbeitrag ist dort 0,75 % statt 0,50 %) — die 0,25 % Differenz nennen
# wir auf dem Blatt, rechnen aber den bundesweiten Standardsatz.
SV_DIENSTNEHMER_RATE_2026 = Decimal("0.1807")
SV_COMPONENTS_2026: dict[str, Decimal] = {
    "Krankenversicherung": Decimal("0.0387"),
    "Pensionsversicherung": Decimal("0.1025"),
    "Arbeitslosenversicherung": Decimal("0.0295"),
    "Arbeiterkammerumlage": Decimal("0.0050"),
    "Wohnbauförderungsbeitrag": Decimal("0.0050"),
}
# Höchstbeitragsgrundlage (laufende Bezüge) — oberhalb wird kein SV-Beitrag mehr fällig.
SV_HOECHSTBEITRAGSGRUNDLAGE_MONAT_2026 = Decimal("6930")

# self-check: the curated component split reproduces the published total rate exactly.
assert sum(SV_COMPONENTS_2026.values()) == SV_DIENSTNEHMER_RATE_2026


def _cent(x: Decimal) -> Decimal:
    """Kaufmännisch auf Cent runden (ROUND_HALF_UP) — die im Lohnverrechnung übliche
    Rundung; deterministisch und exakt (Decimal, nicht float)."""
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def sv_dienstnehmer(brutto: Decimal, *, cap: Decimal | None = None) -> Decimal:
    """SV-Dienstnehmeranteil = 18,07 % vom Brutto (Angestellte), gedeckelt bei der
    Höchstbeitragsgrundlage `cap` (monatlich, falls angegeben). Auf Cent gerundet."""
    base = Decimal(brutto)
    if cap is not None and base > cap:
        base = Decimal(cap)
    return _cent(base * SV_DIENSTNEHMER_RATE_2026)


def lohnsteuer_breakdown(bemessungsgrundlage: Decimal) -> list[dict]:
    """Progressive Aufschlüsselung der Jahres-Lohnsteuer: je *aktiver* Tarifstufe ein
    Eintrag {von, bis, betrag_in_stufe, satz, steuer} (nur Stufen mit betrag_in_stufe > 0).
    Die Steuer der Stufe ist noch nicht gerundet — `lohnsteuer_jahr` rundet die Summe."""
    x = Decimal(bemessungsgrundlage)
    out: list[dict] = []
    if x <= 0:
        return out
    for i, (low, rate) in enumerate(BRACKETS_2026):
        if x <= low:
            break
        high = BRACKETS_2026[i + 1][0] if i + 1 < len(BRACKETS_2026) else None
        upper = x if (high is None or x < high) else high
        taxed = upper - low
        if taxed > 0 and rate > 0:
            out.append({"von": low, "bis": (high if (high is not None and x >= high) else x),
                        "betrag_in_stufe": taxed, "satz": rate, "steuer": taxed * rate})
    return out


def lohnsteuer_jahr(bemessungsgrundlage: Decimal) -> Decimal:
    """Jahres-Lohnsteuer aus der Steuerbemessungsgrundlage nach dem Tarif 2026
    (progressiv). Auf Cent gerundet, exakt (Decimal)."""
    total = sum((row["steuer"] for row in lohnsteuer_breakdown(bemessungsgrundlage)), Decimal("0"))
    return _cent(total)


def top_grenzsteuersatz(bemessungsgrundlage: Decimal) -> Decimal:
    """Der Grenzsteuersatz der höchsten erreichten Tarifstufe (0,20 / 0,30 / …) — die
    natürliche Schwierigkeits-Kennzahl einer Lohnzettel-Aufgabe."""
    x = Decimal(bemessungsgrundlage)
    rate = Decimal("0.00")
    for low, r in BRACKETS_2026:
        if x > low:
            rate = r
        else:
            break
    return rate


# --- German money / percent formatting (Austrian convention) ----------------
def euro(value: Decimal, *, cents: bool = True) -> str:
    """Betrag als „2.129,45 €" (Punkt als Tausender-, Komma als Dezimaltrenner)."""
    q = _cent(Decimal(value)) if cents else Decimal(value).quantize(Decimal("1"))
    neg = q < 0
    q = abs(q)
    whole, _, frac = f"{q:.2f}".partition(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:]); whole = whole[:-3]
    groups.insert(0, whole)
    s = ".".join(groups)
    if cents:
        s = f"{s},{frac}"
    return f"{'-' if neg else ''}{s} €"


def prozent(rate: Decimal) -> str:
    """Rate (0,1807) als „18,07 %" (bis zu zwei Nachkommastellen, Komma-Dezimaltrenner)."""
    p = (Decimal(rate) * 100).quantize(Decimal("0.01"))
    s = f"{p:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"{s} %"
