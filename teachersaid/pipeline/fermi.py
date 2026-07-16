"""Fermi-Werkstatt engine — the computed worked chain, point estimate + acceptable range.

The estimation twin of `pipeline/finanz.py`: the curated model (`grounding/fermi.py`) is
turned into a **correct-by-construction** solution and an assemble-ready `WorksheetContent`.
Two things are DERIVED here (never authored), and both are teacher-judgment SUPPORT, not a
grading engine:

1. **The worked chain + point estimate** — the chain is evaluated at every anchor's `value`
   (a `Decimal` product/quotient), producing the `solution_steps` (teacher-only Rechenweg) and
   the headline `Bezugswert`. The chain arithmetic reproduces the point estimate exactly
   (locked by a test).

2. **The acceptable range** — the anchor `[low, high]` bands are propagated through the SAME
   chain by **interval arithmetic** (all quantities are strictly positive):
       multiply:  [a,b]·[c,d] = [a·c, b·d]
       divide:    [a,b]/[c,d] = [a/d, b/c]
       add:       [a,b]+[c,d] = [a+c, b+d]
   Each anchor appears once per chain, so there is no interval-dependency over-widening — the
   propagated `[low, high]` is the honest plausible band. **Convention:** we present the raw
   propagated interval as the *plausibler Bereich* AND its order-of-magnitude span as the
   coarsest honest grading frame ("richtig = richtige Größenordnung"). Wider anchor bands ⇒ a
   wider range (monotone; locked by a test).

Student side: the Fermi question + a decomposition scaffold (a blank Annahmen-Raster + a
compute box) that invites decomposition WITHOUT dictating the chain — solvable rough or fine
(**selbstdifferenzierend**). The sheet shows only the GIVEN anchor values; the to-be-estimated
values, the point estimate and the range live in teacher-only fields (answer_key /
acceptable_reasoning / solution_steps / teacher_overview) and never leak to the student or
homework projection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from ..grounding import fermi as gf
from ..schema.blocks import SolutionStep
from ..schema.fermi import FermiAnchor, FermiProblem

SUBJECT = "Mathematik"


# ---------------------------------------------------------------------------
#  German number formatting (Austrian convention: '.' thousands, ',' decimal)
# ---------------------------------------------------------------------------
def _round_sig(d: Decimal, sig: int) -> Decimal:
    """Round a positive Decimal to `sig` significant figures (Fermi answers are honest to
    ~1–2 sig figs — precision beyond that is fake)."""
    d = Decimal(d)
    if d == 0:
        return Decimal(0)
    exp = d.adjusted()                       # exponent of the most-significant digit
    quant = Decimal(1).scaleb(exp - (sig - 1))
    return d.quantize(quant, rounding=ROUND_HALF_UP)


def _group_thousands(intdigits: str) -> str:
    groups = []
    while len(intdigits) > 3:
        groups.insert(0, intdigits[-3:])
        intdigits = intdigits[:-3]
    groups.insert(0, intdigits)
    return ".".join(groups)


def _de_number(value: Decimal) -> str:
    """A Decimal as a German number string: '.' thousands, ',' decimal, trailing zeros
    trimmed. 1440 → '1.440'; Decimal('2.2') → '2,2'; Decimal('0.005') → '0,005'."""
    d = Decimal(value)
    neg = d < 0
    s = format(abs(d), "f")                  # no scientific notation
    intp, _, frac = s.partition(".")
    frac = frac.rstrip("0")
    out = _group_thousands(intp) + ("," + frac if frac else "")
    return ("-" if neg else "") + out


def fmt_q(anchor: FermiAnchor, value: Decimal | None = None) -> str:
    """An anchor quantity with its unit ('15 L', '1.440 min', '0,02', '2 Millionen …')."""
    v = anchor.value if value is None else value
    return f"{_de_number(v)} {anchor.unit}".strip()


def human_de(value: Decimal, unit: str, *, sig: int = 2) -> str:
    """A (usually large) result at `sig` significant figures with a readable German scale word
    — '1,6 Millionen L', '3,0 Milliarden Schläge', '34.000 Luftballons', '28 …'."""
    d = _round_sig(Decimal(value), sig)
    a = abs(d)
    if a >= Decimal("1e9"):
        return f"{_de_number(_round_sig(d / Decimal('1e9'), sig))} Milliarden {unit}".strip()
    if a >= Decimal("1e6"):
        return f"{_de_number(_round_sig(d / Decimal('1e6'), sig))} Millionen {unit}".strip()
    return f"{_de_number(d)} {unit}".strip()


# --- order of magnitude ------------------------------------------------------
_OOM_LABEL = {
    0: "Einer", 1: "Zehner", 2: "Hunderter", 3: "Tausender", 4: "Zehntausender",
    5: "Hunderttausender", 6: "Millionen", 7: "Zehnmillionen", 8: "Hundertmillionen",
    9: "Milliarden", 10: "Zehnmilliarden", 11: "Hundertmilliarden", 12: "Billionen",
}


def _oom(d: Decimal) -> int:
    """The power-of-ten bin (floor of log10) of a positive value."""
    return int(math.floor(math.log10(float(d)))) if d > 0 else 0


def _oom_label(e: int) -> str:
    return _OOM_LABEL.get(e, f"10^{e}")


# ---------------------------------------------------------------------------
#  The derived solution — worked chain + point estimate + propagated range
# ---------------------------------------------------------------------------
@dataclass
class FermiSolution:
    point: Decimal                     # the point estimate (chain at every anchor's value)
    low: Decimal                       # propagated lower bound
    high: Decimal                      # propagated upper bound
    unit: str
    steps: list[SolutionStep] = field(default_factory=list)      # the worked Rechenweg
    estimated_lines: list[str] = field(default_factory=list)     # per-anchor teacher sanity
    given_lines: list[str] = field(default_factory=list)

    def oom(self) -> int:
        return _oom(self.point)

    def range_str(self, sig: int) -> str:
        return f"{human_de(self.low, self.unit, sig=sig)} bis {human_de(self.high, self.unit, sig=sig)}"

    def point_str(self, sig: int) -> str:
        return human_de(self.point, self.unit, sig=sig)

    def oom_str(self) -> str:
        lo_e, hi_e, pt_e = _oom(self.low), _oom(self.high), self.oom()
        base = f"liegt im Bereich der {_oom_label(pt_e)} (10^{pt_e})"
        if hi_e > lo_e:
            span = hi_e - lo_e
            return (f"{base}; die plausiblen Schätzungen streuen über {span} "
                    f"Zehnerpotenz{'en' if span > 1 else ''} ({_oom_label(lo_e)}–{_oom_label(hi_e)})")
        return base


def _prov_tag(anchor: FermiAnchor) -> str:
    """A short teacher-facing provenance tag for an anchor (Datenquelle / Quelle / Schätzung)."""
    p = anchor.provenance
    if p.kind == "dataset":
        from ..grounding import data_store
        src = data_store.source_ref_for(p.dataset_id)
        who = (src.attribution if src else None) or p.dataset_id
        return f"Datenquelle: {who}"
    if p.kind == "cited":
        return f"Quelle: {p.source.attribution}"
    return "begründete Schätzung"


def _sanity_line(anchor: FermiAnchor) -> str:
    """The teacher per-anchor sanity line: 'label: Bezugswert X (plausibel low–high) — prov'."""
    band = (f"plausibel {_de_number(anchor.low)}–{fmt_q(anchor, anchor.high)}"
            if not anchor.is_exact() else "exakt")
    return f"{anchor.label}: Bezugswert {fmt_q(anchor)} ({band}) — {_prov_tag(anchor)}."


def evaluate_chain(problem: FermiProblem,
                   anchors: dict[str, FermiAnchor] | None = None) -> FermiSolution:
    """Evaluate a Fermi problem's chain: the point estimate (Decimal product/quotient at every
    anchor's value) + the propagated `[low, high]` interval + the worked Rechenweg. `anchors`
    defaults to the curated registry (injectable so tests can widen a band and check the range
    widens monotonically)."""
    anchors = anchors or gf.ANCHORS
    pt = Decimal(1)
    lo = Decimal(1)
    hi = Decimal(1)
    steps: list[SolutionStep] = []
    est_lines: list[str] = []
    given_lines: list[str] = []

    for i, step in enumerate(problem.chain):
        a = anchors[step.anchor_id] if step.anchor_id in anchors else gf.get_anchor(step.anchor_id)
        (given_lines if step.given else est_lines).append(_sanity_line(a))
        label = (step.as_label or a.label)
        if step.op == "multiply":
            pt *= a.value
            lo *= a.low
            hi *= a.high
        elif step.op == "divide":
            pt /= a.value
            lo, hi = lo / a.high, hi / a.low
        elif step.op == "add":
            pt += a.value
            lo += a.low
            hi += a.high

        if i == 0:                                   # seeds running = 1 · value = value
            steps.append(SolutionStep(
                text=f"Beginne mit „{label}“: {fmt_q(a)}."))
        else:
            # the running value's unit is in transition mid-chain (households → pianos → …),
            # so intermediate lines carry no unit; the final Bezugswert line names it.
            verb = {"multiply": "mal", "divide": "geteilt durch", "add": "plus"}[step.op]
            steps.append(SolutionStep(
                text=f"{verb} „{label}“ ({fmt_q(a)}) → rund {_de_number(_round_sig(pt, 3))}."))

    sig = problem.sig
    steps.append(SolutionStep(
        text=f"Bezugswert (Punktschätzung): rund {human_de(pt, problem.result_unit, sig=sig)}."))

    return FermiSolution(point=pt, low=lo, high=hi, unit=problem.result_unit,
                         steps=steps, estimated_lines=est_lines, given_lines=given_lines)


# ---------------------------------------------------------------------------
#  Worksheet builder
# ---------------------------------------------------------------------------
_METHOD = (
    "So gehst du an eine Schätzfrage heran: (1) Zerlege die Frage in kleinere Größen, die du "
    "besser schätzen kannst. (2) Schätze jede Größe — triff eine begründete Annahme. (3) Rechne "
    "die Größen zusammen (mal oder geteilt). (4) Prüfe die Größenordnung: Ist das Ergebnis grob "
    "sinnvoll? Es gibt keine einzige richtige Zahl — gute Annahmen und ein klarer Rechenweg "
    "zählen mehr als die letzte Stelle."
)

# Per-problem qualitative watch-outs (teacher + homework projection — so they carry NO secret
# value, no point estimate and no range: only the typical over-/under-estimate PATTERN).
_WATCH_OUTS: dict[str, list[str]] = {
    "schulwasser": [
        "Häufig zu hoch: der Haushaltswert von ~130 L/Person/Tag wird übernommen — in der "
        "Schule ist man nur einen Teil des Tages, der Wert ist viel kleiner.",
        "Schultage (nicht Kalendertage) verwenden — ein Faktor ~2 Unterschied.",
    ],
    "schulpapier": [
        "Häufig zu niedrig: nur an eigene Blätter gedacht, Kopien/Tests/Ausdrucke vergessen.",
        "Pro Schultag rechnen, nicht pro Kalendertag.",
    ],
    "klavierstimmer_wien": [
        "Häufig zu hoch: alle Tasteninstrumente gezählt — Keyboards und Digitalpianos werden "
        "nicht gestimmt.",
        "Die Division durch die Jahresarbeit einer Stimmer:in nicht vergessen (sonst kommt die "
        "Zahl der Stimmungen heraus, nicht die der Personen).",
    ],
    "schulweg_woche": [
        "„Pro Tag“ heißt hin UND zurück — der Faktor 2 wird oft vergessen.",
        "Über eine Schulwoche (5 Tage) rechnen, nicht über 7 Kalendertage.",
    ],
    "herzschlaege_leben": [
        "Einheiten-Kette sauber halten: Schläge/min · min/Tag · Tage/Jahr · Jahre.",
        "Der Ruhepuls ist eine Schätzung — mit 60 oder mit 90 zu rechnen ändert die "
        "Größenordnung nicht.",
    ],
    "klassenzimmer_ballons": [
        "Raumhöhe nicht vergessen — es ist ein Rauminhalt (Länge · Breite · Höhe), keine Fläche.",
        "Einheiten angleichen: Raum in m³, Ballon in m³ (oder beide in Liter).",
    ],
}


def _given_display(anchor: FermiAnchor) -> str:
    """A given anchor as a rounded student-facing fact ('rund 2 Millionen Personen')."""
    if anchor.value >= Decimal("1e6"):
        return f"{anchor.label}: rund {human_de(anchor.value, anchor.unit, sig=2)}"
    return f"{anchor.label}: rund {fmt_q(anchor)}"


def build_worksheet(problem_id: str, *, today=None):
    """Build an assemble-ready `WorksheetContent` for a Fermi problem + its resolution
    (mirrors `pipeline/finanz.build_worksheet`). Returns (content, resolution).

    The worked chain, point estimate and propagated range are computed here and placed ONLY in
    teacher-only fields; the student/homework side gets the question, the given facts, a blank
    Annahmen-Raster and a compute box (selbstdifferenzierend)."""
    from ..grounding import lehrplan_store as ls
    from ..schema.blocks import InfoBlock, Serves, TableFillPayload, TaskBlock
    from ..schema.response import BoxResponse, NoneResponse
    from ..schema.worksheet import (
        Baustein, TeacherOverview, WorksheetContent, WorksheetMeta,
    )
    from .resolve import resolve_kompetenzbereich

    problem = gf.get_problem(problem_id)
    klasse = problem.klasse
    stufe = ls.stufe_for_klasse(klasse)
    res = resolve_kompetenzbereich(SUBJECT, klasse, problem.kompetenzbereich, today=today)
    sol = evaluate_chain(problem)
    sig = problem.sig
    serves = [Serves(competence_id=problem.competence_id, relation="exercises")]

    given = [gf.get_anchor(aid) for aid in problem.given_ids()]

    # --- student-facing intro + method (no problem-specific numbers) ---------
    intro = InfoBlock(
        id="fermi.intro", kind="callout", callout_role="note",
        content=("In dieser Aufgabe schätzt du eine Zahl, die niemand einfach nachschlägt. Du "
                 "darfst großzügig runden — wichtig ist, dass du deine Annahmen aufschreibst "
                 "und begründest. " + problem.context_note))
    i_method = InfoBlock(id="fermi.method", kind="prose", content=_METHOD)
    infos = [i_method]
    if given:
        i_given = InfoBlock(
            id="fermi.given", kind="key_fact",
            content="Das ist gegeben: " + "; ".join(_given_display(a) for a in given) + ".")
        infos.append(i_given)

    # --- t1: the decomposition scaffold (blank Annahmen-Raster) --------------
    t1 = TaskBlock(
        id="fermi.t1", kind="table_fill",
        prompt=("Zerlege die Frage: Welche Größen musst du schätzen, um sie zu beantworten? "
                "Trage deine Annahmen in die Tabelle ein — je feiner du zerlegst, desto besser."),
        payload=TableFillPayload(
            columns=["Größe, die ich schätze", "mein geschätzter Wert", "Warum dieser Wert?"],
            rows=[[None, None, None] for _ in range(5)]),
        response=NoneResponse(),
        cognitive_level="analyze", dimensions=[problem.dimension], serves=serves, est_minutes=8,
        answer_key=("Zu schätzende Größen (Bezugswerte, Richtwerte — nicht die einzig richtigen "
                    "Zahlen): " + " ".join(sol.estimated_lines)
                    + (" Gegeben auf dem Blatt: "
                       + ", ".join(a.label for a in given) + "." if given else "")),
        acceptable_reasoning=("Akzeptiere jede begründete Annahme im angegebenen Bereich; die "
                              "Spannen sind Richtwerte, keine harten Grenzen. Wer feiner zerlegt "
                              "(mehr Zeilen) und jede Annahme begründet, arbeitet auf höherem "
                              "Niveau."),
        watch_outs=["Es zählt die Begründung, nicht ein bestimmter Wert — eine gut begründete "
                    "Annahme ist auch dann richtig, wenn sie vom Bezugswert abweicht."])

    # --- t2: compute + order-of-magnitude reflection (the modelling task) ----
    t2 = TaskBlock(
        id="fermi.t2", kind="modelling_task",
        prompt=(f"Rechne jetzt mit deinen Annahmen: Wie lautet deine Schätzung für "
                f"{problem.result_label}? Schreibe deinen Rechenweg auf und gib am Ende die "
                f"Größenordnung an (Hunderte, Tausende, Millionen …)."),
        response=BoxResponse(min_height_mm=105),
        cognitive_level="create", dimensions=[problem.dimension], serves=serves, est_minutes=12,
        answer_key=f"Bezugswert (Punktschätzung): rund {sol.point_str(sig)}.",
        acceptable_reasoning=(
            f"Plausibler Bereich (die Annahme-Spannen durch die Rechenkette propagiert): "
            f"{sol.range_str(sig)}. Ergebnis {sol.oom_str()}. Als richtig gilt jede Schätzung "
            f"in dieser Größenordnung — der Rechenweg und begründete Annahmen zählen mehr als "
            f"die genaue Zahl."),
        solution_steps=sol.steps,
        watch_outs=_WATCH_OUTS.get(problem_id, []))

    # --- teacher overview ----------------------------------------------------
    overview = TeacherOverview(
        throughline=(
            f"Eine Fermi-Schätzung als Modellierungsaufgabe: die Frage „{problem.question}“ wird "
            f"in schätzbare Größen zerlegt, multiplikativ verknüpft und die Größenordnung geprüft. "
            f"Selbstdifferenzierend — grob mit wenigen Annahmen lösbar, fein mit sauber "
            f"begründeter Zerlegung. Der akzeptable Bereich ist aus den Annahme-Spannen "
            f"gerechnet, nicht geraten."),
        talking_points=[
            "Zuerst gemeinsam sammeln, WELCHE Größen man überhaupt braucht (t1) — erst dann "
            "rechnen (t2).",
            "Gegeben vs. selbst schätzen: " + (", ".join(a.label for a in given)
                                               if given else "hier ist nichts vorgegeben")
            + " ist/sind vorgegeben, alles andere schätzen die Schüler:innen selbst.",
            f"Bewertung über die Größenordnung, nicht die Nachkommastelle. Das Ergebnis "
            f"{sol.oom_str()}. Zwei Gruppen mit unterschiedlichen Annahmen dürfen "
            f"unterschiedliche Zahlen herausbekommen und trotzdem beide richtig liegen.",
        ],
        extensions=[
            "Ergebnisse der Gruppen vergleichen und diskutieren, WARUM sie auseinanderliegen "
            "(welche Annahme macht den größten Unterschied?).",
            "Eine Annahme bewusst an den Rand ihres Bereichs setzen und sehen, wie stark sich "
            "das Endergebnis ändert (Sensitivität = woher die Streuung kommt).",
        ],
        differentiation=(
            "Basis: mit 2–3 groben Annahmen eine Zahl herausbekommen. Vertiefung: feiner "
            "zerlegen, jede Annahme begründen, den plausiblen Bereich selbst abschätzen und die "
            "Größenordnung benennen."),
        timing_notes="Eine Unterrichtsstunde; t2 eignet sich auch als Partner- oder Gruppenarbeit.")

    subtitle = f"Schätzen und Modellieren · {problem.title}"
    meta = WorksheetMeta(
        title=f"Fermi-Werkstatt: {problem.title}", subtitle=subtitle, subject=SUBJECT,
        stufe=stufe, klasse=klasse, kernfrage=problem.question, fassung=res.fassung,
        lehrplan_label=f"{SUBJECT} · {klasse}. Kl. · {problem.kompetenzbereich} (Modellieren)")
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(SUBJECT, stufe), intro=[intro] + infos,
        sections=[Baustein(id="fermi.kern", title=problem.title,
                           teacher_overview=overview, blocks=[t1, t2])],
        anchor_mode="competence")
    return content, res
