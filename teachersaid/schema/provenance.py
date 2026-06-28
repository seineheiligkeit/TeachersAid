"""Expression provenance — the third provenance axis (the History/GPB asset class).

The project already models two kinds of provenance:
* **fact provenance** for numbers — `SourceRef`/`DataRef` (where a *number* came from);
* **rights provenance** for whole texts — `TextSourceRef.is_clear()` (may we redistribute
  *this text*).

This adds the third, per-block axis the History asset class needs: **expression
provenance** — *where the wording came from*. Copyright protects expression, not facts:
CC BY-SA's attribution + ShareAlike attach to Wikipedia's specific wording/selection/
arrangement, never to the underlying facts. So the question we track per block is not
"where did the facts come from?" but "where did the *expression* come from?" — encoded as
`expression_origin ∈ original | adapted | quoted`.

The trust twist (the project discipline, harder than the law requires): an `original`
history block authored *from* facts read off a source must still record that source with
`role="facts"` — legally optional ("editorial transparency"), but **mandatory-internal**
here, so a Wikipedia-sourced fact is fact-checked at the review gate rather than asserted
unchecked. See `Documents/history-facts-provenance-design.md`.

The obligation booleans are DERIVED (computed, never authored) — the same discipline as
`Nachweis`/`DepthProfile`: the model declares `expression_origin` + `sources`; it may not
produce `attribution_required`/`share_alike_applies`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

# where a block's WORDING came from — the legal-obligation pivot
ExpressionOrigin = Literal[
    "original",   # authored fresh (from facts, or wholly own) → no obligation, renders clean
    "adapted",    # close paraphrase tracking a source → CC BY-SA derivative (attribution + ShareAlike)
    "quoted",     # verbatim quotation → short = Zitatrecht (§42f öUrhG); long = CC BY-SA
]

# what a recorded source was USED for (per the facts-vs-expression line)
SourceRole = Literal[
    "facts",       # consulted for information only — no obligation (the mandatory-internal record)
    "expression",  # this block's wording derives from the source's wording — obligation attaches
]

# a verbatim span at/under this length rides the Austrian Zitatrecht (§42f öUrhG) — a short
# attributed citation, not a redistribution; longer is CC-BY-SA territory (rights gate + prose_lint)
SHORT_QUOTE_MAX_CHARS = 300


class ProvenanceSource(BaseModel):
    """One source behind a block. A `role="facts"` Wikipedia entry on an `original` block
    is the normal, clean case (consulted, no obligation); a `role="expression"` entry marks
    wording that derives from the source (attribution attaches). Reuses the rights vocabulary
    of `SourceRef`/`TextSourceRef` (licence, AT-p.m.a. year, redistributable) so the three
    provenance axes stay consistent."""
    model_config = ConfigDict(extra="forbid")
    title: str
    url: str | None = None
    publisher: str | None = None          # "Wikipedia (de)", "ANNO/ÖNB", …
    licence: str | None = None            # "CC-BY-SA-4.0" | "public-domain" | "CC-BY-4.0" | …
    licence_url: str | None = None
    retrieved: str | None = None          # ISO date the source was consulted
    role: SourceRole                      # "facts" = no obligation; "expression" = obligation
    redistributable: bool = False         # may the wording be embedded? (gated at ingest, path #2)
    author_death_year: int | None = None  # AT 70-Jahre-p.m.a. check for a PD `expression` source
    quote_span: str | None = None         # the verbatim snippet, for `quoted` (length → review flag)

    def rights_clear(self, today_year: int) -> tuple[bool, list[str]]:
        """May this source's WORDING be embedded/redistributed? (A `role="facts"` source never
        needs this — consulting is free; only embedded `expression` is gated.) Mirrors
        `TextSourceRef.is_clear`: an explicit `redistributable`, a CC licence, or PD by the AT
        70-Jahre-p.m.a. rule (NOT US PD) clears it. Returns (ok, reasons-if-not)."""
        if self.redistributable:
            return True, []
        lic = (self.licence or "").strip().lower()
        if lic in ("public-domain", "public domain", "pd", "gemeinfrei"):
            if self.author_death_year is None:
                return False, [f"„{self.title}“: gemeinfrei angegeben, aber author_death_year fehlt "
                               f"(AT 70-Jahre-p.m.a.)"]
            if today_year - self.author_death_year < 70:
                return False, [f"„{self.title}“: Autor † {self.author_death_year} — noch nicht "
                               f"70 Jahre p.m.a. (in AT noch geschützt)"]
            return True, []
        if lic.startswith("cc-by") or lic.startswith("cc0") or lic.startswith("cc by"):
            return True, []   # CC permits redistribution (BY-SA adds ShareAlike, recorded separately)
        return False, [f"„{self.title}“: keine nachnutzbare Grundlage (Lizenz {self.licence!r}, "
                       f"redistributable=False)"]


class BlockProvenance(BaseModel):
    """Per-block expression provenance + the sources behind it. Attaches to `BlockBase`
    (both InfoBlock and TaskBlock — a TaskBlock can embed source-derived stimulus). Absent
    on the common case (math, wholly-original prose with no consulted source)."""
    model_config = ConfigDict(extra="forbid")
    expression_origin: ExpressionOrigin = "original"
    sources: list[ProvenanceSource] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _drop_derived(cls, data):
        """The obligation booleans are computed, never authored — strip them on input so a
        model_dump()→model_validate() round-trip (the JsonStore path) is clean and an LLM
        echoing them is absorbed, not rejected. Genuine unknown keys still hit extra=forbid."""
        if isinstance(data, dict):
            data = {k: v for k, v in data.items()
                    if k not in ("attribution_required", "share_alike_applies")}
        return data

    # --- DERIVED (computed, never authored): the legal obligation the renderer keys on ---
    @computed_field  # type: ignore[prop-decorator]
    @property
    def attribution_required(self) -> bool:
        """Render a source/attribution line only when the wording is not our own."""
        return self.expression_origin != "original"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def share_alike_applies(self) -> bool:
        """A CC BY-SA derivative can push the whole worksheet under ShareAlike — flagged,
        not silently inherited (policy: `adapted` is discouraged; prefer original/quoted)."""
        return self.attribution_required and any(
            (s.licence or "").upper().startswith("CC-BY-SA") for s in self.sources
        )

    def facts_sources(self) -> list[ProvenanceSource]:
        return [s for s in self.sources if s.role == "facts"]

    def expression_sources(self) -> list[ProvenanceSource]:
        return [s for s in self.sources if s.role == "expression"]

    def rights_gate(self, today_year: int) -> tuple[bool, list[str]]:
        """The ingest gate (the `ingest_text` analogue): may this block's embedded wording be
        redistributed? `original` (nothing embedded) is always clear; a short `quoted` span rides
        the Zitatrecht (attribution suffices); otherwise every `expression` source must be
        rights-clear. Compliance is legal, not cosmetic — a fail blocks staging."""
        if self.expression_origin == "original":
            return True, []
        exprs = self.expression_sources()
        if not exprs:
            return False, [f"expression_origin='{self.expression_origin}', aber keine "
                           f"role='expression'-Quelle eingetragen"]
        problems: list[str] = []
        for s in exprs:
            if self.expression_origin == "quoted":
                span = s.quote_span or ""
                if 0 < len(span) <= SHORT_QUOTE_MAX_CHARS:
                    continue   # short citation under §42f öUrhG — attribution rendered, no licence needed
            ok, reasons = s.rights_clear(today_year)
            problems += reasons
        return (not problems), problems
