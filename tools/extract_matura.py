"""Deterministic extractor for SRDP (Zentralmatura) exam PDFs → structured JSON.

No LLM in the path (the ``parse_lehrplan`` / ``fetch_*`` precedent). Turns the official
**Aufgabenheft** (``…_AU.pdf``) and **Korrekturheft** (``…_LO.pdf``) into per-task records
we can use for **calibration (#1)** and as a Matura-orientation idea corpus over the whole
~10-year archive (the filename convention `KL25_PT1_AHS_MAT_00_DE_{AU,LO}` is stable).

The mathematical content is largely vector/image, so we extract **structure + text**, not
the formulas: per task — number, title, context/instruction, the **operator** and its
**answer format**, the **point scheme**, the **Grundkompetenz** (where the Korrekturheft
prints it — only on genuinely open-format tasks), plus the exam's **Beurteilungsschlüssel**.

The pure parsing functions take strings (unit-tested offline); only ``read_pdf_text`` and
``main`` touch PyMuPDF / the filesystem.

    python tools/extract_matura.py <pdf> [<pdf> ...]      # AU+LO of the same exam are merged
    python tools/extract_matura.py <pdf> -o out.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --- filename metadata ----------------------------------------------------------------
# Two conventions seen across the archive:
#   modern (≥KL20):  KL25_PT1_AHS_MAT_00_DE_AU   (one file; both Teile inside)
#   early  (KL14):   KL14_PT1_AHS_MAT_T1_CC_AU   (Teil 1 / Teil 2 in SEPARATE files)
# The 6th slot is the variant ("00" | "T1" | "T2" | "SR"); the 7th is the language —
# "DE"/"CC" for Math/Deutsch, but a CEFR code ("B1" | "B2" | "A2") for the language exams,
# so the slot is alphanumeric, not just letters.
_NAME_RE = re.compile(
    r"([A-Za-z]{2})(\d{2})_PT(\d)_([A-Z]{3})_([A-Z]{3})_([A-Za-z0-9]+)_([A-Za-z0-9]{2})_(AU|LO)",
    re.IGNORECASE,
)
_TERMIN = {"KL": "Haupttermin", "NT": "Nebentermin", "WT": "Wintertermin"}


def parse_filename(name: str) -> dict | None:
    """Pull exam metadata from a stable SRDP filename, e.g.
    ``KL25_PT1_AHS_MAT_00_DE_AU`` → 2025, Haupttermin, AHS, MAT, DE, Aufgaben.

    ``file_teil`` is 1/2 when the file is a single-Teil booklet (early ``_T1_``/``_T2_``
    naming), else None (modern combined file — the Teil split is in the task headers)."""
    m = _NAME_RE.search(os.path.basename(name))
    if not m:
        return None
    termin, yy, pt, schulform, subject, variant, lang, kind = m.groups()
    tm = re.fullmatch(r"[Tt](\d)", variant)
    return {
        "termin": _TERMIN.get(termin.upper(), termin.upper()),
        "year": 2000 + int(yy),
        "pruefungsteil": int(pt),
        "schulform": schulform.upper(),
        "subject": subject.upper(),
        "variant": variant.upper(),
        "file_teil": int(tm.group(1)) if tm else None,
        "language": lang.upper(),
        "kind": "aufgaben" if kind.upper() == "AU" else "loesungen",
    }


# --- header / task splitting ----------------------------------------------------------
_HEADER_RE = re.compile(r"S\.\s*\d+\s*/\s*\d+")           # "S. 3/36" page marker
_RUNHEAD_RE = re.compile(r"/\s*AHS\s*/|/\s*BHS\s*/")      # "… / AHS / Mathematik" run-head
# Task header: "Aufgabe N" optionally followed by "(Teil 2)" / "(Teil 2, Best-of-Wertung)".
_TASK_RE = re.compile(r"(?m)^\s*Aufgabe\s+(\d+)\b[ \t]*(\([^)]*\))?\s*$")


def strip_headers(text: str) -> str:
    """Drop the repeating page header/footer lines so titles & content line up."""
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            out.append("")
            continue
        if _HEADER_RE.search(s) or _RUNHEAD_RE.search(s):
            continue
        out.append(ln)
    return "\n".join(out)


def teil_info(header_paren: str | None) -> dict:
    """Teil / Best-of flags from a task header's trailing parenthetical (e.g. '(Teil 2,
    Best-of-Wertung)')."""
    h = header_paren or ""
    return {"teil": 2 if "Teil 2" in h else 1, "best_of": "Best-of" in h}


