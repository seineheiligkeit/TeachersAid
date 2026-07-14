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


# --- scan crops (IIIF Image API region) --------------------------------------
# A student task may only operate on artifacts that are ON the sheet, so the OCR-Prüfung
# (compare the machine OCR against the page image) needs the matching page region embedded
# as a sourced raster.  These helpers compute the crop region deterministically from the
# SAME ALTO the excerpt lines came from, so the depicted lines and the printed excerpt agree
# by construction.  No OCR correction happens; the crop is a faithful slice of the scan.

@dataclass(frozen=True)
class Region:
    """A pixel rectangle in the ALTO/IIIF-image coordinate space (they coincide for ANNO —
    the ALTO Page WIDTH/HEIGHT equal the full image dimensions, so no scaling is needed)."""
    x: int
    y: int
    w: int
    h: int

    def as_iiif(self) -> str:
        return f"{self.x},{self.y},{self.w},{self.h}"


def _line_bbox(line) -> tuple[int, int, int, int] | None:
    """The pixel bbox of one ALTO ``TextLine`` — its own HPOS/VPOS/WIDTH/HEIGHT when present,
    else the union of its ``String`` boxes.  Returns None when nothing is positioned."""
    attrib = line.attrib
    keys = ("HPOS", "VPOS", "WIDTH", "HEIGHT")
    if all(k in attrib for k in keys):
        return (int(attrib["HPOS"]), int(attrib["VPOS"]),
                int(attrib["WIDTH"]), int(attrib["HEIGHT"]))
    boxes = []
    for node in line.findall(".//{*}String"):
        sa = node.attrib
        if all(k in sa for k in keys):
            boxes.append((int(sa["HPOS"]), int(sa["VPOS"]), int(sa["WIDTH"]), int(sa["HEIGHT"])))
    if not boxes:
        return None
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[0] + b[2] for b in boxes)
    y1 = max(b[1] + b[3] for b in boxes)
    return (x0, y0, x1 - x0, y1 - y0)


def alto_line_boxes(raw: bytes | str) -> list[tuple[str, tuple[int, int, int, int] | None]]:
    """Reproduce ``alto_to_text``'s exact line sequence, pairing each output line with its
    ALTO pixel bbox (None for the blank separators inserted between TextBlocks).  The i-th
    entry's text is exactly ``alto_to_text(raw).splitlines()[i]``, so a 1-based physical
    OCR-line number maps directly to a bbox for the crop-region math."""
    root = ET.fromstring(raw)
    out: list[tuple[str, tuple[int, int, int, int] | None]] = []
    for block in root.findall(".//{*}TextBlock"):
        block_lines: list[tuple[str, tuple[int, int, int, int] | None]] = []
        for line in block.findall(".//{*}TextLine"):
            tokens = [node.attrib.get("CONTENT", "")
                      for node in line.findall(".//{*}String")]
            text = " ".join(token for token in tokens if token)
            block_lines.append((text, _line_bbox(line)))
        if block_lines:
            if out and out[-1][0] != "":
                out.append(("", None))
            out.extend(block_lines)
    while out and out[-1][0] == "":
        out.pop()
    return out


def page_pixels(raw: bytes | str) -> tuple[int | None, int | None]:
    """The ALTO ``Page`` WIDTH/HEIGHT — the full-image pixel space to clamp a padded region to."""
    root = ET.fromstring(raw)
    page = root.find(".//{*}Page")
    if page is None:
        return None, None
    w = page.attrib.get("WIDTH")
    h = page.attrib.get("HEIGHT")
    return (int(w) if w else None, int(h) if h else None)


def region_for_lines(raw: bytes | str, spec: str, *, pad: int = 90,
                     page_width: int | None = None,
                     page_height: int | None = None) -> Region:
    """Padded union bbox of the ALTO TextLines for physical OCR-line range ``A-B`` (1-based,
    counted exactly as ``alto_to_text`` numbers them — blank block separators included)."""
    match = re.fullmatch(r"(\d+)-(\d+)", spec.strip())
    if not match:
        raise ValueError("crop line spec expects A-B")
    start, end = map(int, match.groups())
    boxes_all = alto_line_boxes(raw)
    if not (1 <= start <= end <= len(boxes_all)):
        raise ValueError(f"crop lines {spec} outside 1-{len(boxes_all)}")
    boxes = [box for _text, box in boxes_all[start - 1:end] if box]
    if not boxes:
        raise ValueError(f"crop lines {spec}: no positioned TextLines in range")
    x0 = min(b[0] for b in boxes) - pad
    y0 = min(b[1] for b in boxes) - pad
    x1 = max(b[0] + b[2] for b in boxes) + pad
    y1 = max(b[1] + b[3] for b in boxes) + pad
    x0 = max(0, x0)
    y0 = max(0, y0)
    if page_width is not None:
        x1 = min(page_width, x1)
    if page_height is not None:
        y1 = min(page_height, y1)
    return Region(x0, y0, x1 - x0, y1 - y0)


