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
    """Remove an element, grafting its tail onto the previous node / parent with a
    separating space (collapsed later by normspace) so stripping a mid-sentence
    superscript can't fuse two words, e.g. 'Beziehungen<sup>6</sup> verwenden'."""
    parent = el.getparent()
    if parent is None:
        return
    graft = " " + (el.tail or "")
    prev = el.getprevious()
    if prev is not None:
        prev.tail = (prev.tail or "") + graft
    else:
        parent.text = (parent.text or "") + graft
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
    # a single Hoch span may hold several refs, e.g. "2, 7" or "8, 13" — take every number
    for s in node.xpath('.//span[contains(@class,"Hoch")]'):
        for d in re.findall(r"\d+", s.text_content() or ""):
            n = int(d)
            (ut if 1 <= n <= 13 else ut_other).append(n)
    dims = []
    for s in node.xpath('.//span[contains(@class,"Fett")]'):
        t = normspace(s.text_content())
        if re.fullmatch(r"[A-ZÄÖÜ](\s*,\s*[A-ZÄÖÜ])*", t):
            dims += [x.strip() for x in t.split(",")]
    csel = node.xpath('./div[contains(@class,"content")]')
    base = csel[0] if csel else node
    # NB: do NOT strip aria-hidden spans — in some subjects (e.g. DGB "(I) …" bullets)
    # the *entire* competence text sits inside an aria-hidden span. The bullet dash is
    # inside the SymE marker div, which we strip; Hoch superscripts are stripped explicitly.
    for sel in ('.//span[contains(@class,"sr-only")]',
                './/div[contains(@class,"SymE")]',
                './/span[contains(@class,"Hoch")]'):
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
        self.anwendung = {}        # klasse(int|0) -> [str]  (Anwendungsbereiche / Lehrstoff)
        self.vorschlaege = {}      # klasse(int|0) -> [str]  (optional digital-tool suggestions, MINT)
        self.ut_genannt = []
        self.warnings = []
        self._kb_counter = {}      # (klasse,kbcode)->n
        self._kbcode_for_name = {}

    def klassen(self):
        ks = {c["klasse"] for c in self.competences if c["klasse"]}
        ks |= {k for k in self.anwendung if k}          # cross-class subjects carry grades only here
        return sorted(ks)

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
            "vorschlaege_digitale_technologien": [
                {"klasse": (k if k else None), "items": v}
                for k, v in sorted(self.vorschlaege.items())
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
    list_mode = None         # "competences" | "anwendung" | "vorschlaege"
    anwendung_global = False # True when Anwendungsbereiche span all Klassen (cross-class subjects)
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
                anwendung_global = False
                if n > 1:
                    cur.warnings.append(
                        f"Duplicate subject heading '{t}' — assigned code {code}; "
                        "QA should resolve the Schulform/variant distinction.")
            continue

        if not active or cur is None:
            continue

        # --- bullets: route by section + list_mode ---
        if tag == "li":
            if not li_has_content(el):
                continue
            text, dims, ut, ut_other = extract_competence(el)
            if not text:
                continue
            # competences live ONLY in the Kompetenzbeschreibungen section and only while
            # not collecting Anwendungsbereiche / Vorschläge — this kills the pre-class leak
            if section == "kompetenzbeschreibungen" and list_mode not in ("anwendung", "vorschlaege"):
                level = el.get("aria-level")
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
                    "source_ref": f"{cur.name} / {('%d. Klasse' % klasse) if klasse else 'alle Klassen'} / "
                                  f"{kbname or '—'}",
                }
                if ut_other:
                    comp["superscripts_other"] = ut_other   # likely exponents/other footnotes
                cur.competences.append(comp)
            elif list_mode == "anwendung":
                cur.anwendung.setdefault(klasse or 0, []).append(text)
            elif list_mode == "vorschlaege":
                cur.vorschlaege.setdefault(klasse or 0, []).append(text)
            elif section == "kompetenzmodell" and cur_dim is not None:
                cur_dim["items"].append(text)
            elif section == "konzepte":
                cur.konzepte.append({"name": "", "text": text})
            else:
                cur.prose.append({"section": section or "_", "label": "", "text": text})
            continue

        # --- headings & paragraphs (h1-h4, p) ---
        if tag in ("h1", "h2", "h3", "h4", "p"):
            t = normspace(el.text_content())
            if not t:
                continue
            tl = t.lower()
            is_heading = ("ErlUeberschr" in c) or tag in ("h2", "h3", "h4")

            # Klasse marker — may carry an inline Kompetenzbereich on the same line, e.g.
            # DGB "1. Klasse: Kompetenzbereich Orientierung: …". The first Klasse marker also
            # marks the start of the competence-bearing part for class-first subjects.
            mk = re.match(r"^(\d)\.\s*klasse\b\s*:?\s*(.*)$", t, re.I)
            if mk and section in ("kompetenzbeschreibungen", "kompetenzmodell", None):
                section = "kompetenzbeschreibungen"
                klasse = int(mk.group(1))
                cur_dim = None
                rest = re.sub(r"^Kompetenzbereich\s+", "", mk.group(2).strip(" :"), flags=re.I).strip()
                kbname = rest or None
                list_mode = "anwendung" if anwendung_global else "competences"
                continue

            # section switch (kompetenzbeschreibungen/lehrstoff may be a plain Abs; others = headings)
            matched_section = None
            for key, name in SECTION_KEYS:
                if tl.startswith(key) or key in tl[:48]:
                    matched_section = name
                    break
            if matched_section == "kompetenzbeschreibungen":
                section = "kompetenzbeschreibungen"
                cur_dim = cur_concept = None
                list_mode = "competences"
                cur.prose.append({"section": section, "label": t, "text": ""})
                continue
            if matched_section and is_heading:
                section = matched_section
                cur_dim = cur_concept = None
                list_mode = None
                cur.prose.append({"section": section, "label": t, "text": ""})
                continue

            # Anwendungsbereiche marker. It is "global" (Lehrstoff for ALL Klassen, re-walking
            # them) when it precedes any Klasse OR its own text names a Klasse range, e.g.
            # "Anwendungsbereiche (1. bis 4. Klasse)" (BIO, MAT) / "(3. und 4. Klasse)" (CHE2).
            # A bare per-Klasse "Anwendungsbereiche" (Physik) is NOT global.
            if re.match(r"^anwendungsbereich", tl):
                list_mode = "anwendung"
                if klasse is None or re.search(r"\d\s*\.?\s*(?:bis|und)\s*\d\s*\.?\s*klasse", tl):
                    anwendung_global = True
                continue
            # optional "Vorschläge für den Einsatz digitaler Technologien" (MINT) — not competences
            if re.match(r"^vorschl[aä]ge", tl):
                list_mode = "vorschlaege"
                continue

            if tl.startswith("die schülerinnen und schüler können"):
                if section == "kompetenzbeschreibungen" and list_mode not in ("anwendung", "vorschlaege"):
                    list_mode = "competences"
                continue

            # "Dieser Lehrplan greift folgende übergreifende Themen auf: …"
            if "übergreifende themen" in tl and "greift" in tl:
                node = copy.deepcopy(el)
                for s in node.xpath('.//span[contains(@class,"Hoch")]'):
                    for d in re.findall(r"\d+", s.text_content() or ""):
                        cur.ut_genannt.append(int(d))
                cur.ut_genannt = sorted(set(x for x in cur.ut_genannt if 1 <= x <= 13))
                cur.prose.append({"section": "didaktik", "label": "Übergreifende Themen", "text": t})
                continue

            if is_heading:
                if section == "kompetenzbeschreibungen":
                    if anwendung_global:
                        # global Anwendungsbereiche section (MAT/BIO/CHE2): it re-walks the
                        # Klassen and reuses the "Kompetenzbereich N: …" headings as Lehrstoff
                        # group labels — none of it is competences.
                        continue
                    if tl.startswith("kompetenzbereich"):
                        # explicit KB heading — always (re)opens competences, even mid-Anwendung
                        # (DGB interleaves Anwendungsbereiche between KBs within a Klasse)
                        kbname = re.sub(r"^Kompetenzbereich\s+", "", t, flags=re.I).strip()
                        list_mode = "competences"
                        continue
                    if list_mode in ("anwendung", "vorschlaege"):
                        # prefix-less heading inside a Lehrstoff block = sub-label; keep mode
                        # (CHE2 "Einführung …", MAT content-area labels)
                        continue
                    # prefix-less heading while collecting competences = a Kompetenzbereich
                    kbname = t.strip()
                    list_mode = "competences"
                    continue
                # explicit "Kompetenzbereich …" outside the section opens it
                if tl.startswith("kompetenzbereich"):
                    section = "kompetenzbeschreibungen"
                    kbname = re.sub(r"^Kompetenzbereich\s+", "", t, flags=re.I).strip()
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
                if section == "konzepte":
                    cur_concept = {"name": t, "text": ""}
                    cur.konzepte.append(cur_concept)
                    continue
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

    # curated SubjectCompetenceModel overlay (hand-authored from QA) — fills handlungsdimensionen,
    # content_areas, modality, and variant labels the parser can't reliably auto-detect.
    models = {}
    mf = OUT / "subject_models.json"
    if mf.exists():
        models = {k: v for k, v in json.loads(mf.read_text(encoding="utf-8")).items()
                  if not k.startswith("_")}

    registry = []
    for s in subjects:
        if args.only and s.code != args.only:
            continue
        d = s.to_dict()
        ov = models.get(s.code)
        if ov:
            auto = {dd["code"]: dd for dd in d["competence_model"]["handlungsdimensionen"]}
            dims = []
            for od in ov.get("dimensions", []):
                m = dict(od)
                a = auto.get(od["code"], {})
                if a.get("descriptor"):
                    m.setdefault("descriptor", a["descriptor"])
                if a.get("items"):
                    m.setdefault("items", a["items"])
                dims.append(m)
            d["competence_model"] = {
                "handlungsdimensionen": dims,
                "content_areas": ov.get("content_areas"),
                "notes": ov.get("notes", ""),
            }
            if ov.get("variant"):
                d["variant"] = ov["variant"]
        (OUT / f"{s.code}.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        registry.append({
            "code": d["code"], "name": d["name"], "type": d["type"], "variant": d["variant"],
            "klassen": d["klassen"], "n_competences": len(d["competences"]),
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
