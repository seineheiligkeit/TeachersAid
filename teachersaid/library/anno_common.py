"""Shared machinery for the SELF-CONTAINED ANNO/ÖNB Quellenarbeit worksheets.

Both GPB sheets — the oppositional 1871 Leitmeritzer Leitartikel and the official 1873
Wiener-Zeitung Festrede — embed their working materials ON the sheet: the line-numbered OCR
excerpt as a ``source_text`` block and a scan crop of the matching page region as a sourced
raster.  So every task operates on artifacts that are printed, and the OCR-Prüfung (compare the
machine text against the page image) happens entirely on paper.  *Referenced-only is a rights
fallback, not a didactic mode* — external navigation is enrichment, never a task dependency.

Both sources are Public Domain Mark (the ÖNB-Labs subset), so embedding is fully rights-clear —
the same OCR text is already redistributed in the staged DEU twins.  This module holds the parts
both sheets share: the crop Asset (same file-backed ``file:raster`` path as
``pipeline/image_sources.py``), the Public-Domain-Mark expression provenance for the embedded
excerpt, the demoted-link ``Digitalisat`` block, the OCR-explaining intro callout, and the human
ANNO viewer URL.  Each sheet's own module carries its verbatim OCR excerpt as a byte-locked
constant (drift-guarded against ``runs/ingest/texts_src/*.json`` by the tests).

The crop binaries live under ``runs/anno/files/`` (git-ignored, rebuildable); each has a tracked
``runs/anno/<id>.json`` record.  Re-materialise with
``python tools/fetch_anno.py --rehydrate runs/anno/<crop_id>.json``.
"""
from __future__ import annotations

from ..config import RUNS_DIR
from ..schema.assets import Asset, AssetProvenance
from ..schema.blocks import InfoBlock
from ..schema.provenance import BlockProvenance, ProvenanceSource

PD_MARK = "Public Domain Mark 1.0"
PD_MARK_URL = "https://creativecommons.org/publicdomain/mark/1.0/"
REPOSITORY = "Österreichische Nationalbibliothek, ÖNB Labs/ANNO"


def viewer_url(aid: str, datum: str, seite: int) -> str:
    """The human-readable ANNO viewer page — returns an ordinary HTML page (unlike the IIIF
    canvas, which returns machine JSON).  This is the demoted ``Digitalisat`` link; no task
    depends on it."""
    return f"https://anno.onb.ac.at/cgi-content/anno?aid={aid}&datum={datum}&seite={seite}"


def crop_file(crop_id: str):
    """Absolute path to the (git-ignored, rebuildable) scan-crop binary, resolved from the
    configured ``RUNS_DIR`` — never a hard-coded home path."""
    return RUNS_DIR / "anno" / "files" / f"{crop_id}.jpg"


def scan_crop_asset(*, crop_id: str, sha1: str, caption: str, viewer: str, depicts: str) -> Asset:
    """One rights-clear scan crop as a file-backed sourced raster (media-policy role
    ``source`` → ``must_be_sourced`` → ``public_domain``).  Same asset shape as
    ``pipeline/image_sources.py`` (``file:raster`` + provenance); the pure renderer only reads
    the PNG hand-off, and neither assemble nor verify stats the binary."""
    return Asset(
        id=crop_id, role="source", lane="content", generator="file:raster",
        spec={"path": str(crop_file(crop_id)), "sha1": sha1},
        correctness_surface="Exakter, rechtefreier Scanausschnitt des Originals (Identität per SHA-1).",
        machine_generatable=False,
        provenance=AssetProvenance(
            source=viewer, rights="public_domain",
            note=(f"Bildausschnitt des Originalscans ({REPOSITORY}); {PD_MARK}. "
                  f"Gezeigt: {depicts}."),
        ),
        caption=caption,
    )


def excerpt_provenance(*, title: str, publisher: str, viewer: str, retrieved: str) -> BlockProvenance:
    """Expression provenance for the embedded verbatim OCR excerpt: a *wörtliches Zitat* riding
    the genuine Public-Domain-Mark status of the ÖNB-Labs subset (``redistributable=True`` — the
    same PD basis under which the DEU twins already redistribute this text).  No ``quote_span``:
    the whole PD excerpt is redistributed on the PD basis, not a short citation under Zitatrecht,
    so no length flag — the student sheet auto-renders the ``Quelle: … · Lizenz: …`` line."""
    return BlockProvenance(
        expression_origin="quoted",
        sources=[ProvenanceSource(
            title=title, url=viewer, publisher=publisher,
            licence=PD_MARK, licence_url=PD_MARK_URL, retrieved=retrieved,
            role="expression", redistributable=True,
        )],
    )


def digitalisat_block(*, block_id: str, viewer: str, retrieved: str) -> InfoBlock:
    """The demoted link as a low-key ``prose`` ``Digitalisat`` line (the whole page online),
    student-visible, no task depends on it.  Carries an ``original`` + ``role="facts"``
    provenance so the prose-provenance gate stays clean (the ``Quelle`` citation itself is
    auto-rendered from the embedded ``source_text``, so this block does not repeat it)."""
    return InfoBlock(
        id=block_id, kind="prose",
        content=(f"Digitalisat der vollständigen Zeitungsseite ({REPOSITORY}): {viewer} — "
                 "für die Aufgaben brauchst du nur dieses Blatt, der Link ist zum Weiterstöbern."),
        provenance=BlockProvenance(
            expression_origin="original",
            sources=[ProvenanceSource(
                title="ANNO-Digitalisat (Seitennachweis)", url=viewer, publisher=REPOSITORY,
                licence=PD_MARK, licence_url=PD_MARK_URL, retrieved=retrieved,
                role="facts", redistributable=True)],
        ),
    )


def ocr_callout(*, block_id: str = "anno.ocr") -> InfoBlock:
    """Introduce the term OCR BEFORE any task uses it (SME feedback: no unexplained
    abbreviations), and frame the OCR errors as the method, not a defect.  The two examples are
    real errors from these very sheets („sind“→„find“, „und“→„nnd“)."""
    return InfoBlock(
        id=block_id, kind="callout", callout_role="note",
        content=(
            "OCR heißt automatische Texterkennung. Ein Computer hat den gedruckten Text der "
            "alten Zeitung „gelesen“ und in Buchstaben umgewandelt. Die alte Frakturschrift (die "
            "„altdeutschen“ Buchstaben) kennt er schlecht. Darum verliest er sich oft: Aus „sind“ "
            "wird „find“, aus „und“ wird „nnd“. Diese Fehler sind kein Ärgernis. Sie sind dein "
            "Arbeitsauftrag: Vergleiche den Maschinentext (OCR) mit dem Scan und entscheide "
            "selbst, was wirklich dasteht. Unsichere Stellen markierst du mit einem [?]."
        ),
    )


def procedure_block(*, block_id: str = "anno.methode") -> InfoBlock:
    """The 4-step method — generic, so it never pre-states a task's answer."""
    return InfoBlock(
        id=block_id, kind="procedure",
        content=(
            "So gehst du vor: 1. Quelle bestimmen (Wer schreibt? Wann? Was für ein Text?). "
            "2. Maschinentext (OCR) und Scanausschnitt vergleichen. 3. Wortwahl und Perspektive "
            "am Wortlaut belegen — mit Zeilennummern. 4. Ein begründetes Quellenurteil "
            "formulieren und ehrlich sagen, was die Quelle NICHT belegt."
        ),
    )
