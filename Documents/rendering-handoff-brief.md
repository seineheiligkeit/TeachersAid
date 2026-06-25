# Rendering handoff brief

**For: an agent taking over the rendering layer.** You own how a reviewed `WorksheetContent`
becomes deliverable documents. You are free to swap the rendering tool (ReportLab today, but HTML→PDF,
Typst, LaTeX, or editable `.docx` are all fair game) — **as long as you honour the contract in §2.**
Everything else in `teachersaid/rendering/` is yours to replace.

Read this brief, then the reference implementation (§5) and the inputs you must reproduce (§4).

## 1 · The job

Turn one **renderer-independent `WorksheetContent`** object (already generated and human-reviewed) into
**three pure projections**: a **student** sheet, a **teacher** guide, and a **homework** sheet. "Pure
projection" is the load-bearing idea: all three are functions of the *same* object, so the answer key
can never drift from the task. The product's documented weak flank is *use-ready output* — the bar is
"a teacher prints it (or drops it into Word) and hands it out without reformatting." Clear that bar.

## 2 · The contract (do NOT break)

**2a. Entry points** — keep these signatures; the orchestrator (`pipeline/orchestrator.py::_render_all`)
and the API (`api/app.py`) call them. Swap the *bodies*, not the seams.

```python
render_student_sheet(content: WorksheetContent, out_path, assets: dict[str,Path] | None) -> Path
render_teacher_guide(content: WorksheetContent, out_path, assets) -> Path
render_homework(content:     WorksheetContent, out_path, assets) -> Path
rasterise(pdf_path, out_dir=None, dpi=110) -> list[Path]   # dashboard preview image(s)
```
- `assets` is `{asset_id: rendered_image_path}` — content-bearing visuals are **code-generated**
  (matplotlib) by `pipeline/assets.py` *before* rendering. You just embed them by `asset_ref`.
  `intentionally_flawed` assets are built wrong **on purpose** — render them as-is, never "fix" them.
- `rasterise` produces the PNG the dashboard embeds as a preview. If you move off PDF (e.g. to docx/
  html), provide an equivalent "preview image of page 1" and update `_render_all` + the API accordingly.

