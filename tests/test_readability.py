"""Roadmap A6 — the Wiener Sachtextformel (Bamberger/Vanecek), advisory-lane only.

Covers: the German syllable-counting heuristic against a fixed word list (including the
hiatus counter-examples the module docstring names by name — Familie/Nation/Museum);
WSTF1 against one hand-computed fixture text; the verify() hook firing on a deliberately
heavy text but staying silent on an easy Klasse-appropriate text (and never a `problem`,
only a `warning` — the lint-lane rule); RichText with a math run (skipped, no crash); and
the <MIN_WORDS_FOR_ESTIMATE guard returning None.
"""

from __future__ import annotations

from datetime import date

from teachersaid.grounding import lehrplan_store as ls
from teachersaid.pipeline.readability import (
    MIN_WORDS_FOR_ESTIMATE,
    _count_syllables,
    estimate_block,
    extract_prose,
    klasse_to_schulstufe,
    wstf,
)
from teachersaid.pipeline.resolve import resolve_kompetenzbereich
from teachersaid.pipeline.verify import verify
from teachersaid.schema.blocks import InfoBlock, TaskBlock
from teachersaid.schema.richtext import InlineRun
from teachersaid.schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

IN = date(2026, 3, 1)
PHY = "Physik"
PHY_KB = "Strahlung und Radioaktivität"

# --- 1) the syllable counter against a fixed German word list -----------------------------
# Includes the tricky hiatus cases named in the module docstring by name (Familie/Nation/
# Museum — the trailing/mid-word -ie, the -io- of Latin -tion endings, and the Latin -eum
# suffix all disambiguated from their diphthong-reading look-alikes), plus the closed-class
# monosyllabic pronouns/adverbs that also end in "ie" (die/sie/wie/nie) which must NOT be
# read as the polysyllabic loanword ending.

_SYLLABLE_CASES = {
    "Haus": 1, "Boot": 1, "Freund": 1, "Quelle": 2, "Feuer": 2, "Bäume": 2,
    "Lehrerin": 3, "Elektrizität": 5,
    "Familie": 4,      # Fa-mi-li-e — trailing -ie is hiatus (loanword ending), not diphthong
    "Chemie": 3,       # Che-mi-e — same trailing -ie hiatus
    "Serie": 3, "Studie": 3,   # more of the same loanword -ie ending
    "Nation": 3,       # Na-ti-on — io is hiatus (German has no "io" diphthong at all)
    "Museum": 3,       # Mu-se-um — the Latin -eum suffix is hiatus, not the eu-diphthong
    "Idee": 2,         # a doubled identical vowel is ONE long nucleus, not hiatus
    "die": 1, "sie": 1, "wie": 1, "nie": 1,   # closed-class: whole word IS the long-i sound
    "Wiese": 2, "Liebe": 2, "Tier": 1,        # mid-word "ie" is the ordinary long-i spelling
    "usw": 1,          # a vowel-less abbreviation still counts as 1 (every word has a nucleus)
}


def test_syllable_counter_fixed_word_list():
    for word, expected in _SYLLABLE_CASES.items():
        got = _count_syllables(word)
        assert got == expected, f"{word}: expected {expected}, got {got}"


# --- 2) WSTF1 against one hand-computed fixture text ---------------------------------------
#
# Fixture (37 words, 6 sentences — by-hand counts below, matching wstf()'s own tokenizer):
#   Die Sonne scheint am Himmel. Vögel singen fröhlich in den Bäumen. Kinder spielen
#   gemeinsam im Garten. Ein Hund läuft schnell über die große Wiese. Die bunten Blumen
#   blühen im Sommer. Am Abend gehen alle müde nach Hause.
#
# Per-word syllable counts (hand-counted): Die1 Sonne2 scheint1 am1 Himmel2 Vögel2 singen2
# fröhlich2 in1 den1 Bäumen2 Kinder2 spielen2 gemeinsam3 im1 Garten2 Ein1 Hund1 läuft1
# schnell1 über2 die1 große2 Wiese2 Die1 bunten2 Blumen2 blühen2 im1 Sommer2 Am1 Abend2
# gehen2 alle2 müde2 nach1 Hause2  -> n=37
#   MS (>=3 syll): {gemeinsam} -> 1 word          -> MS% = 100*1/37 = 2.702703
#   ES (==1 syll): Die,scheint,am,in,den,im,Ein,Hund,läuft,schnell,die,Die,im,Am,nach
#                  -> 15 words                    -> ES% = 100*15/37 = 40.540541
#   IW (>6 letters): scheint(7) fröhlich(8) spielen(7) gemeinsam(9) schnell(7)
#                  -> 5 words                     -> IW% = 100*5/37 = 13.513514
#   SL = n / n_sentences = 37 / 6 = 6.166667
# WSTF1 = 0.1935*2.702703 + 0.1672*6.166667 + 0.1297*13.513514 - 0.0327*40.540541 - 0.875
#       = 0.523... + 1.031... + 1.752... - 1.325... - 0.875 = 1.106067 (rounded)