def split_tasks(text: str) -> dict[int, dict]:
    """Split a heft's full (header-stripped) text into {task_nr: {header, block}}."""
    cleaned = strip_headers(text)
    marks = list(_TASK_RE.finditer(cleaned))
    blocks: dict[int, dict] = {}
    for i, m in enumerate(marks):
        nr = int(m.group(1))
        end = marks[i + 1].start() if i + 1 < len(marks) else len(cleaned)
        blocks[nr] = {"header": (m.group(2) or "").strip(),
                      "block": cleaned[m.end():end].strip()}
    return blocks


def _first_nonempty(block: str) -> str:
    for ln in block.splitlines():
        if ln.strip():
            return ln.strip()
    return ""


# --- operators ------------------------------------------------------------------------
# nominalised verb as printed in the Korrekturheft point-key → canonical operator infinitive
_OP_NOMINAL = {
    "ankreuzen": "ankreuzen", "angeben": "angeben", "aufstellen": "aufstellen",
    "ermitteln": "ermitteln", "berechnen": "berechnen", "ergänzen": "ergänzen",
    "eintragen": "eintragen", "einzeichnen": "einzeichnen", "skizzieren": "skizzieren",
    "zuordnungen": "zuordnen", "zuordnung": "zuordnen", "zuordnen": "zuordnen",
    "vervollständigen": "vervollständigen", "erstellen": "erstellen",
    "beschriften": "beschriften", "kennzeichnen": "kennzeichnen", "markieren": "markieren",
    "veranschaulichen": "veranschaulichen", "umformen": "umformen", "ablesen": "ablesen",
    "beschreiben": "beschreiben", "interpretieren": "interpretieren",
    "nachweisen": "nachweisen", "zeigen": "zeigen", "abschätzen": "(ab)schätzen",
    "schätzen": "(ab)schätzen",
}
# "Ein (halber) Punkt für [das|die|vier|…] [richtige[s]] <Nominalform>…"
_POINTKEY_RE = re.compile(
    r"für\s+(?:das|die|den|alle|vier|zwei|drei|jede)?\s*"
    r"(?:richtige[ns]?\s+)?([A-ZÄÖÜ][A-Za-zäöüß]+)"
)


def operator_from_pointkey(sentence: str) -> str | None:
    """The operator named in a Korrekturheft point-key sentence (canonical infinitive)."""
    m = _POINTKEY_RE.search(sentence)
    if not m:
        return None
    return _OP_NOMINAL.get(m.group(1).lower())


# --- Korrekturheft (LO) task ----------------------------------------------------------
_GK_RE = re.compile(r"Grundkompetenz:\s*([A-Z]{2}\s?\d+\.\d+)")
_POINT_LINE_RE = re.compile(r"(?m)^.*?\b(?:Punkt|P\.)\b.*$")
_HALF_RE = re.compile(r"halbe[rn]?\s+Punkt|½")
_SUBPART_RE = re.compile(r"(?m)^([a-d]\d)\)")


