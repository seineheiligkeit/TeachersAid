"""Offline fixtures for the deterministic ÖNB-Labs/ANNO ALTO fetch seam."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.fetch_anno import (Region, alto_line_boxes, alto_to_text, build_record,
                              check_rights, crop_url, manifest_url, page_pixels, page_ref,
                              region_for_lines, select_lines)

FIXTURES = Path(__file__).parent / "fixtures"


def test_manifest_resolves_exact_page_resources():
    manifest = json.loads((FIXTURES / "anno_manifest.json").read_text(encoding="utf-8"))
    ref = page_ref("wzt18480315", manifest, 1)
    assert ref.issue_label == "Wiener Zeitung 1848-03-15"
    assert ref.canvas_url.endswith("/canvas/00000001")
    assert ref.alto_url.endswith("/resource/00000001.xml")
    assert ref.image_url.endswith("/00000001/full/full/0/default.jpg")
    assert ref.manifest_url == manifest_url("wzt18480315")


def test_alto_parser_preserves_ocr_errors_and_block_boundaries():
    raw = (FIXTURES / "anno_page.xml").read_bytes()
    text = alto_to_text(raw)
    assert text == ("Wien, 15. März.\nDie Freihelt ist ausgerufen.\n\n"
                    "Anzeige: Unterricht in Wlen.")
    assert "Freihelt" in text and "Wlen" in text  # no silent correction
    assert select_lines(text, "2-4") == "Die Freihelt ist ausgerufen.\n\nAnzeige: Unterricht in Wlen."


def test_anno_record_is_public_domain_mark_clear_and_auditable():
    manifest = json.loads((FIXTURES / "anno_manifest.json").read_text(encoding="utf-8"))
    ref = page_ref("wzt18480315", manifest, 1)
    record = build_record(ref, "Die Freihelt ist ausgerufen.", title="Bericht",
                          lines="2-2", retrieved="2026-07-11")
    assert record["ocr_policy"]["verbatim"] is True
    assert record["ocr_policy"]["silent_corrections"] is False
    assert record["source_ref"]["rights_basis"] == "public_domain_mark"
    assert record["source_ref"]["url"] == ref.canvas_url
    assert check_rights(record["source_ref"]) == (True, [])


def test_public_domain_mark_requires_explicit_mark_and_bad_inputs_fail():
    from teachersaid.schema.texts import TextSourceRef

    source = {
        "author": "Nicht ausgewiesen", "title": "Bericht", "repository": "ANNO",
        "rights_basis": "public_domain_mark", "licence": "unklar", "attribution": "ANNO",
    }
    ok, reasons = TextSourceRef.model_validate(source).is_clear(2026)
    assert not ok and "Public Domain Mark" in reasons[0]
    with pytest.raises(ValueError):
        manifest_url("../../bad")
    with pytest.raises(ValueError):
        select_lines("eins\nzwei", "0-2")


# --- scan-crop region math (offline; self-contained worksheets embed the page image) --------
def test_alto_line_boxes_text_sequence_matches_alto_to_text():
    """The i-th (text, box) pair's text is exactly alto_to_text's i-th line — so a physical
    OCR-line number maps 1:1 to a bbox (blank block-separators carry a None box)."""
    raw = (FIXTURES / "anno_page_coords.xml").read_bytes()
    pairs = alto_line_boxes(raw)
    assert [text for text, _box in pairs] == alto_to_text(raw).splitlines()
    assert pairs[2] == ("", None)                       # the block separator, no box
    assert pairs[0][1] == (100, 100, 300, 40)           # TextLine l1's own bbox
    assert pairs[3][1] == (80, 260, 400, 44)


def test_page_pixels_reads_the_alto_page_dimensions():
    raw = (FIXTURES / "anno_page_coords.xml").read_bytes()
    assert page_pixels(raw) == (1000, 1400)


def test_region_for_lines_is_the_padded_union_bbox():
    raw = (FIXTURES / "anno_page_coords.xml").read_bytes()
    # lines 1-2 (both in the first block): union of (100,100,300,40) and (90,150,360,42)
    #   x0=90 y0=100 x1=450 y1=192 → padded by 10 → (80,90,380,112)
    assert region_for_lines(raw, "1-2", pad=10) == Region(80, 90, 380, 112)
    # lines 1-4 skip the blank line 3 (None box); include l3 → x1=480 y1=304
    assert region_for_lines(raw, "1-4", pad=0) == Region(80, 100, 400, 204)


def test_region_for_lines_clamps_to_the_page_and_rejects_bad_specs():
    raw = (FIXTURES / "anno_page_coords.xml").read_bytes()
    pw, ph = page_pixels(raw)
    huge = region_for_lines(raw, "1-4", pad=5000, page_width=pw, page_height=ph)
    assert huge == Region(0, 0, 1000, 1400)             # clamped to the page, x0/y0 floored at 0
    with pytest.raises(ValueError):
        region_for_lines(raw, "3-3", pad=0)             # a blank-only range has no positioned line
    with pytest.raises(ValueError):
        region_for_lines(raw, "not-a-range", pad=0)


def test_line_bbox_falls_back_to_the_union_of_string_boxes():
    """A TextLine without its own HPOS/VPOS/WIDTH/HEIGHT uses the union of its String boxes."""
    raw = (
        '<alto xmlns="http://www.loc.gov/standards/alto/ns-v3#"><Layout><Page WIDTH="500" '
        'HEIGHT="500"><PrintSpace><TextBlock><TextLine>'
        '<String CONTENT="A" HPOS="10" VPOS="20" WIDTH="30" HEIGHT="15"/>'
        '<String CONTENT="B" HPOS="50" VPOS="18" WIDTH="20" HEIGHT="17"/>'
        '</TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    )
    (_text, box), = alto_line_boxes(raw)
    assert box == (10, 18, 60, 17)                       # x:10..70, y:18..35


def test_crop_url_rewrites_the_iiif_region_and_size_segments():
    image_url = "https://iiif.onb.ac.at/images/ANNO/lmz18710902/00000001/full/full/0/default.jpg"
    url = crop_url(image_url, Region(66, 1397, 1001, 837))
    assert url == ("https://iiif.onb.ac.at/images/ANNO/lmz18710902/00000001/"
                   "66,1397,1001,837/full/0/default.jpg")
    assert crop_url(image_url, Region(1, 2, 3, 4), size="1200,").endswith(
        "/1,2,3,4/1200,/0/default.jpg")


def test_staged_annotation_keeps_the_fetched_ocr_verbatim():
    source = json.loads((Path("runs/ingest/texts_src/anno-lehrertag-1871.json"))
                        .read_text(encoding="utf-8"))
    annotated = json.loads((Path("runs/ingest/texts/deu-anno-lehrertag-1871.json"))
                           .read_text(encoding="utf-8"))
    assert annotated["text"] == source["text"]
    assert annotated["source"] == source["source_ref"]
    assert "Frei\nheiten" in annotated["text"]             # OCR line break was not repaired


def test_weltausstellung_annotation_keeps_the_fetched_ocr_verbatim():
    source = json.loads((Path("runs/ingest/texts_src/anno-weltausstellung-1873.json"))
                        .read_text(encoding="utf-8"))
    annotated = json.loads((Path("runs/ingest/texts/deu-anno-weltausstellung-1873.json"))
                           .read_text(encoding="utf-8"))
    assert annotated["text"] == source["text"]
    assert annotated["source"] == source["source_ref"]
    assert source["source_ref"]["rights_basis"] == "public_domain_mark"
    assert source["canvas_url"].endswith("/ANNO/wrz18730502/canvas/00000003")
    # OCR errors preserved, never silently corrected ("find" = sind, "wahrhast" = wahrhaft)
    assert "Bald find es" in annotated["text"]
    assert "wahrhast kaiserlichen" in annotated["text"]
    assert "stimmten begeistert em." in annotated["text"]