_FIXTURE_TEXT = (
    "Die Sonne scheint am Himmel. Vögel singen fröhlich in den Bäumen. Kinder spielen "
    "gemeinsam im Garten. Ein Hund läuft schnell über die große Wiese. Die bunten Blumen "
    "blühen im Sommer. Am Abend gehen alle müde nach Hause."
)
_FIXTURE_EXPECTED_WSTF = 1.106067


def test_wstf_hand_computed_fixture():
    got = wstf(_FIXTURE_TEXT)
    assert got is not None
    assert abs(got - _FIXTURE_EXPECTED_WSTF) < 1e-3


# --- 3) verify(): silent on easy Klasse-appropriate text, warns on deliberately heavy text --

def _model():
    return ls.get_subject_model(PHY)


def _content_with_info(text: str, *, klasse: int = 4) -> tuple[WorksheetContent, object]:
    res = resolve_kompetenzbereich(PHY, klasse, PHY_KB, today=IN)
    info = InfoBlock(id="info1", kind="prose", content=text)
    meta = WorksheetMeta(
        title="Lesbarkeits-Test", subject=PHY, stufe="Unterstufe", klasse=klasse,
        fassung=res.fassung, lehrplan_label=f"{PHY} · {klasse}. Klasse",
    )
    content = WorksheetContent(
        meta=meta, subject_model=_model(), intro=[],
        sections=[Baustein(id="s1", title="Info", blocks=[info])],
    )
    return content, res


_EASY_TEXT = (
    "Die Sonne scheint am Himmel. Vögel singen in den Bäumen. Kinder spielen fröhlich "
    "im Garten. Ein Hund läuft schnell über die Wiese. Die Blumen blühen bunt und schön. "
    "Am Abend gehen alle nach Hause."
)

_HEAVY_TEXT = (
    "Die Industrialisierung, die im ausgehenden achtzehnten Jahrhundert in Großbritannien "
    "ihren Ausgang nahm und sich in der Folgezeit über weite Teile Kontinentaleuropas "
    "ausbreitete, veränderte nicht nur die wirtschaftlichen Produktionsverhältnisse, sondern "
    "führte auch zu tiefgreifenden gesellschaftlichen Umwälzungen, die sich insbesondere in "
    "der Urbanisierung, der Entstehung eines Industrieproletariats sowie einer zunehmenden "
    "Differenzierung der sozialen Schichten manifestierten, wobei gleichzeitig neue "
    "politische Bewegungen entstanden, welche die bestehenden Herrschaftsverhältnisse "
    "grundlegend infrage stellten."
)


def test_easy_klasse_text_produces_no_readability_warning():
    content, res = _content_with_info(_EASY_TEXT, klasse=1)
    report = verify(content, res)
    assert report.problems == []
    assert not any("Sachtextformel" in w for w in report.warnings)


def test_heavy_text_triggers_readability_warning_advisory_only():
    content, res = _content_with_info(_HEAVY_TEXT, klasse=1)
    report = verify(content, res)
    # advisory lane: never a problem, always a warning
    assert report.problems == []
    hits = [w for w in report.warnings if "Sachtextformel" in w]
    assert len(hits) == 1
    assert "info1" in hits[0]
    assert "Zielstufe" in hits[0]


