"""M1 verification: canonical models load the schema §8 examples and round-trip,
and the generation views up-convert to canonical content."""

from __future__ import annotations

import pytest

from teachersaid.schema import (
    Baustein,
    BlockProvenance,
    InfoBlock,
    ProvenanceSource,
    SubjectCompetenceModel,
    TaskBlock,
    WorksheetContent,
    WorksheetMeta,
    plain_text,
    printable_coverage,
)
from teachersaid.schema.competence import CompetenceDimension
from teachersaid.schema.generation_views import GenWorksheetBody, body_to_canonical

PHYSIK_MODEL = SubjectCompetenceModel(
    subject="Physik",
    stufe="Unterstufe",
    dimensions=[
        CompetenceDimension(id="W", label="Fachwissen anwenden"),
        CompetenceDimension(id="E", label="Erkenntnisgewinnung / Experimentieren"),
        CompetenceDimension(
            id="S", label="Standpunkte begründen / aus naturwiss. Sicht bewerten"
        ),
    ],
    task_kind_extensions=["experiment_protocol", "source_critique"],
)

FASSUNG = {
    "kurztitel": "AHS-Lehrplan (konsolidiert)",
    "bgbl": "BGBl. II Nr. 204/2024",
    "doknr": "NOR40264237",
    "valid_from": "2024-09-01",
    "valid_to": "2026-08-31",
}


def _str_s2_b2() -> TaskBlock:
    # schema §8 — the penetration ≠ danger task
    return TaskBlock(
        id="str.s2.b2",
        kind="open_response",
        prompt=(
            "WLAN-Signale gehen durch Wände, schaden dir aber nicht – "
            "Gammastrahlung dagegen ist gefährlich. Beide durchdringen Materie. "
            "Erkläre den Unterschied."
        ),
        response={"mode": "lines", "n": 3},
        cognitive_level="analyze",
        dimensions=["S", "W"],
        serves=[{"competence_id": "PHY.US.4.STR.02", "relation": "exercises"}],
        est_minutes=6,
        acceptable_reasoning=(
            "Funkwellen = niedrige Energie, durchdringen, verändern aber keine "
            "Atome (nicht-ionisierend); Gamma = extrem hohe Energie, ionisierend "
            "→ Zellschaden. Kernpunkt: Durchdringung ≠ Gefahr."
        ),
        watch_outs=[
            "Lob die Trennung 'durchdringen' vs 'schaden' — genau hier liegt die Einsicht."
        ],
    )


def _str_s3() -> TaskBlock:
    # schema §8 — statements check with payload + load-bearing watch-out
    return TaskBlock(
        id="str.s3",
        kind="true_false_justify",
        prompt="Entscheide richtig/falsch und begründe oder korrigiere.",
        payload={
            "kind": "true_false_justify",
            "statements": [
                "UV-Strahlung ist ungefährlich, weil sie nicht ionisierend ist.",
                "Je höher die Energie, desto eher kann Strahlung Atome verändern (ionisieren).",
                "Wenn ich mit dem Handy telefoniere, werde ich radioaktiv.",
            ],
        },
        response={
            "mode": "table",
            "columns": ["Aussage", "richtig / falsch", "Begründung / Korrektur"],
            "rows": 3,
        },
        cognitive_level="evaluate",
        dimensions=["S"],
        serves=[{"competence_id": "PHY.US.4.STR.02", "relation": "exercises"}],
        est_minutes=9,
        answer_key=(
            "1 falsch (UV schädigt Zellen trotz nicht-ionisierend) · 2 richtig · "
            "3 falsch (Funkwellen, kein Kernzerfall)"
        ),
        watch_outs=[
            "Statement 1 ist die zentrale Falle — 'nicht-ionisierend' ≠ 'harmlos'."
        ],
    )


