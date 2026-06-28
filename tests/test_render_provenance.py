"""Phase 3: the pure attribution projection of expression provenance.

Student/homework get a source+licence line ONLY when the wording creates an obligation
(`attribution_required`); `original` blocks stay clean. The teacher copy shows the full
sources list — including the `role="facts"` records hidden from students."""

from __future__ import annotations

from teachersaid.rendering import reportlab_base as rb
from teachersaid.rendering.blocks_to_flowables import block_flowables
from teachersaid.schema import BlockProvenance, InfoBlock, ProvenanceSource


def _text(block, projection):
    S = rb.styles()
    flat, stack = [], list(block_flowables(block, projection, S, 400, {}, number=1))
    while stack:
        f = stack.pop()
        inner = getattr(f, "_content", None)
        if inner:
            stack.extend(inner)
        else:
            getp = getattr(f, "getPlainText", None)
            if getp:
                flat.append(getp())
    return "\n".join(flat)


def _info(prov):
    return InfoBlock(id="i1", kind="prose",
                     content="Der Wiener Kongress ordnete 1814/15 Europa neu.", provenance=prov)


def test_original_facts_block_is_clean_for_students_visible_to_teacher():
    prov = BlockProvenance(expression_origin="original", sources=[ProvenanceSource(
        title="Wiener Kongress", publisher="Wikipedia (de)", licence="CC-BY-SA-4.0",
        role="facts", retrieved="2026-06-28",
        url="https://de.wikipedia.org/wiki/Wiener_Kongress")])
    block = _info(prov)

    s_text = _text(block, "student")
    assert "Quelle" not in s_text and "Wikipedia" not in s_text  # original → clean for students

    t_text = _text(block, "teacher")
    assert "Provenienz" in t_text                 # the teacher sees the evidentiary basis…
    assert "Fakten" in t_text and "Wiener Kongress" in t_text  # …incl. the hidden facts record
    assert "2026-06-28" in t_text


def test_adapted_cc_by_sa_prints_attribution_and_licence_for_students():
    prov = BlockProvenance(expression_origin="adapted", sources=[ProvenanceSource(
        title="Wiener Kongress", publisher="Wikipedia (de)", licence="CC-BY-SA-4.0",
        role="expression", redistributable=True)])
    block = _info(prov)

    s_text = _text(block, "student")
    assert "Quelle" in s_text and "Wiener Kongress" in s_text
    assert "CC BY-SA 4.0" in s_text                                   # human licence label
    assert "creativecommons.org/licenses/by-sa/4.0" in s_text         # the licence link

    t_text = _text(block, "teacher")
    assert "ShareAlike" in t_text and "Quellenangabe erforderlich" in t_text


def test_quoted_pd_attributes_without_sharealike():
    prov = BlockProvenance(expression_origin="quoted", sources=[ProvenanceSource(
        title="Eine PD-Rede", licence="public-domain", role="expression",
        author_death_year=1859, quote_span="… ein kurzes Zitat …")])
    block = _info(prov)

    s_text = _text(block, "student")
    assert "Quelle" in s_text and "gemeinfrei" in s_text
    assert "ShareAlike" not in _text(block, "teacher")


def test_no_provenance_renders_nothing_extra():
    s_text = _text(_info(None), "student")
    assert "Quelle" not in s_text and "Provenienz" not in s_text
