"""Deterministic Wikipedia source-record helper (the History/GPB facts layer).

Records the *citation* for a Wikipedia article — title, canonical URL, a permalink to the
exact revision, the text licence (CC BY-SA 4.0) — as a `ProvenanceSource`. It fetches
**metadata only**, never the article prose: the facts-vs-expression line means we author
worksheet text *from* the facts (no CC BY-SA obligation), and this helper just stamps the
`role="facts"` record so a Wikipedia-sourced fact is fact-checkable at the review gate (the
mandatory-internal rule). No LLM in the path — the precedent of `tools/fetch_*`.

A permalink (`…?title=…&oldid=<revid>`) cites the *exact version* consulted, so the record
stays stable when the live article changes (good provenance, and dated like a "Stand").

    python tools/fetch_wikipedia.py "Wiener Kongress" --lang de
    python tools/fetch_wikipedia.py "Wiener Kongress" --role facts   # default
"""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from datetime import date

from teachersaid.schema.provenance import ProvenanceSource

_SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
_PERMALINK = "https://{lang}.wikipedia.org/w/index.php?title={title}&oldid={oldid}"
_CC_BY_SA = "https://creativecommons.org/licenses/by-sa/4.0/"


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-WP-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_source(title: str, *, lang: str = "de", role: str = "facts",
                 retrieved: str | None = None) -> ProvenanceSource:
    """Build a `ProvenanceSource` for a Wikipedia article from its REST summary. `role`
    defaults to ``facts`` (consult-only, no obligation); pass ``expression`` only if you
    actually embed the article's wording (which inherits CC BY-SA — see the rights gate)."""
    data = _get_json(_SUMMARY.format(lang=lang, title=urllib.parse.quote(title.replace(" ", "_"))))
    canonical = (data.get("titles", {}).get("canonical")
                 or data.get("title") or title).replace("_", " ")
    page_url = data.get("content_urls", {}).get("desktop", {}).get("page")
    oldid = data.get("revision")
    stand = (data.get("timestamp") or "")[:10]            # ISO date of the consulted revision
    url = page_url
    if oldid and page_url:
        url = _PERMALINK.format(lang=lang, title=urllib.parse.quote(canonical.replace(" ", "_")),
                                oldid=oldid)
    return ProvenanceSource(
        title=canonical,
        url=url,
        publisher=f"Wikipedia ({lang})",
        licence="CC-BY-SA-4.0",
        licence_url=_CC_BY_SA,
        retrieved=retrieved or date.today().isoformat(),
        role=role,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("title")
    ap.add_argument("--lang", default="de")
    ap.add_argument("--role", default="facts", choices=["facts", "expression"])
    args = ap.parse_args()
    src = fetch_source(args.title, lang=args.lang, role=args.role)
    print(json.dumps(src.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