def test_verbatim_sources_are_exempt_from_the_advisory():
    # A verbatim selected source (a source_text block, a quoted expression) is
    # deliberately hard — "Text ggf. vereinfachen" is inapplicable BY CONSTRUCTION
    # (the difficulty IS the Quellenarbeit). The estimate stays computable; only the
    # verify warning is suppressed. Locked on the GPB flagship too (wk.q1).
    from teachersaid.pipeline.readability import advisory_exempt
    from teachersaid.schema.provenance import BlockProvenance

    src = InfoBlock(id="q1", kind="source_text", content=_HEAVY_TEXT)
    assert advisory_exempt(src)
    quoted = InfoBlock(
        id="q2", kind="prose", content=_HEAVY_TEXT,
        provenance=BlockProvenance(expression_origin="quoted"),
    )
    assert advisory_exempt(quoted)
    plain = InfoBlock(id="i1", kind="prose", content=_HEAVY_TEXT)
    assert not advisory_exempt(plain)

    content, res = _content_with_info(_HEAVY_TEXT, klasse=1)
    content.sections[0].blocks[0] = src           # same heavy text, but a source_text block
    report = verify(content, res)
    assert not any("Sachtextformel" in w for w in report.warnings)


def test_klasse_to_schulstufe_mapping():
    assert klasse_to_schulstufe(1) == 5    # Unterstufe Klasse 1 -> Schulstufe 5
    assert klasse_to_schulstufe(4) == 8    # Unterstufe Klasse 4 -> Schulstufe 8
    assert klasse_to_schulstufe(5) == 9    # Oberstufe Klasse 5 -> Schulstufe 9
    assert klasse_to_schulstufe(8) == 12   # Oberstufe Klasse 8 -> Schulstufe 12


# --- 4) RichText with math runs: skipped, no crash ------------------------------------------

def test_richtext_math_runs_are_skipped_not_crashed():
    # a math run's LaTeX would corrupt syllable/word counts if included — must be dropped
    runs = [
        InlineRun(text="Die Fläche berechnet sich aus "),
        InlineRun(text="A = \\pi r^2", math=True),
        InlineRun(text=" für einen Kreis mit gegebenem Radius."),
    ]
    prose = extract_prose(runs)
    assert "\\pi" not in prose and "r^2" not in prose
    assert "Fläche" in prose and "Kreis" in prose

    # exercised through a real TaskBlock too (no crash end-to-end)
    task = TaskBlock(
        id="t1", kind="open_response",
        prompt=[
            InlineRun(text="Berechne die Fläche "),
            InlineRun(text="A = \\pi r^2", math=True),
            InlineRun(text=" für r = 3 cm und erkläre den Rechenweg in eigenen Worten "
                            "in mindestens zwei vollständigen Sätzen für die Übung."),
        ],
        response={"mode": "lines", "n": 3}, cognitive_level="apply", est_minutes=10,
    )
    # should not raise, regardless of whether it clears the word-count floor
    estimate_block(task)


def test_richtext_plain_string_still_works():
    assert extract_prose("Hallo Welt") == "Hallo Welt"
    assert extract_prose(None) == ""


# --- 5) the <MIN_WORDS_FOR_ESTIMATE guard ----------------------------------------------------

def test_short_snippet_returns_none():
    short = "Nenne drei Beispiele für Strahlungsarten in der Physik."  # well under the floor
    assert len(short.split()) < MIN_WORDS_FOR_ESTIMATE
    assert wstf(short) is None

    info = InfoBlock(id="i1", kind="prose", content=short)
    assert estimate_block(info) is None


def test_empty_text_returns_none():
    assert wstf("") is None
    assert wstf("   ") is None


def test_estimate_block_reads_content_then_prompt():
    info = InfoBlock(id="i1", kind="prose", content=_EASY_TEXT)
    task = TaskBlock(id="t1", kind="open_response", prompt=_EASY_TEXT,
                     response={"mode": "lines", "n": 2}, cognitive_level="understand",
                     est_minutes=5)
    assert estimate_block(info) is not None
    assert estimate_block(task) is not None
    assert estimate_block(info) == wstf(_EASY_TEXT)
