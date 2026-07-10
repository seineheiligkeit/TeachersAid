"""Specimen sheet for the DATA-CHART recipe family after the figstyle port (roadmap A1).

Renders every statistical/data recipe in `pipeline/assets.py` with realistic Austrian-classroom
demo data, through the real `build_asset` seam (so what you see is exactly what a worksheet gets).
Each recipe lands as its own PNG; LOOK at them and tune the recipe (spacing, ticks, label size)
until they read like a printed Austrian schoolbook.

    python -m tools.charts_specimen [OUTDIR]     # default: runs/specimens/charts
"""
from __future__ import annotations

import sys
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline.assets import build_asset
from teachersaid.schema.assets import Asset

# recipe id -> a realistic spec (Austrian classroom data)
CASES: dict[str, dict] = {
    "bar_chart": {
        "categories": ["Wien", "Niederösterreich", "Oberösterreich", "Steiermark", "Tirol"],
        "values": [2_028_399, 1_734_546, 1_555_296, 1_265_198, 774_753],
        "ylabel": "Einwohner:innen", "title": "Bevölkerung nach Bundesland (2024)"},
    "bar_chart_small": {
        "categories": ["Deutsch", "Englisch", "Latein", "Französisch"],
        "values": [42.5, 30.0, 12.2, 15.3], "ylabel": "Anteil in %",
        "title": "Erste lebende Fremdsprache"},
    "line": {
        "series": [
            {"label": "Wien", "x": list(range(2015, 2025)),
             "y": [1_800_000 + i * 30_000 for i in range(10)]},
            {"label": "Graz", "x": list(range(2015, 2025)),
             "y": [270_000 + i * 4_000 for i in range(10)]},
            {"label": "Linz", "x": list(range(2015, 2025)),
             "y": [200_000 + i * 2_500 for i in range(10)]}],
        "xlabel": "Jahr", "ylabel": "Einwohner:innen", "title": "Stadtbevölkerung im Trend"},
    "line_long": {
        "categories": [str(y) for y in range(1960, 2025)],
        "values": [7_047_539 + i * 33_000 for i in range(65)],
        "xlabel": "Jahr", "ylabel": "Personen", "title": "Bevölkerung Österreichs 1960–2024"},
    "scatter": {
        "points": [[52, 3.1], [61, 3.8], [70, 4.9], [55, 3.4], [83, 6.2], [66, 4.4],
                   [74, 5.6], [90, 7.0], [48, 2.8], [78, 5.9]], "fit": True,
        "xlabel": "Lernzeit (min)", "ylabel": "Punkte", "title": "Lernzeit und Testergebnis"},
    "histogram": {
        "values": [3, 4, 4, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 8, 8, 9, 4, 5, 6, 7, 6, 5, 6, 7, 8],
        "xlabel": "Note (Punkte)", "title": "Verteilung der Klassenarbeit"},
    "boxplot": {
        "groups": [
            {"label": "Klasse A", "summary": {"min": 4, "q1": 9, "median": 13, "q3": 17, "max": 22}},
            {"label": "Klasse B", "values": [6, 8, 9, 11, 12, 12, 14, 16, 19]}],
        "xlabel": "Punkte", "title": "Zwei Klassen im Vergleich"},
    "number_line": {
        "min": 0, "max": 14, "step": 2,
        "marks": [{"at": 2, "label": "Zitronensaft"}, {"at": 3, "label": "Essig"},
                  {"at": 6.7, "label": "Milch"}, {"at": 7.4, "label": "Blut"},
                  {"at": 8.3, "label": "Backpulver-Lösung"}, {"at": 11.5, "label": "Ammoniak"}]},
    "population_pyramid": {
        "age_groups": ["0–14", "15–29", "30–44", "45–59", "60–74", "75+"],
        "male": [325_000, 380_000, 410_000, 445_000, 320_000, 150_000],
        "female": [308_000, 366_000, 402_000, 448_000, 350_000, 235_000],
        "title": "Altersstruktur Österreich (schematisch)"},
    "timeline": {
        "events": [{"at": 1918, "label": "Ausrufung der Republik"},
                   {"at": 1938, "label": "Anschluss an das Deutsche Reich"},
                   {"at": 1945, "label": "Kriegsende, Zweite Republik"},
                   {"at": 1955, "label": "Staatsvertrag und Neutralität"},
                   {"at": 1995, "label": "Beitritt zur Europäischen Union"}],
        "title": "Österreich im 20. Jahrhundert"},
    "climate_diagram": {
        "temp": [-1, 1, 5, 10, 15, 18, 20, 19, 15, 9, 4, 0],
        "precip": [40, 38, 50, 55, 70, 90, 85, 80, 60, 50, 55, 45],
        "title": "Klimadiagramm Wien"},
}


# demo key -> real generator id (a couple of keys are extra variants of one recipe)
_GEN = {"line_long": "matplotlib:line", "bar_chart_small": "matplotlib:bar_chart"}


def render(outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, spec in CASES.items():
        gen = _GEN.get(name, "matplotlib:" + name)
        a = Asset(id=name, role="figure", generator=gen, spec=spec)
        paths.append(build_asset(a, outdir=outdir))
    return paths


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNS_DIR / "specimens" / "charts"
    for p in render(out):
        print(p)