**2b. Read only `schema/`.** Rendering must import only `teachersaid/schema/` — never `pipeline/`,
`llm/`, or the store, and never hold its own copy of task data. That import boundary *is* the no-drift
guarantee. (`grounding/` is fine if you need labels, but you shouldn't.)

**2c. The three projections** (currently `should_render()` + the per-block logic in
`blocks_to_flowables.py`):

| | student | teacher | homework |
|---|---|---|---|
| blocks shown | `modality == "printable"` only | **all** | `printable` **and not** `flags.equipment_dependent` |
| **answer write-space** (response lines/box/table) | shown | **omitted** — a guide, not a blank | shown |
| answer_key / acceptable_reasoning / rubric | hidden | shown | hidden |
| teacher_note, per-task meta (Niveau/Dimension/min/serves) | hidden | shown | hidden |
| watch_outs | hidden | shown (`⚠ …`) | shown as student-facing `Tipp: …` |
| self_check | hidden | — | shown (`Selbstkontrolle: …`) |
| section **teacher_overview** (Roter Faden + talking points + extensions) | hidden | shown (the "rough guide") | hidden |
| **Fassung stamp** (BGBl./DokNr.) | hidden | shown | hidden |
| derived **Nachweis** (coverage + gaps) + **DepthProfile** | — | **appended** | — |

**Audience rule (the spine of 2c):** the student and homework sheets carry *only* student-facing content;
everything regulatory or pedagogical — the Fassung stamp, competence ids, the Nachweis, and the teacher
guide layer — is teacher-only. And the teacher guide is a **guide**: it shows the expected answer + talking
points + extensions and **omits the write-in space** (the teacher already knows the topic).

**2d. Derived fields are READ-ONLY.** `content.nachweis` and `content.depth_profile` are produced by
`pipeline/assemble.py`. Render them (teacher view) but never compute or mutate them.

## 3 · The schema surfaces you must handle

All in `teachersaid/schema/` (`extra="forbid"` Pydantic — trust the types):
- **Document:** `meta` (title, subtitle, subject, klasse, kernfrage, `fassung` stamp, lehrplan_label,
  `content_language`); `intro: list[Block]`; `sections: list[Baustein]` (Baustein = title +
  `teacher_overview` + `blocks`). `teacher_overview` is a typed **`TeacherOverview`** (throughline ·
  talking_points · extensions · differentiation · timing_notes), teacher-only.
  *(NB: `Baustein`/`TeacherOverview` live in `schema/worksheet.py`, not blocks.py.)*
- **InfoBlock.kind** ∈ prose · key_fact · example · procedure · figure (`asset_refs`) · data_reference ·
  callout (`callout_role` ∈ note/warning/reveal/tip). Plus `teacher_note`, `watch_outs`.
- **TaskBlock:** `prompt` (RichText), `payload` (matching · ordering · multiple_choice ·
  true_false_justify · table_fill · data_interpretation(`asset_ref`) · decision_scenario · other),
  `response` (ResponseSpec, see below), `cognitive_level`, `dimensions`, `content_area`, `serves[]`,
  `est_minutes`, `answer_key`, `acceptable_reasoning`, `rubric[]`, `watch_outs`, `self_check`,
  `flags` (e.g. equipment_dependent), `modality`, `asset_refs`.
- **ResponseSpec.mode** ∈ lines{n} · box{min_height_mm} · table{columns,rows} · choices{options} ·
  none · diagram · drawing · artifact. These are **affordances** (how much answer space / what input),
  not layout — turn them into ruled lines / boxes / grids / checkboxes.
- **RichText** = `str | list[InlineRun]`; `InlineRun{text, mark ∈ bold/italic/term/code, ref_block}`.
  `ref_block` is an intra-sheet reference to another block id. Use `schema/richtext.py` helpers
  (`plain_text`, and the current `reportlab_base.richtext_markup` as a reference for mark handling).

## 4 · What you must reproduce (the reviewed inputs)

The human has reviewed these content objects — your renderer must render them faithfully:
- `teachersaid/library/` — the master library (Physik *Strahlung*, Biologie *Immunsystem*, Mathematik).
  Get them via `from teachersaid.library import EXAMPLES; EXAMPLES[i].build()`.
- `teachersaid/demo/strahlung.py` (the deep hero) and `teachersaid/demo/worked_examples.py` (the v0.4
  edge cases: an **oral** speaking_task that must be ABSENT from the student sheet; a cross-curricular
  sheet citing two subject models; an `intentionally_flawed` truncated-axis graph; a `rubric` +
  `artifact` response).

Render each to student/teacher/homework and eyeball them (`runs/store/<id>/*.pdf` after `seed`, or call
the render functions directly). They are the acceptance fixtures.

## 5 · Reference implementation (current = ReportLab)

`teachersaid/rendering/`:
- `reportlab_base.py` — **the only file that imports ReportLab.** Styles + primitives: `para` (escapes
  RichText), `raw_para` (takes pre-built markup — don't double-escape), `richtext_markup`, `ruled_lines`,
  `answer_box`, `grid_table`, `spacer`. Carlito font with Helvetica fallback.
- `blocks_to_flowables.py` — pure `block_flowables(block, projection, …)` + `should_render(block,
  projection)`; the per-kind/per-response/per-payload mapping. **This file encodes the projection
  rules in §2c** — read it before you reimplement.
- `_document.py` — `build_pdf(content, projection, out_path, assets)`: header → intro → sections, and
  the appended teacher Nachweis/DepthProfile page.
- `student_sheet.py` / `teacher_guide.py` / `homework.py` — thin wrappers over `build_pdf`.
- `qa_raster.py` — `rasterise()` via PyMuPDF (no system poppler dependency).

The "no HTML→PDF, ReportLab only" line in `CLAUDE.md` is *this implementation's* choice (determinism, no
poppler dep). It is **not** a constraint on you — if HTML+CSS (WeasyPrint/Playwright), Typst, or `.docx`
gives better use-ready output, take it. Editable `.docx` output is explicitly a wanted future target
(`project-handoff.md §7`).

## 6 · Acceptance criteria

1. **Tests green** (or your equivalent): `tests/test_render_smoke.py`, `tests/test_worked_examples.py`,
   `tests/test_library.py` (the seed renders every example). Invariants they pin:
   - student **hides** answer keys; teacher **shows** them.
   - the oral `speaking_task` is **absent** from the student sheet, present in the teacher guide.
   - the `intentionally_flawed` asset is rendered (not corrected).
   - rubric criteria surface in the teacher guide; PDFs are non-trivial (> ~1.5 KB); raster produced.
2. **Visual quality:** use-ready, clean German typography, figures scaled to width, unambiguous answer
   affordances (lines/box/table). Verify by rendering the §4 fixtures.
3. **Dashboard integration:** `GET /api/items/{id}/pdf/{student|teacher|homework}` still serves, and a
   page-1 preview image is produced for the queue. Update `_render_all` + the API if your output
   format changes.

## 7 · Gotchas

- `para` vs `raw_para` — if you pre-build inline markup, don't let the engine escape it again (you'll
  print literal `<b>` tags).
- **Modality filtering is load-bearing** — oral/enactive blocks must not appear on the student/homework
  sheets (it's how the "we don't print what can't be printed" scope line is enforced).
- Don't author `Nachweis`/`DepthProfile`; they're derived (read-only) and there are tests asserting it.
- Keep the font fallback graceful (Carlito if present, else a safe default) so it renders on any machine.

## 8 · Run / test

```bash
pip install -e .
python -m pytest -q tests/test_render_smoke.py tests/test_worked_examples.py tests/test_library.py
python -m teachersaid seed && python -m teachersaid    # review output in the dashboard
```
Output lands in `runs/store/<item_id>/` (student.pdf, teacher.pdf, homework.pdf, raster/*.png).
