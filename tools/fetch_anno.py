"""Deterministic ÖNB-Labs/ANNO ALTO-OCR fetcher for annotated media texts.

ÖNB Labs publishes a deliberately rights-clean subset of ANNO (issues 1568–1877) whose
pages are marked with the Public Domain Mark and exposed as IIIF Presentation manifests,
page images, and ALTO XML OCR.  This tool selects one issue page, preserves the OCR tokens
verbatim, and emits a ``TextSourceRef``-shaped record for the annotation/SME step.

No OCR correction happens here.  ALTO ``String/@CONTENT`` values are joined with spaces in
their document order; line and block boundaries are preserved.  A bad OCR token therefore
stays bad.  Consumers may select an excerpt by physical OCR lines, but any transcription
repair must be verified against the page image and recorded later by the SME.

    python tools/fetch_anno.py lmz18710902 --page 2 --list
    python tools/fetch_anno.py lmz18710902 --page 2 --lines 10-24 \
        --title "Kurzer Zeitungsbericht" --out runs/ingest/texts_src/anno-report.json
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

MANIFEST = "https://iiif.onb.ac.at/presentation/ANNO/{issue_id}/manifest"
USER_AGENT = "TeachersAid-ANNO-ingest/1.0 (Lehrmaterial-Engine; annotated-text library)"
THROTTLE_S = 1.0
RETRIES = 3
_ISSUE = re.compile(r"[A-Za-z0-9_-]+")
_last_request = 0.0


@dataclass(frozen=True)
class PageRef:
    issue_id: str
    issue_label: str
    page: int
    canvas_url: str
    alto_url: str
    image_url: str | None
    manifest_url: str


def _get(url: str) -> bytes:
    """Polite, throttled GET with bounded retry for the documented IIIF surface."""
    global _last_request
    backoff = THROTTLE_S
    for attempt in range(RETRIES):
        wait = _last_request + THROTTLE_S - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            _last_request = time.monotonic()
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except (urllib.error.HTTPError, urllib.error.URLError):
            if attempt == RETRIES - 1:
                raise
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError("unreachable")


def manifest_url(issue_id: str) -> str:
    if not _ISSUE.fullmatch(issue_id):
        raise ValueError("issue id may contain only letters, digits, '_', '-'")
    return MANIFEST.format(issue_id=issue_id)


def fetch_manifest(issue_id: str) -> dict:
    return json.loads(_get(manifest_url(issue_id)).decode("utf-8"))


def _resource_id(value) -> str | None:
    if isinstance(value, dict):
        return value.get("@id") or value.get("id")
    return None


def page_ref(issue_id: str, manifest: dict, page: int) -> PageRef:
    """Resolve a 1-based physical page to its exact canvas, ALTO and image resources."""
    if page < 1:
        raise ValueError("page must be >= 1")
    sequences = manifest.get("sequences") or []
    canvases = sequences[0].get("canvases", []) if sequences else []
    target = None
    for idx, canvas in enumerate(canvases, start=1):
        label = str(canvas.get("label", ""))
        try:
            label_page = int(label)
        except ValueError:
            label_page = idx
        if label_page == page:
            target = canvas
            break
    if target is None:
        raise ValueError(f"page {page} not found (manifest has {len(canvases)} canvases)")

    alto = None
    for annotation_list in target.get("otherContent", []):
        for annotation in annotation_list.get("resources", []):
            resource = annotation.get("resource") or {}
            if "alto" in str(resource.get("format", "")).casefold():
                alto = _resource_id(resource)
                break
    if not alto:
        raise ValueError(f"page {page} has no ALTO OCR resource")
    images = target.get("images") or []
    image = _resource_id((images[0].get("resource") or {})) if images else None
    canvas_url = _resource_id(target)
    if not canvas_url:
        raise ValueError(f"page {page} has no stable canvas id")
    return PageRef(
        issue_id=issue_id,
        issue_label=str(manifest.get("label") or issue_id),
        page=page,
        canvas_url=canvas_url,
        alto_url=alto,
        image_url=image,
        manifest_url=manifest_url(issue_id),
    )


def alto_to_text(raw: bytes | str) -> str:
    """ALTO XML → OCR text without correcting, normalising, or de-hyphenating tokens."""
    root = ET.fromstring(raw)
    lines: list[str] = []
    for block in root.findall(".//{*}TextBlock"):
        block_lines: list[str] = []
        for line in block.findall(".//{*}TextLine"):
            tokens = [node.attrib.get("CONTENT", "")
                      for node in line.findall(".//{*}String")]
            block_lines.append(" ".join(token for token in tokens if token))
        if block_lines:
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend(block_lines)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def select_lines(text: str, spec: str | None) -> str:
    if not spec:
        return text
    match = re.fullmatch(r"(\d+)-(\d+)", spec.strip())
    if not match:
        raise ValueError("--lines expects A-B")
    start, end = map(int, match.groups())
    rows = text.splitlines()
    if not (1 <= start <= end <= len(rows)):
        raise ValueError(f"line selection {spec} outside 1-{len(rows)}")
    return "\n".join(rows[start - 1:end])


def _issue_year(label: str) -> str | None:
    match = re.search(r"\b(1[5-8]\d{2})[-.]\d{2}[-.]\d{2}\b", label)
    return match.group(1) if match else None


def build_record(ref: PageRef, text: str, *, title: str | None = None,
                 author: str = "Nicht ausgewiesen", lines: str | None = None,
                 retrieved: str | None = None) -> dict:
    title = title or ref.issue_label
    retrieved = retrieved or date.today().isoformat()
    attribution = (f"{title}; {ref.issue_label}, Seite {ref.page}. "
                   "Österreichische Nationalbibliothek, ÖNB Labs/ANNO; "
                   "Public Domain Mark 1.0. OCR unverändert übernommen.")
    source_ref = {
        "author": author,
        "title": title,
        "year": _issue_year(ref.issue_label),
        "author_death_year": None,
        "rights_basis": "public_domain_mark",
        "licence": "Public Domain Mark 1.0",
        "repository": "ÖNB Labs / ANNO",
        "url": ref.canvas_url,
        "retrieved": retrieved,
        "attribution": attribution,
    }
    return {
        "issue_id": ref.issue_id,
        "issue_label": ref.issue_label,
        "page": ref.page,
        "manifest_url": ref.manifest_url,
        "canvas_url": ref.canvas_url,
        "alto_url": ref.alto_url,
        "image_url": ref.image_url,
        "retrieved": retrieved,
        "selection": {"ocr_lines": lines},
        "ocr_policy": {
            "verbatim": True,
            "silent_corrections": False,
            "status": "machine_ocr_unverified",
            "note": ("OCR-Zeichenfolge unverändert. Fehler, die eine Aufgabe berühren, müssen "
                     "am Seitenbild geprüft und in der Annotation markiert werden."),
        },
        "source_ref": source_ref,
        "text": text,
        "n_lines": len(text.splitlines()),
    }


def check_rights(source_ref: dict) -> tuple[bool, list[str]]:
    from teachersaid.schema.texts import TextSourceRef

    return TextSourceRef.model_validate(source_ref).is_clear(date.today().year)


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue_id", help="ÖNB IIIF ANNO issue id, e.g. lmz18710902")
    parser.add_argument("--page", type=int, required=True, help="physical issue page (1-based)")
    parser.add_argument("--lines", help="optional physical OCR-line selection A-B")
    parser.add_argument("--title", help="article/advert title for TextSourceRef")
    parser.add_argument("--author", default="Nicht ausgewiesen")
    parser.add_argument("--list", action="store_true", help="print numbered OCR lines; write nothing")
    parser.add_argument("--out", help="output record JSON")
    args = parser.parse_args()

    manifest = fetch_manifest(args.issue_id)
    ref = page_ref(args.issue_id, manifest, args.page)
    text = alto_to_text(_get(ref.alto_url))
    if args.list:
        print(f"# {ref.issue_label} · page {ref.page}")
        print(f"# canvas: {ref.canvas_url}")
        for number, line in enumerate(text.splitlines(), start=1):
            print(f"{number:>4}| {line}")
        return
    text = select_lines(text, args.lines)
    record = build_record(ref, text, title=args.title, author=args.author, lines=args.lines)
    ok, reasons = check_rights(record["source_ref"])
    record["rights_check"] = {"clear": ok, "reasons": reasons}
    output = json.dumps(record, ensure_ascii=False, indent=2)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output + "\n", encoding="utf-8")
        print(path)
    else:
        print(output)


if __name__ == "__main__":
    main()
