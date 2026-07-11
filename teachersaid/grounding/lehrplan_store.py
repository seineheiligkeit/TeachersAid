"""Loads Lehrplan grounding from the competence catalogs at `lehrplan/`.

Reads the deterministic-parser output (`_meta.json`, `subject_models.json`, per-subject
`<CODE>.json`) and adapts it to the engine schema (`FassungRef` /
`SubjectCompetenceModel` / `ResolvedCompetence`).

**Two stages, one store.** The Unterstufe catalog lives at `lehrplan/` (16 subjects,
~571 competences); the Oberstufe catalog at `lehrplan/oberstufe/` (18 subjects, semesterised
into Kompetenzmodule, with a typed `descriptor`/`lehrstoff` split). Every public function takes
a `stufe` argument (default "Unterstufe"); the resolver drives it from the requested Klasse
(1–4 → Unterstufe, 5–8 → Oberstufe) via `stufe_for_klasse`. The Oberstufe carries
`semester`/`kompetenzmodul`/`kind` onto each `ResolvedCompetence`.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from ..config import FASSUNG, LEHRPLAN_DIR
from ..schema.competence import CompetenceDimension, SubjectCompetenceModel
from ..schema.worksheet import FassungRef, ResolvedCompetence

OBERSTUFE_DIR = LEHRPLAN_DIR / "oberstufe"

# The engine's Modality enum is printable|oral|enactive; the catalog also uses
# "audio" (Hören). Map it to the nearest non-printable modality for the model.
_MODALITY_MAP = {"audio": "oral"}

# A genuine 1-display-name→2-codes collision in the RIS source: two Unterstufe subjects
# are both headed "CHEMIE" — CHE (AHS Gym/RG, 4. Kl.) and CHE2 (Wirtschaftskundliches
# Realgymnasium, vierstündig, 3.–4. Kl.). The parser reads both names verbatim, so any
# subject-name routing (`_code_for`/`_name_to_code`) collapses onto CHE and CHE2's six
# coverage cells stay permanently unreachable. Curate a DISTINCT engine display name here
# — keyed (stufe, code), applied in `_meta` at load, so it survives a catalog re-parse
# (editing `_meta.json` would be clobbered). `_name_to_code` then auto-builds the alias
# from this name (distinct name → CHE2), while plain "Chemie" still routes to CHE below.
_DISPLAY_NAME_OVERRIDES = {
    ("Unterstufe", "CHE2"): "Chemie (Wirtschaftskundliches Realgymnasium)",
}

# Common German subject names → Unterstufe catalog code (registry names added at load).
_ALIASES_US = {
    "physik": "PHY",
    "chemie": "CHE",  # AHS 4.-Kl. variant; CHE2 routes via its distinct display name (above)
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

# Oberstufe codes differ for several subjects (FS1/FS2→FSP; +ETH/GRI/INF/DGE/HOE/PUP).
_ALIASES_OS = {
    "physik": "PHY", "chemie": "CHE",
    "biologie": "BIO", "biologie und umweltbildung": "BIO",
    "mathematik": "MAT", "mathe": "MAT", "deutsch": "DEU",
    "geographie und wirtschaftliche bildung": "GWB", "geographie": "GWB",
    "geografie": "GWB", "gwb": "GWB",
    "geschichte und politische bildung": "GPB", "geschichte": "GPB", "gpb": "GPB",
    "latein": "LAT", "griechisch": "GRI",
    "lebende fremdsprache": "FSP", "lebende fremdsprache (erste, zweite)": "FSP",
    "erste lebende fremdsprache": "FSP", "zweite lebende fremdsprache": "FSP",
    "fremdsprache": "FSP", "englisch": "FSP", "französisch": "FSP",
    "italienisch": "FSP", "spanisch": "FSP", "russisch": "FSP",
    "ethik": "ETH",
    "psychologie und philosophie": "PUP", "psychologie": "PUP", "philosophie": "PUP",
    "informatik": "INF",
    "darstellende geometrie": "DGE",
    "haushaltsökonomie und ernährung": "HOE", "haushaltsökonomie": "HOE",
    "musik": "MUS", "kunst und gestaltung": "KUG", "kunst": "KUG",
    "bewegung und sport": "BUS", "sport": "BUS",
}


def _norm_stufe(stufe: str | None) -> str:
    return "Oberstufe" if (stufe or "").strip().lower().startswith("ober") else "Unterstufe"


def stufe_for_klasse(klasse: int | None) -> str:
    """In the AHS the Klasse fixes the stage: 1–4 = Unterstufe, 5–8 = Oberstufe."""
    return "Oberstufe" if (klasse or 0) >= 5 else "Unterstufe"


def _dir(stufe: str):
    return OBERSTUFE_DIR if _norm_stufe(stufe) == "Oberstufe" else LEHRPLAN_DIR


@lru_cache(maxsize=2)
def _meta(stufe: str = "Unterstufe") -> dict:
    with open(_dir(stufe) / "_meta.json", encoding="utf-8") as fh:
        meta = json.load(fh)
    # Apply the curated display-name overrides once (the dict is freshly loaded and
    # cached, so every downstream reader — list_subjects, _name_to_code, the competence
    # index, stats/coverage — sees the disambiguated name). See _DISPLAY_NAME_OVERRIDES.
    st = _norm_stufe(stufe)
    for s in meta.get("subjects", []):
        override = _DISPLAY_NAME_OVERRIDES.get((st, s.get("code")))
        if override:
            s["name"] = override
    return meta


@lru_cache(maxsize=2)
def _models(stufe: str = "Unterstufe") -> dict:
    with open(_dir(stufe) / "subject_models.json", encoding="utf-8") as fh:
        return {k: v for k, v in json.load(fh).items() if not k.startswith("_")}


@lru_cache(maxsize=None)
def _subject(code: str | None, stufe: str = "Unterstufe") -> dict | None:
    if not code:
        return None
    p = _dir(stufe) / f"{code}.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=2)
def _name_to_code(stufe: str = "Unterstufe") -> dict[str, str]:
    table = dict(_ALIASES_OS if _norm_stufe(stufe) == "Oberstufe" else _ALIASES_US)
    for s in _meta(stufe).get("subjects", []):
        table.setdefault(s["name"].casefold(), s["code"])
        table.setdefault(s["code"].casefold(), s["code"])
    return table


def _code_for(subject: str, stufe: str = "Unterstufe") -> str | None:
    if subject in _models(stufe):  # already a catalog code, e.g. "PHY"
        return subject
    return _name_to_code(stufe).get(subject.strip().casefold())


def _dim_ids(code: str, stufe: str = "Unterstufe") -> set[str]:
    return {d["code"] for d in _models(stufe).get(code, {}).get("dimensions", [])}


def get_fassung() -> FassungRef:
    # Use the config constant (identical to lehrplan/_meta on the load-bearing
    # fields) so the stamped Fassung stays stable across the codebase.
    return FassungRef(**FASSUNG)


def _content_dim(c) -> CompetenceDimension:
    # Unterstufe content_areas are {code,label}; Oberstufe uses plain strings.
    if isinstance(c, str):
        return CompetenceDimension(id=c, label=c)
    return CompetenceDimension(id=c["code"], label=c["label"])


def get_subject_model(subject: str, stufe: str = "Unterstufe") -> SubjectCompetenceModel | None:
    code = _code_for(subject, stufe)
    ov = _models(stufe).get(code) if code else None
    if ov is None:
        return None

    def to_dim(d: dict) -> CompetenceDimension:
        raw = d.get("modality", "printable")
        return CompetenceDimension(
            id=d["code"], label=d["label"], note=d.get("note"),
            modality=_MODALITY_MAP.get(raw, raw),
        )

    return SubjectCompetenceModel(
        subject=subject,
        stufe=_norm_stufe(stufe),
        dimensions=[to_dim(d) for d in ov.get("dimensions", [])],
        content_areas=[_content_dim(c) for c in (ov.get("content_areas") or [])],
        task_kind_extensions=ov.get("task_kind_extensions", []),
    )


def list_subjects(stufe: str = "Unterstufe") -> list[str]:
    return [
        s["name"] for s in _meta(stufe).get("subjects", [])
        if s.get("type") == "pflichtgegenstand"
    ]


def uebergreifende_themen(stufe: str = "Unterstufe") -> dict[int, str]:
    """The übergreifende-Themen legend (nr → label) for a stage, from `_meta`. These are
    the cross-cutting Bildungsanliegen (Umweltbildung, Medienbildung, …) that competences
    across many subjects carry — the anchor of the fächerübergreifende Projektwoche bundle
    (Wave C3). A competence's tags live on `ResolvedCompetence.uebergreifende_themen`."""
    return {int(u["nr"]): u["label"] for u in _meta(stufe).get("uebergreifende_themen", [])}


