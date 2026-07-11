"""Wahl-Werkstatt — d'Hondt seat allocation + coalition arithmetic (GPB, Politische Bildung).

The politics twin of the maths/physics parametric engines: the recipes register into the
SHARED ``_RECIPES`` (``pipeline/parametrize.py``), so ``make_variants`` / templates drive them
unchanged. Everything load-bearing is **computed** — seat allocations by the d'Hondt divisor
method, minimal winning coalitions by exhaustive subset search — never authored. Party votes
are either a **real cited slice** (the BMI Nationalratswahl-2024 dataset, ``grounding/data/
bmi_nrw_2024.json``) or **clean sampled numbers**; both are supported (paired recipes:
``mandate_dhondt`` / ``mandate_dhondt_nrw``, ``koalitions_arithmetik`` / ``koalitions_nrw``).

**Honesty (load-bearing, ON the sheet).** The real Nationalrat Mandatsverteilung is a
three-stage Ermittlungsverfahren (Hare-Wahlzahl in the 39 Regional- und 9 Landeswahlkreisen;
d'Hondt only at the third, federal stage) plus a 4-%-Sperrklausel. We teach the **d'Hondt
principle at federal level as a deliberate didactic simplification** — ``HONESTY_NOTE`` states
this on every worksheet. We never present a computed allocation as *the* official result;
where the real 2024 federal totals are used, comparing-and-discussing the difference is the
honest (and pedagogically rich) framing — e.g. running d'Hondt on ALL parties hands KPÖ/BIER
seats they did not get, which is exactly what the 4-%-Hürde prevents.

Anchoring (see ``Documents/anchoring-modes.md``): competence mode, GPB 4. Klasse — the
Wahlsystem is genuine *politische Sachkompetenz* (GPB.US.4.ALL.07: „Demokratie", „Föderalismus",
„Kompetenzverteilung … Bund" als Konzepte anwenden), the compare-and-discuss / coalition
judgment is *politische Urteilskompetenz* (GPB.US.4.ALL.09).
"""

from __future__ import annotations

import random
from fractions import Fraction
from itertools import combinations

from ..schema.parametric import Instance, ParametricTask
from ..schema.blocks import Serves, SolutionStep
from .parametrize import Unsuitable, _recipe

# --- anchoring + real-data constants --------------------------------------------------
GPB_SUBJECT = "Geschichte und politische Bildung"
KLASSE = 4
NRW_DATASET = "bmi_nrw_2024"

# GPB.US.4 competences this class genuinely exercises (verbatim ids from lehrplan/GPB.json)
COMP_SACH = "GPB.US.4.ALL.07"     # fachspezifische Konzepte: „Demokratie", „Föderalismus", …
COMP_URTEIL = "GPB.US.4.ALL.09"   # eigene politische Urteile formulieren und begründen
COMP_WILLE = "GPB.US.4.ALL.10"    # an Prozessen der politischen Willensbildung teilnehmen

HONESTY_NOTE = (
    "So funktioniert die echte Mandatsverteilung: Bei der Nationalratswahl werden die "
    "183 Mandate in einem dreistufigen Ermittlungsverfahren vergeben — zuerst in den "
    "39 Regionalwahlkreisen, dann in den 9 Landeswahlkreisen (jeweils nach der Wahlzahl "
    "bzw. dem Hare-Verfahren) und erst in der dritten Stufe kommt auf Bundesebene das "
    "D'Hondt-Verfahren zum Einsatz. Außerdem gilt eine 4-%-Hürde (oder ein Grundmandat). "
    "In dieser Werkstatt üben wir bewusst vereinfacht das D'Hondt-Prinzip direkt auf "
    "Bundesebene. Unser Ergebnis zeigt, wie das Verhältnisprinzip Stimmen in Sitze "
    "übersetzt — es ist aber nicht das vollständige amtliche Verfahren, und unsere "
    "berechneten Sitze sind nicht die amtliche Mandatsverteilung."
)


# ==============================================================================
# Core algorithms — COMPUTED, correct by construction (tested directly)
# ==============================================================================
def dhondt(votes: dict[str, int], seats: int) -> tuple[dict[str, int], list[tuple[Fraction, str, int]]]:
    """Allocate ``seats`` by the d'Hondt (Höchstzahl / divisor) method.

    Returns ``(alloc, ranked)`` where ``alloc[party]`` is the seat count and ``ranked`` is
    the full list of quotients ``(Fraction(votes, k), party, k)`` sorted descending — the
    first ``seats`` entries are the awarded seats (so ``ranked[n-1]`` is the party winning the
    n-th seat). Ties are broken deterministically by higher total votes, then party order —
    real law uses a Losentscheid; we avoid a lot by construction (a degenerate tie at the cut
    is rejected upstream via `Unsuitable`)."""
    order = {p: i for i, p in enumerate(votes)}
    quotients: list[tuple[Fraction, str, int]] = [
        (Fraction(votes[p], k), p, k) for p in votes for k in range(1, seats + 1)
    ]
    # sort desc by quotient, then higher votes, then earlier party order (stable, deterministic)
    quotients.sort(key=lambda t: (t[0], votes[t[1]], -order[t[1]]), reverse=True)
    alloc = {p: 0 for p in votes}
    for _q, p, _k in quotients[:seats]:
        alloc[p] += 1
    return alloc, quotients


