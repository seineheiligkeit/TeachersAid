"""Deterministic SRDP Matura exam extractor (tools/extract_matura.py).

Tests the pure string parsers on inline fixtures taken verbatim from the 2025 AHS Math
exam (the PDFs themselves are external/large, not committed)."""
from __future__ import annotations

from tools import extract_matura as ex
from teachersaid.grounding import operators as ops


def test_parse_filename():
    m = ex.parse_filename("bd9a232d-KL25_PT1_AHS_MAT_00_DE_AU.pdf")
    assert (m["year"], m["termin"], m["schulform"], m["subject"]) == \
        (2025, "Haupttermin", "AHS", "MAT")
    assert m["variant"] == "00" and m["language"] == "DE" and m["kind"] == "aufgaben"
    assert m["file_teil"] is None and m["pruefungsteil"] == 1
    assert ex.parse_filename("KL25_PT1_AHS_MAT_00_DE_LO.pdf")["kind"] == "loesungen"
    # early split-booklet naming: Teil 1/2 in separate files, language CC
    e = ex.parse_filename("KL14_PT1_AHS_MAT_T2_CC_LO.pdf")
    assert e["year"] == 2014 and e["variant"] == "T2" and e["file_teil"] == 2
    assert e["language"] == "CC" and e["kind"] == "loesungen"
    assert ex.parse_filename("not-an-exam.pdf") is None


def test_au_pointmarker_variants():
    # 2025 writes "[0 / 1 P.]", 2020 writes "[0 / ½ / 1 Punkt]" — both must parse
    half = ex.parse_au_task(1, "T\nAufgabenstellung:\nKreuzen Sie an. [0 / ½ / 1 Punkt]")
    assert half["half_points"] is True
    full = ex.parse_au_task(1, "T\nAufgabenstellung:\nGeben Sie an. [0 / 1 P.]")
    assert full["half_points"] is False


def test_merge_unifies_operator_year_stably():
    """Older Lösungshefte phrase the point-key descriptively (no nominalised operator);
    the unified operator falls back to the year-stable AU imperative."""
    au = {"meta": {}, "tasks": [{"nr": 1, "teil": 1, "best_of": False, "title": "T",
          "context": "", "instruction": "Kreuzen Sie an.", "operator": "ankreuzen",
          "answer_format": None, "half_points": False}]}
    lo = {"meta": {"kind": "loesungen"}, "beurteilungsschluessel": [], "total_points": None,
          "tasks": [{"nr": 1, "teil": 1, "best_of": False, "title": "T", "operator": None,
                     "operators": [], "point_keys": [], "n_subparts": 0,
                     "grundkompetenz": None, "half_points": False}]}
    t = ex.merge(au, lo)["tasks"][0]
    assert t["operator"] == "ankreuzen" and t["operator_au"] == "ankreuzen"
    assert t["operator_lo"] is None


def test_split_tasks_handles_teil2_headers():
    text = (
        "8. Mai 2025 / AHS / Mathematik\nS. 3/36\n"
        "Aufgabe 1\nTerme\nsome body\n"
        "Aufgabe 25 (Teil 2)\nGarten\nbody\n"
        "Aufgabe 26 (Teil 2, Best-of-Wertung)\nWirkstoffe\nbody\n"
    )
    blocks = ex.split_tasks(text)
    assert set(blocks) == {1, 25, 26}
    assert "Terme" in blocks[1]["block"]
    assert blocks[25]["header"] == "(Teil 2)"
    assert ex.teil_info(blocks[1]["header"]) == {"teil": 1, "best_of": False}
    assert ex.teil_info(blocks[25]["header"]) == {"teil": 2, "best_of": False}
    assert ex.teil_info(blocks[26]["header"]) == {"teil": 2, "best_of": True}


def test_strip_headers_removes_runheads():
    txt = "8. Mai 2025 / AHS / Mathematik\nS. 4/32\nAufgabe 2\nDefinitionsmenge"
    out = ex.strip_headers(txt)
    assert "AHS / Mathematik" not in out and "S. 4/32" not in out
    assert "Aufgabe 2" in out and "Definitionsmenge" in out