def grade_map(subject: str, stufe: str = "Unterstufe") -> dict[int, list[str]]:
    code = _code_for(subject, stufe)
    data = _subject(code, stufe)
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

    1. inline-tagged dimensions from the catalog (sciences W/E/S; Oberstufe descriptors);
    2. else the kompetenzbereich_code where it *is* a dimension;
    3. else a parenthesised tag in the text (DGB "(T)", Geometr. Zeichnen "(H1)").
    Empty when the catalog carries no per-competence dimension (MAT process axis, GWB,
    GPB strands, Oberstufe lehrstoff) — plan() falls back to the model's first dimension.
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


def anwendungsbereiche_for(subject: str, klasse: int, stufe: str = "Unterstufe") -> list[str]:
    """The Lehrstoff / Anwendungsbereiche items for a grade (incl. cross-class).

    For subjects whose Kompetenzbereiche are the W/E/S dimensions or competence strands
    (sciences, GPB), the *thematic* content lives here, so resolve() matches topics
    against this too. The Oberstufe catalog has no separate `anwendungsbereiche` block
    (its thematic content is the `lehrstoff`-kind competences) → returns [].
    """
    code = _code_for(subject, stufe)
    data = _subject(code, stufe)
    if not data:
        return []
    out: list[str] = []
    for blk in data.get("anwendungsbereiche", []):
        k = blk.get("klasse")
        if k is None or k == klasse:
            out.extend(blk.get("items", []))
    return out


