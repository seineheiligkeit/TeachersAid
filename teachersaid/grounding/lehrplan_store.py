"""Loads Lehrplan grounding from the full competence catalog at `lehrplan/`.

Reads the deterministic-parser output (`lehrplan/_meta.json`, `subject_models.json`,
and per-subject `<CODE>.json`) — all 16 Unterstufe Pflichtgegenstände, ~571 verbatim
competences — and adapts it to the engine schema (`FassungRef` /
`SubjectCompetenceModel` / `ResolvedCompetence`). This replaces the earlier
Physik-only YAML stub; the catalog's competence JSON already matches
`ResolvedCompetence`, so the only real adaptation is per-competence dimension
resolution and subject-name → catalog-code lookup.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from ..config import FASSUNG, LEHRPLAN_DIR
from ..schema.competence import CompetenceDimension, SubjectCompetenceModel
from ..schema.worksheet import FassungRef, ResolvedCompetence

# The engine's Modality enum is printable|oral|enactive; the catalog also uses
# "audio" (Hören). Map it to the nearest non-printable modality for the model.
_MODALITY_MAP = {"audio": "oral"}

# Common German subject names → catalog code (registry names are added at load).
_ALIASES = {
    "physik": "PHY",
    "chemie": "CHE",  # AHS variant; CHE2 is the Wirtschaftskundliches-RG variant
    "biologie": "BIO", "biologie und umweltbildung": "BIO",
    "mathematik": "MAT", "mathe": "MAT",
    "deutsch": "DEU",
    "geographie und wirtschaftliche bildung": "GWB", "geographie": "GWB",
    "geografie": "GWB", "gwb": "GWB",
    "geschichte und politische bildung": "GPB", "geschichte": "GPB", "gpb": "GPB",
    "latein": "LAT",
    "erste lebende fremdsprache": "FS1", "lebende fremdsprache": "FS1",
    "fremdsprache": "FS1", "englisch": "FS1", "französisch": "FS1",
    "italienisch": "FS1", "spanisch": "FS1", "russisch": "FS1",
    "zweite lebende fremdsprache": "FS2",
    "digitale grundbildung": "DGB",
    "geometrisches zeichnen": "GEZ",
    "musik": "MUS",
    "kunst und gestaltung": "KUG", "kunst": "KUG",
    "technik und design": "TED", "technik": "TED",
    "bewegung und sport": "BUS", "sport": "BUS",
}


@lru_cache(maxsize=1)
def _meta() -> dict:
    with open(LEHRPLAN_DIR / "_meta.json", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _models() -> dict:
    with open(LEHRPLAN_DIR / "subject_models.json", encoding="utf-8") as fh:
        return {k: v for k, v in json.load(fh).items() if not k.startswith("_")}


@lru_cache(maxsize=None)
def _subject(code: str | None) -> dict | None:
    if not code:
        return None
    p = LEHRPLAN_DIR / f"{code}.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _name_to_code() -> dict[str, str]:
    table = dict(_ALIASES)
    for s in _meta().get("subjects", []):
        table.setdefault(s["name"].casefold(), s["code"])
        table.setdefault(s["code"].casefold(), s["code"])
    return table


def _code_for(subject: str) -> str | None:
    if subject in _models():  # already a catalog code, e.g. "PHY"
        return subject
    return _name_to_code().get(subject.strip().casefold())


def _dim_ids(code: str) -> set[str]:
    return {d["code"] for d in _models().get(code, {}).get("dimensions", [])}


def get_fassung() -> FassungRef:
    # Use the config constant (identical to lehrplan/_meta on the load-bearing
    # fields) so the stamped Fassung stays stable across the codebase.
    return FassungRef(**FASSUNG)


def get_subject_model(subject: str) -> SubjectCompetenceModel | None:
    code = _code_for(subject)
    ov = _models().get(code) if code else None
    if ov is None:
        return None

    def to_dim(d: dict) -> CompetenceDimension:
        raw = d.get("modality", "printable")
        return CompetenceDimension(
            id=d["code"],
            label=d["label"],
            note=d.get("note"),
            modality=_MODALITY_MAP.get(raw, raw),
        )

    return SubjectCompetenceModel(
        subject=subject,
        stufe="Unterstufe",
        dimensions=[to_dim(d) for d in ov.get("dimensions", [])],
        content_areas=[
            CompetenceDimension(id=c["code"], label=c["label"])
            for c in (ov.get("content_areas") or [])
        ],
        task_kind_extensions=ov.get("task_kind_extensions", []),
    )


def list_subjects() -> list[str]:
    return [
        s["name"] for s in _meta().get("subjects", [])
        if s.get("type") == "pflichtgegenstand"
    ]


def grade_map(subject: str) -> dict[int, list[str]]:
    code = _code_for(subject)
    data = _subject(code)
    if not data:
        return {}
    klassen = data.get("klassen", [])
    out: dict[int, list[str]] = {}
    for c in data.get("competences", []):
        kb = c.get("kompetenzbereich")
        if not kb:
            continue
        grades = [c["klasse"]] if c.get("klasse") else klassen  # null = cross-class
        for k in grades:
            out.setdefault(k, [])
            if kb not in out[k]:
                out[k].append(kb)
    return out


_DIM_TAG = re.compile(r"\(([A-ZÄÖÜ][A-Z0-9]?)\)")


def _resolve_dims(c: dict, dim_ids: set[str]) -> list[str]:
    """Best-effort DimensionRef(s) for one competence, against the subject model.

    1. inline-tagged dimensions from the catalog (sciences: W/E/S);
    2. else the kompetenzbereich_code where it *is* a dimension (Deutsch ZUH/LES/SCH,
       FS, Musik, Latein, …);
    3. else a parenthesised tag in the text (DGB "(T)", Geometr. Zeichnen "(H1)").
    Empty when the catalog carries no per-competence dimension (MAT process axis,
    GWB, GPB strands) — plan() then falls back to the subject model's first dimension.
    """
    dims = [d for d in c.get("dimensions", []) if d in dim_ids]
    if dims:
        return dims
    code = c.get("kompetenzbereich_code")
    if code in dim_ids:
        return [code]
    for tag in _DIM_TAG.findall(c.get("text", "")):
        if tag in dim_ids:
            return [tag]
    return []


def anwendungsbereiche_for(subject: str, klasse: int) -> list[str]:
    """The Lehrstoff / Anwendungsbereiche items for a grade (incl. cross-class).

    For subjects whose Kompetenzbereiche are the W/E/S dimensions or competence
    strands (sciences, GPB), the *thematic* content lives here, not in the
    competence's kompetenzbereich — so resolve() matches topics against this too.
    """
    code = _code_for(subject)
    data = _subject(code)
    if not data:
        return []
    out: list[str] = []
    for blk in data.get("anwendungsbereiche", []):
        k = blk.get("klasse")
        if k is None or k == klasse:
            out.extend(blk.get("items", []))
    return out


def competences_for(subject: str, klasse: int) -> list[ResolvedCompetence]:
    code = _code_for(subject)
    data = _subject(code)
    if not data or klasse not in data.get("klassen", []):
        return []
    dim_ids = _dim_ids(code)
    out: list[ResolvedCompetence] = []
    for c in data.get("competences", []):
        ck = c.get("klasse")
        if ck is not None and ck != klasse:
            continue  # null klasse = cross-class competence, applies to every grade
        out.append(
            ResolvedCompetence(
                id=c["id"],
                kompetenzbereich=c.get("kompetenzbereich") or "—",
                klasse=ck if ck is not None else klasse,
                text=(c.get("text") or "").strip(),
                source_ref=c.get("source_ref"),
                dimensions=_resolve_dims(c, dim_ids),
                uebergreifende_themen=c.get("uebergreifende_themen", []),
            )
        )
    return out


@lru_cache(maxsize=1)
def _competence_index() -> dict[str, dict]:
    """competence_id -> {subject_code, subject, kompetenzbereich, kompetenzbereich_code, klasse}."""
    idx: dict[str, dict] = {}
    for s in _meta().get("subjects", []):
        if s.get("type") != "pflichtgegenstand":
            continue
        data = _subject(s["code"]) or {}
        for c in data.get("competences", []):
            idx[c["id"]] = {
                "subject_code": s["code"], "subject": s["name"],
                "kompetenzbereich": c.get("kompetenzbereich"),
                "kompetenzbereich_code": c.get("kompetenzbereich_code"),
                "klasse": c.get("klasse"),
            }
    return idx


def competence_meta(competence_id: str) -> dict | None:
    """Look up a single competence's subject/Kompetenzbereich by its catalog id."""
    return _competence_index().get(competence_id)


def competence_count(subject: str) -> int:
    """Number of catalog competences for a subject (by name or code)."""
    data = _subject(_code_for(subject))
    return len(data.get("competences", [])) if data else 0
