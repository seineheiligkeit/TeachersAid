"""Preview the Zeitband engine (`pipeline/zeitleiste.py`) — the computed Schulbuch-Zeitleiste, the
successor to the flat `matplotlib:timeline`. Renders the ENGINE's real output (not the design-only
`tools/zeitleiste_mockup.py`) over the two revise-flagged sheets' content.

    python -m tools.zeitband_specimen   # -> runs/specimens/zeitleiste/engine_*.png

  engine_m1.png            M1 Zeitband: Stichwort labels alternating above/below, decade ticks +
                           Zeitpfeil, phase band, Zäsur, focus event      (c0214-shaped, short labels)
  engine_synchronoptik.png M2: two curated semantic lanes (Europa above / Österreich below)
  engine_lupe.png          M3: the detail-window answer to clustered history (c0213-shaped)
  engine_arbeitsobjekt.png M4: the student work-object — year chips + Ereignis-Kärtchen bank
  engine_demotion.png      ►1 in action: the c0213 SENTENCE labels auto-demoted to chips + a legend
"""
from __future__ import annotations

from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline.zeitleiste import zeitband_scene, zeitband_to_png

OUT = RUNS_DIR / "specimens" / "zeitleiste"

# c0214 Europäische Integration — the SME's short Stichwörter (the sentences live in the Darstellung)
_M1 = {
    "title": "Europäische Integration 1951–2020",
    "events": [
        {"at": 1951, "label": "Montanunion (EGKS)"},
        {"at": 1957, "label": "Römische Verträge"},
        {"at": 1989, "label": "Fall des Eisernen Vorhangs", "zaesur": True},
        {"at": 1993, "label": "Vertrag von Maastricht"},
        {"at": 1995, "label": "EU-Beitritt Österreichs", "focus": True},
        {"at": 2002, "label": "Euro-Bargeld"},
        {"at": 2004, "label": "Osterweiterung"},
        {"at": 2009, "label": "Vertrag von Lissabon"},
        {"at": 2020, "label": "Brexit"},
    ],
    "phases": [{"from": 1951, "to": 1957, "label": "EGKS"},
               {"from": 1957, "to": 1993, "label": "EWG / EG"},
               {"from": 1993, "to": 2020, "label": "Europäische Union"}],
    "lupe": "off",
}

# M2 Synchronoptik — the mockup's curated strands (the 1955/1972/1989/1994 Austrian events await SME)
_SYNOP = {
    "title": "Europäische Integration und Österreichs Weg in die EU",
    "strands": ["Europäische Ebene", "Österreich"],
    "events": [
        {"at": 1951, "label": "Montanunion (EGKS)", "strand": "Europäische Ebene"},
        {"at": 1957, "label": "Römische Verträge", "strand": "Europäische Ebene"},
        {"at": 1993, "label": "Maastricht", "strand": "Europäische Ebene"},
        {"at": 2002, "label": "Euro-Bargeld", "strand": "Europäische Ebene"},
        {"at": 2009, "label": "Vertrag von Lissabon", "strand": "Europäische Ebene"},
        {"at": 1955, "label": "Staatsvertrag", "strand": "Österreich"},
        {"at": 1972, "label": "Freihandelsabkommen", "strand": "Österreich"},
        {"at": 1989, "label": "Beitrittsansuchen", "strand": "Österreich"},
        {"at": 1995, "label": "EU-Beitritt", "strand": "Österreich", "focus": True},
    ],
    "lupe": "off",
}

# c0213 Kolonialismus — the real SENTENCE labels (all > 32 chars → the demotion path), + spans
_C0213 = {
    "title": "Kolonialismus und Imperialismus – Stationen 1494–1919",
    "events": [
        {"at": 1494, "label": "Vertrag von Tordesillas: Aufteilung der überseeischen Welt "
                              "zwischen Spanien und Portugal"},
        {"at": 1602, "label": "Gründung der Niederländischen Ostindien-Kompanie (VOC)"},
        {"at": 1834, "label": "Abschaffung der Sklaverei im Britischen Empire"},
        {"at": 1857, "label": "Aufstand gegen die britische Herrschaft in Indien"},
        {"at": 1884, "to": 1885,
         "label": "Berliner Konferenz: Regeln für die Aufteilung Afrikas"},
        {"at": 1904, "to": 1908, "focus": True,
         "label": "Kolonialkrieg gegen Herero und Nama in Deutsch-Südwestafrika"},
        {"at": 1919, "label": "Neuverteilung der Kolonien als Völkerbundmandate nach dem "
                              "Ersten Weltkrieg"},
    ],
}


def render(out: Path | None = None) -> Path:
    out = out or OUT
    out.mkdir(parents=True, exist_ok=True)
    zeitband_to_png(zeitband_scene(_M1), out / "engine_m1.png")
    zeitband_to_png(zeitband_scene(_SYNOP), out / "engine_synchronoptik.png")
    zeitband_to_png(zeitband_scene({**_C0213, "lupe": "auto"}), out / "engine_lupe.png")
    zeitband_to_png(zeitband_scene({**_M1, "variant": "arbeitsobjekt"}),
                    out / "engine_arbeitsobjekt.png")
    zeitband_to_png(zeitband_scene({**_C0213, "lupe": "off"}), out / "engine_demotion.png")
    return out


if __name__ == "__main__":
    print(render())