def parse_lo_task(nr: int, block: str, header: str = "") -> dict:
    point_keys = [ln.strip() for ln in _POINT_LINE_RE.findall(block)
                  if "für" in ln and ("Punkt" in ln or "P." in ln)]
    ops = [op for k in point_keys if (op := operator_from_pointkey(k))]
    gk = _GK_RE.search(block)
    subparts = _SUBPART_RE.findall(block)
    title = _first_nonempty(block)
    return {
        "nr": nr,
        **teil_info(header),
        "title": title,
        "operators": ops,
        "operator": ops[0] if ops else None,
        "point_keys": point_keys,
        "half_points": bool(_HALF_RE.search(block)),
        "n_subparts": len(subparts),
        "grundkompetenz": gk.group(1).replace("  ", " ") if gk else None,
    }


# --- Aufgabenheft (AU) task -----------------------------------------------------------
_AUFG_RE = re.compile(r"Aufgabenstellung:\s*", re.IGNORECASE)
_FORMAT_RE = re.compile(r"\[(\d+)\s+aus\s+(\d+)\]")
_POINTMARK_RE = re.compile(r"\[\s*0\s*/\s*(½\s*/\s*)?1\s*(?:P\.|Punkt)\s*\]")
# imperative (separable verbs) → operator, e.g. "Kreuzen Sie … an", "Geben Sie … an"
_IMPERATIVE = [
    (re.compile(r"\bKreuzen\s+Sie\b.*\ban\b", re.S), "ankreuzen"),
    (re.compile(r"\bGeben\s+Sie\b.*\ban\b", re.S), "angeben"),
    (re.compile(r"\bStellen\s+Sie\b.*\bauf\b", re.S), "aufstellen"),
    (re.compile(r"\bTragen\s+Sie\b.*\bein\b", re.S), "eintragen"),
    (re.compile(r"\bZeichnen\s+Sie\b.*\bein\b", re.S), "einzeichnen"),
    (re.compile(r"\bOrdnen\s+Sie\b.*\bzu\b", re.S), "zuordnen"),
    (re.compile(r"\bErmitteln\s+Sie\b", re.S), "ermitteln"),
    (re.compile(r"\bBerechnen\s+Sie\b", re.S), "berechnen"),
    (re.compile(r"\bErgänzen\s+Sie\b", re.S), "ergänzen"),
    (re.compile(r"\bSkizzieren\s+Sie\b", re.S), "skizzieren"),
    (re.compile(r"\bVervollständigen\s+Sie\b", re.S), "vervollständigen"),
    (re.compile(r"\bBeschreiben\s+Sie\b", re.S), "beschreiben"),
    (re.compile(r"\bInterpretieren\s+Sie\b", re.S), "interpretieren"),
]


def operator_from_instruction(text: str) -> str | None:
    for rx, op in _IMPERATIVE:
        if rx.search(text):
            return op
    return None


def parse_au_task(nr: int, block: str, header: str = "") -> dict:
    title = _first_nonempty(block)
    parts = _AUFG_RE.split(block, maxsplit=1)
    context, instruction = (parts[0], parts[1]) if len(parts) == 2 else (block, "")
    # context excludes the title line
    ctx_lines = context.splitlines()
    if ctx_lines and ctx_lines[0].strip() == title:
        ctx_lines = ctx_lines[1:]
    fmt = _FORMAT_RE.search(block)
    pm = _POINTMARK_RE.search(block)
    return {
        "nr": nr,
        **teil_info(header),
        "title": title,
        "context": "\n".join(ln for ln in ctx_lines if ln.strip()).strip(),
        "instruction": instruction.strip(),
        "operator": operator_from_instruction(instruction or block),
        "answer_format": (f"{fmt.group(1)} aus {fmt.group(2)}" if fmt else None),
        "max_points": 1,
        "half_points": bool(pm and pm.group(1)),
    }


# --- Beurteilungsschlüssel ------------------------------------------------------------
_GRADE_RE = re.compile(
    r"(\d+(?:,\d+)?)\s*[–-]\s*(\d+(?:,\d+)?)\s*Punkte\s*\n\s*"
    r"(Sehr gut|Gut|Befriedigend|Genügend|Nicht genügend)",
    re.IGNORECASE,
)


