"""The entity registry — the corpus-global single source of truth for named entities.

The grounding twin of `chemistry.py` (cited atomic weights) and `data_store.py` (cited
datasets), applied to **who/where/what**: canonical persons, places, events and works that
the corpus refers to by name. Each entity is a *selected, never authored* fact — a canonical
name, aliases, dates, a one-line role, and a **cited** `source` (a de.wikipedia.org facts
record, the metadata-only pattern of `tools/fetch_wikipedia.py`; copyright protects expression,
not facts, so consulting is free). The data lives in `grounding/entities/<domain>.json`; this
module reads it and is the resolver.

Why a registry (Wave C2): the Sachverhalt modules each re-state a person's dates or an event's
year in their own fact-set. Nothing stopped two modules from disagreeing (Napoleon born 1769 in
one, 1796 in another) — a silent corpus rot. The registry makes the facts canonical and *linkable*
(`Actor.entity_id`/`HistEvent.entity_id`); `pipeline/entity_lint.py` then scans the whole corpus
for contradictions, and `verwandte_module` finds every module that shares an entity.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..config import GROUNDING_ENTITIES
from ..schema.provenance import ProvenanceSource

EntityKind = Literal["person", "place", "event", "work"]


class EntityError(ValueError):
    """A registry-integrity failure (duplicate id, malformed entry) — a load-time guard."""


class Entity(BaseModel):
    """One canonical entity. Dates carry kind-appropriate semantics: a `person` has
    `born`/`died`; an `event`/`work` has `start`/`end`; a `place` has none. `year_range()`
    normalises them so the lint can compare a linked date against one envelope."""
    model_config = ConfigDict(extra="forbid")
    entity_id: str
    kind: EntityKind
    name: str                                   # the canonical name
    aliases: list[str] = Field(default_factory=list)
    born: int | None = None                     # person: birth year
    died: int | None = None                     # person: death year
    start: int | None = None                    # event/work: from year
    end: int | None = None                      # event/work: to year
    role: str                                   # a one-line description
    source: ProvenanceSource                    # cited (role="facts")
    domain: str = ""                            # set at load from the file stem (not in JSON)

    def year_range(self) -> tuple[int, int] | None:
        """The [lo, hi] year envelope this entity 'owns' (person life / event span), or None
        when it carries no dates (a place). A single known year collapses to (y, y)."""
        lo, hi = (self.born, self.died) if self.kind == "person" else (self.start, self.end)
        if lo is None and hi is None:
            return None
        lo = lo if lo is not None else hi
        hi = hi if hi is not None else lo
        return (lo, hi)  # type: ignore[return-value]

    def names(self) -> list[str]:
        """Canonical name + aliases — the strings a module might use to refer to this entity."""
        return [self.name, *self.aliases]

    def display_dates(self) -> str:
        r = self.year_range()
        if r is None:
            return ""
        lo, hi = r
        return str(lo) if lo == hi else f"{lo}–{hi}"


# --- loading -----------------------------------------------------------------
@lru_cache(maxsize=1)
def load_registry() -> dict[str, Entity]:
    """All entities, keyed by `entity_id`. Reads every `grounding/entities/*.json`. Raises
    `EntityError` on a duplicate id or a duplicate canonical name (the registry must be a
    single source of truth). Cached; call `load_registry.cache_clear()` in tests that swap data."""
    registry: dict[str, Entity] = {}
    by_name: dict[str, str] = {}
    if not GROUNDING_ENTITIES.exists():
        return registry
    for path in sorted(GROUNDING_ENTITIES.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        for ent in raw.get("entities", []):
            try:
                e = Entity.model_validate({**ent, "domain": path.stem})
            except Exception as exc:  # noqa: BLE001
                raise EntityError(f"{path.name}: ungültiger Eintrag {ent.get('entity_id')!r}: {exc}")
            if e.entity_id in registry:
                raise EntityError(f"doppelte entity_id {e.entity_id!r} "
                                  f"({path.name} und {registry[e.entity_id].domain})")
            key = e.name.casefold()
            if key in by_name:
                raise EntityError(f"doppelter kanonischer Name {e.name!r} "
                                  f"({e.entity_id} und {by_name[key]})")
            by_name[key] = e.entity_id
            registry[e.entity_id] = e
    return registry


def all_entities() -> list[Entity]:
    return sorted(load_registry().values(), key=lambda e: e.entity_id)


def get_entity(entity_id: str) -> Entity | None:
    return load_registry().get(entity_id)


def entities_by_domain() -> dict[str, list[Entity]]:
    out: dict[str, list[Entity]] = {}
    for e in all_entities():
        out.setdefault(e.domain, []).append(e)
    return out


# --- name resolution ---------------------------------------------------------
@lru_cache(maxsize=1)
def _alias_index() -> dict[str, str]:
    """Case-folded name/alias → entity_id. Canonical names win over aliases on collision, so a
    lookup stays deterministic even if two entities share a loose alias."""
    idx: dict[str, str] = {}
    for e in all_entities():                       # aliases first, then canonicals overwrite
        for a in e.aliases:
            idx.setdefault(a.casefold(), e.entity_id)
    for e in all_entities():
        idx[e.name.casefold()] = e.entity_id
    return idx


def find_by_name(name: str) -> Entity | None:
    """Exact (case-insensitive) canonical-name or alias lookup. None if unknown."""
    eid = _alias_index().get((name or "").strip().casefold())
    return get_entity(eid) if eid else None


@lru_cache(maxsize=1)
def _boundary_res() -> list[tuple[str, re.Pattern[str]]]:
    """(entity_id, compiled matcher) for every name/alias ≥ 4 chars — a left word-boundary,
    case-insensitive substring match (so 'Napoleon' finds 'Napoleons', 'Wien' finds 'Wiener').
    Only used for advisory discovery (verwandte_module keyword/label hits, the unlinked-name lint)."""
    out: list[tuple[str, re.Pattern[str]]] = []
    for e in all_entities():
        for token in e.names():
            if len(token) < 4:
                continue
            pat = re.compile(r"(?<![0-9A-Za-zÄÖÜäöüß])" + re.escape(token), re.IGNORECASE)
            out.append((e.entity_id, pat))
    return out


def match_entities(text: str) -> set[str]:
    """entity_ids whose canonical name or an alias occurs in `text` (advisory discovery)."""
    if not text:
        return set()
    return {eid for eid, pat in _boundary_res() if pat.search(text)}
