"""Offline tests for the Wikisource verbatim-text fetch tool (tools/fetch_wikisource.py).

Network is never touched: the HTML fixture mirrors real rendered MediaWiki markup
(a de.wikisource poem with a Textdaten box, a PageNumber scan-marker, a footnote ref,
an edit-section link, an NBSP and old spaced punctuation, plus a la.wikisource inline
verse-number gutter). The deterministic HTML->text walker, the selection/reflow helpers,
the metadata scrape, the permalink, and the record + rights gate are locked here; the
MediaWiki API call is exercised via a monkeypatched urlopen (no real request)."""
from __future__ import annotations

import argparse
import json

import pytest

from tools import fetch_wikisource as fw

NBSP = " "

# A structurally faithful slice of rendered de.wikisource HTML: a Textdaten metadata box
# (skipped as body, but scraped for author/title/year/edition), then the poem with a
# PageNumber span, a footnote <sup>, an editsection link, an NBSP (&#160;), spaced
# punctuation, and a stanza gap (double <br/>).
POEM_HTML = """
<div class="mw-parser-output">
<table id="Textdaten"><tbody>
<tr><td>Autor:</td><td><span id="ws-author">Theodor Fontane</span></td></tr>
<tr><td>Titel:</td><td><span id="ws-title">Herr von Ribbeck</span></td></tr>
<tr><td>Entstehungsdatum:</td><td><span id="ws-year">1889</span></td></tr>
<tr><td>aus:</td><td>Gedichte, S. 318&#8211;319</td></tr>
</tbody></table>
<div class="mw-heading mw-heading2"><h2>Text</h2><span class="mw-editsection">[Bearbeiten]</span></div>
<div class="poem">
<p><span class="PageNumber" id="Seite_318">[318]</span>Herr von Ribbeck auf Ribbeck im Havelland<br/>
Ein Birnbaum in seinem&#160;Garten stand<sup class="reference">[1]</sup><br/><br/>
Und kam die goldene Herbsteszeit ,<br/>
Und die Birnen leuchteten weit und breit .<br/></p>
</div>
</div>
"""

# a la.wikisource verse line carrying the inline number gutter "3  <text>"
VERSE_GUTTER_HTML = '<div class="poem"><p>3  Longeque inferior agnus.<br/></p></div>'


# --- the deterministic HTML -> text walker -----------------------------------
def test_html_to_text_strips_apparatus_keeps_verbatim():
    txt = fw.html_to_text(POEM_HTML)
    lines = txt.split("\n")
    assert lines[0] == "Herr von Ribbeck auf Ribbeck im Havelland"
    # PageNumber scan-marker, footnote ref, editsection are dropped (never in body text)
    assert "[318]" not in txt and "[1]" not in txt and "Bearbeiten" not in txt
    # Textdaten metadata is not body text
    assert "Autor:" not in txt and "Theodor Fontane" not in txt
    # NBSP normalised to a plain space (no U+00A0 survives)
    assert NBSP not in txt and "seinem Garten stand" in txt
    # old spaced punctuation tightened
    assert "Herbsteszeit," in txt and "weit und breit." in txt


def test_html_to_text_preserves_one_stanza_gap():
    txt = fw.html_to_text(POEM_HTML)
    # exactly one blank line between the two stanzas (double <br/>), never a run
    assert "\n\n" in txt and "\n\n\n" not in txt
    stanza2 = txt.split("\n\n")[1].split("\n")
    assert stanza2[0].startswith("Und kam die goldene Herbsteszeit")


def test_verse_number_gutter_stripped_by_default_kept_on_flag():
    assert fw.html_to_text(VERSE_GUTTER_HTML) == "Longeque inferior agnus."
    kept = fw.html_to_text(VERSE_GUTTER_HTML, strip_verse_numbers=False)
    assert kept.startswith("3 ") and kept.endswith("Longeque inferior agnus.")


# --- metadata scrape ---------------------------------------------------------
def test_extract_metadata_reads_textdaten_box():
    meta = fw.extract_metadata(POEM_HTML)
    assert meta["author"] == "Theodor Fontane"
    assert meta["title"] == "Herr von Ribbeck"
    assert meta["year"] == "1889"
    assert meta["edition"] and meta["edition"].startswith("Gedichte, S. 318")


