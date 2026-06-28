"""The prose-provenance gate (History/GPB asset class) — DETERMINISTIC, advisory.

The prose analogue of `figure_lint` (the (c)-label gate): it extends the project
invariant — every content-bearing claim is exactly one of (a) constructed / (b) sourced
+ cited / (c) illustrative — from *numbers* to *history prose*, via the expression-
provenance axis (`schema/provenance.py`).

Two complementary, structurally-checkable warnings (never blocking — like the (c)-label,
prose-fact detection is imperfect and a warning is the honest tool):

* **(A) consistency** — whenever a block CARRIES `provenance`, check it is coherent with the
  obligation: `adapted`/`quoted` must name a `role="expression"` source; an `adapted`
  redistribution needs a redistributable basis; a long verbatim `quoted` span exceeds the
  Austrian Zitatrecht (§42f öUrhG) into CC-BY-SA territory; a CC-BY-SA derivative trips
  ShareAlike (policy: `adapted` is discouraged — prefer original + short quote).
* **(B) facts-source required** — the *mandatory-internal* rule (the project's trust twist on
  the brief): an in-scope history fact block authored `original` must record at least one
  `role="facts"` source, so a Wikipedia-sourced fact is fact-checked at the review gate rather
  than asserted unchecked. A fact block with no provenance at all is the same warning.

**Scope** of (B): GPB worksheets (any served competence id starts with ``GPB.`` — the stable
catalog prefix) ∪ any block flagged `flags.historical_fact` (the cross-subject opt-in for GWB
local history, KUG art history). (A) applies wherever provenance is present, any subject.

The real *rights* gate (PD 70-p.m.a. math, redistribution licensing) lives at **ingest**
(Phase 4, where the date is in hand, cf. `orch.ingest_text`); here we only flag the
structurally-obvious, so verify stays date-free and advisory.
"""

from __future__ import annotations

from ..schema.enums import Role
from ..schema.provenance import SHORT_QUOTE_MAX_CHARS

# InfoBlock kinds that definitionally assert content (→ need a facts basis when historical).
# `callout` (note/tip/warning) is pedagogical scaffolding, not a factual claim → exempt.
_FACT_KINDS = {"prose", "key_fact", "example", "source_text"}


def _is_gpb(content) -> bool:
    """A worksheet is in the history asset class if it serves a GPB competence (robust:
    the catalog id prefix, not the display subject name) — falls back to the subject name."""
    for b in content.iter_blocks():
        for s in getattr(b, "serves", []):
            if (s.competence_id or "").startswith("GPB."):
                return True
    return "Geschichte" in (getattr(content.meta, "subject", "") or "")


def _check_consistency(block_id: str, prov) -> list[str]:
    """(A): a block that carries provenance must be coherent with its declared obligation."""
    out: list[str] = []
    origin = prov.expression_origin
    if origin == "original":
        return out  # nothing to embed → handled by the (B) facts-source rule
    exprs = prov.expression_sources()
    if not exprs:
        out.append(
            f"{block_id}: expression_origin='{origin}', aber keine role='expression'-Quelle — "
            f"die Formulierung stammt aus einer Quelle; diese als role='expression' eintragen.")
    if origin == "adapted":
        for s in exprs:
            if not s.redistributable:
                out.append(
                    f"{block_id}: adaptierte (paraphrasierte) Quelle '{s.title}' nicht als "
                    f"redistributable markiert — Einbettung braucht eine nachnutzbare Lizenz "
                    f"(beim Ingest geprüft), sonst nur referenzieren.")
    if origin == "quoted":
        for s in exprs:
            if s.quote_span and len(s.quote_span) > SHORT_QUOTE_MAX_CHARS:
                out.append(
                    f"{block_id}: langes wörtliches Zitat ({len(s.quote_span)} Zeichen) — über "
                    f"das Zitatrecht (§42f UrhG) hinaus; als CC-BY-SA-Nutzung prüfen oder kürzen.")
    if prov.share_alike_applies:
        out.append(
            f"{block_id}: CC-BY-SA-{origin} → ShareAlike kann das ganze Arbeitsblatt erfassen "
            f"(Policy: 'adapted' vermeiden — lieber original aus Fakten + kurzes Zitat).")
    return out


def lint_content(content) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    gpb = _is_gpb(content)
    for b in content.iter_blocks():
        prov = getattr(b, "provenance", None)
        flags = getattr(b, "flags", None)
        in_scope = gpb or bool(flags and getattr(flags, "historical_fact", False))

        if prov is not None:
            warnings += _check_consistency(b.id, prov)
            # the mandatory-internal facts-source record for an in-scope original fact block
            if (in_scope and prov.expression_origin == "original"
                    and not prov.facts_sources()):
                warnings.append(
                    f"{b.id}: Geschichts-Faktenblock (original) ohne role='facts'-Quelle — die "
                    f"recherchierte Quelle (z. B. Wikipedia) eintragen, damit der Fakt am "
                    f"Review-Gate geprüft werden kann (Pflicht-intern, nicht gerendert).")
            continue

        # no provenance at all → only an in-scope fact-bearing InfoBlock is flagged
        if in_scope and b.role == Role.INFO and b.kind in _FACT_KINDS:
            warnings.append(
                f"{b.id}: Geschichts-Faktenblock ohne Provenienz — Quelle als role='facts' "
                f"(recherchiert) eintragen oder als illustrative/schematisch kennzeichnen.")
    return problems, warnings
