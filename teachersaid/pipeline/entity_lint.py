"""The corpus-global entity lint — DETERMINISTIC, the guard against cross-module fact rot.

`pipeline/sachverhalt_lint.py` guards ONE module's authored prose against ITS OWN fact-set.
This lint guards the whole corpus against the *entity registry* (`grounding/entities.py`): every
module that links a canonical entity must agree with it, and no two modules may quietly assert
conflicting dates for the same entity. Names/dates are curated facts (select-never-author); this
is the machine check that keeps them consistent as the corpus grows.

Three checks (design mandate Wave C2):

* **(c) a linked date contradicts the registry — HARD.** A `HistEvent` linked to an entity whose
  numeric `at` falls outside the entity's year range (e.g. an event linked to `napoleon-bonaparte`
  dated 1850, after his 1821 death). Also fires on an `entity_id` that is not in the registry
  (a dangling link). Run in the ingest gate.
* **(a) the same entity_id carries conflicting dates anywhere — HARD (corpus scan).** Aggregated
  across every module: a point-in-time entity linked to two different years is a genuine conflict.
* **(b) a name matches a registry alias but carries no entity_id — ADVISORY.** A likely-missing
  link, surfaced (not blocked) so a curator can wire it. Also: an `AnnotatedText` whose
  `author_death_year` disagrees with the registry person it names (a real cross-source check).

`check_module` (module vs registry) is self-contained and drives the gate; `scan_corpus` adds the
cross-module aggregate; `verwandte_module` is the read-only "related modules" query.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..grounding.entities import Entity, get_entity, load_registry, match_entities


@dataclass(frozen=True)
class Finding:
    """One lint result. `severity` gates behaviour: 'problem' blocks the ingest gate, 'warning'
    is advisory. `module` is the sachverhalt/text id; `entity_id` the entity at issue (if any)."""
    severity: str            # "problem" | "warning"
    code: str                # "unknown_link" | "date_contradiction" | "cross_module_conflict"
    #                          | "unlinked_alias" | "author_date_mismatch"
    module: str
    message: str
    entity_id: str | None = None

    def format(self) -> str:
        mark = "PROBLEM" if self.severity == "problem" else "Hinweis"
        return f"[{mark}] {self.module}: {self.message}"


def _reg(registry: dict[str, Entity] | None) -> dict[str, Entity]:
    return registry if registry is not None else load_registry()


def _linked(sv) -> list[tuple[str, str, object]]:
    """(carrier_kind, entity_id, carrier) for every linked Actor/HistEvent in the module."""
    out: list[tuple[str, str, object]] = []
    for a in sv.actors:
        if getattr(a, "entity_id", None):
            out.append(("actor", a.entity_id, a))
    for e in sv.timeline:
        if getattr(e, "entity_id", None):
            out.append(("event", e.entity_id, e))
    return out


# --- per-module checks (drive the ingest gate) -------------------------------
def check_module(sv, *, registry: dict[str, Entity] | None = None) -> tuple[list[str], list[str]]:
    """Check ONE Sachverhalt against the registry. Returns (problems, warnings) — the same shape
    as `sachverhalt_lint.lint`, so the ingest gate composes them. HARD: a dangling entity_id, or a
    linked event whose year contradicts the registry. ADVISORY: an unlinked name that matches a
    registry alias (likely should link)."""
    reg = _reg(registry)
    problems: list[str] = []
    warnings: list[str] = []

    linked_ids: set[str] = set()
    for carrier_kind, eid, carrier in _linked(sv):
        linked_ids.add(eid)
        ent = reg.get(eid)
        if ent is None:
            problems.append(
                f"{carrier_kind} „{_carrier_name(carrier)}“ verweist auf entity_id "
                f"'{eid}', die es im Register nicht gibt (grounding/entities).")
            continue
        if carrier_kind == "event":
            msg = _event_date_problem(carrier, ent)
            if msg:
                problems.append(msg)

    # (b) advisory: an actor/event whose name matches a registry entity but isn't linked
    for a in sv.actors:
        if getattr(a, "entity_id", None):
            continue
        hit = _sole_match(a.name, reg)
        if hit and hit not in linked_ids:
            warnings.append(
                f"Akteur „{a.name}“ passt zu Registereintrag '{hit}', ist aber nicht verlinkt "
                f"(entity_id fehlt) — vermutlich verknüpfen.")
    for e in sv.timeline:
        if getattr(e, "entity_id", None):
            continue
        hit = _sole_match(e.label, reg)
        if hit and hit not in linked_ids:
            warnings.append(
                f"Ereignis „{e.label}“ passt zu Registereintrag '{hit}', ist aber nicht verlinkt "
                f"(entity_id fehlt) — vermutlich verknüpfen.")
    return problems, warnings


def _carrier_name(carrier) -> str:
    return getattr(carrier, "name", None) or getattr(carrier, "label", "?")


def _event_date_problem(event, ent: Entity) -> str | None:
    """A linked HistEvent whose numeric `at` is outside the entity's year range → a message."""
    at = event.at
    if not isinstance(at, int):
        return None
    rng = ent.year_range()
    if rng is None:
        return None
    lo, hi = rng
    if lo <= at <= hi:
        return None
    return (f"Ereignis „{event.label}“ ist mit '{ent.entity_id}' ({ent.display_dates()}) "
            f"verknüpft, nennt aber das Jahr {at} — das widerspricht dem Register.")


