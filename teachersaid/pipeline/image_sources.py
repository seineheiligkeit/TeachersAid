"""Ingest and derive GPB/BE worksheets from curated historical images.

This is the image analogue of ``text_tasks``.  The exact file is selected and
rights-gated once; Beschreibung, Analyse and Interpretation tasks are projections
of curated annotations, so no answer is authored at worksheet-build time.
"""

from __future__ import annotations

import hashlib
import shutil
from datetime import date
from pathlib import Path

from PIL import Image

from ..schema.assets import Asset, AssetProvenance
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.image_sources import ImageAnnotation, ImageSource
from ..schema.response import BoxResponse, LinesResponse
from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta
from ..store.imagesourcestore import ImageSourceRecord


def _sha1(path: Path) -> str:
    digest = hashlib.sha1()  # noqa: S324 - Commons uses SHA-1 as a file identity, not security
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest_image_source(
    store,
    image_source: ImageSource,
    *,
    file: str | Path,
    source: str = "curated",
    status: str = "in_review",
    today: date | None = None,
) -> ImageSourceRecord:
    """Rights-check, verify and materialise one exact historical image.

    Both copyright layers must clear independently.  The binary must also match
    the Commons machine record (SHA-1, dimensions and MIME-family), preventing a
    metadata record from accidentally blessing a different file.
    """

    year = (today or date.today()).year
    ok, reasons = image_source.source.is_clear(year)
    if not ok:
        raise ValueError(f"rights: {image_source.id} not clear - " + "; ".join(reasons))

    src = Path(file)
    if not src.is_file():
        raise ValueError(f"image source {image_source.id}: binary not found: {src}")
    if _sha1(src) != image_source.source.sha1:
        raise ValueError(f"image source {image_source.id}: SHA-1 does not match source record")
    with Image.open(src) as opened:
        if opened.size != (image_source.source.width, image_source.source.height):
            raise ValueError(
                f"image source {image_source.id}: dimensions {opened.size} do not match "
                f"record {(image_source.source.width, image_source.source.height)}"
            )
        if image_source.source.mime == "image/jpeg" and opened.format != "JPEG":
            raise ValueError(f"image source {image_source.id}: expected JPEG binary")
        if image_source.source.mime == "image/png" and opened.format != "PNG":
            raise ValueError(f"image source {image_source.id}: expected PNG binary")

    suffix = ".jpg" if image_source.source.mime == "image/jpeg" else ".png"
    dest = store.files_dir / f"{image_source.id}{suffix}"
    if src.resolve() != dest.resolve():
        shutil.copyfile(src, dest)
    record = ImageSourceRecord(
        id=image_source.id,
        image_source=image_source,
        file=str(dest),
        source=source,
        status=status,
    )
    return store.upsert(record)


def _task(annotation: ImageAnnotation, number: int, serves, subject: str) -> TaskBlock:
    if annotation.kind == "beschreibung":
        response = LinesResponse(n=4)
        minutes = 6
    elif annotation.kind == "analyse":
        response = LinesResponse(n=6)
        minutes = 8
    else:
        response = BoxResponse(min_height_mm=50)
        minutes = 10
    return TaskBlock(
        id=f"bild.t{number}",
        kind="image_analysis" if subject.casefold() == "kunst und gestaltung" else "source_analysis",
        prompt=annotation.question,
        response=response,
        cognitive_level=annotation.cognitive_level,
        dimensions=annotation.dimensions,
        serves=list(serves[:1]),
        est_minutes=minutes,
        answer_key=annotation.answer,
    )


