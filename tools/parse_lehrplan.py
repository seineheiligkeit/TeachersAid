#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_lehrplan.py — deterministic extractor for the Austrian AHS Lehrplan (RIS XHTML).

Turns the consolidated RIS document (`Documents/RIS Dokument.html`) into a per-subject
competence catalog under `lehrplan/`, organised around the project's schema v0.3
(`ResolvedCompetence` / `SubjectCompetenceModel` / `FassungRef`).

Scope: the **Unterstufe Pflichtgegenstände** of the Achter Teil only (Oberstufe is deferred).
Competence *text is extracted verbatim* — no paraphrase — because it is legal curriculum text.

Re-run for a future Fassung: drop the new RIS export in place and run again; the structure
(RIS "Absatztyp" CSS classes) is stable across Fassungen. Only the FASSUNG constant below
and, occasionally, the SUBJECT_CODES map need touching.

Dependency: lxml (already present; otherwise `pip install lxml`).

Usage:
    python tools/parse_lehrplan.py                 # all Unterstufe subjects -> lehrplan/*.json
    python tools/parse_lehrplan.py --only PHY      # just one subject code (debugging)
"""
from __future__ import annotations
import argparse, copy, json, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import lxml.html

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Documents" / "RIS Dokument.html"
OUT = ROOT / "lehrplan"

# The Fassung this export corresponds to (schema v0.3 / project-handoff §2).
FASSUNG = {
    "kurztitel": "Lehrplan der allgemeinbildenden höheren Schule (AHS)",
    "bgbl": "BGBl. II Nr. 204/2024",
    "stammfassung": "BGBl. Nr. 88/1985",
    "doknr": "NOR40264237",
    "valid_from": "2024-09-01",
    "valid_to": "2026-08-31",
}

# Canonical 3-char subject codes (curated; stable — these become part of competence IDs).
SUBJECT_CODES = {
    "DEUTSCH": "DEU",
    "ERSTE LEBENDE FREMDSPRACHE": "FS1",
    "ZWEITE LEBENDE FREMDSPRACHE": "FS2",
    "LATEIN": "LAT",
    "MATHEMATIK": "MAT",
    "GEOMETRISCHES ZEICHNEN": "GEZ",
    "DIGITALE GRUNDBILDUNG": "DGB",
    "CHEMIE": "CHE",
    "PHYSIK": "PHY",
    "BIOLOGIE UND UMWELTBILDUNG": "BIO",
    "GESCHICHTE UND POLITISCHE BILDUNG": "GPB",
    "GEOGRAPHIE UND WIRTSCHAFTLICHE BILDUNG": "GWB",
    "MUSIK": "MUS",
    "KUNST UND GESTALTUNG": "KUG",
    "TECHNIK UND DESIGN": "TED",
    "BEWEGUNG UND SPORT": "BUS",
}

# German stopwords skipped when abbreviating a Kompetenzbereich name into a 3-letter code.
KB_STOP = {"und", "der", "die", "das", "von", "im", "in", "für", "zur", "zum",
           "mit", "am", "des", "den", "oder", "the", "an", "auf"}

SECTION_KEYS = [
    ("bildungs- und lehraufgabe", "lehraufgabe"),
    ("didaktische grundsätze", "didaktik"),
    ("zentrale fachliche konzepte", "konzepte"),
    ("kompetenzmodell", "kompetenzmodell"),
    ("kompetenzbeschreibungen", "kompetenzbeschreibungen"),
    ("lehrstoff", "kompetenzbeschreibungen"),
]


def normspace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def drop(el):
    """Remove an element but graft its tail text onto the previous node / parent."""
    parent = el.getparent()
    if parent is None:
        return
    tail = el.tail or ""
    prev = el.getprevious()
    if tail:
        if prev is not None:
            prev.tail = (prev.tail or "") + tail
        else:
            parent.text = (parent.text or "") + tail
    parent.remove(el)


def kb_code(name: str) -> str:
    """Deterministic 3-letter code from a Kompetenzbereich name (first content word)."""
    name = re.sub(r"^Kompetenzbereich\s+", "", name, flags=re.I)
    for w in re.findall(r"[A-Za-zÄÖÜäöüß]+", name):
        if w.lower() in KB_STOP:
            continue
        ascii_w = (unicodedata.normalize("NFKD", w)
                   .encode("ascii", "ignore").decode().upper())
        ascii_w = re.sub(r"[^A-Z]", "", ascii_w)
        if ascii_w:
            return ascii_w[:3]
    return "XXX"


def cls(el) -> str:
    return el.get("class", "") or ""


def is_g1(el) -> bool:
    return "UeberschrG1" in cls(el)


def extract_competence(li):
    """Return (verbatim_text, dimensions[], uebergreifende_themen[]) for a competence <li>."""
    node = copy.deepcopy(li)
    ut, ut_other = [], []
    for s in node.xpath('.//span[contains(@class,"Hoch")]'):
        t = normspace(s.text_content())
        if t.isdigit():
            (ut if 1 <= int(t) <= 13 else ut_other).append(int(t))
    dims = []
    for s in node.xpath('.//span[contains(@class,"Fett")]'):
        t = normspace(s.text_content())
        if re.fullmatch(r"[A-ZÄÖÜ](\s*,\s*[A-ZÄÖÜ])*", t):
            dims += [x.strip() for x in t.split(",")]
    csel = node.xpath('./div[contains(@class,"content")]')
    base = csel[0] if csel else node
    for sel in ('.//span[contains(@class,"sr-only")]',
                './/div[contains(@class,"SymE")]',
                './/span[contains(@class,"Hoch")]',
                './/span[@aria-hidden="true"]'):
        for e in base.xpath(sel):
            drop(e)
    text = normspace(base.text_content())
    # de-duplicate dimension list preserving order
    seen = set()
    dims = [d for d in dims if not (d in seen or seen.add(d))]
    seen = set()
    ut = [u for u in ut if not (u in seen or seen.add(u))]
    seen = set()
    ut_other = [u for u in ut_other if not (u in seen or seen.add(u))]
    return text, dims, ut, ut_other


def li_has_content(li) -> bool:
    return bool(li.xpath('./div[contains(@class,"content")]')
                or li.xpath('.//div[contains(@class,"Aufzaehlung")]'))


class Subject:
    def __init__(self, name, code, stype, variant=None):
        self.name = name
        self.code = code
        self.type = stype          # "pflichtgegenstand" | "zusatz"
        self.variant = variant
        self.prose = []            # [{section,label,text}]
        self.konzepte = []         # [{name,text}]
        self.dimensions = []       # [{code,label,descriptor,items[]}]
        self.competences = []      # [{id,...}]
        self.anwendung = {}        # klasse(int|0) -> [str]
        self.ut_genannt = []
        self.warnings = []
        self._kb_counter = {}      # (klasse,kbcode)->n
        self._kbcode_for_name = {}

    def klassen(self):
        ks = sorted({c["klasse"] for c in self.competences if c["klasse"]})
        return ks

    def next_id(self, klasse, kbname):
        code = self._kbcode_for_name.get(kbname)
        if code is None:
            code = kb_code(kbname)
            # disambiguate collisions within the subject
            existing = {v for v in self._kbcode_for_name.values()}
            if code in existing:
                base, i = code, 2
                while f"{code}{i}" in existing:
                    i += 1
                code = f"{code}{i}"
            self._kbcode_for_name[kbname] = code
        k = klasse if klasse else 0
        key = (k, code)
        self._kb_counter[key] = self._kb_counter.get(key, 0) + 1
        kpart = str(k) if k else "x"
        return f"{self.code}.US.{kpart}.{code}.{self._kb_counter[key]:02d}", code

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "stufe": "Unterstufe",
            "type": self.type,
            "variant": self.variant,
            "klassen": self.klassen(),
            "source_ref": f"Achter Teil / A. Pflichtgegenstände / 1. Unterstufe / {self.name}"
                          + (f" [{self.variant}]" if self.variant else ""),
            "uebergreifende_themen_genannt": self.ut_genannt,
            "competence_model": {"handlungsdimensionen": self.dimensions},
            "zentrale_konzepte": self.konzepte,
            "competences": self.competences,
            "anwendungsbereiche": [
                {"klasse": (k if k else None), "items": v}
                for k, v in sorted(self.anwendung.items())
            ],
            "prose": self.prose,
            "parse_warnings": self.warnings,
        }


def parse():
    raw = SRC.read_text(encoding="utf-8")
    doc = lxml.html.fromstring(raw)
    body = doc.body if doc.body is not None else doc

    subjects = []
    cur: Subject | None = None
    active = False           # inside Unterstufe Pflichtgegenstände block
    seen_pflicht = False
    done = False             # past the Unterstufe Pflicht block — never re-activate
    used_codes = {}

    section = None           # lehraufgabe|didaktik|konzepte|kompetenzmodell|kompetenzbeschreibungen
    klasse = None
    kbname = None
    cur_dim = None           # active Handlungsdimension dict (in kompetenzmodell)
    cur_concept = None       # active concept dict (in konzepte)
    list_mode = None         # "competences" | "anwendung"
    ut_cand = defaultdict(Counter)   # nr -> Counter(label) ; resolved by majority vote

    def finalize():
        nonlocal cur
        if cur is not None:
            subjects.append(cur)
        cur = None

    for el in body.iter():
        tag = el.tag if isinstance(el.tag, str) else None
        if tag is None:
            continue
        c = cls(el)

        # --- footnote ÜT legend: the 1..13 list repeats once per subject; table-cell
        #     noise (e.g. "2 bis 4 Wochenstunden") is rare, so resolve by majority vote ---
        if "TabText" in c:
            t = normspace(el.text_content())
            m = re.match(r"^(\d{1,2})\s*([A-ZÄÖÜ].+)$", t)
            if m:
                n = int(m.group(1))
                if 1 <= n <= 13:
                    ut_cand[n][normspace(m.group(2))] += 1
            continue

        # --- structural backbone: G1 headings drive scope + subject boundaries ---
        if is_g1(el):
            if done:
                continue
            t = normspace(el.text_content())
            tl = t.lower()
            if tl.startswith("a. pflichtgegenst"):
                seen_pflicht = True
                continue
            if seen_pflicht and not active and re.match(r"^1\.\s*unterstufe", tl):
                active = True
                continue
            if active and re.match(r"^2\.\s*oberstufe", tl):
                # end of the Unterstufe Pflichtgegenstände block — stop for good
                finalize()
                active = False
                done = True
                continue
            if active:
                finalize()
                if "LEHRPLANZUSATZ" in t.upper():
                    stype = "zusatz"
                    base = "DAZ"
                else:
                    stype = "pflichtgegenstand"
                    base = SUBJECT_CODES.get(t.upper(), kb_code(t))
                n = used_codes.get(base, 0) + 1
                used_codes[base] = n
                code = base if n == 1 else f"{base}{n}"
                variant = None
                if n > 1:
                    variant = f"Variante {n}"
                cur = Subject(t, code, stype, variant)
                section = klasse = kbname = cur_dim = cur_concept = list_mode = None
                if n > 1:
                    cur.warnings.append(
                        f"Duplicate subject heading '{t}' — assigned code {code}; "
                        "QA should resolve the Schulform/variant distinction.")
            continue

        if not active or cur is None:
            continue

        # --- competence / application bullets ---
        if tag == "li":
            if not li_has_content(el):
                continue
            text, dims, ut, ut_other = extract_competence(el)
            if not text:
                continue
            level = el.get("aria-level")
            if section == "kompetenzmodell" and cur_dim is not None:
                cur_dim["items"].append(text)
            elif list_mode == "anwendung":
                cur.anwendung.setdefault(klasse if klasse else 0, []).append(text)
            else:
                cid, kbc = cur.next_id(klasse, kbname or "Allgemein")
                comp = {
                    "id": cid,
                    "klasse": klasse,
                    "kompetenzbereich": kbname,
                    "kompetenzbereich_code": kbc,
                    "text": text,
                    "dimensions": dims,
                    "uebergreifende_themen": ut,
                    "aria_level": int(level) if level and level.isdigit() else None,
                    "source_ref": f"{cur.name} / {('%d. Klasse' % klasse) if klasse else 'Klasse n/a'} / "
                                  f"{kbname or '—'}",
                }
                if ut_other:
                    # superscripts outside 1..13 — likely exponents/other footnotes, not ÜT refs
                    comp["superscripts_other"] = ut_other
                cur.competences.append(comp)
            continue

        # --- headings & paragraphs (h1-h4, p) ---
        if tag in ("h1", "h2", "h3", "h4", "p"):
            t = normspace(el.text_content())
            if not t:
                continue
            tl = t.lower()

            # section switch?
            matched_section = None
            for key, name in SECTION_KEYS:
                if tl.startswith(key) or key in tl[:40]:
                    matched_section = name
                    break

            is_heading = ("ErlUeberschr" in c) or tag in ("h2", "h3", "h4")

            # Klasse marker (e.g. "2. Klasse:")
            mk = re.match(r"^(\d)\.\s*klasse\b", tl)
            if mk and ("ErlText" in c or "Erl" in c or is_heading or tag == "p"):
                klasse = int(mk.group(1))
                kbname = None
                list_mode = None
                cur_dim = None
                continue

            if matched_section and is_heading:
                section = matched_section
                cur_dim = None
                cur_concept = None
                list_mode = None
                cur.prose.append({"section": section, "label": t, "text": ""})
                continue

            # Anwendungsbereiche marker
            if re.match(r"^anwendungsbereich", tl):
                list_mode = "anwendung"
                continue

            # "Die Schülerinnen und Schüler können"
            if tl.startswith("die schülerinnen und schüler können"):
                if section != "kompetenzmodell":
                    list_mode = "competences"
                continue

            # ÜbergreifendeThemen sentence
            if "übergreifende themen" in tl and "greift" in tl:
                node = copy.deepcopy(el)
                for s in node.xpath('.//span[contains(@class,"Hoch")]'):
                    tt = normspace(s.text_content())
                    if tt.isdigit():
                        cur.ut_genannt.append(int(tt))
                cur.ut_genannt = sorted(set(cur.ut_genannt))
                cur.prose.append({"section": "didaktik", "label": "Übergreifende Themen", "text": t})
                continue

            if is_heading:
                # Kompetenzbereich heading
                if tl.startswith("kompetenzbereich"):
                    kbname = re.sub(r"^Kompetenzbereich\s+", "", t).strip()
                    list_mode = "competences"
                    continue
                # Handlungsdimension heading inside Kompetenzmodell, e.g. "Fachwissen anwenden (W)"
                if section == "kompetenzmodell":
                    md = re.search(r"\(([A-ZÄÖÜ])\)\s*$", t)
                    if md:
                        cur_dim = {"code": md.group(1),
                                   "label": re.sub(r"\s*\([A-ZÄÖÜ]\)\s*$", "", t).strip(),
                                   "descriptor": "", "items": []}
                        cur.dimensions.append(cur_dim)
                        continue
                # concept name inside Zentrale fachliche Konzepte
                if section == "konzepte":
                    cur_concept = {"name": t, "text": ""}
                    cur.konzepte.append(cur_concept)
                    continue
                # otherwise a generic sub-heading
                cur.prose.append({"section": section or "_", "label": t, "text": ""})
                continue

            # plain paragraph (Abs / ErlText prose) -> attach to current context
            if section == "kompetenzmodell" and cur_dim is not None and not cur_dim["descriptor"]:
                cur_dim["descriptor"] = t
            elif section == "konzepte" and cur_concept is not None:
                cur_concept["text"] = (cur_concept["text"] + " " + t).strip()
            elif cur.prose and section in ("lehraufgabe", "didaktik", "konzepte", "kompetenzmodell"):
                cur.prose[-1]["text"] = (cur.prose[-1]["text"] + " " + t).strip()
            else:
                cur.prose.append({"section": section or "_", "label": "", "text": t})

    finalize()
    ut_legend = {n: ut_cand[n].most_common(1)[0][0] for n in sorted(ut_cand)}
    return subjects, ut_legend


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="restrict to one subject code (e.g. PHY)")
    args = ap.parse_args()

    subjects, ut_legend = parse()
    OUT.mkdir(exist_ok=True)

    registry = []
    for s in subjects:
        if args.only and s.code != args.only:
            continue
        d = s.to_dict()
        (OUT / f"{s.code}.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        registry.append({
            "code": s.code, "name": s.name, "type": s.type, "variant": s.variant,
            "klassen": s.klassen(), "n_competences": len(s.competences),
            "file": f"{s.code}.json",
        })

    if not args.only:
        meta = {
            "fassung": FASSUNG,
            "stufe": "Unterstufe",
            "scope": "Achter Teil — A. Pflichtgegenstände — 1. Unterstufe",
            "uebergreifende_themen": [
                {"nr": n, "label": ut_legend[n]} for n in sorted(ut_legend)
            ],
            "id_scheme": "<SUBJ>.US.<KLASSE>.<KB>.<nn>  (KLASSE=1..4 or x; KB=3-letter code from Kompetenzbereich)",
            "subjects": registry,
        }
        (OUT / "_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # summary to stdout
    print(f"{'CODE':6} {'KL':10} {'#COMP':>5}  NAME")
    total = 0
    for r in registry:
        total += r["n_competences"]
        print(f"{r['code']:6} {str(r['klassen']):10} {r['n_competences']:5d}  {r['name']}"
              + (f"  [{r['variant']}]" if r["variant"] else ""))
    print(f"\n{len(registry)} subjects, {total} competences, "
          f"{len(ut_legend)} übergreifende-Themen legend entries")


if __name__ == "__main__":
    main()
