"""Master library of curated 'great worksheet' example content objects.

Each `Example` is a hand-authored `WorksheetContent` builder grounded in the
`lehrplan/` catalog (correct competence IDs, dimensions, Fassung). These serve two
roles:

1. **Offline demo content.** The orchestrator's offline path (`_generate_content`)
   serves these when there is no `ANTHROPIC_API_KEY`, so the dashboard exercises the
   full content→render→review loop without the LLM. With a key, the same flow
   generates fresh content for any catalog subject/topic.
2. **Gold seeds.** They are the few-shot references and the quality bar for what a
   "great" worksheet looks like (see `Documents/master-library-plan.md`).

`seed_library()` pushes every example through the pipeline into the review store as
a *pending content item* — i.e. straight into the dashboard's Gate-2 review queue.
The persistent library is the version-controlled builder modules; the store is just
the review/approval surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from ..demo import strahlung, worked_examples
from ..schema.worksheet import WorksheetContent
from . import bio_immunsystem


@dataclass(frozen=True)
class Example:
    key: str          # stable identifier
    subject: str      # must map to a catalog subject (see lehrplan_store aliases)
    klasse: int
    topic: str        # the request topic; must resolve to Kompetenzbereiche
    build: Callable[[], WorksheetContent]


# First pass — the MINT wedge, fully catalog-integrated and verify-clean.
EXAMPLES: list[Example] = [
    Example("phy-strahlung", "Physik", 4, "Strahlung und Radioaktivität",
            strahlung.build_content),
    Example("bio-immunsystem", "Biologie", 4, "Immunsystem und Impfungen",
            bio_immunsystem.build_content),
    Example("mat-unfaires-spiel", "Mathematik", 4, "Daten und Zufall",
            worked_examples.build_math_unfair_game),
]


def find(subject: str, topic: str) -> Example | None:
    """The example whose subject matches and whose topic overlaps the request."""
    s = subject.strip().casefold()
    t = (topic or "").casefold()
    for ex in EXAMPLES:
        if ex.subject.casefold() == s and (ex.topic.casefold() in t or t in ex.topic.casefold()):
            return ex
    return None


def seed_library(store=None, *, today: date | None = None) -> list:
    """Run every example through the pipeline into the review store as a pending
    content item (so it lands in the dashboard's review queue). Returns the items."""
    from ..pipeline import orchestrator as orch
    from ..schema.worksheet import BundleRequest
    from ..store.repository import ReviewStore

    store = store or ReviewStore()
    out = []
    for ex in EXAMPLES:
        req = BundleRequest(subject=ex.subject, klasse=ex.klasse, topic_raw=ex.topic)
        idea = orch.submit_on_demand(store, req, today=today)
        content = orch.approve_idea(store, idea.id)  # offline path serves ex.build()
        out.append(content)
    return out
