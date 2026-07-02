"""Track 1 #2 — the numeric-claims lint: prose numbers in a task next to a SOURCED
data figure must be derivable from the cited dataset slice (at claimed precision)."""

from __future__ import annotations

from teachersaid.grounding import lehrplan_store as ls
from teachersaid.grounding.data_store import series_to_spec
from teachersaid.pipeline.number_lint import _claims, lint_content
from teachersaid.schema.assets import Asset
from teachersaid.schema.blocks import TaskBlock
from teachersaid.schema.datasets import DataRef
from teachersaid.schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

REF = DataRef(dataset_id="statistik_austria_bevstand_2024", series="pyramide_5j")
GWB = "Geographie und wirtschaftliche Bildung"


def _de(n: float) -> str:
    """German thousands format: 9158750 → '9.158.750'."""
    return f"{n:,.0f}".replace(",", ".")


def _content(answer: str) -> WorksheetContent:
    model = ls.get_subject_model(GWB)
    assert model is not None
    asset = Asset(id="abb1", role="figure", generator="matplotlib:population_pyramid",
                  spec={"title": "Bevölkerungspyramide Österreich"}, data_source=REF)
    task = TaskBlock(
        id="t1", kind="open_response", prompt="Lies die Bevölkerungspyramide (Abb. 1) ab.",
        response={"mode": "lines", "n": 3}, cognitive_level="understand",
        est_minutes=5, asset_refs=["abb1"], answer_key=answer,
    )
    meta = WorksheetMeta(
        title="Pyramide lesen", subject=GWB, stufe="Unterstufe", klasse=3,
        kernfrage="Was zeigt die Pyramide?", fassung=ls.get_fassung(),
        lehrplan_label="GWB · 3. Klasse",
    )
    return WorksheetContent(meta=meta, subject_model=model, intro=[],
                            sections=[Baustein(id="s1", title="Aufgaben", blocks=[task])],
                            assets=[asset])


def _slice():
    spec, notes = series_to_spec(REF, "matplotlib:population_pyramid")
    assert spec and not notes, notes
    return spec


def test_derivable_numbers_pass():
    spec = _slice()
    m, f = sum(spec["male"]), sum(spec["female"])
    diff_rounded = round(abs(f - m), -3)          # "um die X mehr Frauen", gerundet
    answer = (f"Österreich hat {_de(m + f)} Einwohner:innen, davon {_de(f)} Frauen und "
              f"{_de(m)} Männer — also rund {_de(diff_rounded)} mehr Frauen.")
    problems, warnings = lint_content(_content(answer))
    assert problems == [] and warnings == [], warnings


def test_percent_share_passes():
    spec = _slice()
    combined = [a + b for a, b in zip(spec["male"], spec["female"])]
    share = 100 * sum(combined[:3]) / sum(combined)   # 0–14 = die ersten drei 5er-Bänder
    answer = ("Die 0- bis 14-Jährigen stellen " + f"{share:.1f}".replace(".", ",")
              + " % der Bevölkerung.")
    _, warnings = lint_content(_content(answer))
    assert warnings == [], warnings


def test_invented_number_is_flagged():
    _, warnings = lint_content(_content("In Österreich leben 4.999.999 Frauen."))
    assert len(warnings) == 1 and "4.999.999" in warnings[0], warnings


def test_small_counts_years_and_dates_ignored():
    answer = ("Nenne 3 Gruppen. Die Daten sind vom 1.1.2024; seit 1960 sinkt die "
              "Geburtenrate, und in 30 Jahren wird sich das Verhältnis verschieben.")
    _, warnings = lint_content(_content(answer))
    assert warnings == [], warnings


def test_unsourced_or_illustrative_figure_not_checked():
    c = _content("Hier stehen 123.456 erfundene Personen.")
    c.assets[0].data_source = None
    c.assets[0].illustrative = True
    _, warnings = lint_content(c)
    assert warnings == []


def test_german_number_parsing():
    got = {(round(v, 3), pct) for v, pct, _sig, _raw in
           _claims("9.158.750 Menschen · 21,2 % · 3 Mio. Fahrgäste · Stand 1.1.2024")}
    assert (9158750.0, False) in got
    assert (21.2, True) in got
    assert (3_000_000.0, False) in got
    # the date is stripped whole — it must NOT tokenize as 1.202 (the regression)
    vals = {v for v, _p in got}
    assert 1202.0 not in vals and 2024.0 not in vals


def test_space_grouped_thousands_parse_as_one_token():
    # regular space and no-break space as German thousands separators
    got = {v for v, _p, _s, _r in _claims("1 703 809 Personen und 104 080 US-Dollar")}
    assert 1_703_809.0 in got and 104_080.0 in got
    assert 703.0 not in got and 80.0 not in got


def test_mean_and_median_derivations_pass():
    spec = _slice()
    vals = sorted(spec["male"])
    mean = sum(vals) / len(vals)
    med = (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2 if len(vals) % 2 == 0 \
        else vals[len(vals) // 2]
    answer = (f"Der Mittelwert liegt bei rund {_de(round(mean, -2))}, der Median bei "
              + f"{med:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
    _, warnings = lint_content(_content(answer))
    assert warnings == [], warnings