def test_operator_from_pointkey():
    cases = {
        "Ein Punkt für das richtige Ankreuzen.": "ankreuzen",
        "Ein Punkt für das Angeben der richtigen Koordinaten von A.": "angeben",
        "Ein Punkt für vier richtige Zuordnungen, ein halber Punkt für zwei oder drei "
        "richtige Zuordnungen.": "zuordnen",
        "Ein Punkt für das richtige Ermitteln von r.": "ermitteln",
        "Ein halber Punkt für das Ankreuzen des ersten richtigen Satzteils": "ankreuzen",
        "Ein Punkt für das richtige Aufstellen der Formel.": "aufstellen",
    }
    for sent, op in cases.items():
        assert ex.operator_from_pointkey(sent) == op


def test_parse_lo_task_gk_and_halfpoints():
    block = ("Argument einer quadratischen Funktion\nf(0) = 1\n"
             "Ein Punkt für das richtige Ermitteln von r.\nGrundkompetenz: FA 4.3")
    t = ex.parse_lo_task(10, block, header="")
    assert t["title"] == "Argument einer quadratischen Funktion"
    assert t["operator"] == "ermitteln" and t["grundkompetenz"] == "FA 4.3"
    assert t["teil"] == 1 and t["half_points"] is False

    half = ("Allgemeine Sinusfunktionen\n"
            "Ein Punkt für vier richtige Zuordnungen, ein halber Punkt für zwei oder drei "
            "richtige Zuordnungen.")
    th = ex.parse_lo_task(12, half, header="")
    assert th["operator"] == "zuordnen" and th["half_points"] is True


def test_parse_au_task_format_and_operator():
    block = ("Terme\nFür die von null verschiedenen ganzen Zahlen a und b gilt: a = -4 b\n"
             "Aufgabenstellung:\n"
             "Kreuzen Sie die beiden Terme an, die in jedem Fall eine natürliche Zahl "
             "ergeben. [2 aus 5]\na - b\n[0 / 1 P.]")
    t = ex.parse_au_task(1, block, header="")
    assert t["title"] == "Terme"
    assert t["answer_format"] == "2 aus 5"
    assert t["operator"] == "ankreuzen"
    assert t["half_points"] is False
    assert "Für die von null" in t["context"] and "Aufgabenstellung" not in t["context"]


def test_operator_from_instruction():
    assert ex.operator_from_instruction("Kreuzen Sie den Term an.") == "ankreuzen"
    assert ex.operator_from_instruction("Ermitteln Sie den Wert von r.") == "ermitteln"
    assert ex.operator_from_instruction("Ordnen Sie die vier Graphen zu.") == "zuordnen"
    assert ex.operator_from_instruction("Es gibt hier kein Verb.") is None


def test_parse_beurteilungsschluessel():
    text = ("32 – 36 Punkte\nSehr gut\n27 – 31,5 Punkte\nGut\n22 – 26,5 Punkte\n"
            "Befriedigend \n17 – 21,5 Punkte\nGenügend \n0 – 16,5 Punkte\nNicht genügend")
    rows = ex.parse_beurteilungsschluessel(text)
    assert len(rows) == 5
    assert rows[0] == {"grade": "Sehr gut", "min": 32.0, "max": 36.0}
    assert rows[3]["grade"] == "Genügend" and rows[3]["max"] == 21.5


def test_extracted_operators_are_known_srdp_math_operators():
    """Every operator the extractor can name is a recognised SRDP Mathematik operator —
    ties the corpus to the operators grounding (operators.MATHEMATIK)."""
    catalog_text = " ".join(o.forms.lower() for o in ops.MATHEMATIK)
    for canonical in set(ex._OP_NOMINAL.values()):
        assert canonical.lower() in catalog_text, \
            f"{canonical!r} not in the MAT operator catalog"