# --- selection / reflow (presentational, wording untouched) ------------------
def test_slice_lines_selects_and_validates():
    text = "eins\nzwei\ndrei\nvier"
    assert fw.slice_lines(text, "2-3") == "zwei\ndrei"
    with pytest.raises(ValueError):
        fw.slice_lines(text, "3-99")           # out of range
    with pytest.raises(ValueError):
        fw.slice_lines(text, "bad")            # malformed spec


def test_reflow_clauses_breaks_prose_one_clause_per_line():
    prose = ("Es war einmal ein kleines Maedchen, dem war Vater und Mutter gestorben, "
             "und es war so arm; endlich hatte es gar nichts mehr.")
    out = fw.reflow_clauses(prose).split("\n")
    assert len(out) >= 3
    assert out[0] == "Es war einmal ein kleines Maedchen,"
    # wording is untouched — rejoining the clauses restores the original text
    assert " ".join(out) == prose


def test_zeilen_preview_numbers_only_nonblank_lines():
    # matches rendering's numbered_text convention (blank = stanza gap, unnumbered)
    prev = fw.zeilen_preview("Zeile A\n\nZeile B")
    numbered = [p for p in prev if p.strip()]
    assert numbered[0].strip().startswith("1 ") and numbered[1].strip().startswith("2 ")
    assert prev[1] == ""                       # the gap stays blank/unnumbered


# --- permalink + record + rights gate ----------------------------------------
def test_permalink_shape():
    link = fw.permalink("de", "Der Zauberlehrling (1827)", 3467076)
    assert link.startswith("https://de.wikisource.org/w/index.php?title=")
    assert "Der_Zauberlehrling" in link and "oldid=3467076" in link


def _args(**kw):
    base = dict(author=None, work_title=None, work_year=None, attribution=None,
                death_year=1898, rights="public_domain_pma", lines=None, reflow="none",
                keep_verse_numbers=False)
    base.update(kw)
    return argparse.Namespace(**base)


def test_build_record_shapes_source_ref_and_permalink():
    parse = {"revid": 42, "text": POEM_HTML}
    text = fw.html_to_text(POEM_HTML)
    meta = fw.extract_metadata(POEM_HTML)
    rec = fw.build_record(site="de", page="Herr von Ribbeck", args=_args(),
                          parse=parse, section_heading=None, text=text, page_meta=meta,
                          today="2026-03-01")
    assert rec["revid"] == 42
    assert rec["permalink"].endswith("oldid=42")
    sr = rec["source_ref"]
    assert sr["author"] == "Theodor Fontane"          # from Textdaten when not overridden
    assert sr["author_death_year"] == 1898 and sr["rights_basis"] == "public_domain_pma"
    assert sr["url"] == rec["permalink"]
    assert rec["n_zeilen"] == sum(1 for ln in text.split("\n") if ln.strip())


def test_check_rights_runs_the_real_gate():
    parse = {"revid": 1, "text": POEM_HTML}
    text = fw.html_to_text(POEM_HTML)
    meta = fw.extract_metadata(POEM_HTML)
    clear = fw.build_record(site="de", page="P", args=_args(death_year=1898), parse=parse,
                            section_heading=None, text=text, page_meta=meta)
    ok, reasons = fw.check_rights(clear["source_ref"])
    assert ok and not reasons                         # Fontane d. 1898 -> PD (AT 70 p.m.a.)
    recent = fw.build_record(site="de", page="P", args=_args(death_year=2010), parse=parse,
                             section_heading=None, text=text, page_meta=meta)
    ok2, reasons2 = fw.check_rights(recent["source_ref"])
    assert not ok2 and reasons2                       # d. 2010 -> not yet 70 p.m.a.


# --- the MediaWiki API wrapper (monkeypatched — no real network) --------------
class _FakeResp:
    def __init__(self, payload: dict) -> None:
        self._b = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _patch_api(monkeypatch, payload):
    monkeypatch.setattr(fw.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(fw, "_last_request", 0.0)
    monkeypatch.setattr(fw.urllib.request, "urlopen",
                        lambda req, timeout=30: _FakeResp(payload))


def test_api_returns_payload(monkeypatch):
    _patch_api(monkeypatch, {"parse": {"revid": 7, "text": "<p>x</p>"}})
    data = fw._api("de", action="parse", page="P")
    assert data["parse"]["revid"] == 7


def test_api_raises_clean_on_error(monkeypatch):
    _patch_api(monkeypatch, {"error": {"code": "missingtitle", "info": "The page does not exist."}})
    with pytest.raises(SystemExit, match="does not exist"):
        fw._api("de", action="parse", page="Nope")
