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
from .decorative import seed_assets  # noqa: F401 — re-exported (decorative kit seeder)


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
    """Run every example through the full pipeline (brainstorm → flesh out) into the
    review store as a pending content item, so it lands in the dashboard's review
    queue ready for approval into the library. Returns the content items."""
    from ..pipeline import orchestrator as orch
    from ..store.repository import ReviewStore

    store = store or ReviewStore()
    out = []
    for ex in EXAMPLES:
        bs = orch.submit_brainstorm(
            store, ex.subject, ex.klasse, ex.topic,
            note="Master-Library-Beispiel (kuratiert).", source="ai",
        )
        orch.approve_brainstorm(store, bs.id)
        out.append(orch.flesh_out(store, bs.id, today=today))  # offline path serves ex.build()
    return out


def seed_arrangements(store=None, *, today: date | None = None) -> list:
    """Stage the curated Lernarrangement hero(es) into the arrangement store for
    review (assemble → verify → render the bundle). Idempotent: `upsert` preserves
    status. New for v0.5 (Phase 5); the GWB Gemeinderat-Planspiel is the first hero."""
    from ..demo import gwb_standort
    from ..pipeline import arrange
    from ..store.arrangementstore import ArrangementStore

    store = store or ArrangementStore()
    return [arrange.stage_arrangement(
        store, gwb_standort.build_arrangement(), arr_id="gwb-standort",
        source="curated", today=today)]


def seed_datasets(store=None, *, status: str = "in_review") -> list:
    """Stage the curated grounded-facts datasets (grounding/data/) into the dataset
    store for HITL review. Idempotent: `upsert` preserves status. New for the
    grounded-facts data layer; the Statistik-Austria population data is the first."""
    from ..pipeline import orchestrator as orch

    return orch.seed_datasets(store, status=status)


def seed_texts(store=None, *, status: str = "in_review") -> list:
    """Stage the curated annotated authentic texts (library/texts.py) into the text
    store for HITL review (cf. seed_datasets). The Deutsch asset class."""
    from ..pipeline import orchestrator as orch

    return orch.seed_texts(store, status=status)


def seed_history(store=None, *, today: date | None = None) -> list:
    """Stage the curated History asset-class flagship (GPB 'Der Wiener Kongress') as a
    content item for Gate-2 review. The worksheet carries expression provenance (an
    original-from-Wikipedia-facts learn text + a real PD primary source quoted under
    Zitatrecht); verify runs the prose + rights gates. Cf. seed_texts/seed_datasets."""
    from ..pipeline import orchestrator as orch
    from ..pipeline.resolve import resolve_grade
    from ..store.repository import ReviewStore
    from . import gpb_wiener_kongress as wk

    store = store or ReviewStore()
    res = resolve_grade(wk.SUBJECT, 3, today=today)
    return [orch.stage_worksheet(store, wk.build_content(), res, source="curated")]


def seed_sachverhalte(store=None, *, status: str = "in_review") -> list:
    """Stage the curated Sachverhalte (library/sachverhalte.py) into the Sachverhalt store
    for HITL review (the content/exposition layer — fact-check the facts + sources before a
    worksheet derives from them). Idempotent: `upsert` preserves status. Cf. seed_texts."""
    from ..pipeline import orchestrator as orch

    return orch.seed_sachverhalte(store, status=status)


def seed_blocks(store=None, *, status: str = "approved") -> list:
    """Harvest every example worksheet's blocks into the block library. These come
    from the curated, SME-reviewed examples, so they seed straight as `approved`
    (the library the composer draws on). Idempotent: `upsert` preserves the status
    of blocks that already exist, so this never un-approves or re-approves edits."""
    from .block import harvest
    from ..store.blockstore import BlockStore

    store = store or BlockStore()
    out = []
    for ex in EXAMPLES:
        for lb in harvest(ex.build(), example_key=ex.key):
            lb.status = status
            out.append(store.upsert(lb))
    return out