def parse_beurteilungsschluessel(text: str) -> list[dict]:
    out = []
    for lo, hi, grade in _GRADE_RE.findall(text):
        out.append({"grade": grade.strip(),
                    "min": float(lo.replace(",", ".")),
                    "max": float(hi.replace(",", "."))})
    return out


# ======================================================================================
#  Subject-aware parsers (Phase 2 of the home-PC archive build)
#  Math (above) is solid; the languages below have different exam shapes, so each gets a
#  faithful parser. The shared filename-metadata + grade-key machinery is reused. Each
#  ``parse_<subject>(text)`` is pure (string in, dict out) and unit-tested offline.
# ======================================================================================

def _value_after(block: str, label: str) -> str | None:
    """First non-empty line after the line containing ``label`` (the SRDP Korrekturhefte
    print a field label on its own line, the value on the next)."""
    lines = block.splitlines()
    for i, ln in enumerate(lines):
        if label in ln:
            for nxt in lines[i + 1:]:
                if nxt.strip():
                    return nxt.strip()
    return None


# --- Deutsch (Unterrichtssprache) -----------------------------------------------------
# Detection regex (on the Arbeitsauftrag imperative) → canonical operator FORM as printed
# in grounding/operators.DEUTSCH. A test ties these targets to that catalog.
_DE_OPERATORS = [
    (re.compile(r"\bfassen\s+Sie\b.*\bzusammen|zusammenfass", re.I | re.S), "zusammenfassen"),
    (re.compile(r"\bgeben\s+Sie\b.*\bwieder|wiedergeb", re.I | re.S), "wiedergeben"),
    (re.compile(r"analysier|untersuch", re.I), "analysieren / untersuchen"),
    (re.compile(r"charakterisier", re.I), "charakterisieren"),
    (re.compile(r"\berkläre|erklären\b", re.I), "erklären"),
    (re.compile(r"erläuter", re.I), "erläutern"),
    (re.compile(r"erschließ", re.I), "erschließen"),
    (re.compile(r"in\s+Beziehung\s+setzen|setzen\s+Sie\b.*\bin\s+Beziehung", re.I | re.S),
     "in Beziehung setzen"),
    (re.compile(r"vergleich|gegenüber(stell|zustell)", re.I), "vergleichen / einander gegenüberstellen"),
    (re.compile(r"appellier", re.I), "appellieren"),
    (re.compile(r"begründ|Gründe\s+an", re.I), "begründen / Gründe angeben"),
    (re.compile(r"beurteil", re.I), "beurteilen"),
    (re.compile(r"bewert", re.I), "bewerten"),
    (re.compile(r"\bdeuten|interpretier", re.I), "deuten / interpretieren"),
    (re.compile(r"diskutier|erörter|auseinandersetz", re.I), "diskutieren / erörtern / sich auseinandersetzen mit"),
    (re.compile(r"entwerf|entwickeln\s+Sie", re.I), "entwerfen"),
    (re.compile(r"kommentier|Stellung\s+(?:zu\s+)?(?:nehmen|nimmst)|nehmen\s+Sie\b.*\bStellung",
                re.I | re.S), "kommentieren / Stellung nehmen"),
    (re.compile(r"überprüf|\bprüfen\s+Sie\b", re.I), "(über)prüfen"),
    (re.compile(r"vorschlag|Vorschläge\s+mach", re.I), "vorschlagen / Vorschläge machen"),
    (re.compile(r"bestimm|einordn|\bordnen\s+Sie\b.*\bzu\b|zuordn", re.I | re.S),
     "bestimmen / einordnen / zuordnen"),
    (re.compile(r"beschreib", re.I), "beschreiben"),
    (re.compile(r"\bnennen|benennen", re.I), "(be)nennen"),
]


def operator_de(instruction: str) -> str | None:
    """Canonical Deutsch operator named by an Arbeitsauftrag (or None). Picks the operator
    whose match starts EARLIEST — the imperative head — so a trailing adverb (e.g. "Deuten
    Sie … *vergleichend*") doesn't outvote the lead verb."""
    instr = _clean_instr(instruction)
    best, best_pos = None, len(instr) + 1
    for rx, op in _DE_OPERATORS:
        m = rx.search(instr)
        if m and m.start() < best_pos:
            best, best_pos = op, m.start()
    return best