def seat_cut_quotient(votes: dict[str, int], seats: int) -> Fraction:
    """The smallest awarded Höchstzahl (the ``seats``-th largest quotient) — the 'cut'."""
    _, ranked = dhondt(votes, seats)
    return ranked[seats - 1][0]


def votes_needed_for_next_seat(votes: dict[str, int], seats: int, party: str) -> int:
    """Smallest number of ADDITIONAL votes ``party`` would need for one more seat.

    The party's next Höchstzahl uses divisor ``alloc+1``; it must strictly exceed the
    current cut (the smallest awarded quotient). Returns the extra votes required."""
    alloc, ranked = dhondt(votes, seats)
    cut = ranked[seats - 1][0]                       # smallest awarded quotient
    divisor = alloc[party] + 1
    # need votes_new / divisor > cut  →  votes_new > cut * divisor  →  smallest integer above
    threshold = cut * divisor
    needed = int(threshold) + 1                      # strictly greater (floor+1)
    return max(0, needed - votes[party])


def winning_coalitions(seats: dict[str, int], majority: int) -> list[frozenset[str]]:
    """Every party combination whose combined seats reach ``majority``."""
    parties = list(seats)
    out: list[frozenset[str]] = []
    for r in range(1, len(parties) + 1):
        for combo in combinations(parties, r):
            if sum(seats[p] for p in combo) >= majority:
                out.append(frozenset(combo))
    return out


def minimal_winning_coalitions(seats: dict[str, int], majority: int) -> list[frozenset[str]]:
    """Minimal winning coalitions: winning, but losing if ANY single member leaves.

    (Equivalent to 'no proper subset is winning' — see the note in `dhondt`'s module.)"""
    wins = set(winning_coalitions(seats, majority))
    return [c for c in wins if not any((c - {p}) in wins for p in c)]


def _fmt_coalition(c: frozenset[str], seats: dict[str, int], order: list[str]) -> str:
    """'ÖVP + SPÖ (92 Mandate)' — parties in a stable order, with the seat sum."""
    members = [p for p in order if p in c]
    total = sum(seats[p] for p in members)
    return " + ".join(members) + f" ({total} Mandate)"


def _fmt_coalitions(cs: list[frozenset[str]], seats: dict[str, int], order: list[str]) -> str:
    """A deterministically-ordered, human-readable list of coalitions (or a clear 'keine')."""
    if not cs:
        return "keine"
    keyed = sorted(cs, key=lambda c: (len(c), [order.index(p) for p in sorted(c, key=order.index)]))
    return "; ".join(_fmt_coalition(c, seats, order) for c in keyed)


# ==============================================================================
# Sampled recipes — clean invented numbers (the practice Übungsreihe)
# ==============================================================================
_LISTEN = ["Liste A", "Liste B", "Liste C", "Liste D", "Liste E"]


@_recipe("mandate_dhondt")
def _mandate_dhondt(rng: random.Random) -> Instance:
    """Mandatsverteilung nach D'Hondt aus Parteistimmen (saubere Beispielzahlen).

    Frage-Varianten: Sitze einer Partei · welche Partei das n-te Mandat erhält · [Stretch]
    wie viele Stimmen einer Partei zu einem weiteren Mandat gefehlt haben. Die Sitze sind
    per Höchstzahlverfahren COMPUTED; der Rechenweg ist die Höchstzahlentabelle."""
    n = rng.choice([3, 4, 5])
    parties = _LISTEN[:n]
    # distinct vote counts in thousands → clean divisions, unambiguous ordering
    votes = {p: v * 1000 for p, v in zip(parties, rng.sample(range(8, 61), n))}
    seats = rng.choice([7, 8, 9, 10, 11, 12])
    alloc, ranked = dhondt(votes, seats)
    # reject a tie at the cut (would need a Losentscheid — keep school examples clean)
    if ranked[seats - 1][0] == ranked[seats][0]:
        raise Unsuitable
    total_votes = sum(votes.values())
    listing = ", ".join(f"{p}: {votes[p]} Stimmen" for p in parties)
    lead = (f"Bei einer Wahl mit {seats} zu vergebenden Mandaten entfallen auf die Parteien "
            f"folgende Stimmen — {listing} (insgesamt {total_votes} Stimmen).")

    ask = rng.choice(["sitze", "nth", "luecke"])
    steps = _dhondt_steps(votes, seats, alloc, parties)
    if ask == "sitze":
        ziel = rng.choice(parties)
        frage = (f" Wie viele der {seats} Mandate erhält {ziel} nach dem D'Hondt-Verfahren?")
        answer = f"{ziel} erhält {alloc[ziel]} Mandat(e)."
    elif ask == "nth":
        n_seat = rng.randint(1, seats)
        winner = ranked[n_seat - 1][1]
        frage = f" Welche Partei erhält das {n_seat}. Mandat?"
        answer = (f"Das {n_seat}. Mandat geht an {winner} "
                  f"(Höchstzahl {int(ranked[n_seat - 1][0])}).")
    else:  # luecke (stretch): the first party just missing a seat
        ziel = ranked[seats][1]                      # party of the first non-awarded quotient
        need = votes_needed_for_next_seat(votes, seats, ziel)
        frage = (f" {ziel} hat knapp ein weiteres Mandat verpasst. Wie viele zusätzliche "
                 f"Stimmen hätte {ziel} mindestens gebraucht, um noch ein Mandat zu erhalten?")
        answer = (f"{ziel} hätte mindestens {need} zusätzliche Stimmen gebraucht "
                  f"(die kleinste vergebene Höchstzahl liegt bei {int(ranked[seats - 1][0])}).")
        steps = steps + [SolutionStep(
            text=(f"Die kleinste noch vergebene Höchstzahl ist {int(ranked[seats - 1][0])}. "
                  f"{ziel} müsste mit dem Teiler {alloc[ziel] + 1} darüber kommen: "
                  f"benötigte Stimmen ≈ {int(ranked[seats - 1][0]) * (alloc[ziel] + 1)}, "
                  f"also {need} mehr als bisher."))]
    return Instance(params={"aufgabe": lead + frage}, answer=answer, steps=steps)


