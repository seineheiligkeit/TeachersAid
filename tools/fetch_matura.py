"""Deterministic downloader for the SRDP (Zentralmatura) exam archive on matura.gv.at.

No LLM in the path (the ``fetch_*`` precedent). Scrapes the TYPO3 *tx_downloads* +
Solr ``/downloads`` archive, where **each exam is a "Collection"** served as a zip of its
Aufgaben-/Korrekturhefte (e.g. ``KL25_PT1_AHS_MAT_00_DE_{AU,LO}.pdf``). The Solr facets are
``year`` (2013/14…now) × ``documentType`` (Klausuren | Kompensationsprüfungen) × ``subject``
× ``schoolType`` (AHS/BHS/BRP); results paginate via ``tx_solr[page]``.

The download URL carries a per-collection **cHash** anti-tamper token, so it cannot be
fabricated — we scrape the real hrefs from the result pages, then fetch the zips. The whole
public archive is **CC BY 4.0 (IWG 2022)**, attribution *"Datenquelle: Bundesministerium für
Bildung"*; third-party texts/images embedded in language/Deutsch exams may carry separate
rights (recorded in the manifest, the reuser clears them).

    python tools/fetch_matura.py --list --subject Mathematik --school-type AHS    # dry-run
    python tools/fetch_matura.py --subject Mathematik --year 2024/25              # download
    python tools/fetch_matura.py --all --standard-only --extract                  # full archive

Output lands under ``runs/matura/`` (git-ignored; sync via Drive). Idempotent: a collection
already recorded in the manifest is skipped. The pure parsing functions take HTML strings and
are unit-tested offline; only ``http_get`` / ``main`` touch the network and filesystem.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://www.matura.gv.at"
DOWNLOADS = BASE + "/downloads"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
LICENCE = "CC BY 4.0 (IWG 2022)"
ATTRIBUTION = "Datenquelle: Bundesministerium für Bildung"

OUT_DIR = os.path.join("runs", "matura")

# Solr facet vocabulary (verified against the live site, 29 Jun 2026). ``subject`` values are
# the catalog's own slugs; language skills are sub-facets under the language.
DOCUMENT_TYPES = {
    "Klausuren": "/Frühere Prüfungsaufgaben/Klausuren/",
    "Kompensationsprüfungen": "/Frühere Prüfungsaufgaben/Kompensationsprüfungen/",
}
SCHOOL_TYPES = ("AHS", "BHS", "BRP")
# canonical subject slug → the SRDP code our grounding uses (operators.py / lehrplan_store)
SUBJECT_CODE = {
    "Mathematik": "MAT", "Angewandte Mathematik": "AMT",
    "Unterrichtssprache/Deutsch": "DEU",
    "Klassische Sprachen/Latein": "LAT", "Klassische Sprachen/Griechisch": "GRI",
    "Lebende Fremdsprachen/Englisch": "ENG", "Lebende Fremdsprachen/Französisch": "FRA",
    "Lebende Fremdsprachen/Italienisch": "ITA", "Lebende Fremdsprachen/Spanisch": "SPA",
}


# --- URL building ---------------------------------------------------------------------
def build_search_url(*, document_type="Klausuren", subject=None, school_type=None,
                     year=None, page=1) -> str:
    """A faceted Solr ``/downloads`` query URL. ``subject`` is a slug like
    ``"Mathematik"`` or ``"Lebende Fremdsprachen/Englisch"``; ``year`` is ``"2024/25"``."""
    filt = []
    dt = DOCUMENT_TYPES.get(document_type, document_type)
    filt.append(("documentType", dt))
    if subject:
        filt.append(("subject", "/%s/" % subject.strip("/")))
    if school_type:
        filt.append(("schoolType", school_type))
    if year:
        filt.append(("year", year))
    params = []
    for i, (k, v) in enumerate(filt):
        params.append(("tx_solr[filter][%d]" % i, "%s:%s" % (k, v)))
    if page and page > 1:
        params.append(("tx_solr[page]", str(page)))
    return DOWNLOADS + "?" + urllib.parse.urlencode(params)


def download_url(collection_id: int | str, chash: str) -> str:
    """The collection-zip download URL (the cHash is required and per-collection)."""
    q = urllib.parse.urlencode({
        "tx_downloads_details[action]": "download",
        "tx_downloads_details[collection]": str(collection_id),
        "tx_downloads_details[controller]": "Collection",
        "cHash": chash,
    })
    return DOWNLOADS + "/download?" + q


# --- HTML parsing (pure) --------------------------------------------------------------
# A result item pairs a download anchor (collection id + cHash) with a following
# pretty-title anchor (/downloads/download/<title>). We scan anchors in document order.
_COLL_RE = re.compile(
    r"tx_downloads_details(?:%5B|\[)collection(?:%5D|\])=(\d+)"
    r"(?:[^\"']*?)cHash=([0-9a-f]+)", re.I)
_TITLE_RE = re.compile(r'href="(?:https?://[^/"]+)?/downloads/download/([^"?]+)"', re.I)
_ANCHOR_RE = re.compile(r'href="([^"]+)"', re.I)


def _unquote(s: str) -> str:
    return urllib.parse.unquote(html.unescape(s))


def parse_collections(page_html: str) -> list[dict]:
    """Extract ``[{collection, chash, title}]`` from a Solr result page, pairing each
    download anchor with the next pretty-title anchor (titles disambiguate translations /
    accessibility / termin)."""
    out: list[dict] = []
    pending: dict | None = None
    for m in _ANCHOR_RE.finditer(page_html):
        href = html.unescape(m.group(1))
        cm = _COLL_RE.search(href)
        if cm:
            pending = {"collection": int(cm.group(1)), "chash": cm.group(2)}
            continue
        tm = _TITLE_RE.search(m.group(0))
        if tm and pending is not None:
            pending["title"] = _unquote(tm.group(1)).replace("–", "-").strip()
            out.append(pending)
            pending = None
    # de-dupe by collection id, keep first (titled) occurrence
    seen, uniq = set(), []
    for c in out:
        if c["collection"] in seen:
            continue
        seen.add(c["collection"])
        uniq.append(c)
    return uniq


def parse_facet_values(page_html: str, facet: str) -> list[str]:
    """Distinct values offered for a facet (``year`` | ``subject`` | ``schoolType``) — used
    for discovery (``--all`` enumerates years from the live page, not a hard-coded list)."""
    key = "%s%%3A" % facet  # urlencoded "facet:"
    vals = set()
    for m in re.finditer(key + r"([^\"&]+)", page_html):
        v = urllib.parse.unquote_plus(html.unescape(m.group(1)))
        vals.add(v.strip("/"))
    return sorted(vals)


def last_page(page_html: str) -> int:
    """Highest ``tx_solr[page]=N`` referenced (pagination bound); 1 if none."""
    pages = [int(m.group(1)) for m in
             re.finditer(r"tx_solr(?:%5B|\[)page(?:%5D|\])=(\d+)", page_html)]
    return max(pages) if pages else 1


# --- title classification (pure) ------------------------------------------------------
_TERMIN_RE = re.compile(r"(Haupttermin|Herbsttermin|Wintertermin|Nebentermin)", re.I)
_YEAR_RE = re.compile(r"(\d{4})/(\d{2})")


def classify_title(title: str) -> dict:
    """Pull termin / year / variant from a collection title. ``variant`` flags the
    non-standard German editions we usually skip (``--standard-only``)."""
    t = title
    tm = _TERMIN_RE.search(t)
    ym = _YEAR_RE.search(t)
    low = t.lower()
    if "blindheit" in low or "sehbehinderung" in low:
        variant = "accessibility"
    elif "übersetzung" in low or "uebersetzung" in low:
        variant = "translation"
    else:
        variant = "standard"
    return {
        "termin": tm.group(1).title() if tm else None,
        "year": ("%s/%s" % (ym.group(1), ym.group(2))) if ym else None,
        "variant": variant,
    }


def safe_slug(title: str) -> str:
    s = re.sub(r"[^\w]+", "_", title, flags=re.U).strip("_")
    return re.sub(r"_+", "_", s)


# --- network + filesystem -------------------------------------------------------------
def http_get(url: str, *, binary=False, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def discover(*, document_type="Klausuren", subject=None, school_type=None,
             year=None, delay=0.4) -> list[dict]:
    """All collections matching the filters, across result pages. Each dict gains the
    classified termin/year/variant and a stable slug."""
    first = http_get(build_search_url(document_type=document_type, subject=subject,
                                      school_type=school_type, year=year))
    pages = last_page(first)
    found = parse_collections(first)
    for p in range(2, pages + 1):
        time.sleep(delay)
        found += parse_collections(http_get(build_search_url(
            document_type=document_type, subject=subject, school_type=school_type,
            year=year, page=p)))
    # de-dupe across pages
    seen, uniq = set(), []
    for c in found:
        if c["collection"] in seen:
            continue
        seen.add(c["collection"])
        c.update(classify_title(c.get("title", "")))
        c["slug"] = safe_slug(c.get("title", str(c["collection"])))
        uniq.append(c)
    return uniq


def _load_manifest(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def fetch_collection(coll: dict, out_dir: str, manifest: dict, *, delay=0.4) -> str | None:
    """Download one collection zip (idempotent via the manifest). Returns the zip path."""
    cid = str(coll["collection"])
    if cid in manifest and os.path.exists(manifest[cid].get("zip", "")):
        return manifest[cid]["zip"]
    url = download_url(coll["collection"], coll["chash"])
    data = http_get(url, binary=True)
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, coll.get("slug", cid) + ".zip")
    with open(zip_path, "wb") as fh:
        fh.write(data)
    manifest[cid] = {
        "collection": coll["collection"], "title": coll.get("title"),
        "termin": coll.get("termin"), "year": coll.get("year"),
        "variant": coll.get("variant"), "zip": zip_path, "bytes": len(data),
        "source_url": url, "licence": LICENCE, "attribution": ATTRIBUTION,
    }
    time.sleep(delay)
    return zip_path


def main(argv: list[str] | None = None) -> int:
    try:  # German titles + glyphs must print on a cp1252 Windows console
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Download SRDP Matura exam collections.")
    ap.add_argument("--subject", help="subject slug, e.g. 'Mathematik' or "
                    "'Lebende Fremdsprachen/Englisch' (omit with --all)")
    ap.add_argument("--year", help="e.g. '2024/25' (omit = all years)")
    ap.add_argument("--school-type", choices=SCHOOL_TYPES)
    ap.add_argument("--document-type", default="Klausuren",
                    choices=list(DOCUMENT_TYPES))
    ap.add_argument("--all", action="store_true",
                    help="enumerate every subject from the live facet list")
    ap.add_argument("--standard-only", action="store_true",
                    help="skip translation/accessibility editions (= --variant standard)")
    ap.add_argument("--variant", choices=("standard", "translation", "accessibility"),
                    help="keep only this edition. 'accessibility' (Blindheit/Sehbehinderung) "
                    "linearises the vector math → real numbers + textual figure descriptions.")
    ap.add_argument("--list", action="store_true", help="dry-run: print, don't download")
    ap.add_argument("--extract", action="store_true",
                    help="unzip + run extract_matura on each downloaded pair")
    ap.add_argument("-o", "--out", default=OUT_DIR)
    args = ap.parse_args(argv)

    subjects = [args.subject]
    if args.all:
        # the curated leaf subjects we ground (operators.py). A language-parent slug like
        # "Lebende Fremdsprachen/Englisch" returns all its skill booklets in one crawl, so
        # we deliberately do NOT also crawl the Hören/Lesen/… sub-facets (would duplicate).
        subjects = list(SUBJECT_CODE)

    colls: list[dict] = []
    for subj in subjects:
        found = discover(document_type=args.document_type, subject=subj,
                         school_type=args.school_type, year=args.year)
        for c in found:
            c["subject_slug"] = subj
        colls += found
    want_variant = "standard" if args.standard_only else args.variant
    if want_variant:
        colls = [c for c in colls if c.get("variant") == want_variant]

    print("%d collection(s) found" % len(colls))
    for c in colls:
        print("  [%s] %s" % (c["collection"], c.get("title")))
    if args.list:
        return 0

    os.makedirs(args.out, exist_ok=True)
    man_path = os.path.join(args.out, "manifest.json")
    manifest = _load_manifest(man_path)
    zips = []
    for c in colls:
        sub_dir = os.path.join(args.out, "zips",
                               SUBJECT_CODE.get(c.get("subject_slug", ""), "MISC"))
        z = fetch_collection(c, sub_dir, manifest, delay=0.4)
        with open(man_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
        if z:
            zips.append(z)
            print("  got %s" % os.path.basename(z))

    if args.extract:
        _extract_all(zips, args.out)
    print("done: %d zip(s); manifest → %s" % (len(zips), man_path))
    return 0


def _extract_all(zips: list[str], out_dir: str) -> None:
    """Unzip each collection and run the extractor over the PDFs it contains."""
    import zipfile
    from tools import extract_matura  # local import; keeps this tool importable bare
    pdf_dir = os.path.join(out_dir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    json_dir = os.path.join(out_dir, "json")
    os.makedirs(json_dir, exist_ok=True)
    for z in zips:
        with zipfile.ZipFile(z) as zf:
            pdfs = [zf.extract(n, pdf_dir) for n in zf.namelist()
                    if n.lower().endswith(".pdf")]
        if not pdfs:
            continue
        try:
            out = os.path.join(json_dir, os.path.splitext(os.path.basename(z))[0] + ".json")
            extract_matura.main([*pdfs, "-o", out])
        except Exception as e:  # extraction is best-effort per exam; keep going
            print("  ! extract failed for %s: %s" % (os.path.basename(z), e))


if __name__ == "__main__":
    raise SystemExit(main())