_DE_TASK_RE = re.compile(r"(?m)^\s*Thema\s*(\d+)\s*/\s*Aufgabe\s*(\d+)")
_DE_ARBEITS_RE = re.compile(r"Möglichkeiten\s+zu\s+Arbeitsauftrag\s*\d+\s*:")


def parse_deutsch(text: str) -> dict:
    """Deutsch demand from the **Korrekturheft** (richest: labelled fields per Aufgabe).
    Returns ``{aufgaben: [{thema, aufgabe, textsorte, wortanzahl, situation,
    schreibhandlungen[], arbeitsauftraege[{text, operator}]}]}``. The AU/LO share the
    Themenpaket→Textsorte structure; the LO additionally names the Schreibhandlungen."""
    cleaned = strip_headers(text)
    marks = list(_DE_TASK_RE.finditer(cleaned))
    aufgaben = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(cleaned)
        block = cleaned[m.start():end]
        textsorte = _value_after(block, "Textsorte:")
        wort = _value_after(block, "Wortanzahl:")
        sh_raw = _value_after(block, "werden sollen:") or ""
        schreibhandlungen = [s.strip() for s in re.split(r"[,/]", sh_raw) if s.strip()]
        arbeits = []
        for am in _DE_ARBEITS_RE.finditer(block):
            tail = block[am.end():]
            instr = next((ln.strip() for ln in tail.splitlines() if ln.strip()), "")
            arbeits.append({"text": instr, "operator": operator_de(instr)})
        aufgaben.append({
            "thema": int(m.group(1)), "aufgabe": int(m.group(2)),
            "textsorte": textsorte, "wortanzahl": wort,
            "situation": _value_after(block, "Situation:"),
            "schreibhandlungen": schreibhandlungen,
            "arbeitsauftraege": arbeits,
        })
    return {"aufgaben": aufgaben}


# --- Latein / Griechisch (klassische Sprachen) ----------------------------------------
_LAT_POINTS_RE = re.compile(r"\((\d+)\s*Punkte?\)")
_LAT_SOURCE_RE = re.compile(r"\(([^()]*,[^()]*)\)\s*$", re.M)  # "(Ovid, Heroides)"
# imperative head of an IT Arbeitsaufgabe → operator infinitive
_LAT_OPS = [
    (re.compile(r"^Übersetzen\s+Sie", re.I), "übersetzen"),
    (re.compile(r"^Trennen\s+Sie", re.I), "trennen (Wortbildung)"),
    (re.compile(r"^Ordnen\s+Sie\b.*\bzu", re.I | re.S), "zuordnen"),
    (re.compile(r"^Kreuzen\s+Sie\b.*\ban", re.I | re.S), "ankreuzen"),
    (re.compile(r"^Belegen\s+Sie", re.I), "belegen"),
    (re.compile(r"^Benennen\s+Sie|^Nennen\s+Sie", re.I), "benennen"),
    (re.compile(r"^Bestimmen\s+Sie", re.I), "bestimmen"),
    (re.compile(r"^Geben\s+Sie\b.*\ban", re.I | re.S), "angeben"),
    (re.compile(r"^Ergänzen\s+Sie", re.I), "ergänzen"),
    (re.compile(r"^Finden\s+Sie", re.I), "finden"),
    (re.compile(r"^Wählen\s+Sie\b.*\b(Ankreuzen|aus)\b", re.I | re.S), "ankreuzen (Auswahl)"),
    (re.compile(r"^Gliedern\s+Sie", re.I), "gliedern"),
    (re.compile(r"^Verfassen\s+Sie", re.I), "verfassen"),
    (re.compile(r"^Setzen\s+Sie\s+sich\b.*\bauseinander", re.I | re.S), "auseinandersetzen"),
    (re.compile(r"^Erklären\s+Sie|^Erläutern\s+Sie", re.I), "erklären"),
    (re.compile(r"^Vergleichen\s+Sie", re.I), "vergleichen"),
    (re.compile(r"^Zitieren\s+Sie", re.I), "zitieren"),
    (re.compile(r"^Beschreiben\s+Sie", re.I), "beschreiben"),
    (re.compile(r"^Untersuchen\s+Sie|^Analysieren\s+Sie", re.I), "analysieren"),
    (re.compile(r"^Interpretieren\s+Sie|^Deuten\s+Sie", re.I), "interpretieren"),
]
_LAT_NUM_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s")


