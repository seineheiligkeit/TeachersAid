#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_lehrplan_oberstufe.py — deterministic extractor for the AHS **Oberstufe** (RIS XHTML).

Sibling of tools/parse_lehrplan.py (Unterstufe). The Oberstufe is structurally different and
each competence is captured with one of two **kinds**:

  * kind="descriptor" — the abstract Kompetenzmodell competences (the Handlungs-/Kompetenz-
    bereich "Die SuS können …" statements: W/E/S for the sciences, Übersetzungs-/Interpretations-
    kompetenzen for Latein/Griechisch, the 5 Ethik-Kompetenzbereiche, the Maths dimensions).
    Grade-independent (klasse=null); these are the load-bearing competences for the
    languages/humanities.
  * kind="lehrstoff" — the per-semester Lehrstoff / Inhaltsbereiche / Anwendungsbereiche
    (the content the descriptors are exercised on); carries klasse + semester + kompetenzmodul.

Both are emitted so a worksheet can `serve` either layer. Structural handling:
  - Subjects (UeberschrG1); the model section is an `ErlUeberschrL` matching MODEL_RE (or, for
    Physik, the "W:/E:/S:" ErlText headings); the Lehrstoff section is any "…Lehrstoff…" heading
    or the first "N. Klasse" marker.
  - Competence items are `li` bullets OR `Abs` paragraphs (subject-dependent); the Inhaltsbereich
    is a topic heading (Math/Chemie), a bold lead-in (Physik), or a Fertigkeit label (FS).

Output: lehrplan/oberstufe/<CODE>.json. Text is extracted VERBATIM (legal curriculum text).

Usage:
    python tools/parse_lehrplan_oberstufe.py                 # all Oberstufe Pflichtgegenstände
    python tools/parse_lehrplan_oberstufe.py --only MAT PHY CHE BIO FSP LAT
