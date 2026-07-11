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
    status. The GWB Gemeinderat-Planspiel is the v0.5 hero; the two FS1 Realien
    (`realie_arrange.build_arrangement`) are wrapped as Lernarrangements (Realien Phase 2b)
    — the Realie worksheet as role material, the speaking as an interaction anchor."""
    from ..demo import gwb_standort
    from ..pipeline import arrange
    from ..pipeline.realie_arrange import build_arrangement as build_realie_arrangement
    from ..store.arrangementstore import ArrangementStore
    from .realie_bahnhof import BAHNHOF
    from .realie_cafe import CAFE

    store = store or ArrangementStore()
    out = [arrange.stage_arrangement(
        store, gwb_standort.build_arrangement(), arr_id="gwb-standort",
        source="curated", today=today)]
    for at, rid in [(BAHNHOF, "realie-bahnhof"), (CAFE, "realie-cafe")]:
        out.append(arrange.stage_arrangement(
            store, build_realie_arrangement(at, today=today), arr_id=rid,
            source="curated", today=today))
    return out


def seed_uet_arrangements(arrangement_store=None, block_store=None, *, today: date | None = None) -> list:
    """Stage the fächerübergreifende Projektwoche flagship (Wave C3) from the APPROVED block
    corpus: ÜT 11 (Umweltbildung für nachhaltige Entwicklung), Klasse 4 — the ÜT×Klasse with
    the widest science+geography approved-block spread (Physik · Geographie · Technik · Biologie
    · Chemie). `compose_uet` assembles one small worksheet per subject, wraps them as a
    Lernarrangement whose shared Projektwoche product anchors a ÜT competence no single sheet
    reaches, and stages it for Gate-2 review. Idempotent (stable arr_id). Composed, not authored:
    it needs an approved block corpus; a thin corpus yields an honest gap (nothing staged)."""
    from ..pipeline import orchestrator as orch
    from ..store.arrangementstore import ArrangementStore
    from ..store.blockstore import BlockStore

    arrangement_store = arrangement_store or ArrangementStore()
    block_store = block_store or BlockStore()
    return [orch.compose_uet_arrangement(
        arrangement_store, block_store, 11, 4, "doppelstunde",
        arr_id="uet-umweltbildung-4", source="curated", today=today)]


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


def seed_wahl(store=None, *, today: date | None = None) -> list:
    """Stage the Wahl-Werkstatt (GPB, Politische Bildung, 4. Kl.): two sampled Übungsreihen
    (D'Hondt-Mandatsverteilung · Koalitionsarithmetik) plus the Nationalratswahl-2024
    showcase (real cited BMI data, CC BY 4.0). Every sheet carries the didaktische-
    Vereinfachung note (pipeline/wahl.py). Cf. seed_history — the seat allocations are
    COMPUTED (d'Hondt / minimal winning coalitions), the numbers real or clean-sampled."""
    from ..pipeline import wahl
    from ..store.repository import ReviewStore

    store = store or ReviewStore()
    return wahl.stage_wahl_werkstatt(store, today=today)


def seed_hybrid_image(store=None, *, today: date | None = None) -> list:
    """Stage the BIO flower raster+code flagship for Gate-2 review."""
    from ..pipeline import orchestrator as orch
    from ..pipeline.resolve import resolve_grade
    from ..store.repository import ReviewStore
    from . import bio_bluete_hybrid as flower

    store = store or ReviewStore()
    res = resolve_grade(flower.SUBJECT, flower.KLASSE, today=today)
    return [orch.stage_worksheet(store, flower.build_content(), res, source="curated")]


def seed_anno_quellenarbeit(store=None, *, today: date | None = None) -> list:
    """Stage the referenced-only ANNO/ÖNB newspaper-source worksheet for Gate-2 review."""
    from ..pipeline import orchestrator as orch
    from ..pipeline.resolve import resolve_grade
    from ..store.repository import ReviewStore
    from . import gpb_anno_quellenarbeit as anno

    store = store or ReviewStore()
    res = resolve_grade(anno.SUBJECT, anno.KLASSE, today=today)
    return [orch.stage_worksheet(store, anno.build_content(), res, source="curated")]


def seed_textsorten(store=None, *, today: date | None = None) -> list:
    """Stage the curated Deutsch Textsorten-scaffold worksheets (the German genre layer —
    teach a Textsorte richly and EARLIER than the Matura merely checks it) as content items
    for Gate-2 review. Mirrors `seed_history` (`orch.stage_worksheet`): the top-3 SRDP
    Textsorten by archive frequency — Zusammenfassung (3. Kl.) · Kommentar (4. Kl.) ·
    Textinterpretation (4. Kl.) — each a verstehen→planen→verfassen scaffold anchored to a
    real Schreiben-competence. See `Documents/matura-deutsch-coverage.md`."""
    from ..pipeline import orchestrator as orch
    from ..pipeline.textsorte_scaffold import build_worksheet
    from ..store.repository import ReviewStore

    store = store or ReviewStore()
    out = []
    for tsid, kl in (("zusammenfassung", 3), ("kommentar", 4), ("textinterpretation", 4)):
        content, res = build_worksheet(tsid, kl, today=today)
        out.append(orch.stage_worksheet(store, content, res, source="curated"))
    return out


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
