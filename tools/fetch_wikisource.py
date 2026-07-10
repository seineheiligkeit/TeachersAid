"""Deterministic Wikisource verbatim-text fetch tool (the `fetch_wikipedia.py` sibling).

Fetches the EXACT revision of a ``<lang>.wikisource.org`` page via the MediaWiki API and
converts the rendered HTML to plain text with a deterministic tag-walker — the verbatim
wording is *selected* from the recorded revision, never authored (no LLM in the path; the
``parse_lehrplan.py`` / ``fetch_wikipedia.py`` precedent). The output JSON is the record
the annotation step consumes: the text + a revision PERMALINK + ``TextSourceRef``-shaped
rights fields (author, death year, PD basis) + the honest edition note read from the
page's Textdaten box. *A PD work is not automatically a PD text*: the record names which
edition/transcription the wording follows, so the SME can judge it at the gate.

Deterministic transformations (presentational only — never a wording change):

- markup stripped; metadata boxes (Textdaten), page-number markers ("[217]"), footnote
  refs, section-edit links and Wikisource line-number gutters dropped;
- whitespace normalised (NBSP → space, runs collapsed, space before punctuation removed);
- inline verse-number gutters ("5  <tab>Calumniari …", the la.wikisource convention)
  stripped from line starts (``--keep-verse-numbers`` disables);
- blank-line runs collapse to one (a stanza/paragraph gap);
- ``--lines A-B``: a physical-line slice (an *excerpt* is selection, not authoring);
- ``--reflow clauses``: prose paragraphs re-broken one clause per line, so tasks can
  reference "Zeile N" (wording untouched; the worksheet renderer numbers non-blank lines).

Wikisource rate-limits bursts (HTTP 429), so requests are throttled and retried politely.

    python tools/fetch_wikisource.py "Der Zauberlehrling (1827)" --site de --list
    python tools/fetch_wikisource.py "Fabulae (Phaedrus)/Liber I" --site la --sections
    python tools/fetch_wikisource.py "Fabulae (Phaedrus)/Liber I" --site la \
        --section "I. Lupus et agnus." --author Phaedrus --death-year 50 \
        --work-title "Fabulae I,1 (Lupus et agnus)" --work-year "~40 n. Chr." \
        --out runs/ingest/texts_src/lat-lupus-agnus.json
"""

from __future__ import annotations

import argparse
import html as htmllib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

API = "https://{site}.wikisource.org/w/api.php"
PERMALINK = "https://{site}.wikisource.org/w/index.php?title={title}&oldid={revid}"
USER_AGENT = "TeachersAid-Wikisource-ingest/1.0 (Lehrmaterial-Engine; annotated-texts library)"
THROTTLE_S = 3.0            # polite inter-request gap — Wikisource 429s rapid bursts
RETRIES = 4

# --- deterministic HTML → text -------------------------------------------------------

# subtrees that are navigation/metadata, never text
_SKIP_TAGS = {"style", "script", "table", "figure", "audio", "img"}
_SKIP_CLASS = {
    "noprint", "ws-noexport", "pr1pn", "pr2pn", "pagenumber", "mw-editsection",
    "reference", "references", "printfooter", "catlinks", "hiddenstructure",
    "andereversion", "mw-heading", "titulusheaderbox", "zeilennummer",
    "mw-cite-backlink", "magnify", "mw-empty-elt", "sidenotes", "wst-sidenote",
}
_SKIP_IDS = {"textdaten", "ws-data", "spoken", "gesprochenertext", "normdaten"}

# a la.wikisource inline verse-number gutter: digits + wide whitespace at line start
_VERSE_NO = re.compile(r"^\s*\d{1,4}\s{2,}")


