"""Pure Block → ReportLab flowables mapping, parameterised by projection.

This is where the no-drift guarantee becomes concrete: all three projections call
this one function over the SAME blocks; nothing here holds its own copy of task
data. Projection ∈ {"student", "teacher", "homework"}.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether

from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.enums import Role
from ..schema.richtext import InlineRun, plain_text
from . import reportlab_base as rb

_CALLOUT_LABELS = {
    "note": "Hinweis", "warning": "Achtung", "reveal": "Auflösung", "tip": "Tipp",
}

# payloads that ARE their own interaction surface (numbers in blanks · draw-connections · tick-boxes ·
# spoken role cards) → no generic write-space underneath; the affordance can't double up.
# `true_false_justify` is NOT here — its justification genuinely needs lines. `role_play` is oral —
# the cue cards are the surface, the speaking happens in the room (served via an arrangement anchor).
_SELF_CONTAINED_PAYLOADS = {"ordering", "matching", "multiple_choice", "role_play"}


def _image(asset_path: Path, max_w: float):
    img = Image(str(asset_path))
    if img.imageWidth > max_w:
        scale = max_w / img.imageWidth
        img.drawWidth = max_w
        img.drawHeight = img.imageHeight * scale
    return img


def _citation_flowables(refs, citations, S):
    """A "Quelle: …" line under any figure whose data references a vetted dataset.
    Student-visible on every projection — citing the source IS curriculum
    (Quellenkritik / Datenkompetenz)."""
    out = []
    for ref in refs:
        cite = (citations or {}).get(ref)
        if cite:
            out.append(rb.para("Quelle: " + cite, S["meta"]))
    return out


# --- expression provenance (History/GPB asset class) -------------------------
# the licence link the attribution line carries (CC BY-SA's "+ ShareAlike" obligation)
_LICENCE_URLS = {
    "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}
_LICENCE_LABELS = {
    "CC-BY-SA-4.0": "CC BY-SA 4.0", "CC-BY-4.0": "CC BY 4.0", "CC0-1.0": "CC0 1.0",
    "public-domain": "gemeinfrei",
}
_ORIGIN_LABELS = {
    "original": "eigene Formulierung", "adapted": "adaptiert (Paraphrase)",
    "quoted": "wörtliches Zitat",
}
_ROLE_LABELS = {"facts": "Fakten", "expression": "Formulierung"}


def _attribution_line(s) -> str:
    """The student-visible source/licence line for a source whose wording we use."""
    head = f"Quelle: „{s.title}“"
    if s.publisher:
        head += f" ({s.publisher})"
    lic = (s.licence or "").upper()
    label = _LICENCE_LABELS.get(s.licence or "", s.licence)
    url = s.licence_url or _LICENCE_URLS.get(lic)
    if label:
        seg = f"Lizenz: {label}"
        if url:
            seg += f" ({url})"
        return head + ". " + seg
    return head


def _provenance_flowables(prov, projection: str, S):
    """Pure projection of `BlockProvenance`. Student/homework: a source/licence line ONLY
    when `attribution_required` (original blocks stay clean). Teacher: the full sources list
    incl. the `role="facts"` records hidden from students — the evidentiary basis to fact-check.
    """
    if prov is None or (not prov.sources and not prov.attribution_required):
        return []
    if projection == "teacher":
        head = f"Provenienz: {_ORIGIN_LABELS.get(prov.expression_origin, prov.expression_origin)}"
        if prov.attribution_required:
            head += " · Quellenangabe erforderlich"
        if prov.share_alike_applies:
            head += " · ShareAlike"
        out = [rb.para(head, S["meta"])]
        for s in prov.sources:
            line = f"– [{_ROLE_LABELS.get(s.role, s.role)}] „{s.title}“"
            if s.publisher:
                line += f", {s.publisher}"
            if s.licence:
                line += f", {_LICENCE_LABELS.get(s.licence, s.licence)}"
            if s.retrieved:
                line += f" (abgerufen {s.retrieved})"
            if s.url:
                line += f" — {s.url}"
            out.append(rb.para(line, S["meta"]))
        return out
    # student / homework — only the obligation-bearing line(s)
    if not prov.attribution_required:
        return []
    srcs = prov.expression_sources() or prov.sources
    return [rb.para(_attribution_line(s), S["meta"]) for s in srcs]


def _info_flowables(b: InfoBlock, projection: str, S, width, assets, citations=None):
    out = []
    if b.kind == "figure" and b.asset_refs:
        for ref in b.asset_refs:
            p = assets.get(ref)
            if p:
                out.append(_image(p, width))
        if b.content:
            out.append(rb.para(b.content, S["meta"]))
        out += _citation_flowables(b.asset_refs, citations, S)
    elif b.kind == "callout":
        label = _CALLOUT_LABELS.get(b.callout_role or "note", "Hinweis")
        out.append(rb.raw_para(f"<b>{label}:</b> " + rb.richtext_markup(b.content), S["callout"]))
    elif b.kind == "key_fact":
        out.append(rb.raw_para("▸ " + rb.richtext_markup(b.content), S["key_fact"]))
    elif b.kind == "source_text":
        txt = b.content if isinstance(b.content, str) else plain_text(b.content)
        # a Realie (numbered=False) renders as a real-artifact card; an authentic text keeps its
        # line numbers (tasks reference "Zeile N").
        out.append(rb.numbered_text(txt, S["body"], width) if b.numbered
                   else rb.material_card(txt, S["body"], width))
    else:
        out.append(rb.para(b.content, S["body"]))

    if projection == "teacher" and b.teacher_note:
        out.append(rb.para("Lehrkraft: " + rb.richtext_markup(b.teacher_note), S["teacher"]))
    if b.watch_outs:
        if projection == "teacher":
            for w in b.watch_outs:
                out.append(rb.para("⚠ " + w, S["watch"]))
        elif projection == "homework":
            for w in b.watch_outs:
                out.append(rb.para("Tipp: " + w, S["callout"]))
    out += _provenance_flowables(b.provenance, projection, S)
    return out


def _payload_flowables(b: TaskBlock, S, width):
    out = []
    p = b.payload
    if p is None:
        return out
    if p.kind == "true_false_justify":
        for i, stmt in enumerate(p.statements, 1):
            out.append(rb.para(f"{i}. {stmt}", S["body"]))
    elif p.kind == "multiple_choice":
        for opt in p.options:
            out.append(rb.para("☐ " + opt, S["body"]))
    elif p.kind == "ordering":
        for item in p.items:
            out.append(rb.para("____  " + item, S["body"]))
    elif p.kind == "matching":
        # connectable loose blocks — the student draws a line from each entry to its match (the
        # right column is shuffled). The blocks ARE the response surface (no write-space below).
        out.append(rb.connect_blocks(list(p.left), list(p.right or [""] * len(p.left)), width))
    elif p.kind == "table_fill":
        rows = [p.columns] + [["" if c is None else c for c in row] for row in p.rows]
        out.append(rb.grid_table(rows, width))
    elif p.kind == "decision_scenario":
        out.append(rb.para(p.stem, S["body"]))
    elif p.kind == "role_play":
        # a Sprechkarte: one cue card per partner. The cards ARE the response surface (oral).
        out.append(rb.cue_cards(list(p.cues), width))
    return out


def _response_flowables(b: TaskBlock, S, width):
    r = b.response
    mode = r.mode
    if mode == "lines":
        return [rb.spacer(1), rb.ruled_lines(r.n, width)]
    if mode == "box":
        return [rb.spacer(1), rb.answer_box(r.min_height_mm, width)]
    if mode == "table":
        rows = [r.columns] + [[""] * len(r.columns) for _ in range(r.rows)]
        return [rb.spacer(1), rb.grid_table(rows, width)]
    if mode == "choices":
        return [rb.para("☐ " + o, S["body"]) for o in r.options]
    if mode in ("diagram", "drawing", "artifact"):
        guide = getattr(r, "guide", None) or getattr(r, "produces", None) or ""
        lead = {"diagram": "Diagramm zeichnen", "drawing": "Skizze",
                "artifact": "Produkt"}[mode]
        # raw_para: the <i> tags are intentional markup; escape only the dynamic guide
        # (rb.para would escape the tags too → literal "<i>" in the PDF).
        inner = lead + (f": {rb.richtext_markup(guide)}" if guide else "")
        out = [rb.raw_para(f"<i>[{inner}]</i>", S["meta"])]
        out.append(rb.answer_box(45, width))
        return out
    return []


def _solution_step_flowables(steps, S):
    """Render a worked-solution step list as bulleted teacher lines (text + inline-math expr).
    Shared by the primary Rechenweg and every alternative Lösungsweg — one layout, no drift."""
    out = []
    for st in steps:
        line = rb.richtext_markup(st.text)
        if st.expr:
            line += "   " + rb.richtext_markup([InlineRun(text=st.expr, math=True)])
        out.append(rb.raw_para("• " + line, S["teacher"]))
    return out


def _task_flowables(b: TaskBlock, projection: str, S, width, assets, number, citations=None):
    out = [rb.raw_para(f"<b>{number}.</b> " + rb.richtext_markup(b.prompt), S["prompt"])]
    # embed every referenced asset (any task kind), + a data_interpretation payload's asset
    refs = list(b.asset_refs or [])
    if b.payload and getattr(b.payload, "kind", None) == "data_interpretation":
        ar = getattr(b.payload, "asset_ref", None)
        if ar and ar not in refs:
            refs.append(ar)
    for ref in refs:
        p = assets.get(ref)
        if p:
            out.append(_image(p, width * 0.75))
    out += _citation_flowables(refs, citations, S)
    out += _payload_flowables(b, S, width)
    # The teacher guide is a guide, not a blank to fill in: skip the answer space. And a
    # self-contained payload (ordering/matching/MC) is its OWN response surface — adding generic
    # write-space would just duplicate it (the redundant lines the SME flagged).
    pk = getattr(b.payload, "kind", None)
    if projection != "teacher" and pk not in _SELF_CONTAINED_PAYLOADS:
        out += _response_flowables(b, S, width)

    if projection == "teacher":
        # teacher-only solution figure(s) — solved puzzle grids and computed solution plots.
        # Student/homework projections never traverse this id channel.
        for ref in b.solution_asset_refs:
            p = assets.get(ref)
            if p:
                out.append(rb.para("Lösungsraster:" if b.kind == "puzzle" else
                                   "Lösungsabbildung:", S["label"]))
                out.append(_image(p, width * 0.75))
        dims = ", ".join(b.dimensions)
        serves = ", ".join(f"{s.competence_id} ({s.relation})" for s in b.serves)
        # only an EXPLICIT difficulty prints (a delivered ramp band / SME estimate);
        # the derived fallback would just restate the cognitive level.
        diff = {1: " · Anforderung: leicht", 2: " · Anforderung: mittel",
                3: " · Anforderung: anspruchsvoll"}.get(b.difficulty, "")
        out.append(rb.para(
            f"Niveau: {b.cognitive_level}{diff} · Dimension: {dims} · ~{b.est_minutes} min"
            + (f" · dient: {serves}" if serves else ""),
            S["meta"],
        ))
        if b.answer_key:
            out.append(rb.raw_para("Lösung: " + rb.richtext_markup(b.answer_key), S["answer"]))
        if b.acceptable_reasoning:
            out.append(rb.raw_para(
                "Akzeptabler Spielraum: " + rb.richtext_markup(b.acceptable_reasoning),
                S["answer"],
            ))
        if b.solution_steps:                          # the primary derived Rechenweg (Maths)
            out.append(rb.para("Rechenweg:", S["label"]))
            out += _solution_step_flowables(b.solution_steps, S)
        if b.solution_paths:                          # A4: the other legitimate strategies
            out.append(rb.para("Alternative Lösungswege:", S["label"]))
            for path in b.solution_paths:
                lead = f"Schüler könnten auch ({path.strategy}):"
                if path.note:                          # when this route suits the drawn numbers
                    lead += f" {path.note}"
                out.append(rb.para(lead, S["teacher"]))
                out += _solution_step_flowables(path.steps, S)
        for crit in b.rubric:
            out.append(rb.para(
                f"Kriterium — {crit.criterion}: " + " / ".join(crit.levels), S["teacher"]
            ))
        for w in b.watch_outs:
            out.append(rb.para("⚠ " + w, S["watch"]))
    elif projection == "homework":
        for w in b.watch_outs:
            out.append(rb.para("Tipp: " + w, S["callout"]))
        if b.self_check:
            out.append(rb.raw_para(
                "Selbstkontrolle: " + rb.richtext_markup(b.self_check), S["callout"]
            ))
    out += _provenance_flowables(b.provenance, projection, S)
    return out


def block_flowables(block, projection, S, width, assets, number=None, citations=None):
    """Render one block. `number` is the task counter (only used for TaskBlocks).
    `citations` maps asset_id → a "Quelle: …" line for figures with vetted data."""
    if block.role == Role.INFO:
        fl = _info_flowables(block, projection, S, width, assets, citations)
    else:
        fl = _task_flowables(block, projection, S, width, assets, number, citations)
    fl.append(rb.spacer(2.5))
    return [KeepTogether(fl)] if block.role == Role.TASK else fl


def should_render(block, projection: str) -> bool:
    """Projection-level filtering.

    student: drop non-printable (oral/enactive) blocks — they don't print.
    homework: drop teacher-present / equipment-dependent blocks.
    teacher: render everything.
    """
    if projection == "student":
        return block.modality == "printable"
    if projection == "homework":
        if block.modality != "printable":
            return False
        if block.flags and block.flags.equipment_dependent:
            return False
        return True
    return True