def _clean_instr(s: str) -> str:
    """Drop the control-char / bullet glyphs PyMuPDF leaves and leading non-letters, so an
    imperative head matches."""
    s = re.sub(r"[\x00-\x1f]", " ", s or "")
    return re.sub(r"^[^A-Za-zÄÖÜäöü]+", "", s).strip()


def operator_lat(instruction: str) -> str | None:
    head = _clean_instr(instruction)
    for rx, op in _LAT_OPS:
        if rx.match(head):
            return op
    return None


def parse_latein(text: str) -> dict:
    """Latein/Griechisch demand from the **Aufgabenheft**: the Übersetzungstext (ÜT) +
    Interpretationstext (IT) point split, each text's source author, and the numbered IT
    Arbeitsaufgaben (operator + points). Anchored on the lettered section headers
    ``A. Übersetzungstext`` / ``B. Interpretationstext`` (the bare words also appear in the
    Hinweise)."""
    cleaned = strip_headers(text)
    out: dict = {"uebersetzung": None, "interpretation": None, "arbeitsaufgaben": []}
    ut = re.search(r"A\.\s*Übersetzungstext(.*?)(?:B\.\s*Interpretationstext|$)", cleaned, re.S)
    it = re.search(r"B\.\s*Interpretationstext(.*?)"
                   r"(?:Arbeitsaufgaben\s+zum\s+Interpretationstext|$)", cleaned, re.S)
    aa = re.search(r"Arbeitsaufgaben\s+zum\s+Interpretationstext(.*)$", cleaned, re.S)
    if ut:
        body = ut.group(1)
        p = _LAT_POINTS_RE.search(body[:300])
        src = _LAT_SOURCE_RE.findall(body)
        out["uebersetzung"] = {"operator": "übersetzen",
                               "points": int(p.group(1)) if p else None,
                               "source": src[-1].strip() if src else None}
    if it:
        body = it.group(1)
        p = _LAT_POINTS_RE.search(body[:300])
        src = _LAT_SOURCE_RE.findall(body)
        out["interpretation"] = {"points": int(p.group(1)) if p else None,
                                 "source": src[-1].strip() if src else None}
    if aa:
        region = aa.group(1)
        nums = list(_LAT_NUM_RE.finditer(region))
        for i, nm in enumerate(nums):
            end = nums[i + 1].start() if i + 1 < len(nums) else len(region)
            chunk = region[nm.end():end]
            instr = " ".join(_clean_instr(chunk).splitlines()[:3])
            pts = _LAT_POINTS_RE.search(chunk)
            out["arbeitsaufgaben"].append({
                "nr": int(nm.group(1)), "operator": operator_lat(instr),
                "points": int(pts.group(1)) if pts else None,
            })
    return out


# --- Lebende Fremdsprachen (Eng/Fra/Ita/Spa) ------------------------------------------
_FS_SKILLS = ["Sprachverwendung im Kontext", "Hören", "Lesen", "Schreiben"]
_CEFR_RE = re.compile(r"\b(A2|B1|B2|C1)\b")
_NUMWORD = {"eine": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5}
_FS_FORMAT_HINTS = [
    (re.compile(r"\[\s*richtig\s*/\s*falsch|true\s*/\s*false", re.I), "true_false"),
    (re.compile(r"multiple[- ]choice|\[\d+\s+aus\s+\d+\]", re.I), "multiple_choice"),
    (re.compile(r"\bzuordn|matching\b", re.I), "matching"),
    (re.compile(r"Lückentext|gap|word\s*formation|Wortbildung", re.I), "gap_fill"),
    (re.compile(r"kurzantwort|short[- ]answer|open[- ]ended", re.I), "short_answer"),
]


