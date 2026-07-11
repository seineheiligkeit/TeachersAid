"""Rights-first Wikimedia Commons image fetcher for historical Bildquellen.

Commons' ``imageinfo/extmetadata`` is the authority for the exact digital file.
The tool deliberately models two independent questions:

1. Is the underlying work clear in Austria (for example 70 Jahre p.m.a.)?
2. Is this exact scan/photograph licensed or marked for reuse?

A public-domain work does *not* answer question 2.  Work clearance is therefore a
required per-item assertion; reproduction clearance is parsed from machine-readable
Commons metadata.  Ambiguous or incomplete data fails closed before any binary is
written.  Pytest exercises parsers against fixtures and never calls the network.

Example (the Wave-B flagship)::

    python tools/fetch_commons.py "File:Afgevaardigden ... RP-P-OB-87.274.jpg" \
      --id gpb-isabey-wiener-kongress --creator "Bernhard J. Dondorf, nach Isabey" \
      --work-title "Der Wiener Congress 1815" --work-date "1833-1872" \
      --work-death-year 1902 --work-evidence "Rijksmuseum: public domain; Dondorf d. 1902" \
      --repository "Rijksmuseum Amsterdam / Wikimedia Commons" \
      --attribution "..." --out-dir runs/ingest/image_sources
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "TeachersAid-Commons-ingest/1.0 (educational image-source corpus)"
THROTTLE_S = 1.5
RETRIES = 4
_last_request = 0.0


class RightsError(ValueError):
    """The record is not sufficiently clear to redistribute."""


def _get(url: str) -> bytes:
    global _last_request
    backoff = THROTTLE_S
    for attempt in range(RETRIES):
        wait = _last_request + THROTTLE_S - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            _last_request = time.monotonic()
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            if attempt == RETRIES - 1:
                raise
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                raise
            retry_after = float(getattr(exc, "headers", {}).get("Retry-After") or backoff)
            time.sleep(max(retry_after, backoff))
            backoff *= 2
    raise RuntimeError("unreachable")


def fetch_metadata(title: str) -> dict:
    if not title.startswith("File:"):
        raise ValueError("Commons title must start with 'File:'")
    query = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|sha1|extmetadata",
            "titles": title,
        }
    )
    return json.loads(_get(f"{API}?{query}").decode("utf-8"))


def _value(metadata: dict, key: str):
    value = metadata.get(key)
    return value.get("value") if isinstance(value, dict) else None


def parse_file(data: dict) -> dict:
    """Select exactly one file record from a MediaWiki response."""
    pages = data.get("query", {}).get("pages", [])
    if len(pages) != 1 or pages[0].get("missing") is True:
        raise ValueError("Commons response did not contain exactly one existing file")
    page = pages[0]
    infos = page.get("imageinfo") or []
    if len(infos) != 1:
        raise ValueError("Commons file has no unambiguous imageinfo record")
    info = infos[0]
    required = {"url", "descriptionurl", "sha1", "width", "height", "mime", "extmetadata"}
    missing = sorted(required - set(info))
    if missing:
        raise ValueError("Commons imageinfo missing: " + ", ".join(missing))
    return {"pageid": page.get("pageid"), "title": page.get("title"), **info}


def reproduction_rights(info: dict) -> dict:
    """Parse the exact-file licence from extmetadata; reject ambiguous records."""
    meta = info["extmetadata"]
    short = str(_value(meta, "LicenseShortName") or "").strip()
    terms = str(_value(meta, "UsageTerms") or "").strip()
    code = str(_value(meta, "License") or "").strip().casefold()
    url = str(_value(meta, "LicenseUrl") or "").strip() or None
    categories = str(_value(meta, "Categories") or "")
    attr_raw = str(_value(meta, "AttributionRequired") or "").strip().casefold()
    if not short or not terms or attr_raw not in {"true", "false"}:
        raise RightsError(
            "reproduction rights unclear: LicenseShortName, UsageTerms and "
            "AttributionRequired are mandatory"
        )
    attribution_required = attr_raw == "true"
    folded = f"{short} {terms} {code}".casefold()
    if code == "cc0" or "creative commons zero" in folded or "cc0" in folded:
        basis = "cc0"
    elif "cc-by-sa" in code or "cc by-sa" in folded or "attribution-sharealike" in folded:
        basis = "cc_by_sa"
    elif code.startswith("cc-by") or "cc by" in folded or "creative commons attribution" in folded:
        basis = "cc_by"
    elif (
        "public domain" in folded
        and (url and "creativecommons.org/publicdomain/mark" in url.casefold()
             or "CC-PD-Mark" in categories)
    ):
        basis = "public_domain_mark"
    else:
        raise RightsError(
            f"reproduction rights unclear or unsupported: short={short!r}, code={code!r}"
        )
    if basis in {"cc_by", "cc_by_sa"} and not attribution_required:
        raise RightsError("Commons reports a CC BY licence but AttributionRequired is false")
    return {
        "basis": basis,
        "licence": terms if short in terms else f"{short}: {terms}",
        "licence_url": url,
        "attribution_required": attribution_required,
        "evidence": (
            "Wikimedia Commons imageinfo/extmetadata: "
            f"LicenseShortName={short}; UsageTerms={terms}; License={code}; "
            f"AttributionRequired={attr_raw}."
        ),
    }


def build_record(
    info: dict,
    *,
    asset_id: str,
    creator: str,
    work_title: str,
    work_date: str | None,
    work_basis: str,
    work_death_year: int | None,
    work_evidence: str,
    repository: str,
    attribution: str,
    retrieved: str | None = None,
) -> dict:
    """Build an ``ImageSourceRef``-shaped provenance record and run both gates."""
    meta = info["extmetadata"]
    rights = reproduction_rights(info)
    if not (_value(meta, "Credit") or repository.strip()):
        raise RightsError("source repository/credit is missing")
    record = {
        "id": asset_id,
        "commons_title": info["title"],
        "pageid": info.get("pageid"),
        "source_ref": {
            "creator": creator,
            "title": work_title,
            "work_date": work_date,
            "repository": repository,
            "description_url": info["descriptionurl"],
            "file_url": info["url"],
            "retrieved": retrieved or date.today().isoformat(),
            "attribution": attribution,
            "mime": info["mime"],
            "width": info["width"],
            "height": info["height"],
            "sha1": info["sha1"],
            "work_rights": {
                "basis": work_basis,
                "creator": creator,
                "creator_death_year": work_death_year,
                "licence": "Public Domain Mark 1.0" if work_basis == "public_domain_mark" else None,
                "evidence": work_evidence,
            },
            "reproduction_rights": rights,
            "rights_metadata": {
                key: _value(meta, key)
                for key in (
                    "LicenseShortName", "UsageTerms", "LicenseUrl", "License",
                    "AttributionRequired", "Copyrighted", "Credit", "Artist", "Categories"
                )
            },
        },
        "rights_caution": (
            "PD-work != PD-reproduction: work_rights and reproduction_rights were "
            "checked independently for this item."
        ),
    }
    from teachersaid.schema.image_sources import ImageSourceRef

    parsed = ImageSourceRef.model_validate(record["source_ref"])
    ok, reasons = parsed.is_clear(date.fromisoformat(record["source_ref"]["retrieved"]).year)
    if not ok:
        raise RightsError("; ".join(reasons))
    record["rights_check"] = {"clear": True, "reasons": []}
    return record


def download_binary(record: dict, out_dir: Path) -> Path:
    """Download only after rights have cleared; verify Commons SHA-1."""
    ref = record["source_ref"]
    suffix = ".jpg" if ref["mime"] == "image/jpeg" else ".png"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{record['id']}{suffix}"
    payload = _get(ref["file_url"])
    digest = hashlib.sha1(payload).hexdigest()  # noqa: S324 - identity field from Commons
    if digest != ref["sha1"]:
        raise ValueError(f"download SHA-1 {digest} does not match Commons {ref['sha1']}")
    path.write_bytes(payload)
    return path


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("title", help="exact Commons title, including File:")
    parser.add_argument("--id", required=True, help="stable local id / output stem")
    parser.add_argument("--creator", required=True)
    parser.add_argument("--work-title", required=True)
    parser.add_argument("--work-date")
    parser.add_argument(
        "--work-basis",
        choices=["public_domain_pma", "public_domain_mark", "cc0", "cc_by", "cc_by_sa", "cleared"],
        default="public_domain_pma",
    )
    parser.add_argument("--work-death-year", type=int)
    parser.add_argument("--work-evidence", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--attribution", required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/ingest/image_sources"))
    parser.add_argument("--list", action="store_true", help="rights dry-run; do not download/write")
    args = parser.parse_args()

    info = parse_file(fetch_metadata(args.title))
    record = build_record(
        info,
        asset_id=args.id,
        creator=args.creator,
        work_title=args.work_title,
        work_date=args.work_date,
        work_basis=args.work_basis,
        work_death_year=args.work_death_year,
        work_evidence=args.work_evidence,
        repository=args.repository,
        attribution=args.attribution,
    )
    if args.list:
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return
    binary = download_binary(record, args.out_dir)
    record["binary"] = {"path": str(binary), "sha1_verified": True}
    metadata = args.out_dir / f"{args.id}.rights.json"
    metadata.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {metadata} and {binary} (rights_clear=true)")


if __name__ == "__main__":
    main()
