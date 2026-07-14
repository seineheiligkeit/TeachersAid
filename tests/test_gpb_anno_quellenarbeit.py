"""Self-contained GPB Quellenarbeit through the real worksheet/review seam.

Both ANNO sheets embed their working materials ON the sheet (line-numbered OCR excerpt +
a page scan crop), so tasks operate on printed artifacts and the ANNO link is enrichment,
not a dependency. These tests lock: the OCR excerpts byte-match the tracked source records
(drift guard, no silent OCR correction); verify stays clean without ever statting the binary;
the embedded source carries Public-Domain-Mark expression provenance; the Zeile references in
the tasks point at the actually-rendered line numbers; and restaging rebuilds in place.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from teachersaid.library import anno_common
from teachersaid.library import gpb_anno_quellenarbeit as anno
from teachersaid.library import gpb_anno_weltausstellung as anno2
from teachersaid.library import seed_anno_quellenarbeit, seed_anno_weltausstellung
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.resolve import resolve_grade
from teachersaid.pipeline.verify import verify
from teachersaid.store.repository import ReviewStore

TODAY = date(2026, 3, 1)

# The scan-crop binaries are git-ignored (rebuildable via tools/fetch_anno.py --rehydrate).
# Rendering needs them; assemble/verify never touch them. Guard only the render-dependent tests
# so the suite still passes on a fresh clone without the binaries and without network.
_CROPS_PRESENT = (anno_common.crop_file(anno.CROP_ID).is_file()
                  and anno_common.crop_file(anno2.CROP_ID).is_file())
needs_crops = pytest.mark.skipif(not _CROPS_PRESENT,
                                 reason="scan-crop binaries absent (rebuild with fetch_anno --rehydrate)")

SHEETS = [("lehrertag", anno, "anno-lehrertag-1871"),
          ("weltausstellung", anno2, "anno-weltausstellung-1873")]


def _zeile_of(excerpt: str, needle: str) -> int | None:
    """The RENDERED line number of the first line containing `needle` — reproducing
    reportlab_base.numbered_text (only non-blank lines are numbered), so a task's „Zeile N“
    reference is checked against what the student actually sees."""
    n = 0
    for line in excerpt.split("\n"):
        if line.strip():
            n += 1
            if needle in line:
                return n
    return None


# --- byte-lock: the embedded excerpt is the verbatim tracked OCR (no silent correction) ------
@pytest.mark.parametrize("name,mod,stem", SHEETS)
def test_ocr_excerpt_byte_locks_against_tracked_source(name, mod, stem):
    record = json.loads(
        Path(f"runs/ingest/texts_src/{stem}.json").read_text(encoding="utf-8"))
    assert mod.OCR_EXCERPT == record["text"]                 # exact bytes, OCR errors and all
    assert record["source_ref"]["rights_basis"] == "public_domain_mark"


def test_known_ocr_errors_are_preserved_verbatim():
    assert "nnd Frei" in anno.OCR_EXCERPT and "Deutscheu" in anno.OCR_EXCERPT
    assert "Bald find es" in anno2.OCR_EXCERPT and "wahrhast" in anno2.OCR_EXCERPT


# --- self-contained structure + verify clean (no binary needed) ------------------------------
@pytest.mark.parametrize("name,mod,stem", SHEETS)
def test_worksheet_is_self_contained_and_verify_clean(name, mod, stem):
    content = mod.build_content()
    resolved = resolve_grade(mod.SUBJECT, mod.KLASSE, today=TODAY)
    assemble(content, resolved)
    report = verify(content, resolved)               # does NOT stat the crop binary
    assert report.problems == [], report.problems

    # the page scan crop is embedded as a rights-clear sourced raster
    assert len(content.assets) == 1
    asset = content.assets[0]
    assert asset.generator == "file:raster" and asset.role == "source"
    assert asset.provenance.rights == "public_domain"

    # the OCR excerpt is embedded as a line-numbered source_text with PD expression provenance
    source_texts = [b for b in content.iter_blocks() if getattr(b, "kind", None) == "source_text"]
    assert len(source_texts) == 1 and source_texts[0].numbered is True
    prov = source_texts[0].provenance
    assert prov is not None and prov.expression_origin == "quoted"
    assert prov.attribution_required is True and prov.share_alike_applies is False
    assert prov.expression_sources()[0].redistributable is True


@pytest.mark.parametrize("name,mod,stem", SHEETS)
def test_prose_provenance_gate_is_clean(name, mod, stem):
    """No prose-lint warning: the source_text carries provenance and the prose Digitalisat block
    is original+facts (so the GPB fact-block rule is satisfied)."""
    from teachersaid.pipeline.prose_lint import lint_content

    problems, warnings = lint_content(mod.build_content())
    assert problems == [] and warnings == []


# --- the OCR term is explained; no unexplained/machine abbreviations on student text ----------
@pytest.mark.parametrize("name,mod,stem", SHEETS)
def test_ocr_term_is_introduced_and_no_machine_jargon(name, mod, stem):
    content = mod.build_content()
    intro_text = " ".join(str(b.content) for b in content.intro)
    assert "OCR" in intro_text and "Texterkennung" in intro_text     # the term is defined
    student_text = intro_text + " ".join(
        str(getattr(b, "content", "") or getattr(b, "prompt", "")) for b in content.iter_blocks())
    for jargon in ("IIIF", "JSON", "canvas", "ALTO"):
        assert jargon not in student_text


# --- the human viewer link is present but demoted (no task depends on it) ---------------------
@pytest.mark.parametrize("name,mod,stem", SHEETS)
def test_viewer_link_present_but_never_a_task_dependency(name, mod, stem):
    content = mod.build_content()
    digitalisat = [b for b in content.iter_blocks()
                   if getattr(b, "id", "").endswith(".digitalisat")]
    assert len(digitalisat) == 1
    assert mod.ANNO_VIEWER.startswith("https://anno.onb.ac.at/cgi-content/anno?aid=")
    assert mod.ANNO_VIEWER in str(digitalisat[0].content)
    # no task prompt tells the student to open the link / go online
    for task in (b for b in content.iter_blocks() if b.role == "task"):
        low = str(task.prompt).casefold()
        assert "anno.onb" not in low and "online" not in low and "internet" not in low


# --- competence + dimension anchoring (kept: GPB.US.3.ALL.*) ----------------------------------
def test_lehrertag_competences_and_dimensions():
    content = anno.build_content()
    tasks = [b for b in content.iter_blocks() if b.role == "task"]
    assert {s.competence_id for t in tasks for s in t.serves} <= {
        "GPB.US.3.ALL.02", "GPB.US.3.ALL.03", "GPB.US.3.ALL.07"}
    assert {"HME", "HOR"} <= {d for t in tasks for d in t.dimensions}


def test_weltausstellung_competences_include_standort():
    content = anno2.build_content()
    tasks = [b for b in content.iter_blocks() if b.role == "task"]
    served = {s.competence_id for t in tasks for s in t.serves}
    assert served <= {"GPB.US.3.ALL.02", "GPB.US.3.ALL.03", "GPB.US.3.ALL.07", "GPB.US.3.ALL.09"}
    assert "GPB.US.3.ALL.09" in served                 # the Standort task is the didactic point
    assert {"HME", "HOR"} <= {d for t in tasks for d in t.dimensions}


# --- Zeile references point at the ACTUALLY RENDERED line numbers ------------------------------
def test_lehrertag_zeile_references_are_accurate():
    ex = anno.OCR_EXCERPT
    assert _zeile_of(ex, "stolze Schiff") == 18        # t3
    assert _zeile_of(ex, "ruderlosen Wrak") == 21      # t3
    assert _zeile_of(ex, "lüsternen Geiers") == 26     # t3
    for needle, zeile in [("finde»", 4), ("nnd Frei", 8), ("genng", 10), ("zn einem", 12),
                          ("Deutscheu", 15)]:           # t2 examples, all within the printed crop
        assert _zeile_of(ex, needle) == zeile


def test_weltausstellung_zeile_references_are_accurate():
    ex = anno2.OCR_EXCERPT
    assert _zeile_of(ex, "Bald find es") == 6          # t2 (visible in the crop)
    assert _zeile_of(ex, "erleuchtete Entschließung") == 15   # t3
    assert _zeile_of(ex, "hochherzige Fürsorge") == 17        # t3
    assert _zeile_of(ex, "Fortschritt Gemeingut") == 31       # t4
    assert _zeile_of(ex, "Gott segne") == 44                  # t4 (after the blank line)


# --- the SME's „copy-paste“ fix: t1 is the student's own determination FROM the source --------
def test_weltausstellung_intro_does_not_pre_state_the_source_determination():
    content = anno2.build_content()
    intro_text = " ".join(str(b.content) for b in content.intro)
    # the intro teaches method + context only — it does NOT name who speaks / to whom / Textsorte
    for leak in ("Bürgermeister", "Kaiser", "Ansprache", "Festrede", "Majestät"):
        assert leak not in intro_text
    # …while the embedded source (which t1 reads) DOES carry the answer
    assert "Bürgermeister" in anno2.OCR_EXCERPT and "Majestät" in anno2.OCR_EXCERPT


# --- restaging rebuilds IN PLACE (id/status/created_at/feedback preserved) --------------------
@needs_crops
@pytest.mark.parametrize("name,mod,stem", SHEETS)
def test_restage_worksheet_rebuilds_in_place(name, mod, stem, tmp_path):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.models import ReviewItem
    from teachersaid.schema.worksheet import BundleRequest

    store = ReviewStore(tmp_path / "store")
    seed = ReviewItem(id="", stage="content", source="curated", status="pending",
                      title="alt", request=BundleRequest(subject=mod.SUBJECT, klasse=mod.KLASSE,
                                                         topic_raw="alt"))
    store.create(seed)
    store.append_feedback(seed.id, "request-changes", "überarbeiten")
    created_at = store.get(seed.id).created_at

    content = mod.build_content()
    res = resolve_grade(mod.SUBJECT, mod.KLASSE, today=TODAY)
    item = orch.restage_worksheet(store, seed.id, content, res, source="curated",
                                  title=content.meta.title)
    assert item.id == seed.id                       # same id → same review/feedback linkage
    assert item.status == "pending"                 # status preserved
    assert item.created_at == created_at            # created_at preserved
    assert len(item.feedback) == 1                  # the SME feedback survives
    assert item.error is None and item.verify_problems == []
    assert item.content.assets and item.artifacts.student_pdf


# --- seeding stages a pending content item (renders — needs the crop binaries) ----------------
@needs_crops
def test_seed_anno_worksheet_stages_pending_content(tmp_path):
    store = ReviewStore(tmp_path / "store")
    [item] = seed_anno_quellenarbeit(store, today=TODAY)
    assert item.source == "curated" and item.stage == "content" and item.status == "pending"
    assert item.error is None and item.verify_problems == []
    assert item.content and item.artifacts and item.artifacts.student_pdf


@needs_crops
def test_seed_weltausstellung_stages_pending_content(tmp_path):
    store = ReviewStore(tmp_path / "store")
    [item] = seed_anno_weltausstellung(store, today=TODAY)
    assert item.source == "curated" and item.stage == "content" and item.status == "pending"
    assert item.error is None and item.verify_problems == []
    assert item.content and item.artifacts and item.artifacts.student_pdf