def parse_language(meta: dict, text: str) -> dict:
    """Modern-FS demand: the **skill** + **CEFR level** (from the header), the task count
    and the item formats present. Languages are skill-split booklets, so the durable demand
    signal is *which skills × levels* are exercised and *which formats* — not a per-item
    operator parse (the SRDP FS exams aren't operator-driven the way Deutsch/Math are)."""
    head = "\n".join(text.splitlines()[:12])
    skill = next((s for s in _FS_SKILLS if s in head), None)
    cefr = None
    cm = _CEFR_RE.search(head)
    if cm:
        cefr = cm.group(1)
    # the booklet states its own total ("… enthält drei Aufgaben") — authoritative; else
    # count the task headers that appear in the body.
    wm = re.search(r"enthält\s+(\w+)\s+(?:Aufgabe|Schreibaufträge|Tasks?)", text)
    n_tasks = _NUMWORD.get(wm.group(1).lower(), 0) if wm else 0
    if not n_tasks:
        n_tasks = len(re.findall(r"(?m)^\s*(?:Aufgabe|Task|Text)\s+\d+\b", text))
    formats = sorted({fmt for rx, fmt in _FS_FORMAT_HINTS if rx.search(text)})
    return {"skill": skill, "cefr": cefr, "n_tasks": n_tasks or None, "formats": formats}


# --- PDF I/O + assembly ---------------------------------------------------------------
def read_pdf_text(path: str) -> str:
    import fitz  # PyMuPDF — already a project dep
    doc = fitz.open(path)
    return "\n".join(p.get_text() for p in doc)


_MATH_SUBJECTS = {"MAT", "AMT"}
_DEUTSCH_SUBJECTS = {"DEU"}
_LATEIN_SUBJECTS = {"LAT", "GRI"}
_FS_SUBJECTS = {"ENG", "FRA", "ITA", "SPA"}


def subject_kind(subject: str | None) -> str:
    s = (subject or "").upper()
    if s in _DEUTSCH_SUBJECTS:
        return "deutsch"
    if s in _LATEIN_SUBJECTS:
        return "latein"
    if s in _FS_SUBJECTS:
        return "language"
    return "math"  # MAT/AMT and unknown fall through to the task/point parser


def extract(path: str) -> dict:
    """One heft → a structured record. Dispatches on subject: Math/AMT use the task+point
    parser; Deutsch/Latein/languages use their faithful per-subject parser."""
    meta = parse_filename(path) or {"kind": "unknown"}
    text = read_pdf_text(path)
    kind = subject_kind(meta.get("subject"))
    base = {"meta": meta, "source": os.path.basename(path), "subject_kind": kind}
    if kind == "deutsch":
        return {**base, "deutsch": parse_deutsch(text)}
    if kind == "latein":
        return {**base, "latein": parse_latein(text)}
    if kind == "language":
        return {**base, "language": parse_language(meta, text)}
    # Mathematik / Angewandte Mathematik (and unknown subjects)
    blocks = split_tasks(text)
    parse = parse_lo_task if meta.get("kind") == "loesungen" else parse_au_task
    tasks = [parse(nr, b["block"], b["header"]) for nr, b in sorted(blocks.items())]
    if meta.get("file_teil"):  # single-Teil booklet → the file fixes every task's Teil
        for t in tasks:
            t["teil"] = meta["file_teil"]
    out = {**base, "tasks": tasks}
    if meta.get("kind") == "loesungen":
        bw = parse_beurteilungsschluessel(text)
        out["beurteilungsschluessel"] = bw
        out["total_points"] = max((r["max"] for r in bw), default=None)
    return out