def _sole_match(text: str, reg: dict[str, Entity]) -> str | None:
    """The single registry entity whose name/alias occurs in `text`, else None (ambiguous or no
    match → no advisory, to keep the false-positive rate low)."""
    hits = match_entities(text)
    hits &= reg.keys()
    return next(iter(hits)) if len(hits) == 1 else None


# --- corpus-global scan ------------------------------------------------------
def scan_corpus(*, sachverhalte: Iterable | None = None, texts: Iterable | None = None,
                registry: dict[str, Entity] | None = None) -> list[Finding]:
    """Scan the whole corpus. Runs `check_module` per Sachverhalt, then the cross-module aggregate
    (a) — a point-in-time entity linked to two different years anywhere — and the text
    author-date cross-check. `sachverhalte`/`texts` default to the live corpus (`gather_corpus`)."""
    reg = _reg(registry)
    if sachverhalte is None or texts is None:
        g_sv, g_tx = gather_corpus()
        sachverhalte = g_sv if sachverhalte is None else sachverhalte
        texts = g_tx if texts is None else texts

    findings: list[Finding] = []
    # observations of an entity's date across the corpus: entity_id → {year → {modules}}
    obs: dict[str, dict[int, set[str]]] = {}

    for sv in sachverhalte:
        probs, warns = check_module(sv, registry=reg)
        for p in probs:
            code = "unknown_link" if "im Register nicht gibt" in p else "date_contradiction"
            findings.append(Finding("problem", code, sv.id, p))
        for w in warns:
            findings.append(Finding("warning", "unlinked_alias", sv.id, w))
        for _kind, eid, carrier in _linked(sv):
            if _kind == "event" and isinstance(carrier.at, int):
                obs.setdefault(eid, {}).setdefault(carrier.at, set()).add(sv.id)

    # (a) cross-module: a point event linked to two different years is a real conflict
    for eid, years in obs.items():
        ent = reg.get(eid)
        if ent is None or len(years) < 2:
            continue
        rng = ent.year_range()
        if rng and rng[0] == rng[1]:                       # a point-in-time entity
            spread = ", ".join(f"{y} ({'/'.join(sorted(mods))})" for y, mods in sorted(years.items()))
            findings.append(Finding(
                "problem", "cross_module_conflict", "/".join(sorted({m for ms in years.values() for m in ms})),
                f"Entität '{eid}' ({ent.display_dates()}) wird mit widersprüchlichen Jahren "
                f"verknüpft: {spread}.", entity_id=eid))

    # text author-date cross-check (advisory): a named author vs the registry person
    for t in texts or []:
        src = getattr(t, "source", None)
        author = getattr(src, "author", "") or ""
        died = getattr(src, "author_death_year", None)
        if not author or died is None:
            continue
        cand = [get_entity(e) for e in match_entities(author) if e in reg]
        persons = [c for c in cand if c and c.kind == "person" and c.died is not None]
        if persons and all(c.died != died for c in persons):
            names = ", ".join(f"{c.entity_id}†{c.died}" for c in persons)
            findings.append(Finding(
                "warning", "author_date_mismatch", getattr(t, "id", "?"),
                f"Text nennt Autor „{author}“ mit Sterbejahr {died}, das Register sagt {names}.",
                entity_id=persons[0].entity_id))
    return findings