def _minimal_content() -> WorksheetContent:
    meta = WorksheetMeta(
        title="Strahlung und Radioaktivität",
        subject="Physik",
        stufe="Unterstufe",
        klasse=4,
        fassung=FASSUNG,
        lehrplan_label="Physik, 4. Klasse — Strahlung und Radioaktivität",
    )
    intro = [
        InfoBlock(
            id="str.intro",
            kind="prose",
            content="Strahlung umgibt uns ständig – aber nicht jede Strahlung ist gefährlich.",
        )
    ]
    section = Baustein(
        id="str.s",
        title="Durchdringung ≠ Gefahr",
        teacher_overview={"throughline": "Energie entscheidet, nicht Durchdringung."},
        blocks=[_str_s2_b2(), _str_s3()],
    )
    return WorksheetContent(
        meta=meta, subject_model=PHYSIK_MODEL, intro=intro, sections=[section]
    )


def test_taskblocks_construct_and_validate():
    t1, t2 = _str_s2_b2(), _str_s3()
    assert t1.response.mode == "lines" and t1.response.n == 3
    assert t2.payload.kind == "true_false_justify"
    assert len(t2.payload.statements) == 3
    assert t2.response.mode == "table"
    assert t1.cognitive_level == "analyze"


def test_worksheet_content_roundtrip():
    c = _minimal_content()
    dumped = c.model_dump()
    reloaded = WorksheetContent.model_validate(dumped)
    assert reloaded.meta.title == "Strahlung und Radioaktivität"
    assert list(reloaded.iter_blocks())[1].id == "str.s2.b2"
    # JSON round-trip too
    js = c.model_dump_json()
    again = WorksheetContent.model_validate_json(js)
    assert again.sections[0].blocks[1].payload.statements[0].startswith("UV-Strahlung")


def test_richtext_normalisation():
    t = _str_s2_b2()
    # a bare string stays a string (collapsed), plain_text flattens cleanly
    assert isinstance(t.prompt, str)
    assert "WLAN" in plain_text(t.prompt)


def test_printable_coverage():
    assert printable_coverage(PHYSIK_MODEL) == 1.0


# --- expression provenance (History/GPB asset class) -------------------------
def test_provenance_obligations_are_derived():
    # (#1) original-from-facts: a Wikipedia role="facts" source → no obligation, clean render
    orig = BlockProvenance(
        expression_origin="original",
        sources=[ProvenanceSource(
            title="Wiener Kongress", url="https://de.wikipedia.org/wiki/Wiener_Kongress",
            publisher="Wikipedia (de)", licence="CC-BY-SA-4.0", retrieved="2026-06-28",
            role="facts")],
    )
    assert orig.attribution_required is False
    assert orig.share_alike_applies is False           # facts role never triggers ShareAlike
    assert len(orig.facts_sources()) == 1 and not orig.expression_sources()

    # (#2 adapted) close paraphrase of CC-BY-SA text → derivative: attribution + ShareAlike
    adapted = BlockProvenance(
        expression_origin="adapted",
        sources=[ProvenanceSource(title="Wiener Kongress", licence="CC-BY-SA-4.0",
                                  role="expression", redistributable=True)],
    )
    assert adapted.attribution_required is True
    assert adapted.share_alike_applies is True

    # (#2 quoted) a short verbatim quote leans on Zitatrecht, not CC-BY-SA → no ShareAlike
    quoted = BlockProvenance(
        expression_origin="quoted",
        sources=[ProvenanceSource(title="Eine PD-Quelle", licence="public-domain",
                                  role="expression", author_death_year=1859,
                                  quote_span="… ein wörtliches Zitat …")],
    )
    assert quoted.attribution_required is True
    assert quoted.share_alike_applies is False


def test_provenance_derived_booleans_not_authorable():
    # the obligation booleans are computed — an attempt to author them is absorbed (stripped
    # + recomputed), never trusted: here a "false" attribution_required on an adapted block is
    # ignored and recomputed to True.
    p = BlockProvenance.model_validate({
        "expression_origin": "adapted", "attribution_required": False,
        "sources": [{"title": "Q", "licence": "CC-BY-SA-4.0", "role": "expression"}],
    })
    assert p.attribution_required is True   # recomputed, not the authored False
    # a genuinely unknown key still trips extra="forbid"
    with pytest.raises(ValueError):
        BlockProvenance.model_validate({"expression_origin": "original", "bogus": 1})