class _TextExtractor(HTMLParser):
    """Walk rendered MediaWiki HTML and emit text lines.

    ``<br>`` flushes the line buffer even when empty (an explicit blank line = a stanza
    gap). Block-element boundaries flush only a NON-empty buffer — they never *create*
    blank lines, because de.wikisource interleaves line-number divs mid-stanza, so a
    ``<p>`` boundary is not a stanza break.
    """

    _BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr",
              "blockquote", "center", "section"}

    def __init__(self, *, strip_verse_numbers: bool = True) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self._buf: list[str] = []
        self.strip_verse_numbers = strip_verse_numbers
        self._skip_tag: str | None = None       # tag name of the skipped subtree root
        self._skip_level = 0

    # -- skip-region bookkeeping
    @staticmethod
    def _skippable(tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        if tag in _SKIP_TAGS:
            return True
        a = dict(attrs)
        classes = {c.casefold() for c in (a.get("class") or "").split()}
        if classes & _SKIP_CLASS:
            return True
        return (a.get("id") or "").casefold() in _SKIP_IDS

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":                                  # void element, never stacked
            if self._skip_tag is None:
                self._flush(force_blank=True)
            return
        if self._skip_tag is not None:
            if tag == self._skip_tag:
                self._skip_level += 1
            return
        if self._skippable(tag, attrs):
            self._skip_tag, self._skip_level = tag, 1
            return
        if tag in self._BLOCK:
            self._flush(force_blank=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br" and self._skip_tag is None:
            self._flush(force_blank=True)

    def handle_endtag(self, tag: str) -> None:
        if self._skip_tag is not None:
            if tag == self._skip_tag:
                self._skip_level -= 1
                if self._skip_level == 0:
                    self._skip_tag = None
            return
        if tag in self._BLOCK:
            self._flush(force_blank=False)

    def handle_data(self, data: str) -> None:
        if self._skip_tag is None and data:
            # raw newlines/tabs are HTML source formatting, not line breaks — <br> is
            # the only line-break signal. (Keep runs: the verse-number regex needs the
            # "digits + wide gap" shape before whitespace collapses.)
            self._buf.append(data.replace("\r", " ").replace("\n", " "))

    # -- line assembly
    def _flush(self, *, force_blank: bool) -> None:
        line = "".join(self._buf).replace(" ", " ")
        self._buf.clear()
        if self.strip_verse_numbers:
            line = _VERSE_NO.sub("", line)
        line = re.sub(r"\s+", " ", line).strip()
        line = re.sub(r" ([,;:.!?])", r"\1", line)       # old/French spaced punctuation
        if line:
            self.lines.append(line)
        elif force_blank:
            self.lines.append("")

    def close(self) -> None:  # flush a trailing unterminated buffer
        super().close()
        if self._skip_tag is None:
            self._flush(force_blank=False)


def html_to_text(html: str, *, strip_verse_numbers: bool = True) -> str:
    """Rendered MediaWiki HTML → plain text (lines; one blank line per stanza gap)."""
    p = _TextExtractor(strip_verse_numbers=strip_verse_numbers)
    p.feed(html)
    p.close()
    lines: list[str] = []
    for ln in p.lines:                                    # collapse blank runs; trim edges
        if ln == "" and (not lines or lines[-1] == ""):
            continue
        lines.append(ln)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


# --- metadata from the Textdaten box (best-effort, absent on la.wikisource) ----------

def _strip_tags(fragment: str) -> str:
    return htmllib.unescape(re.sub(r"<[^>]+>", "", fragment))


def _span_text(html: str, span_id: str) -> str | None:
    m = re.search(rf'id="{span_id}"[^>]*>(.*?)</span>', html, re.S)
    if not m:
        return None
    value = re.sub(r"\s+", " ", _strip_tags(m.group(1))).strip()
    return value or None


def extract_metadata(html: str) -> dict:
    """Author/title/year/publisher + the 'aus:' edition row of the Textdaten box."""
    meta = {
        "author": _span_text(html, "ws-author"),
        "title": _span_text(html, "ws-title"),
        "year": _span_text(html, "ws-year"),
        "publisher": _span_text(html, "ws-publisher"),
        "edition": None,
    }
    if meta["year"] in ("0",):                            # la.wikisource placeholder
        meta["year"] = None
    m = re.search(r"<td[^>]*>\s*aus:\s*</td>\s*<td[^>]*>(.*?)</td>", html, re.S)
    if m:
        meta["edition"] = re.sub(r"\s+", " ", _strip_tags(m.group(1))).strip() or None
    return meta


# --- selection / reflow (presentational, wording untouched) --------------------------

def slice_lines(text: str, spec: str) -> str:
    """Select physical lines "A-B" (1-based, inclusive) of the extracted text."""
    m = re.fullmatch(r"(\d+)-(\d+)", spec.strip())
    if not m:
        raise ValueError(f"--lines expects 'A-B', got {spec!r}")
    a, b = int(m.group(1)), int(m.group(2))
    lines = text.split("\n")
    if not (1 <= a <= b <= len(lines)):
        raise ValueError(f"--lines {spec}: out of range (text has {len(lines)} lines)")
    picked = lines[a - 1:b]
    while picked and picked[0] == "":
        picked.pop(0)
    while picked and picked[-1] == "":
        picked.pop()
    return "\n".join(picked)


# a clause chunk: text up to sentence/clause punctuation (+ closing quotes), + spacing
_CLAUSE = re.compile(r"[^,;:.!?]*[,;:.!?]+[\"“”«»’')\]]*\s*")


def reflow_clauses(text: str, *, min_len: int = 25) -> str:
    """Break prose paragraphs one clause per line (so tasks can cite "Zeile N").

    Splits after ``, ; : . ! ?`` (+ any closing quote) once the accumulated segment
    reaches ``min_len`` chars — deterministic, wording untouched. Blank lines (paragraph
    gaps) pass through.
    """
    out: list[str] = []
    for para in text.split("\n"):
        if not para.strip():
            out.append("")
            continue
        cur = ""
        pos = 0
        for m in _CLAUSE.finditer(para):
            cur += m.group(0)
            pos = m.end()
            if len(cur.rstrip()) >= min_len:
                out.append(cur.rstrip())
                cur = ""
        rest = (cur + para[pos:]).strip()
        if rest:
            out.append(rest)
    return "\n".join(out)


def zeilen_preview(text: str) -> list[str]:
    """The worksheet numbering: non-blank lines count (matches rendering's
    ``numbered_text``), blank lines stay unnumbered — annotation ``zeile`` refs use
    exactly these numbers."""
    out, n = [], 0
    for ln in text.split("\n"):
        if ln.strip():
            n += 1
            out.append(f"{n:>3} {ln}")
        else:
            out.append("")
    return out


# --- MediaWiki API (throttled + 429-retried) ------------------------------------------

_last_request = 0.0


def _api(site: str, **params) -> dict:
    global _last_request
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    url = API.format(site=site) + "?" + urllib.parse.urlencode(params)
    backoff = THROTTLE_S
    for attempt in range(RETRIES):
        wait = _last_request + THROTTLE_S - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            _last_request = time.monotonic()
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:                          # missingtitle, invalidsection, …
                info = data["error"].get("info", data["error"])
                raise SystemExit(f"Wikisource API error: {info}")
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < RETRIES - 1:
                retry_after = float(e.headers.get("Retry-After") or backoff)
                time.sleep(max(retry_after, backoff))
                backoff *= 2
                continue
            raise
    raise RuntimeError("unreachable")


def list_sections(site: str, page: str) -> list[dict]:
    data = _api(site, action="parse", page=page, prop="sections")
    return data["parse"]["sections"]


def find_section(site: str, page: str, heading: str) -> int:
    want = heading.strip().casefold()
    sections = list_sections(site, page)
    for s in sections:
        if _strip_tags(s.get("line", "")).strip().casefold() == want and str(s.get("index", "")).isdigit():
            return int(s["index"])
    available = [_strip_tags(s.get("line", "")) for s in sections]
    raise SystemExit(f"section {heading!r} not found on {page!r}; available: {available}")


def fetch_page(site: str, page: str, section: int | None = None) -> dict:
    params = dict(action="parse", page=page, prop="text|revid|displaytitle")
    if section is not None:
        params["section"] = str(section)
    data = _api(site, **params)
    return data["parse"]


def permalink(site: str, page: str, revid: int) -> str:
    return PERMALINK.format(site=site, title=urllib.parse.quote(page.replace(" ", "_")),
                            revid=revid)


# --- the record ------------------------------------------------------------------------

def build_attribution(author: str, title: str, year: str | None, edition: str | None,
                      site: str) -> str:
    base = f"{author}, „{title}“" + (f" ({year})" if year else "")
    src = f"Wikisource ({site})" + (f": {edition}" if edition else "")
    return f"{base}; gemeinfrei. Textgrundlage: {src}"


def build_record(*, site: str, page: str, args, parse: dict, section_heading: str | None,
                 text: str, page_meta: dict, today: str | None = None) -> dict:
    revid = parse["revid"]
    link = permalink(site, page, revid)
    retrieved = today or date.today().isoformat()
    author = args.author or page_meta.get("author") or ""
    work_title = args.work_title or page_meta.get("title") or page
    work_year = args.work_year or page_meta.get("year")
    attribution = args.attribution or build_attribution(
        author, work_title, work_year, page_meta.get("edition"), site)
    source_ref = {
        "author": author,
        "title": work_title,
        "year": work_year,
        "author_death_year": args.death_year,
        "rights_basis": args.rights,
        "repository": f"Wikisource ({site})",
        "url": link,
        "retrieved": retrieved,
        "attribution": attribution,
    }
    return {
        "site": site,
        "page": page,
        "section": section_heading,
        "revid": revid,
        "permalink": link,
        "retrieved": retrieved,
        "page_metadata": page_meta,
        "transforms": {
            "lines_selected": args.lines,
            "reflow": args.reflow if args.reflow != "none" else None,
            "verse_numbers_stripped": not args.keep_verse_numbers,
        },
        "edition_caveat": ("Wortlaut folgt der zitierten Wikisource-Transkription "
                           "(Edition siehe page_metadata.edition; Orthographie des "
                           "Originals beibehalten)."),
        "source_ref": source_ref,
        "text": text,
        "n_lines": len(text.split("\n")),
        "n_zeilen": sum(1 for ln in text.split("\n") if ln.strip()),
        "zeilen": zeilen_preview(text),
    }


def check_rights(source_ref: dict) -> tuple[bool, list[str]]:
    """Run the real rights gate (`TextSourceRef.is_clear`) on the record."""
    from teachersaid.schema.texts import TextSourceRef

    ref = TextSourceRef.model_validate(source_ref)
    return ref.is_clear(date.today().year)


# --- CLI --------------------------------------------------------------------------------

def main() -> None:
    # UTF-8 all console output: Wikisource text carries characters outside the Windows
    # console's cp1252 (ř, ß, „…", Greek/long-s) — the default encoder would raise
    # UnicodeEncodeError on --list/--sections and on the JSON printed without --out.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):  # non-reconfigurable stream (pytest capture)
            pass
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", help="Wikisource page title (exact)")
    ap.add_argument("--site", default="de", help="wikisource language subdomain (de, la, …)")
    ap.add_argument("--section", default=None,
                    help="extract one section by its heading text (e.g. 'I. Lupus et agnus.')")
    ap.add_argument("--sections", action="store_true", help="list section headings and exit")
    ap.add_argument("--lines", default=None, help="physical-line slice 'A-B' (see --list)")
    ap.add_argument("--reflow", choices=["none", "clauses"], default="none",
                    help="prose: re-break one clause per line (verse needs none)")
    ap.add_argument("--keep-verse-numbers", action="store_true",
                    help="keep inline verse-number gutters (default: strip)")
    ap.add_argument("--author", default=None, help="author for the TextSourceRef (default: Textdaten)")
    ap.add_argument("--death-year", type=int, default=None,
                    help="author death year (the AT 70-Jahre-p.m.a. rule)")
    ap.add_argument("--rights", default="public_domain_pma",
                    choices=["public_domain_pma", "cc_by", "cc0", "cleared"])
    ap.add_argument("--work-title", default=None, help="work title override")
    ap.add_argument("--work-year", default=None, help="work year override")
    ap.add_argument("--attribution", default=None, help="attribution string override")
    ap.add_argument("--list", action="store_true",
                    help="dry run: print metadata + physically numbered lines, write nothing")
    ap.add_argument("--out", default=None, help="write the record JSON here")
    args = ap.parse_args()

    if args.sections:
        for s in list_sections(args.site, args.page):
            print(f"{s.get('index', '?'):>4}  {_strip_tags(s.get('line', ''))}")
        return

    section_idx = find_section(args.site, args.page, args.section) if args.section else None
    parse = fetch_page(args.site, args.page, section_idx)
    page_meta = extract_metadata(parse["text"])
    text = html_to_text(parse["text"], strip_verse_numbers=not args.keep_verse_numbers)
    if args.lines:
        text = slice_lines(text, args.lines)
    if args.reflow == "clauses":
        text = reflow_clauses(text)

    if args.list:
        print(f"# {args.page} (revid {parse['revid']})")
        print(f"# metadata: {json.dumps(page_meta, ensure_ascii=False)}")
        print(f"# permalink: {permalink(args.site, args.page, parse['revid'])}")
        for i, ln in enumerate(text.split("\n"), start=1):
            print(f"{i:>4}| {ln}")
        return

    record = build_record(site=args.site, page=args.page, args=args, parse=parse,
                          section_heading=args.section, text=text, page_meta=page_meta)
    ok, reasons = check_rights(record["source_ref"])
    record["rights_check"] = {"clear": ok, "reasons": reasons}
    out = json.dumps(record, ensure_ascii=False, indent=2)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(out + "\n", encoding="utf-8")
        print(f"wrote {path}  (revid {record['revid']}, {record['n_zeilen']} Zeilen, "
              f"rights_clear={ok})")
    else:
        print(out)
    if not ok:
        print("RIGHTS NOT CLEAR: " + "; ".join(reasons), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