def competences_for(
    subject: str, klasse: int, stufe: str = "Unterstufe",
    *, semester: int | None = None, kompetenzmodul: int | None = None,
) -> list[ResolvedCompetence]:
    """Resolved competences for a subject+grade. `semester`/`kompetenzmodul` (Oberstufe)
    narrow to one module; grade-independent `descriptor` competences are always kept (they
    are the cross-cutting Kompetenzmodell competences that every module exercises)."""
    code = _code_for(subject, stufe)
    data = _subject(code, stufe)
    if not data or klasse not in data.get("klassen", []):
        return []
    dim_ids = _dim_ids(code, stufe)
    out: list[ResolvedCompetence] = []
    for c in data.get("competences", []):
        ck = c.get("klasse")
        if ck is not None and ck != klasse:
            continue  # null klasse = cross-class / grade-independent descriptor
        is_desc = c.get("kind") == "descriptor"
        if kompetenzmodul is not None and not is_desc and c.get("kompetenzmodul") != kompetenzmodul:
            continue
        if semester is not None and not is_desc and semester not in (c.get("semester") or []):
            continue
        out.append(
            ResolvedCompetence(
                id=c["id"],
                kompetenzbereich=c.get("kompetenzbereich") or "—",
                klasse=ck if ck is not None else klasse,
                text=(c.get("text") or "").strip(),
                source_ref=c.get("source_ref"),
                dimensions=_resolve_dims(c, dim_ids),
                uebergreifende_themen=c.get("uebergreifende_themen", []),
                semester=c.get("semester"),
                kompetenzmodul=c.get("kompetenzmodul"),
                kind=c.get("kind"),
            )
        )
    return out


@lru_cache(maxsize=2)
def _competence_index(stufe: str = "Unterstufe") -> dict[str, dict]:
    """competence_id -> {subject_code, subject, kompetenzbereich, kompetenzbereich_code, klasse}."""
    idx: dict[str, dict] = {}
    for s in _meta(stufe).get("subjects", []):
        if s.get("type") != "pflichtgegenstand":
            continue
        data = _subject(s["code"], stufe) or {}
        for c in data.get("competences", []):
            idx[c["id"]] = {
                "subject_code": s["code"], "subject": s["name"],
                "kompetenzbereich": c.get("kompetenzbereich"),
                "kompetenzbereich_code": c.get("kompetenzbereich_code"),
                "klasse": c.get("klasse"),
            }
    return idx


def competence_meta(competence_id: str) -> dict | None:
    """Look up a single competence's subject/Kompetenzbereich by its catalog id.
    The stage is encoded in the id (`.OS.` vs `.US.`)."""
    stufe = "Oberstufe" if ".OS." in competence_id else "Unterstufe"
    return _competence_index(stufe).get(competence_id)


def competence_count(subject: str, stufe: str = "Unterstufe") -> int:
    """Number of catalog competences for a subject (by name or code)."""
    data = _subject(_code_for(subject, stufe), stufe)
    return len(data.get("competences", [])) if data else 0