def test_provenance_roundtrips_and_serialises_derived():
    block = InfoBlock(
        id="wk.intro", kind="prose",
        content="Der Wiener Kongress ordnete 1814/15 Europa neu.",
        provenance=BlockProvenance(
            expression_origin="original",
            sources=[ProvenanceSource(title="Wiener Kongress", publisher="Wikipedia (de)",
                                      licence="CC-BY-SA-4.0", role="facts",
                                      retrieved="2026-06-28")],
        ),
    )
    dumped = block.model_dump()
    # computed obligation booleans serialise (for the API/review surface), still un-authored
    assert dumped["provenance"]["attribution_required"] is False
    # dict and JSON round-trips both preserve the authored fields
    assert InfoBlock.model_validate(dumped).provenance.expression_origin == "original"
    reloaded = InfoBlock.model_validate_json(block.model_dump_json())
    assert reloaded.provenance.expression_origin == "original"
    assert reloaded.provenance.sources[0].role == "facts"
    # the cross-subject opt-in flag is available for non-GPB historical prose
    flagged = InfoBlock(id="x", kind="prose", content="…", flags={"historical_fact": True})
    assert flagged.flags.historical_fact is True


def test_generation_view_carries_provenance():
    body = GenWorksheetBody.model_validate({
        "intro": [{
            "role": "info", "id": "i1", "kind": "prose",
            "content": "Der Wiener Kongress 1814/15.",
            "provenance": {
                "expression_origin": "original",
                "sources": [{"title": "Wiener Kongress", "publisher": "Wikipedia (de)",
                             "licence": "CC-BY-SA-4.0", "role": "facts",
                             "retrieved": "2026-06-28"}],
            },
        }],
        "sections": [],
    })
    content = body_to_canonical(body, meta=_minimal_content().meta, subject_model=PHYSIK_MODEL)
    prov = content.intro[0].provenance
    assert prov is not None and prov.expression_origin == "original"
    assert prov.attribution_required is False and prov.sources[0].role == "facts"


def test_generation_view_to_canonical():
    body = GenWorksheetBody.model_validate(
        {
            "intro": [
                {
                    "role": "info",
                    "id": "i1",
                    "kind": "prose",
                    "content": "Einstieg.",
                }
            ],
            "sections": [
                {
                    "id": "b1",
                    "title": "Kern",
                    "throughline": "Energie entscheidet.",
                    "talking_points": ["Durchdringung ≠ Gefahr?"],
                    "extensions": ["Anwendungen recherchieren."],
                    "blocks": [
                        {
                            "role": "task",
                            "id": "t1",
                            "kind": "open_response",
                            "prompt": "Erkläre den Unterschied.",
                            "response": {"mode": "lines", "n": 3},
                            "cognitive_level": "analyze",
                            "dimensions": ["S"],
                            "serves": [
                                {
                                    "competence_id": "PHY.US.4.STR.02",
                                    "relation": "exercises",
                                }
                            ],
                            "est_minutes": 6,
                        }
                    ],
                }
            ],
        }
    )
    meta = _minimal_content().meta
    content = body_to_canonical(body, meta=meta, subject_model=PHYSIK_MODEL)
    assert isinstance(content, WorksheetContent)
    assert content.nachweis is None  # derived later, never generated
    assert content.sections[0].blocks[0].id == "t1"
    ov = content.sections[0].teacher_overview
    assert ov.throughline == "Energie entscheidet."  # typed TeacherOverview, not a dict
    assert ov.talking_points == ["Durchdringung ≠ Gefahr?"]
    assert ov.extensions == ["Anwendungen recherchieren."]