def merge(au: dict, lo: dict) -> dict:
    """Merge an AU + LO extraction into unified per-task records (the analysis view)."""
    by_nr: dict[int, dict] = {}
    for t in au.get("tasks", []):
        by_nr[t["nr"]] = {"nr": t["nr"], "teil": t.get("teil"), "best_of": t.get("best_of"),
                          "title": t["title"], "context": t.get("context"),
                          "instruction": t.get("instruction"),
                          "answer_format": t.get("answer_format"),
                          "operator_au": t.get("operator"),
                          "half_points": bool(t.get("half_points"))}
    for t in lo.get("tasks", []):
        r = by_nr.setdefault(t["nr"], {"nr": t["nr"], "title": t["title"]})
        r.setdefault("teil", t.get("teil")); r.setdefault("best_of", t.get("best_of"))
        r.update({"operator_lo": t.get("operator"), "operators": t.get("operators"),
                  "point_keys": t.get("point_keys"),
                  "n_subparts": t.get("n_subparts"), "grundkompetenz": t.get("grundkompetenz")})
        if t.get("half_points"):
            r["half_points"] = True
    # unified operator: prefer the year-stable AU imperative, fall back to the LO point-key
    for r in by_nr.values():
        r["operator"] = r.get("operator_au") or r.get("operator_lo")
    meta = dict(lo.get("meta") or au.get("meta") or {})
    meta.pop("kind", None)
    return {"meta": meta,
            "beurteilungsschluessel": lo.get("beurteilungsschluessel"),
            "total_points": lo.get("total_points"),
            "tasks": [by_nr[k] for k in sorted(by_nr)]}


def _pair_key(meta: dict | None) -> tuple:
    m = meta or {}
    return (m.get("year"), m.get("pruefungsteil"), m.get("schulform"), m.get("subject"),
            m.get("variant"), m.get("language"))


# which heft carries the richer demand signal per non-math subject
_RICHER_HEFT = {"deutsch": "loesungen", "latein": "aufgaben", "language": "aufgaben"}


def combine(halves: dict) -> dict:
    """Combine the AU+LO of one exam. Math → the per-task ``merge``; other subjects keep the
    heft that carries the structured demand (Deutsch: the Kommentierung; Latein/FS: the
    Aufgabenheft), with the other's metadata folded in."""
    sample = next(iter(halves.values()))
    kind = sample.get("subject_kind", "math")
    if kind == "math":
        if "aufgaben" in halves and "loesungen" in halves:
            return merge(halves["aufgaben"], halves["loesungen"])
        return sample
    prefer = _RICHER_HEFT.get(kind, "aufgaben")
    chosen = halves.get(prefer) or sample
    meta = dict(chosen.get("meta") or {})
    meta.pop("kind", None)
    rec = {k: v for k, v in chosen.items() if k != "meta"}
    rec["meta"] = meta
    rec["sources"] = sorted(h.get("source") for h in halves.values())
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract SRDP Matura exam PDFs to JSON.")
    ap.add_argument("pdfs", nargs="+", help="AU/LO exam PDFs (pairs are merged)")
    ap.add_argument("-o", "--out", help="write JSON here (default: stdout)")
    args = ap.parse_args(argv)

    extracted = [extract(p) for p in args.pdfs]
    # pair AU+LO of the same exam; emit merged records where both are present
    pairs: dict[tuple, dict] = {}
    singles: list[dict] = []
    for e in extracted:
        k = _pair_key(e.get("meta"))
        if e["meta"].get("kind") in ("aufgaben", "loesungen") and k != (None,) * 6:
            pairs.setdefault(k, {})[e["meta"]["kind"]] = e
        else:
            singles.append(e)
    results = []
    for k, halves in pairs.items():
        results.append(combine(halves))
    results.extend(singles)
    payload = results[0] if len(results) == 1 else results

    out = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