def crop_url(image_url: str, region: Region, *, size: str = "full") -> str:
    """Rewrite a IIIF full-image URL into a region-crop URL (Image API 2.x path grammar
    ``…/{id}/{region}/{size}/{rotation}/{quality}.{fmt}``): replace the region + size
    segments, leave rotation/quality/format untouched."""
    parts = image_url.rstrip("/").split("/")
    if len(parts) < 5:
        raise ValueError(f"not a IIIF image URL: {image_url!r}")
    parts[-4] = region.as_iiif()   # region segment
    parts[-3] = size               # size segment
    return "/".join(parts)


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


def _sha1_bytes(data: bytes) -> str:
    import hashlib

    digest = hashlib.sha1()  # noqa: S324 - a file identity, not a security primitive
    digest.update(data)
    return digest.hexdigest()


def build_crop_record(ref: PageRef, region: Region, *, crop_iiif_url: str, size: str,
                      pad: int, depicts_lines: str, image_bytes: bytes,
                      page_width: int | None, page_height: int | None,
                      crop_id: str, file_path: str, title: str | None = None,
                      author: str = "Nicht ausgewiesen", retrieved: str | None = None) -> dict:
    """The tracked, self-healing record for one scan crop (the binary is git-ignored and
    rebuildable from ``crop.iiif_url``).  Mirrors ``build_record``'s ``source_ref`` shape so a
    crop cites exactly like the OCR excerpt; adds the exact region, IIIF crop URL, saved-file
    sha1 + pixel dims, and the OCR line range it depicts."""
    from PIL import Image
    import io

    retrieved = retrieved or date.today().isoformat()
    with Image.open(io.BytesIO(image_bytes)) as img:
        crop_w, crop_h = img.size
        mime = "image/jpeg" if img.format == "JPEG" else f"image/{(img.format or '').lower()}"
    title = title or f"{ref.issue_label}, Seite {ref.page} (Bildausschnitt)"
    attribution = (f"{title}; {ref.issue_label}, Seite {ref.page}. "
                   "Österreichische Nationalbibliothek, ÖNB Labs/ANNO; "
                   "Public Domain Mark 1.0. Bildausschnitt des Originalscans.")
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
        "id": crop_id,
        "issue_id": ref.issue_id,
        "issue_label": ref.issue_label,
        "page": ref.page,
        "manifest_url": ref.manifest_url,
        "canvas_url": ref.canvas_url,
        "alto_url": ref.alto_url,
        "image_url": ref.image_url,
        "page_pixels": {"width": page_width, "height": page_height},
        "crop": {
            "region": {"x": region.x, "y": region.y, "w": region.w, "h": region.h},
            "iiif_url": crop_iiif_url,
            "size": size,
            "pad": pad,
        },
        "depicts_ocr_lines": depicts_lines,
        "retrieved": retrieved,
        "file": {
            "path": file_path,
            "sha1": _sha1_bytes(image_bytes),
            "width": crop_w,
            "height": crop_h,
            "mime": mime,
            "bytes": len(image_bytes),
        },
        "ocr_policy": {
            "verbatim": True,
            "silent_corrections": False,
            "status": "machine_ocr_unverified",
            "note": ("Bildausschnitt unverändert. Der Scan zeigt die Frakturschrift, "
                     "gegen die die maschinelle OCR geprüft wird."),
        },
        "source_ref": source_ref,
    }


