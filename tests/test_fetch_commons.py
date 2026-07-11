"""Offline fixtures for the rights-first Wikimedia Commons fetch seam."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.fetch_commons import RightsError, build_record, parse_file, reproduction_rights

FIXTURE = Path(__file__).parent / "fixtures" / "commons_imageinfo.json"


def _info() -> dict:
    return parse_file(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_commons_fixture_preserves_exact_file_identity_and_cc0_terms():
    info = _info()
    assert info["pageid"] == 84921882
    assert info["sha1"] == "305042160df70540a974b9f6efe4b6ede3979bab"
    rights = reproduction_rights(info)
    assert rights["basis"] == "cc0"
    assert rights["attribution_required"] is False
    assert "Creative Commons Zero" in rights["licence"]


def test_record_checks_work_and_reproduction_independently():
    record = build_record(
        _info(), asset_id="isabey", creator="Dondorf, nach Isabey",
        work_title="Der Wiener Congress", work_date="1833-1872",
        work_basis="public_domain_pma", work_death_year=1902,
        work_evidence="Latest named creator died in 1902; Rijksmuseum marks work public domain.",
        repository="Rijksmuseum / Wikimedia Commons", attribution="Rijksmuseum, CC0",
        retrieved="2026-07-11",
    )
    assert record["rights_check"]["clear"] is True
    assert "PD-work != PD-reproduction" in record["rights_caution"]
    source = record["source_ref"]
    assert source["work_rights"]["basis"] == "public_domain_pma"
    assert source["reproduction_rights"]["basis"] == "cc0"
    assert source["rights_metadata"]["UsageTerms"] == (
        "Creative Commons Zero, Public Domain Dedication"
    )


def test_unclear_reproduction_and_unproven_pma_fail_closed():
    info = _info()
    meta = info["extmetadata"]
    meta["LicenseShortName"]["value"] = "Public domain"
    meta["UsageTerms"]["value"] = "Public domain"
    meta["License"]["value"] = "pd"
    meta["LicenseUrl"]["value"] = ""
    meta["Categories"]["value"] = "PD-old"
    with pytest.raises(RightsError, match="unclear"):
        reproduction_rights(info)

    clear_info = _info()
    with pytest.raises(RightsError, match="creator_death_year"):
        build_record(
            clear_info, asset_id="x", creator="Unknown", work_title="W", work_date=None,
            work_basis="public_domain_pma", work_death_year=None,
            work_evidence="Old-looking is not proof.", repository="R", attribution="A",
            retrieved="2026-07-11",
        )


def test_missing_machine_rights_fields_fail_closed():
    info = _info()
    del info["extmetadata"]["UsageTerms"]
    with pytest.raises(RightsError, match="mandatory"):
        reproduction_rights(info)
