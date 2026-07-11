"""Wave-B hybrid image flagship: generated flower base + code labels."""
from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..pipeline.labeled_diagram import FLOWER_HYBRID_SPEC
from ..schema.assets import Asset
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

SUBJECT = "Biologie"
KLASSE = 1
TOPIC = "Vielfalt und Aufbau von Blütenpflanzen"
INTENDED_CLAIM = (
    "Stylized longitudinal section of one generalized bisexual flower, showing petals, "
    "sepals, stamens, and a continuous central pistil with stigma, style, ovary, and ovules."
)


def build_content() -> WorksheetContent:
    model = store.get_subject_model(SUBJECT)
    fassung = store.get_fassung()
    student = Asset(
        id="bio-flower-parts-student",
        role="figure",
        lane="content",
        generator="matplotlib:labeled_parts",
        spec={**FLOWER_HYBRID_SPEC, "show_names": False},
        correctness_surface=(
            "Numbers, leader targets and the answer list are derived from one curated parts list; "
            "the raster contributes no labels or task data."
        ),
        illustrative=True,
        caption="Vereinfachtes Blütenmodell; Rasterbasis separat als depictive geprüft.",
    )
    teacher = student.model_copy(deep=True, update={
        "id": "bio-flower-parts-teacher",
        "spec": {**FLOWER_HYBRID_SPEC, "show_names": True},
    })
    task = TaskBlock(
        id="flower.t1",
        kind="structure_overview",
        prompt=(
            "Beschrifte die nummerierten Teile des vereinfachten Blütenmodells. "
            "Ordne anschließend Narbe, Griffel und Fruchtknoten als zusammenhängende "
            "Teile des Stempels ein."
        ),
        response={"mode": "lines", "n": 7},
        cognitive_level="understand",
        dimensions=["W"],
        serves=[{"competence_id": "BIO.US.x.WIS.01", "relation": "exercises"}],
        est_minutes=12,
        asset_refs=[student.id],
        solution_asset_refs=[teacher.id],
        answer_key=(
            "1 Kronblatt · 2 Kelchblatt · 3 Staubbeutel · 4 Narbe · 5 Griffel · "
            "6 Fruchtknoten · 7 Samenanlage. Narbe, Griffel und Fruchtknoten bilden "
            "im vereinfachten Modell den Stempel."
        ),
        watch_outs=[
            "SME muss vor Freigabe prüfen, ob die depictive Rasterbasis den deklarierten "
            "Claim erfüllt; die Grafik ist ein vereinfachtes Modell, keine universelle Blütenform."
        ],
    )
    return WorksheetContent(
        meta=WorksheetMeta(
            title="Die Blüte beschriften",
            subtitle="Hybrid-Abbildung: geprüfte Rasterbasis, Beschriftung aus Code",
            subject=SUBJECT,
            stufe="Unterstufe",
            klasse=KLASSE,
            kernfrage="Wie arbeiten die sichtbaren Teile einer Blüte als zusammenhängendes Modell?",
            fassung=fassung,
            lehrplan_label=(
                "Biologie und Umweltbildung · 1. Klasse · Vielfalt und Angepasstheit "
                "sowie Grundzüge der Systematik von Blütenpflanzen"
            ),
        ),
        subject_model=model,
        intro=[InfoBlock(
            id="flower.i1",
            kind="prose",
            content=(
                "Die Abbildung zeigt ein vereinfachtes, verallgemeinertes Blütenmodell. "
                "Echte Blüten können deutlich anders aussehen; hier werden ausgewählte "
                "Strukturen sichtbar gemacht, damit ihre Lage zueinander untersucht werden kann."
            ),
        )],
        sections=[Baustein(id="flower.parts", title="Bauteile im Zusammenhang", blocks=[task])],
        assets=[student, teacher],
    )
