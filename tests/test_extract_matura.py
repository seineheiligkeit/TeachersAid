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


# --- subject dispatch + the non-math parsers (Phase 2 of the archive build) -----------
def test_filename_language_cefr_slot():
    """The language slot is a CEFR code for FS/Latein (B1/B2/A2), not just letters."""
    lat = ex.parse_filename("KL25_PT1_AHS_LAT_SR_B1_AU.pdf")
    assert lat["subject"] == "LAT" and lat["language"] == "B1"
    eng = ex.parse_filename("KL25_PT3_HTL_ENG_SR_B2_AU.pdf")
    assert eng["subject"] == "ENG" and eng["language"] == "B2"
    deu = ex.parse_filename("KL25_PT1_ALL_DEU_SR_CC_LO.pdf")
    assert deu["subject"] == "DEU" and deu["kind"] == "loesungen"


def test_subject_kind_dispatch():
    assert ex.subject_kind("MAT") == "math" and ex.subject_kind("AMT") == "math"
    assert ex.subject_kind("DEU") == "deutsch"
    assert ex.subject_kind("LAT") == "latein" and ex.subject_kind("GRI") == "latein"
    assert ex.subject_kind("ENG") == "language" and ex.subject_kind("SPA") == "language"


def test_operator_de_maps_to_catalog_forms():
    """The Deutsch operator detector returns canonical forms present in operators.DEUTSCH."""
    forms = {f.strip().lower() for o in ops.DEUTSCH for f in o.forms.split("/")}
    cases = {
        "Geben Sie kurz den Inhalt wieder.": "wiedergeben",
        "Analysieren Sie die sprachliche Gestaltung.": "analysieren / untersuchen",
        "Deuten Sie die Gedichte vergleichend.": "deuten / interpretieren",
        "Nehmen Sie zu der These Stellung.": "kommentieren / Stellung nehmen",
        "Bewerten Sie die Position des Autors.": "bewerten",
    }
    for instr, want in cases.items():
        got = ex.operator_de(instr)
        assert got == want
        # every canonical form the detector emits decomposes into catalog forms
        assert all(p.strip().lower() in forms for p in got.split("/"))


DEU_LO_FIXTURE = (
    "Thema 1 / Aufgabe 1\n"
    "Textsorte:\nTextinterpretation\n"
    "Wortanzahl:\n540 – 660\n"
    "Situation: \nkein abweichender Kontext\n"
    "Schreibhandlungen, \ndie im Sinne der \nTextsorte erfüllt \nwerden sollen:\n"
    "Argumentation, Deskription, Explikation\n"
    "Möglichkeiten zu Arbeitsauftrag 1:  \nGeben Sie kurz den Inhalt wieder.\n"
    "Möglichkeiten zu Arbeitsauftrag 2:  \nAnalysieren Sie die Gestaltung.\n"
    "Thema 1 / Aufgabe 2\n"
    "Textsorte:\nKommentar\nWortanzahl:\n270 – 330\n"
    "Schreibhandlungen, \nwerden sollen:\nArgumentation, Evaluation\n"
    "Möglichkeiten zu Arbeitsauftrag 1:  \nNehmen Sie Stellung.\n"
)


def test_parse_deutsch():
    d = ex.parse_deutsch(DEU_LO_FIXTURE)
    a = d["aufgaben"]
    assert len(a) == 2
    assert a[0]["textsorte"] == "Textinterpretation" and a[0]["wortanzahl"] == "540 – 660"
    assert "Argumentation" in a[0]["schreibhandlungen"]
    ops0 = [w["operator"] for w in a[0]["arbeitsauftraege"]]
    assert ops0 == ["wiedergeben", "analysieren / untersuchen"]
    assert a[1]["textsorte"] == "Kommentar"
    assert a[1]["arbeitsauftraege"][0]["operator"] == "kommentieren / Stellung nehmen"


LAT_AU_FIXTURE = (
    "Hinweise: ein Übersetzungstext (ÜT) sowie ein Interpretationstext (IT).\n"
    "A. Übersetzungstext\n"
    "Übersetzen Sie den folgenden lateinischen Text. (36 Punkte)\n"
    "Cum in suo ille fatigatus quiesceret pomario ...\n"
    "(Petrus Alphonsi, Disciplina Clericalis )\n"
    "B. Interpretationstext\n"
    "Lesen Sie und lösen Sie die Arbeitsaufgaben. (24 Punkte)\n"
    "Veste tegor vili ...\n"
    "(Ovid, Heroides )\n"
    "Arbeitsaufgaben zum Interpretationstext\n"
    "1.\t\nTrennen Sie die folgenden Wörter in ihre Bestandteile. (3 Punkte)\n"
    "2.\t\nKreuzen Sie die passende Übersetzung an. (2 Punkte)\n"
    "3.\t\nVergleichen Sie die beiden Texte. (3 Punkte)\n"
)


def test_parse_latein():
    d = ex.parse_latein(LAT_AU_FIXTURE)
    assert d["uebersetzung"] == {"operator": "übersetzen", "points": 36,
                                 "source": "Petrus Alphonsi, Disciplina Clericalis"}
    assert d["interpretation"]["points"] == 24
    assert d["interpretation"]["source"] == "Ovid, Heroides"
    aa = d["arbeitsaufgaben"]
    assert [a["nr"] for a in aa] == [1, 2, 3]
    assert aa[0]["operator"] == "trennen (Wortbildung)" and aa[0]["points"] == 3
    assert aa[1]["operator"] == "ankreuzen" and aa[2]["operator"] == "vergleichen"


def test_operator_lat_strips_control_glyphs():
    # PyMuPDF leaves \x07 bullet glyphs at the head of an instruction
    assert ex.operator_lat("\x07Trennen Sie die Wörter") == "trennen (Wortbildung)"


def test_parse_language_skill_cefr_tasks():
    text = ("HTL\n14. Jänner 2026\nEnglisch\nSchreiben B2\n"
            "Dieses Aufgabenheft enthält drei Aufgaben. Bitte bearbeiten Sie alle drei.\n")
    lang = ex.parse_language({"subject": "ENG"}, text)
    assert lang["skill"] == "Schreiben" and lang["cefr"] == "B2"
    assert lang["n_tasks"] == 3