def _save_binary(image_bytes: bytes, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(image_bytes)


def crop_command(issue_id: str, page: int, *, crop_lines: str, crop_id: str,
                 files_dir: Path, record_out: Path, pad: int = 90, size: str = "full",
                 title: str | None = None) -> dict:
    """Compute one scan-crop region from the page ALTO, fetch the IIIF crop, save the JPEG
    under ``files_dir`` and write the tracked JSON record to ``record_out``."""
    manifest = fetch_manifest(issue_id)
    ref = page_ref(issue_id, manifest, page)
    if not ref.image_url:
        raise ValueError(f"page {page} has no IIIF image resource to crop")
    alto = _get(ref.alto_url)
    pw, ph = page_pixels(alto)
    region = region_for_lines(alto, crop_lines, pad=pad, page_width=pw, page_height=ph)
    url = crop_url(ref.image_url, region, size=size)
    image_bytes = _get(url)
    dest = files_dir / f"{crop_id}.jpg"
    _save_binary(image_bytes, dest)
    record = build_crop_record(
        ref, region, crop_iiif_url=url, size=size, pad=pad, depicts_lines=crop_lines,
        image_bytes=image_bytes, page_width=pw, page_height=ph, crop_id=crop_id,
        file_path=str(dest), title=title,
    )
    ok, reasons = check_rights(record["source_ref"])
    record["rights_check"] = {"clear": ok, "reasons": reasons}
    record_out.parent.mkdir(parents=True, exist_ok=True)
    record_out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    return record


def rehydrate_command(record_path: Path) -> dict:
    """Re-materialise a crop binary from its tracked record (self-healing): fetch the frozen
    ``crop.iiif_url``, save it to ``file.path``, and verify the sha1.  If the server re-encoded
    and the sha1 drifts, print the NEW sha1 and rewrite the record — an SME-visible diff, never
    a silent change."""
    record = json.loads(record_path.read_text(encoding="utf-8"))
    url = record["crop"]["iiif_url"]
    dest = Path(record["file"]["path"])
    image_bytes = _get(url)
    _save_binary(image_bytes, dest)
    new_sha1 = _sha1_bytes(image_bytes)
    old_sha1 = record["file"].get("sha1")
    if new_sha1 != old_sha1:
        from PIL import Image
        import io

        with Image.open(io.BytesIO(image_bytes)) as img:
            record["file"]["width"], record["file"]["height"] = img.size
        record["file"]["sha1"] = new_sha1
        record["file"]["bytes"] = len(image_bytes)
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        print(f"sha1 drift: {old_sha1} -> {new_sha1} (record updated: {record_path})")
    else:
        print(f"rehydrated {dest} (sha1 {new_sha1} unchanged)")
    return record


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue_id", nargs="?", help="ÖNB IIIF ANNO issue id, e.g. lmz18710902")
    parser.add_argument("--page", type=int, help="physical issue page (1-based)")
    parser.add_argument("--lines", help="optional physical OCR-line selection A-B")
    parser.add_argument("--title", help="article/advert title for TextSourceRef")
    parser.add_argument("--author", default="Nicht ausgewiesen")
    parser.add_argument("--list", action="store_true", help="print numbered OCR lines; write nothing")
    parser.add_argument("--out", help="output record JSON")
    # --- scan-crop mode (self-contained worksheets need the page region embedded) ---
    parser.add_argument("--crop-lines", help="physical OCR-line range A-B to crop as a scan image")
    parser.add_argument("--crop-id", help="stable id for the crop file/record (e.g. gpb-anno-…-crop)")
    parser.add_argument("--pad", type=int, default=90, help="pixel padding around the line union bbox")
    parser.add_argument("--crop-size", default="full", help="IIIF size segment for the crop (default full)")
    parser.add_argument("--files-dir", default="runs/anno/files", help="where crop JPEGs are saved")
    parser.add_argument("--record-out", help="tracked crop record JSON (default runs/anno/<id>.json)")
    parser.add_argument("--rehydrate", help="re-materialise a crop binary from its tracked record JSON")
    args = parser.parse_args()

    if args.rehydrate:
        rehydrate_command(Path(args.rehydrate))
        return

    if args.crop_lines:
        if not (args.issue_id and args.page and args.crop_id):
            parser.error("--crop-lines needs issue_id, --page and --crop-id")
        record_out = Path(args.record_out) if args.record_out else Path("runs/anno") / f"{args.crop_id}.json"
        record = crop_command(
            args.issue_id, args.page, crop_lines=args.crop_lines, crop_id=args.crop_id,
            files_dir=Path(args.files_dir), record_out=record_out, pad=args.pad,
            size=args.crop_size, title=args.title,
        )
        r = record["crop"]["region"]
        print(f"{record_out}  region={r['x']},{r['y']},{r['w']},{r['h']}  "
              f"file={record['file']['path']} ({record['file']['width']}x{record['file']['height']}, "
              f"sha1 {record['file']['sha1']})")
        return

    if not (args.issue_id and args.page):
        parser.error("issue_id and --page are required (or use --rehydrate)")

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
