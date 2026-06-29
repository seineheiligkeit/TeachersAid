"""Pure-function tests for the SRDP archive downloader (tools/fetch_matura.py).

Network/filesystem are untouched: the HTML fixtures below mirror the real TYPO3 *tx_downloads*
+ Solr result markup (a download anchor carrying collection id + cHash, paired with a following
pretty-title anchor), so the parsing/pairing/classification logic is locked offline."""
from __future__ import annotations

from tools import fetch_matura as f

# Two result items (Math AHS Haupttermin + its english-translation sibling) + a facet link +
# pagination — trimmed but structurally faithful to the live page.
FIXTURE = """
<a href="/downloads?tx_solr%5Bfilter%5D%5B0%5D=year%3A2024%2F25">2024/25</a>
<a href="/downloads?tx_solr%5Bfilter%5D%5B2%5D=subject%3A%2FMathematik%2F">Mathematik</a>
<a href="/downloads/download?tx_downloads_details%5Baction%5D=download&amp;tx_downloads_details%5Bcollection%5D=2456&amp;tx_downloads_details%5Bcontroller%5D=Collection&amp;cHash=f46f02e7608229f368b0f9d59512d3de">Herunterladen</a>
<a href="/downloads/download/Haupttermin%202024/25%20-%20Mathematik%20%28AHS%29">Haupttermin 2024/25 - Mathematik (AHS)</a>
<a href="/downloads/download?tx_downloads_details%5Baction%5D=download&amp;tx_downloads_details%5Bcollection%5D=2457&amp;tx_downloads_details%5Bcontroller%5D=Collection&amp;cHash=6820e8b28e9cab82f76ff0cb9a3257d5">Herunterladen</a>
<a href="/downloads/download/Haupttermin%202024/25%20-%20Mathematik%20%28AHS%29%20%5Benglische%20%C3%9Cbersetzung%5D">Haupttermin 2024/25 - Mathematik (AHS) [englische Übersetzung]</a>
<a href="/downloads?tx_solr%5Bfilter%5D%5B0%5D=year%3A2024%2F25&amp;tx_solr%5Bpage%5D=2">2</a>
<a href="/downloads?tx_solr%5Bfilter%5D%5B0%5D=year%3A2024%2F25&amp;tx_solr%5Bpage%5D=3">3</a>
"""


def test_build_search_url():
    url = f.build_search_url(subject="Mathematik", school_type="AHS", year="2024/25")
    assert "documentType" in url and "Klausuren" in url
    assert "subject" in url and "Mathematik" in url
    assert "schoolType" in url and "AHS" in url
    assert "2024%2F25" in url


def test_download_url_carries_chash():
    url = f.download_url(2456, "abc123")
    assert "collection" in url and "2456" in url and "cHash=abc123" in url


def test_parse_collections_pairs_and_dedupes():
    cols = f.parse_collections(FIXTURE)
    assert len(cols) == 2
    a, b = cols
    assert a["collection"] == 2456 and a["chash"].startswith("f46f")
    assert a["title"] == "Haupttermin 2024/25 - Mathematik (AHS)"
    assert "englische Übersetzung" in b["title"]
    # a duplicate collection id is collapsed
    assert len(f.parse_collections(FIXTURE + FIXTURE)) == 2


def test_classify_title():
    std = f.classify_title("Haupttermin 2024/25 - Mathematik (AHS)")
    assert std == {"termin": "Haupttermin", "year": "2024/25", "variant": "standard"}
    tr = f.classify_title("Haupttermin 2024/25 - Mathematik (AHS) [englische Übersetzung]")
    assert tr["variant"] == "translation"
    acc = f.classify_title("Haupttermin 2024/25 - Mathematik (AHS) für Kandidatinnen "
                           "und Kandidaten mit Blindheit oder Sehbehinderung")
    assert acc["variant"] == "accessibility"


def test_last_page_and_facets():
    assert f.last_page(FIXTURE) == 3
    years = f.parse_facet_values(FIXTURE, "year")
    assert "2024/25" in years
    subjects = f.parse_facet_values(FIXTURE, "subject")
    assert "Mathematik" in subjects


def test_safe_slug():
    assert f.safe_slug("Haupttermin 2024/25 - Mathematik (AHS)") == \
        "Haupttermin_2024_25_Mathematik_AHS"


def test_subject_code_map_matches_operator_codes():
    # the slugs we crawl resolve to codes the operators grounding knows
    for code in f.SUBJECT_CODE.values():
        assert code.isupper() and len(code) == 3