def build_worksheet(record: ImageSourceRecord, *, today: date | None = None):
    """Derive one staged worksheet; answers are exactly the curated annotations."""

    from ..grounding import lehrplan_store as ls
    from .resolve import resolve_grade

    image = record.image_source
    res = resolve_grade(image.subject, image.klasse, today=today)
    ref = image.source
    licence = ref.reproduction_rights.licence
    source_line = f"Quelle: {ref.attribution} Lizenz der digitalen Reproduktion: {licence}."
    asset = Asset(
        id=image.image_asset_id,
        role="source",
        lane="content",
        generator="file:raster",
        spec={"path": record.file, "sha1": ref.sha1},
        correctness_surface="Exact rights-cleared historical source file, identity locked by SHA-1.",
        machine_generatable=False,
        provenance=AssetProvenance(
            source=ref.description_url,
            rights="public_domain"
            if ref.reproduction_rights.basis in {"public_domain_mark", "cc0"}
            else "licensed",
            note=(
                f"Work: {ref.work_rights.basis}; reproduction: "
                f"{ref.reproduction_rights.basis} ({licence})."
            ),
        ),
        caption=image.title,
    )

    bridge = (
        ("Arbeite wie bei der ANNO-Quellenarbeit in drei getrennten Schritten: "
         if image.related_text_id else "Arbeite in drei getrennten Schritten: ")
        +
        "zuerst Sichtbares beschreiben, dann die Gestaltung analysieren und erst danach "
        "historisch interpretieren. Das Blatt ist keine Fotografie der Verhandlungen, "
        "sondern eine gestaltete Bildquelle."
    )
    if image.related_sachverhalt_id:
        bridge += " Nutze dein Sachwissen zum Wiener Kongress erst im dritten Schritt."
    blocks = [
        InfoBlock(
            id="bild.quelle",
            kind="figure",
            content=(
                "Bildquelle: Unterscheide stets zwischen dem, was sichtbar ist, und dem, "
                "was du daraus deutest."
            ),
            asset_refs=[image.image_asset_id],
        ),
        InfoBlock(id="bild.nachweis", kind="prose", content=source_line),
    ]
    blocks.extend(
        _task(annotation, number, image.serves, image.subject)
        for number, annotation in enumerate(image.annotations, start=1)
    )
    meta = WorksheetMeta(
        title=image.title,
        subtitle="Beschreibung - Analyse - Interpretation einer Bildquelle",
        subject=image.subject,
        stufe="Unterstufe",
        klasse=image.klasse,
        kernfrage=(
            "Wie erzeugen Bildaufbau und Gestaltung eine bestimmte Wirkung?"
            if image.subject.casefold() == "kunst und gestaltung"
            else "Wie stellt die Bildquelle politische Verhandlungen und Macht dar?"
        ),
        fassung=res.fassung,
        lehrplan_label=f"{image.subject} · {image.klasse}. Klasse · Bildquellenkritik",
    )
    content = WorksheetContent(
        meta=meta,
        subject_model=ls.get_subject_model(image.subject),
        intro=[InfoBlock(id="bild.methode", kind="procedure", content=bridge)],
        sections=[
            Baustein(
                id="bildquellenkritik",
                title="Vom Sehen zum Quellenurteil",
                teacher_overview={
                    "throughline": (
                        "Die drei Erkenntnisschritte sprachlich sauber trennen: Beobachtung, "
                        "Gestaltungsanalyse, historisch begrenzte Deutung."
                    ),
                    "talking_points": [
                        "Eine Druckgrafik ist eine gestaltete Darstellung, kein neutraler Mitschnitt.",
                        "Abwesenheiten im Bild sind ein Analyseanlass, aber kein Beweis dafür, "
                        "wer historisch Einfluss hatte.",
                    ],
                    "timing_notes": "Einzelstunde; Sachverhalt Wiener Kongress als Vorwissen geeignet.",
                },
                blocks=blocks,
            )
        ],
        assets=[asset],
    )
    return content, res


def compose_image_source_worksheet(review_store, image_store, image_id: str, *, today=None):
    """Stage the derived worksheet through the ordinary Gate-2 seam."""

    from .orchestrator import stage_worksheet

    record = image_store.get(image_id)
    if record is None:
        raise KeyError(f"no ImageSource '{image_id}'")
    content, resolution = build_worksheet(record, today=today)
    return stage_worksheet(
        review_store,
        content,
        resolution,
        source="image_source",
        title=f"{record.image_source.subject} {record.image_source.klasse}. Kl. - {record.image_source.title}",
    )