"""
from __future__ import annotations
import argparse, json, re, unicodedata
from pathlib import Path
import lxml.html

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Documents" / "RIS Dokument.html"
OUT = ROOT / "lehrplan" / "oberstufe"

FASSUNG = {
    "kurztitel": "Lehrplan der allgemeinbildenden höheren Schule (AHS)",
    "bgbl": "BGBl. II Nr. 204/2024",
    "stammfassung": "BGBl. Nr. 88/1985",
    "doknr": "NOR40264237",
    "valid_from": "2024-09-01",
    "valid_to": "2026-08-31",
}

SUBJECT_CODES = {
    "ETHIK": "ETH", "DEUTSCH": "DEU",
    "LEBENDE FREMDSPRACHE (ERSTE, ZWEITE)": "FSP", "LEBENDE FREMDSPRACHE": "FSP",
    "LATEIN": "LAT", "GRIECHISCH": "GRI",
    "GESCHICHTE UND POLITISCHE BILDUNG": "GPB",
    "GEOGRAPHIE UND WIRTSCHAFTLICHE BILDUNG": "GWB",
    "MATHEMATIK": "MAT", "BIOLOGIE UND UMWELTBILDUNG": "BIO",
    "CHEMIE": "CHE", "PHYSIK": "PHY",
    "DARSTELLENDE GEOMETRIE": "DGE", "HAUSHALTSÖKONOMIE UND ERNÄHRUNG": "HOE",
    "PSYCHOLOGIE UND PHILOSOPHIE": "PUP", "INFORMATIK": "INF",
    "MUSIK": "MUS", "KUNST UND GESTALTUNG": "KUG", "BEWEGUNG UND SPORT": "BUS",
}
KNOWN_SUBJECTS = set(SUBJECT_CODES)

KB_STOP = {"und", "der", "die", "das", "von", "im", "in", "für", "zur", "zum", "mit", "am",
           "des", "den", "oder", "the", "an", "auf", "bzw", "sowie"}

KLASSE_RE = re.compile(r"^\s*(\d)\.\s*Klasse", re.I)
SEM_HEAD_RE = re.compile(r"^\s*(\d)\.\s*Semester", re.I)
KM_RE = re.compile(r"Kompetenzmodul\s*(\d)", re.I)
INLINE_SEM_RE = re.compile(r"\((\d)\.\s*(?:und\s*(\d)\.\s*)?Semester\)", re.I)
BULLET_RE = re.compile(r"^[\-–—•\s]*Strichaufz[äa]hlung\s*|^[\-–—•]\s*", re.I)
MODEL_RE = re.compile(r"kompetenzmodell|mathematische kompetenzen|kompetenzbeschreibungen", re.I)
WES_RE = re.compile(r"^\s*([WES]):\s")                  # Physik "W: Fachwissen"
DIM_CODE_RE = re.compile(r"^\s*([WES]\d+):(?:\s*[WES]\d+:)?\s*")  # BIO "W1:W1:…" / "W1:…"
INTRO_RE = re.compile(
    r"^\s*(In diesem Bereich|Die Schülerinnen und Schüler (können|zeigen)|Im Rahmen|"
    r"Das Kompetenzmodell|Die (Inhalts|Handlungs|Anforderungs)dimension|Um den)", re.I)
MODEL_END_RE = re.compile(r"^\s*(Die Anforderungsniveaus|Darüber hinaus|Schularbeit|"
                          r"Die Anforderungsdimension)", re.I)
FERTIGKEIT = {"hören", "lesen", "sprechen", "schreiben",
              "an gesprächen teilnehmen und zusammenhängendes sprechen"}
GENERIC_TOPIC = {"lerninhalte", "lehrstoff"}


def normspace(s): return re.sub(r"\s+", " ", (s or "")).strip()
def cls(el): return el.get("class", "") or ""
def is_g1(el): return "UeberschrG1" in cls(el)
def is_erlueber(el): return "ErlUeberschr" in cls(el)


def kb_code(name: str) -> str:
    name = re.sub(r"^(Kompetenzbereich|Inhaltsbereich)\s+", "", name, flags=re.I)
    for w in re.findall(r"[A-Za-zÄÖÜäöüß]+", name):
        if w.lower() in KB_STOP:
            continue
        ascii_w = unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode().upper()
        ascii_w = re.sub(r"[^A-Z]", "", ascii_w)
        if ascii_w:
            return ascii_w[:3]
    return "XXX"


class Subject:
    def __init__(self, name, code):
        self.name = name
        self.code = code
        self.prose_sections = {}
        self.competences = []
        self.warnings = []
        self._kbcode_for_name = {}
        self._counter = {}

    def next_id(self, klasse, kbname):
        code = self._kbcode_for_name.get(kbname)
        if code is None:
            code = kb_code(kbname)
            existing = set(self._kbcode_for_name.values())
            if code in existing:
                i = 2
                while f"{code}{i}" in existing:
                    i += 1
                code = f"{code}{i}"
            self._kbcode_for_name[kbname] = code
        k = klasse if klasse else 0
        self._counter[(k, code)] = self._counter.get((k, code), 0) + 1
        kpart = str(k) if k else "x"
        return f"{self.code}.OS.{kpart}.{code}.{self._counter[(k, code)]:02d}", code

    def add(self, *, klasse, semesters, km, kb, text, kind, dims, variant, ref):
        cid, kbc = self.next_id(klasse or 0, kb)
        self.competences.append({
            "id": cid, "klasse": klasse, "semester": semesters, "kompetenzmodul": km,
            "kompetenzbereich": kb, "kompetenzbereich_code": kbc, "text": text,
            "kind": kind, "dimensions": dims, "variant": variant, "source_ref": ref,
        })

    def klassen(self):
        return sorted({c["klasse"] for c in self.competences if c["klasse"]})

    def to_dict(self):
        n_desc = sum(1 for c in self.competences if c["kind"] == "descriptor")
        return {
            "code": self.code, "name": self.name, "stufe": "Oberstufe",
            "type": "pflichtgegenstand", "variant": None,
            "klassen": self.klassen(), "semester_structure": True,
            "source_ref": f"Achter Teil / A. Pflichtgegenstände / 2. Oberstufe / {self.name}",
            "competence_model": {"handlungsdimensionen": [], "content_areas": None,
                                 "notes": "kind='descriptor' = Kompetenzmodell competences "
                                          "(grade-independent); kind='lehrstoff' = per-semester "
                                          "Inhaltsbereiche. Curate subject_models from the "
                                          "descriptors + prose_sections."},
            "prose_sections": self.prose_sections,
            "competences": self.competences,
            "n_competences": len(self.competences),
            "n_descriptor": n_desc, "n_lehrstoff": len(self.competences) - n_desc,
            "parse_warnings": self.warnings,
        }


def _wes_letter(area: str):
    m = re.match(r"^\s*([WES])\b", area or "")
    return [m.group(1)] if m else []


def parse(only=None):
    doc = lxml.html.fromstring(SRC.read_text(encoding="utf-8"))
    body = doc.body if doc.body is not None else doc

    in_achter = ober = done = False
    subjects, cur = [], None
    mode = None                       # None | "model" | "lehrstoff"
    klasse = semesters = km = topic = variant = dim_area = None
    cur_section = None
    skip = set()

    def finalize():
        nonlocal cur
        if cur is not None and (only is None or cur.code in only):
            subjects.append(cur)
        cur = None

    for el in body.iter():
        if el in skip:
            continue
        c = cls(el); tag = el.tag if isinstance(el.tag, str) else ""

        # ---- G1: scope + subject / variant boundaries ----
        if is_g1(el):
            t = normspace(el.text_content()); tl = t.lower(); up = t.upper()
            for d in el.iterdescendants(): skip.add(d)
            if done:
                continue
            if re.search(r"achter teil", tl):
                in_achter = True; continue
            if in_achter and re.match(r"^2\.\s*oberstufe", tl):
                ober = True; continue
            if not (in_achter and ober):
                continue
            if re.match(r"^b[\.\)]", tl) or "wahlpflicht" in tl or "verbindliche übung" in tl:
                finalize(); done = True; continue
            if re.match(r"^a[\.\)]", tl) or "pflichtgegenst" in tl:
                continue
            if up in KNOWN_SUBJECTS:
                finalize()
                cur = Subject(t, SUBJECT_CODES[up])
                mode = None; klasse = semesters = km = topic = variant = dim_area = None
                cur_section = None
            elif cur is not None:
                variant = t                       # Lehrstoff variant sub-heading (Physik Wochenstunden, FS Sprache)
                cur.warnings.append(f"variant sub-section: {t!r}")
            continue

        if not (ober and cur is not None) or done:
            continue

        # ---- ErlUeberschrL: section headings ----
        if is_erlueber(el):
            t = normspace(el.text_content())
            for d in el.iterdescendants(): skip.add(d)
            if "lehrstoff" in t.lower():
                mode = "lehrstoff"; klasse = semesters = km = topic = None; dim_area = None
                mvar = re.search(r"\(([^)]*j[äa]hrig[^)]*)\)", t)
                variant = mvar.group(1).strip() if mvar else None
                continue
            if MODEL_RE.search(t):
                mode = "model"; dim_area = None; cur_section = t
                continue
            if mode == "model":
                mode = None                       # any other ErlUeberschr ends the model section
            if mode == "lehrstoff":
                topic = None if t.lower() in GENERIC_TOPIC else t
            else:
                cur_section = t; cur.prose_sections.setdefault(t, "")
            continue

        # ---- ErlText: klasse / semester / topic / dimension markers ----
        if "ErlText" in c:
            t = normspace(el.text_content())
            for d in el.iterdescendants(): skip.add(d)
            mk = KLASSE_RE.match(t)
            if mk:
                mode = "lehrstoff"; klasse = int(mk.group(1)); semesters = None; km = None; topic = None
                msi = INLINE_SEM_RE.search(t)
                if msi: semesters = [int(x) for x in msi.groups() if x]
                mkm = KM_RE.search(t)
                if mkm: km = int(mkm.group(1))
                continue
            if mode == "lehrstoff" and SEM_HEAD_RE.match(t):
                semesters = [int(SEM_HEAD_RE.match(t).group(1))]; topic = None
                mkm = KM_RE.search(t)
                if mkm: km = int(mkm.group(1))
                continue
            if WES_RE.match(t):                   # Physik W:/E:/S: dimension heading
                mode = "model"; dim_area = t; continue
            if mode == "model":
                if MODEL_END_RE.match(t):
                    mode = None; continue
                if not INTRO_RE.match(t):
                    dim_area = t
                continue
            if mode == "lehrstoff":
                topic = None if t.lower() in GENERIC_TOPIC else t
                continue
            if cur_section:
                cur.prose_sections[cur_section] = (cur.prose_sections[cur_section] + " " + t).strip()
            continue

        # ---- competence items (li bullets / Abs paragraphs) ----
        is_item = (tag == "li") or ("Abs" in c)
        if not is_item:
            continue

        if mode == "model":
            text = normspace(el.text_content())
            if INTRO_RE.match(text) or ("Abs" in c and len(text) > 220):
                for d in el.iterdescendants(): skip.add(d); continue
            dims = []
            mdc = DIM_CODE_RE.match(text)
            if mdc:
                dims = [mdc.group(1)[0]]
                text = DIM_CODE_RE.sub("", text)
            text = BULLET_RE.sub("", text).strip()
            for d in el.iterdescendants(): skip.add(d)
            if len(text) < 8:
                continue
            area = dim_area or "Kompetenzmodell"
            if not dims:
                dims = _wes_letter(area)
            cur.add(klasse=None, semesters=None, km=None, kb=area, text=text,
                    kind="descriptor", dims=dims, variant=None,
                    ref=f"{cur.name} / Kompetenzmodell / {area}")
            continue

        if mode == "lehrstoff" and klasse:
            if "Abs" in c and normspace(el.text_content()).lower() in FERTIGKEIT:
                topic = normspace(el.text_content())          # FS Fertigkeit sub-heading
                for d in el.iterdescendants(): skip.add(d)
                continue
            kb = topic
            if not kb:
                fett = el.xpath('.//span[contains(@class,"Fett")]')
                if fett:
                    kb = normspace(fett[0].text_content()).rstrip(":").strip()
            text = normspace(el.text_content())
            text = BULLET_RE.sub("", text).strip()
            for d in el.iterdescendants(): skip.add(d)
            if len(text) < 8:
                continue
            if not kb or kb.lower() in GENERIC_TOPIC:
                mcol = re.match(r"^(.{2,60}?):\s", text)
                kb = (mcol.group(1).strip() if mcol
                      else (f"Kompetenzmodul {km}" if km else f"{klasse}. Klasse"))
            cur.add(klasse=klasse, semesters=semesters, km=km, kb=kb, text=text,
                    kind="lehrstoff", dims=[], variant=variant,
                    ref=f"{cur.name} / {klasse}. Klasse / {kb}" + (f" [{variant}]" if variant else ""))
            continue

    finalize()
    return subjects


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", help="subject codes (e.g. MAT PHY CHE)")
    args = ap.parse_args()
    only = set(args.only) if args.only else None
    OUT.mkdir(parents=True, exist_ok=True)
    subjects = parse(only)
    print(f"Parsed {len(subjects)} Oberstufe subject(s):")
    written = {}
    for s in subjects:
        d = s.to_dict()
        if d["n_competences"] == 0:
            print(f"  {s.code:5} {s.name[:36]:36} — 0 competences, skipped (out of scope)")
            continue
        n = written.get(s.code, 0) + 1
        written[s.code] = n
        fname = s.code if n == 1 else f"{s.code}{n}"
        if n > 1:
            d["code"] = fname; d["variant"] = f"Variante {n} (Schulform)"
        (OUT / f"{fname}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        kb = sorted({c["kompetenzbereich"] for c in s.competences})
        print(f"  {fname:5} {s.name[:34]:34} kl={d['klassen']!s:14} "
              f"desc={d['n_descriptor']:3} lehrst={d['n_lehrstoff']:3} KB={len(kb):2} warns={len(s.warnings)}")


if __name__ == "__main__":
    main()