def _dhondt_steps(votes, seats, alloc, parties) -> list[SolutionStep]:
    """The Höchstzahlen table (Stimmen ÷ 1, ÷ 2, …) + the resulting distribution."""
    show = max(alloc.values()) + 1                   # enough columns to see each party's cut
    rows = [SolutionStep(text="Höchstzahlen bilden (Stimmen ÷ 1, ÷ 2, ÷ 3, …):")]
    for p in parties:
        qs = " · ".join(str(votes[p] // k) for k in range(1, show + 1))
        rows.append(SolutionStep(text=f"{p}: {qs}"))
    rows.append(SolutionStep(
        text=(f"Die {seats} größten Höchstzahlen (über alle Parteien) erhalten je ein Mandat. "
              "Sitzverteilung: " + "; ".join(f"{p} = {alloc[p]}" for p in parties) + ".")))
    return rows


@_recipe("koalitions_arithmetik")
def _koalitions_arithmetik(rng: random.Random) -> Instance:
    """Koalitionsarithmetik: welche Parteikombinationen erreichen die Mehrheit? (Beispielzahlen)

    Aus gesampelten Sitzverteilungen werden die minimalen Gewinnkoalitionen COMPUTED
    (erschöpfende Teilmengensuche). Frage-Varianten: alle minimalen Gewinnkoalitionen ·
    solche, die eine bestimmte Partei enthalten bzw. ausschließen."""
    n = rng.choice([4, 5])
    parties = _LISTEN[:n]
    total = rng.choice([35, 41, 45, 51, 61])         # ungerade Sitzzahl → klare Mehrheit
    seats = _random_seat_split(rng, parties, total)
    majority = total // 2 + 1
    if max(seats.values()) >= majority:              # eine Partei hat schon allein die Mehrheit
        raise Unsuitable
    mwc = minimal_winning_coalitions(seats, majority)
    if not mwc:
        raise Unsuitable
    listing = ", ".join(f"{p}: {seats[p]}" for p in parties)
    lead = (f"In einem Gemeinderat mit {total} Sitzen sind die Mandate so verteilt — "
            f"{listing}. Für eine Mehrheit sind {majority} Sitze nötig.")

    ask = rng.choice(["alle", "enthaelt", "ohne"])
    if ask == "alle":
        frage = " Bestimme alle minimalen Gewinnkoalitionen (Mehrheitsbündnisse ohne überflüssigen Partner)."
        result = mwc
        answer = "Minimale Gewinnkoalitionen: " + _fmt_coalitions(result, seats, parties)
    elif ask == "enthaelt":
        ziel = rng.choice(parties)
        result = [c for c in mwc if ziel in c]
        if not result:
            raise Unsuitable
        frage = f" Welche minimalen Gewinnkoalitionen enthalten {ziel}?"
        answer = f"Minimale Gewinnkoalitionen mit {ziel}: " + _fmt_coalitions(result, seats, parties)
    else:  # ohne
        ziel = rng.choice(parties)
        result = [c for c in mwc if ziel not in c]
        if not result:
            raise Unsuitable
        frage = f" Welche minimalen Gewinnkoalitionen kommen OHNE {ziel} aus?"
        answer = f"Minimale Gewinnkoalitionen ohne {ziel}: " + _fmt_coalitions(result, seats, parties)
    steps = _coalition_steps(result, seats, parties, majority)
    return Instance(params={"aufgabe": lead + frage}, answer=answer, steps=steps)


def _random_seat_split(rng: random.Random, parties: list[str], total: int) -> dict[str, int]:
    """A random split of `total` seats over the parties, each ≥ 1, distinct-ish, descending."""
    n = len(parties)
    # random composition into n positive parts
    cuts = sorted(rng.sample(range(1, total), n - 1))
    parts = [b - a for a, b in zip([0] + cuts, cuts + [total])]
    parts.sort(reverse=True)
    return {p: parts[i] for i, p in enumerate(parties)}


def _coalition_steps(result, seats, parties, majority) -> list[SolutionStep]:
    steps = [SolutionStep(text=f"Mehrheit = mehr als die Hälfte der Sitze, hier {majority} Sitze.")]
    if not result:
        steps.append(SolutionStep(text="Keine passende Koalition erreicht die Mehrheit."))
        return steps
    keyed = sorted(result, key=lambda c: (len(c), [parties.index(p) for p in c]))
    for c in keyed:
        members = [p for p in parties if p in c]
        summe = " + ".join(f"{p} ({seats[p]})" for p in members)
        steps.append(SolutionStep(
            text=f"{summe} = {sum(seats[p] for p in members)} ≥ {majority} → Mehrheit, "
                 "und ohne jeden Partner nicht mehr → minimal."))
    return steps


# ==============================================================================
# Real cited slice — the Nationalratswahl 2024 (BMI dataset, CC BY 4.0)
# ==============================================================================
def _nrw_bund_votes() -> tuple[dict[str, int], dict]:
    """The 5 parties over the 4-%-Hürde with their real Bund votes + the dataset totals."""
    from ..grounding import data_store as ds
    dataset = ds.get_dataset(NRW_DATASET)
    if dataset is None:
        raise Unsuitable                             # dataset not curated → no real variant
    bund = dataset.series["bund"]
    by_party = dict(zip(bund["categories"], bund["values"]))
    nr = dataset.totals["nr_parteien"]
    return {p: by_party[p] for p in nr}, dataset.totals


@_recipe("mandate_dhondt_nrw")
def _mandate_dhondt_nrw(rng: random.Random) -> Instance:
    """Nationalratswahl 2024: 183 Mandate nach D'Hondt aus den echten Bundes-Stimmen der
    fünf Parteien über der 4-%-Hürde (REAL cited slice, ``bmi_nrw_2024``).

    Didaktische Vereinfachung (siehe HONESTY_NOTE): das ist das D'Hondt-Prinzip auf
    Bundesebene, nicht das dreistufige amtliche Verfahren. Für 2024 reproduziert es die
    amtliche Gesamt-Mandatszahl je Partei — das ist ein guter Diskussionspunkt, kein
    Beweis, dass die Vereinfachung das ganze Verfahren ersetzt."""
    votes, totals = _nrw_bund_votes()
    seats = totals["mandate_gesamt"]                 # 183
    alloc, ranked = dhondt(votes, seats)
    cut = int(ranked[seats - 1][0])                  # smallest awarded Höchstzahl
    order = list(votes)
    verteilung = ", ".join(f"{p}: {alloc[p]}" for p in
                           sorted(order, key=lambda p: alloc[p], reverse=True))
    method = SolutionStep(text=(
        "Für jede Partei bildet man die Höchstzahlen (Stimmen ÷ 1, ÷ 2, ÷ 3, …) und vergibt "
        f"die 183 größten. Die kleinste noch vergebene Höchstzahl liegt bei etwa {cut}."))

    ask = rng.choice(["gesamt", "sitze"])
    if ask == "gesamt":
        frage = ("Verteile die 183 Mandate nach dem D'Hondt-Verfahren auf die fünf Parteien, "
                 "die die 4-%-Hürde übersprungen haben (Stimmen: "
                 + ", ".join(f"{p} {votes[p]}" for p in order) + ").")
        answer = "Sitzverteilung: " + verteilung + "."
        steps = [method, SolutionStep(text=(
            "Ergebnis: " + verteilung + ". Für 2024 stimmt diese Gesamtverteilung mit der "
            "amtlichen Mandatszahl je Partei überein (die dritte Ermittlungsstufe IST "
            "D'Hondt auf Bundesebene) — die Aufteilung auf die Wahlkreise bleibt dabei "
            "aber offen."))]
    else:  # sitze für eine Partei
        ziel = rng.choice(order)
        frage = (f"Wie viele der 183 Mandate erhält die {ziel} nach dem (vereinfachten) "
                 f"D'Hondt-Verfahren auf Bundesebene? (Stimmen {ziel}: {votes[ziel]}.)")
        answer = f"{ziel}: {alloc[ziel]} Mandate."
        steps = [method, SolutionStep(text="Sitzverteilung insgesamt: " + verteilung + ".")]
    return Instance(params={"aufgabe": frage}, answer=answer, steps=steps)


@_recipe("koalitions_nrw")
def _koalitions_nrw(rng: random.Random) -> Instance:
    """Koalitionsarithmetik im Nationalrat 2024 aus der AMTLICHEN Mandatsverteilung
    (57/51/41/18/16; Quelle BMI). Minimale Gewinnkoalitionen für die Mehrheit von 92."""
    from ..grounding import data_store as ds
    dataset = ds.get_dataset(NRW_DATASET)
    if dataset is None:
        raise Unsuitable
    seats = dict(dataset.totals["mandate_amtlich"])
    majority = dataset.totals["mehrheit"]            # 92
    order = sorted(seats, key=lambda p: seats[p], reverse=True)
    mwc = minimal_winning_coalitions(seats, majority)
    listing = ", ".join(f"{p}: {seats[p]}" for p in order)
    lead = (f"Der Nationalrat 2024 hat 183 Sitze, verteilt auf — {listing}. Für eine "
            f"Mehrheit sind {majority} Mandate nötig.")

    ask = rng.choice(["alle", "enthaelt", "ohne"])
    if ask == "alle":
        result, frage = mwc, " Bestimme alle minimalen Gewinnkoalitionen."
        answer = "Minimale Gewinnkoalitionen: " + _fmt_coalitions(result, seats, order)
    elif ask == "enthaelt":
        ziel = rng.choice(order)
        result = [c for c in mwc if ziel in c]
        if not result:
            raise Unsuitable
        frage = f" Welche minimalen Gewinnkoalitionen enthalten die {ziel}?"
        answer = f"Mit {ziel}: " + _fmt_coalitions(result, seats, order)
    else:
        ziel = rng.choice(order)
        result = [c for c in mwc if ziel not in c]
        if not result:
            raise Unsuitable
        frage = f" Welche minimalen Gewinnkoalitionen kommen ohne die {ziel} aus?"
        answer = f"Ohne {ziel}: " + _fmt_coalitions(result, seats, order)
    return Instance(params={"aufgabe": lead + frage}, answer=answer,
                    steps=_coalition_steps(result, seats, order, majority))


# ==============================================================================
# Templates — a DEDICATED list (not the generic PARAM_TEMPLATES pool). GPB's
# Kompetenzbereiche are competence strands, so these resolve via `resolve_grade`, and every
# sheet carries the didaktische-Vereinfachung note — so they are driven ONLY by
# `wahl_uebungsblatt` (never the generic `variant_worksheet`/`compose_variants`, which would
# drop the honesty note). Anchored to real GPB competences (lehrplan/GPB.json).
# ==============================================================================
WAHL_TEMPLATES: list[ParametricTask] = [
    ParametricTask(
        id="gpb-wahl-mandate", title="Mandatsverteilung nach D'Hondt",
        subject=GPB_SUBJECT, klasse=KLASSE,
        kompetenzbereich="Historische und politische Sachkompetenz", recipe="mandate_dhondt",
        prompt_template="{aufgabe}",
        context_frame="Bei Verhältniswahlen übersetzt ein Rechenverfahren die Stimmen der "
                      "Parteien in Sitze (Mandate). Das gebräuchlichste ist das D'Hondt-Verfahren.",
        serves=[Serves(competence_id=COMP_SACH, relation="exercises")],
        dimensions=["HSA"], cognitive_level="apply", kind="open_response", est_minutes=8),
    ParametricTask(
        id="gpb-wahl-koalition", title="Koalitionsarithmetik",
        subject=GPB_SUBJECT, klasse=KLASSE,
        kompetenzbereich="Politikbezogene Methodenkompetenz", recipe="koalitions_arithmetik",
        prompt_template="{aufgabe}",
        context_frame="Nach einer Wahl muss sich meist eine Koalition finden, die zusammen "
                      "mehr als die Hälfte der Sitze hält — eine Mehrheit für die Regierung.",
        serves=[Serves(competence_id=COMP_SACH, relation="exercises")],
        dimensions=["PME"], cognitive_level="apply", kind="open_response", est_minutes=8),
    ParametricTask(
        id="gpb-wahl-mandate-nrw", title="Mandatsverteilung: Nationalratswahl 2024",
        subject=GPB_SUBJECT, klasse=KLASSE,
        kompetenzbereich="Historische und politische Sachkompetenz", recipe="mandate_dhondt_nrw",
        prompt_template="{aufgabe}",
        serves=[Serves(competence_id=COMP_SACH, relation="exercises")],
        dimensions=["HSA"], cognitive_level="apply", kind="open_response", est_minutes=10),
    ParametricTask(
        id="gpb-wahl-koalition-nrw", title="Koalitionen im Nationalrat 2024",
        subject=GPB_SUBJECT, klasse=KLASSE,
        kompetenzbereich="Politikbezogene Methodenkompetenz", recipe="koalitions_nrw",
        prompt_template="{aufgabe}",
        serves=[Serves(competence_id=COMP_SACH, relation="exercises")],
        dimensions=["PME"], cognitive_level="apply", kind="open_response", est_minutes=8),
]


def find_wahl_template(template_id: str) -> ParametricTask | None:
    return next((t for t in WAHL_TEMPLATES if t.id == template_id), None)


# ==============================================================================
# Worksheet builders — competence-anchored (GPB 4. Kl.), honesty note ON the sheet
# ==============================================================================
def _honesty_block(extra: str | None = None):
    """The didaktische-Vereinfachung callout (InfoKind callout → prose-provenance exempt)."""
    from ..schema.blocks import InfoBlock
    content = HONESTY_NOTE + (f" {extra}" if extra else "")
    return InfoBlock(id="wahl.hinweis", kind="callout", callout_role="warning", content=content)


def wahl_uebungsblatt(template_id: str, n: int = 6, *, today=None):
    """An Übungsreihe of a sampled Wahl recipe, GPB 4. Kl., with the honesty note ON the sheet.

    Returns (content, resolution). Uses `resolve_grade` (GPB's Kompetenzbereiche are the
    competence strands, so the topic/KB path does not apply — the served competence is the
    genuine anchor). Deterministic; the maths is computed."""
    from ..grounding import lehrplan_store as ls
    from ..pipeline.parametrize import make_variants_with_assets
    from ..pipeline.resolve import resolve_grade
    from ..schema.blocks import InfoBlock
    from ..schema.worksheet import Baustein, TeacherOverview, WorksheetContent, WorksheetMeta

    template = find_wahl_template(template_id)
    if template is None:
        raise KeyError(f"no Wahl template '{template_id}'")
    res = resolve_grade(GPB_SUBJECT, KLASSE, today=today)
    blocks, assets = make_variants_with_assets(template, n, ramp=False)
    title = template.title or template.id
    intro = [_honesty_block()]
    if template.context_frame:  # callout (not prose) → framing, not a sourced GPB fact claim
        intro.append(InfoBlock(id="wahl.rahmen", kind="callout", callout_role="note",
                               content=template.context_frame))
    throughline = (
        f"Übungsreihe zur {title}: {n} Varianten derselben Aufgabenstellung mit eigenen "
        "Zahlensätzen, jede mit vollständigem Rechenweg. Die Sitze sind nach dem "
        "D'Hondt-Prinzip berechnet (nicht das dreistufige amtliche Verfahren — siehe der "
        "Hinweis auf dem Blatt). Einsetzbar zum Automatisieren oder als Gruppe A/B."
    )
    meta = WorksheetMeta(
        title=f"Wahl-Werkstatt: {title}", subtitle=f"Übungsreihe — {n} Varianten",
        subject=GPB_SUBJECT, stufe="Unterstufe", klasse=KLASSE,
        kernfrage=f"Wie werden Stimmen in Mandate übersetzt? ({title})", fassung=res.fassung,
        lehrplan_label="Geschichte und politische Bildung · 4. Kl. · Politische Bildung (Wahlsystem)")
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(GPB_SUBJECT, "Unterstufe"),
        intro=intro,
        sections=[Baustein(id="uebung", title=title,
                           teacher_overview=TeacherOverview(throughline=throughline),
                           blocks=blocks)],
        assets=assets)
    return content, res


def nrw_werkstatt_worksheet(*, today=None):
    """The REAL-data showcase: the Nationalratswahl 2024 (cited BMI data) — read the result,
    compute the d'Hondt Mandatsverteilung, discuss the 4-%-Hürde, and work the coalition
    arithmetic + judgment. Returns (content, resolution).

    Every load-bearing number is computed (d'Hondt / coalitions) or selected from the cited
    dataset; the votes bar chart carries the „Quelle: BMI …" citation via its `data_source`.
    Anchors GPB.US.4.ALL.07 (Sachkompetenz) + GPB.US.4.ALL.09 (Urteilskompetenz)."""
    from ..grounding import data_store as ds
    from ..grounding import lehrplan_store as ls
    from ..pipeline.resolve import resolve_grade
    from ..schema.assets import Asset
    from ..schema.blocks import InfoBlock, Serves, TaskBlock
    from ..schema.datasets import DataRef
    from ..schema.response import LinesResponse
    from ..schema.worksheet import Baustein, TeacherOverview, WorksheetContent, WorksheetMeta

    res = resolve_grade(GPB_SUBJECT, KLASSE, today=today)
    dataset = ds.get_dataset(NRW_DATASET)
    bund = dataset.series["bund"]
    all_votes = dict(zip(bund["categories"], bund["values"]))
    nr = dataset.totals["nr_parteien"]
    votes = {p: all_votes[p] for p in nr}
    seats_total = dataset.totals["mandate_gesamt"]        # 183
    majority = dataset.totals["mehrheit"]                 # 92
    alloc, ranked = dhondt(votes, seats_total)
    cut = int(ranked[seats_total - 1][0])
    order = sorted(votes, key=lambda p: alloc[p], reverse=True)
    verteilung = ", ".join(f"{p} {alloc[p]}" for p in order)
    # the 4-%-Hürde deviation: d'Hondt on ALL parties gives the sub-threshold ones seats
    alloc_all, _ = dhondt(all_votes, seats_total)
    intruders = {p: alloc_all[p] for p in all_votes if p not in nr and alloc_all[p] > 0}
    intruder_txt = ", ".join(f"{p} {n_} Mandate" for p, n_ in intruders.items()) or "keine"
    mwc = minimal_winning_coalitions(dict(dataset.totals["mandate_amtlich"]), majority)
    mwc_txt = _fmt_coalitions(mwc, dict(dataset.totals["mandate_amtlich"]), order)

    # the cited real-data figure (votes bar chart); ground_data fills values + stamps the source
    votes_fig = Asset(
        id="nrw.stimmen", role="figure", generator="matplotlib:bar_chart",
        data_source=DataRef(dataset_id=NRW_DATASET, series="bund_hauptparteien"),
        spec={"title": "Nationalratswahl 2024 — gültige Stimmen (Parteien über 2 %)",
              "unit": "Stimmen"})

    def sach(cid=COMP_SACH):
        return [Serves(competence_id=cid, relation="exercises")]

    t_read = TaskBlock(
        id="nrw.t0", kind="source_analysis",
        prompt=("Sieh dir das Wahlergebnis in der Grafik an. Welche drei Parteien erhielten "
                "die meisten Stimmen (in welcher Reihenfolge)? Welche Parteien schafften es "
                "nicht über die 4-%-Hürde?"),
        asset_refs=["nrw.stimmen"], response=LinesResponse(n=3),
        cognitive_level="understand", dimensions=["PME"], serves=sach(),
        est_minutes=5,
        answer_key=("Stärkste drei: FPÖ, ÖVP, SPÖ. Über der 4-%-Hürde (und damit im "
                    "Nationalrat): FPÖ, ÖVP, SPÖ, NEOS, GRÜNE. KPÖ und BIER blieben knapp "
                    "darunter und erhielten keine Mandate."))
    t_mandate = TaskBlock(
        id="nrw.t1", kind="open_response",
        prompt=("Verteile die 183 Mandate nach dem D'Hondt-Verfahren auf die fünf Parteien "
                "über der 4-%-Hürde. Stimmen: "
                + ", ".join(f"{p} {votes[p]}" for p in nr)
                + ". Bilde die Höchstzahlen und vergib die 183 größten."),
        response=LinesResponse(n=6), cognitive_level="apply", dimensions=["HSA"],
        serves=sach(), est_minutes=12,
        answer_key=f"Sitzverteilung: {verteilung}.",
        solution_steps=[
            SolutionStep(text=("Für jede Partei die Höchstzahlen bilden (Stimmen ÷ 1, ÷ 2, …) "
                               f"und die 183 größten vergeben. Kleinste vergebene Höchstzahl ≈ {cut}.")),
            SolutionStep(text=(f"Ergebnis: {verteilung}. Für 2024 stimmt diese Gesamtverteilung "
                               "mit der amtlichen Mandatszahl je Partei überein — die dritte "
                               "Ermittlungsstufe IST D'Hondt auf Bundesebene. Was unser Modell "
                               "nicht leistet: die Aufteilung der Mandate auf die Wahlkreise.")),
        ],
        watch_outs=["Nicht die berechneten Sitze als amtliche Mandatsverteilung ausgeben — "
                    "das amtliche Verfahren ist dreistufig (siehe Hinweis)."])
    t_huerde = TaskBlock(
        id="nrw.t2", kind="position_argument",
        prompt=("Rechne (oder überlege), was passiert, wenn man das D'Hondt-Verfahren auf "
                "ALLE Parteien anwendet — auch auf KPÖ und BIER, die unter 4 % blieben. "
                "Würden sie Mandate bekommen? Begründe, warum es die 4-%-Hürde gibt und "
                "welche Folgen sie hat."),
        response=LinesResponse(n=5), cognitive_level="evaluate", dimensions=["PUR"],
        serves=[Serves(competence_id=COMP_URTEIL, relation="exercises")], est_minutes=12,
        answer_key=(f"Ohne die 4-%-Hürde erhielten (nach D'Hondt) auch: {intruder_txt} — "
                    "die fünf Parlamentsparteien bekämen entsprechend weniger. Amtlich "
                    "erhielten KPÖ und BIER null Mandate."),
        acceptable_reasoning=(
            "Nachvollziehbare Argumente, z. B.: Die 4-%-Hürde verhindert eine starke "
            "Zersplitterung des Nationalrats in viele Kleinparteien und soll stabile "
            "Mehrheiten/Regierungsbildung erleichtern. Gegenargument: Stimmen für "
            "Parteien unter 4 % bleiben ohne Mandat — das kann als weniger repräsentativ "
            "kritisiert werden."),
        watch_outs=["Beide Seiten würdigen: Regierbarkeit/Stabilität vs. Repräsentation "
                    "kleiner Parteien."])
    t_koalition = TaskBlock(
        id="nrw.t3", kind="open_response",
        prompt=("Der Nationalrat 2024 hat 183 Sitze: FPÖ 57, ÖVP 51, SPÖ 41, NEOS 18, "
                "GRÜNE 16. Für eine Mehrheit braucht man 92 Sitze. Finde alle minimalen "
                "Gewinnkoalitionen (Mehrheitsbündnisse, aus denen kein Partner wegfallen "
                "darf)."),
        response=LinesResponse(n=4), cognitive_level="apply", dimensions=["PME"],
        serves=sach(), est_minutes=8,
        answer_key=f"Minimale Gewinnkoalitionen: {mwc_txt}.",
        solution_steps=_coalition_steps(mwc, dict(dataset.totals["mandate_amtlich"]),
                                        order, majority))
    t_urteil = TaskBlock(
        id="nrw.t4", kind="position_argument",
        prompt=("Tatsächlich bildeten ÖVP, SPÖ und NEOS gemeinsam die Regierung (110 "
                "Mandate). ÖVP und SPÖ hätten mit 92 Mandaten schon eine (knappe) Mehrheit "
                "gehabt. Warum wurde NEOS trotzdem in die Koalition geholt? Nenne mögliche "
                "Gründe."),
        response=LinesResponse(n=4), cognitive_level="evaluate", dimensions=["PUR"],
        serves=[Serves(competence_id=COMP_URTEIL, relation="exercises")], est_minutes=10,
        acceptable_reasoning=(
            "Nachvollziehbare Gründe, z. B.: 92 von 183 ist eine hauchdünne Mehrheit — schon "
            "eine einzige abweichende Stimme könnte sie kippen; eine breitere Basis macht die "
            "Regierung stabiler und beschlussfähiger (auch im Bundesrat / bei "
            "Verfassungsmehrheiten). Eine minimale Gewinnkoalition ist rechnerisch möglich, "
            "aber politisch riskant."),
        watch_outs=["Der Unterschied zwischen rechnerischer (minimaler) und politisch "
                    "tragfähiger Mehrheit ist der Kern der Aufgabe."])

    intro = [_honesty_block(
        "Bei der Nationalratswahl 2024 liefert das vereinfachte Bundes-D'Hondt zufällig "
        "genau die amtliche Mandatszahl je Partei — ein guter Anlass zum Vergleichen, aber "
        "kein Ersatz für das vollständige Verfahren.")]
    section = Baustein(
        id="nrw", title="Nationalratswahl 2024: von den Stimmen zu den Mandaten",
        teacher_overview=TeacherOverview(
            throughline=(
                "Am echten, zitierten Ergebnis der Nationalratswahl 2024 nachvollziehen, wie "
                "das Verhältnisprinzip Stimmen in Mandate übersetzt (D'Hondt, vereinfacht auf "
                "Bundesebene), warum die 4-%-Hürde die Sitzverteilung verändert, und welche "
                "Mehrheiten/Koalitionen möglich sind — mit dem ehrlichen Hinweis, dass das "
                "amtliche Verfahren dreistufig ist."),
            talking_points=[
                "Warum reproduziert unser Bundes-D'Hondt hier die amtlichen Gesamtzahlen — "
                "und was macht das echte Verfahren zusätzlich? (Wahlkreise, Grundmandat)",
                "4-%-Hürde: Regierbarkeit vs. Repräsentation kleiner Parteien.",
                "Rechnerische Mehrheit (92) vs. politisch tragfähige Mehrheit.",
            ]),
        blocks=[t_read, t_mandate, t_huerde, t_koalition, t_urteil])
    meta = WorksheetMeta(
        title="Wahl-Werkstatt: Nationalratswahl 2024 — von Stimmen zu Mandaten",
        subtitle="Echte Daten (Quelle: BMI, CC BY 4.0) · D'Hondt · Koalitionen",
        subject=GPB_SUBJECT, stufe="Unterstufe", klasse=KLASSE,
        kernfrage="Wie werden aus Wählerstimmen Mandate — und welche Koalitionen sind möglich?",
        fassung=res.fassung,
        lehrplan_label="Geschichte und politische Bildung · 4. Kl. · Politische Bildung (Wahlen)")
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(GPB_SUBJECT, "Unterstufe"),
        intro=intro, sections=[section], assets=[votes_fig])
    return content, res


# --- staging (seed) ------------------------------------------------------------------
WAHL_UEBUNG_TEMPLATES = ["gpb-wahl-mandate", "gpb-wahl-koalition"]


def stage_wahl_werkstatt(store, *, n: int = 6, today=None) -> list:
    """Stage the Wahl-Werkstatt worksheets (two sampled Übungsreihen + the NRW showcase) as
    Gate-2 content items (assemble → verify → render), via `orch.stage_worksheet`. Returns the
    created ReviewItems."""
    from .orchestrator import stage_worksheet
    items = []
    for tid in WAHL_UEBUNG_TEMPLATES:
        content, res = wahl_uebungsblatt(tid, n, today=today)
        items.append(stage_worksheet(store, content, res, source="wahl", title=content.meta.title))
    content, res = nrw_werkstatt_worksheet(today=today)
    items.append(stage_worksheet(store, content, res, source="wahl", title=content.meta.title))
    return items
