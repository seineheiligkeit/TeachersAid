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
_NAME_RE = re.compile(
    r"([A-Za-z]{2})(\d{2})_PT(\d)_([A-Z]{3})_([A-Z]{3})_(\d+)_([A-Z]{2})_(AU|LO)",
    re.IGNORECASE,
)
_TERMIN = {"KL": "Haupttermin", "NT": "Nebentermin", "WT": "Wintertermin"}


def parse_filename(name: str) -> dict | None:
    """Pull exam metadata from a stable SRDP filename, e.g.
    ``KL25_PT1_AHS_MAT_00_DE_AU`` → year 2025, Haupttermin, Teil 1, AHS, MAT, DE, Aufgaben."""
    m = _NAME_RE.search(os.path.basename(name))
    if not m:
        return None
    termin, yy, part, schulform, subject, variant, lang, kind = m.groups()
    return {
        "termin": _TERMIN.get(termin.upper(), termin.upper()),
        "year": 2000 + int(yy),
        "teil": int(part),
        "schulform": schulform.upper(),
        "subject": subject.upper(),
        "variant": variant,
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
_POINTMARK_RE = re.compile(r"\[\s*0\s*/\s*(½\s*/\s*)?1\s*P\.\s*\]")
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


# --- PDF I/O + assembly ---------------------------------------------------------------
def read_pdf_text(path: str) -> str:
    import fitz  # PyMuPDF — already a project dep
    doc = fitz.open(path)
    return "\n".join(p.get_text() for p in doc)


def extract(path: str) -> dict:
    """One heft → {meta, (beurteilung), tasks[]}."""
    meta = parse_filename(path) or {"kind": "unknown"}
    text = read_pdf_text(path)
    blocks = split_tasks(text)
    if meta.get("kind") == "loesungen":
        tasks = [parse_lo_task(nr, b["block"], b["header"])
                 for nr, b in sorted(blocks.items())]
        return {"meta": meta, "source": os.path.basename(path),
                "total_points": (parse_beurteilungsschluessel(text) or [{}])[0].get("max"),
                "beurteilungsschluessel": parse_beurteilungsschluessel(text),
                "tasks": tasks}
    tasks = [parse_au_task(nr, b["block"], b["header"])
             for nr, b in sorted(blocks.items())]
    return {"meta": meta, "source": os.path.basename(path), "tasks": tasks}


def merge(au: dict, lo: dict) -> dict:
    """Merge an AU + LO extraction into unified per-task records (the analysis view)."""
    by_nr: dict[int, dict] = {}
    for t in au.get("tasks", []):
        by_nr[t["nr"]] = {"nr": t["nr"], "teil": t.get("teil"), "best_of": t.get("best_of"),
                          "title": t["title"], "context": t.get("context"),
                          "instruction": t.get("instruction"),
                          "answer_format": t.get("answer_format"),
                          "operator_au": t.get("operator")}
    for t in lo.get("tasks", []):
        r = by_nr.setdefault(t["nr"], {"nr": t["nr"], "title": t["title"]})
        r.setdefault("teil", t.get("teil")); r.setdefault("best_of", t.get("best_of"))
        r.update({"operator": t.get("operator"), "operators": t.get("operators"),
                  "point_keys": t.get("point_keys"), "half_points": t.get("half_points"),
                  "n_subparts": t.get("n_subparts"), "grundkompetenz": t.get("grundkompetenz")})
    meta = dict(lo.get("meta") or au.get("meta") or {})
    meta.pop("kind", None)
    return {"meta": meta,
            "beurteilungsschluessel": lo.get("beurteilungsschluessel"),
            "total_points": lo.get("total_points"),
            "tasks": [by_nr[k] for k in sorted(by_nr)]}


def _pair_key(meta: dict | None) -> tuple:
    m = meta or {}
    return (m.get("year"), m.get("teil"), m.get("schulform"), m.get("subject"),
            m.get("variant"), m.get("language"))


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
        if "aufgaben" in halves and "loesungen" in halves:
            results.append(merge(halves["aufgaben"], halves["loesungen"]))
        else:
            results.extend(halves.values())
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
