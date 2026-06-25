"""Loads the curated Lehrplan grounding (Fassung, competences, subject models).

This is the demo's stand-in for a full RIS parser: grounded facts hand-curated
from the design docs into grounding/data/*.yaml, for the demo subjects only.
"""

from __future__ import annotations

from functools import lru_cache

import yaml

from ..config import GROUNDING_DATA
from ..schema.competence import CompetenceDimension, SubjectCompetenceModel
from ..schema.worksheet import FassungRef, ResolvedCompetence

# Subject aliasing: the three sciences share one Naturwissenschaften model.
_MODEL_ALIASES = {
    "Chemie": "Physik",
    "Biologie": "Physik",
    "Biologie und Umweltbildung": "Physik",
    "Geographie und wirtschaftliche Bildung": "GWB",
    "Geographie": "GWB",
}


@lru_cache(maxsize=1)
def _raw() -> dict:
    def load(name: str) -> dict:
        with open(GROUNDING_DATA / name, encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    return {
        "fassung": load("fassung.yaml"),
        "physik": load("physik_us.yaml"),
        "models": load("competence_models.yaml"),
    }


def get_fassung() -> FassungRef:
    return FassungRef.model_validate(_raw()["fassung"])


def _model_key(subject: str) -> str | None:
    models = _raw()["models"]
    if subject in models:
        return subject
    return _MODEL_ALIASES.get(subject)


def get_subject_model(subject: str) -> SubjectCompetenceModel | None:
    key = _model_key(subject)
    if key is None:
        return None
    data = dict(_raw()["models"][key])
    dims = [CompetenceDimension.model_validate(d) for d in data.get("dimensions", [])]
    content_areas = [
        CompetenceDimension.model_validate(d) for d in data.get("content_areas", [])
    ]
    return SubjectCompetenceModel(
        subject=data["subject"],
        stufe=data["stufe"],
        dimensions=dims,
        content_areas=content_areas,
        task_kind_extensions=data.get("task_kind_extensions", []),
    )


def list_subjects() -> list[str]:
    return sorted(_raw()["models"].keys())


def _competence_source(subject: str) -> dict | None:
    """Return the raw subject catalogue (only Physik is curated for the demo)."""
    if _model_key(subject) == "Physik" or subject == "Physik":
        return _raw()["physik"]
    return None


def grade_map(subject: str) -> dict[int, list[str]]:
    src = _competence_source(subject)
    return src.get("grade_map", {}) if src else {}


def competences_for(subject: str, klasse: int) -> list[ResolvedCompetence]:
    src = _competence_source(subject)
    if not src:
        return []
    out: list[ResolvedCompetence] = []
    for c in src.get("competences", []):
        if c.get("klasse") == klasse:
            out.append(
                ResolvedCompetence(
                    id=c["id"],
                    kompetenzbereich=c["kompetenzbereich"],
                    klasse=c["klasse"],
                    text=c["text"].strip(),
                    source_ref=c.get("source_ref"),
                    dimensions=c.get("dimensions", []),
                    uebergreifende_themen=c.get("uebergreifende_themen", []),
                )
            )
    return out
