"""Offline fixtures for the deterministic ÖNB-Labs/ANNO ALTO fetch seam."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.fetch_anno import (alto_to_text, build_record, check_rights, manifest_url,
                              page_ref, select_lines)

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


def test_staged_annotation_keeps_the_fetched_ocr_verbatim():
    source = json.loads((Path("runs/ingest/texts_src/anno-lehrertag-1871.json"))
                        .read_text(encoding="utf-8"))
    annotated = json.loads((Path("runs/ingest/texts/deu-anno-lehrertag-1871.json"))
                           .read_text(encoding="utf-8"))
    assert annotated["text"] == source["text"]
    assert annotated["source"] == source["source_ref"]
    assert "Frei\nheiten" in annotated["text"]             # OCR line break was not repaired