def problems(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == "problem"]


# --- the derived joy: related modules ----------------------------------------
def verwandte_module(entity_id: str, *, sachverhalte: Iterable | None = None,
                     texts: Iterable | None = None,
                     registry: dict[str, Entity] | None = None) -> list[dict]:
    """Every corpus module that shares an entity — the 'related modules' query. A module relates
    'via' an explicit `entity_id` link (strong), a name/keyword/label reference (discovery), or, for
    a text, its named author. Links are listed first. Returns [] for an unknown/unshared entity."""
    reg = _reg(registry)
    ent = reg.get(entity_id)
    if ent is None:
        return []
    if sachverhalte is None or texts is None:
        g_sv, g_tx = gather_corpus()
        sachverhalte = g_sv if sachverhalte is None else sachverhalte
        texts = g_tx if texts is None else texts

    out: list[dict] = []
    for sv in sachverhalte:
        via = None
        if any(eid == entity_id for _k, eid, _c in _linked(sv)):
            via = "link"
        else:
            hay = " ".join([sv.topic, *sv.keywords, *[a.name for a in sv.actors],
                            *[e.label for e in sv.timeline], *[c.term for c in sv.concepts],
                            *[r.name for r in sv.regions]])
            if entity_id in match_entities(hay):
                via = "reference"
        if via:
            out.append({"module_id": sv.id, "module_kind": "sachverhalt",
                        "subject": sv.subject, "topic": sv.topic, "via": via})
    for t in texts or []:
        author = getattr(getattr(t, "source", None), "author", "") or ""
        if entity_id in match_entities(author):
            out.append({"module_id": getattr(t, "id", "?"), "module_kind": "text",
                        "subject": getattr(t, "subject", ""),
                        "topic": getattr(t, "title", ""), "via": "author"})
    out.sort(key=lambda r: (r["via"] != "link", r["module_kind"], r["module_id"]))
    return out


# --- corpus gathering (lazy — avoids import cycles) --------------------------
def gather_corpus():
    """(sachverhalte, texts) across the whole in-repo corpus: the curated library flagships +
    everything staged in the stores, deduped by id (a staged record wins over its library seed).
    Lazily imported so `entity_lint` stays cheap to import."""
    from ..library.sachverhalte import SACHVERHALTE
    from ..library.texts import ANNOTATED_TEXTS
    from ..store.sachverhaltstore import SachverhaltStore
    from ..store.textstore import TextStore

    svs: dict[str, object] = {sv.id: sv for sv in SACHVERHALTE}
    try:
        for rec in SachverhaltStore().list():
            svs[rec.sachverhalt.id] = rec.sachverhalt
    except Exception:  # noqa: BLE001 — a missing/empty store must not break the query
        pass
    texts: dict[str, object] = {t.id: t for t in ANNOTATED_TEXTS}
    try:
        for rec in TextStore().list():
            texts[rec.text.id] = rec.text
    except Exception:  # noqa: BLE001
        pass
    return list(svs.values()), list(texts.values())
