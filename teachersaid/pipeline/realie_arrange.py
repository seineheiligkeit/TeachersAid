"""Wrap a Realie as a Lernarrangement — the two engines compose (Realien Phase 2b).

A communicative Realie is already a Sprechanlass; this lifts the speaking from a printable cue to a
first-class arrangement element. The Realie worksheet becomes the role material (read + write + the
Sprechkarte), the role-play becomes the `interaction` phase, and a *broader* Sprechen competence —
holding a short everyday conversation — becomes a `competence_anchor` **served by the interaction**,
not by any printable task. That is the v0.5 payoff: a competence the sheet structurally can't reach.

Reuses the worksheet engine (`text_tasks.build_worksheet`) and the arrangement engine
(`pipeline/arrange.py`) whole — no new renderer, no new derivation. `assemble_arrangement` /
`verify_arrangement` / `render_arrangement` run unchanged.
"""

from __future__ import annotations

from datetime import date

from ..schema.arrangement import (
    ArrangementMeta,
    ArrangementPhase,
    ArrangementRole,
    CompetenceAnchor,
    Lernarrangement,
    SharedProduct,
)
from ..schema.blocks import InfoBlock
from ..schema.texts import AnnotatedText
from .text_tasks import build_worksheet


def _anchor_competence(content, res):
    """The Sprechen competence the live conversation reaches BEYOND the sheet — the first SPR
    competence the worksheet's tasks don't already serve (so it's anchor-only: the v0.5 payoff)."""
    served = {s.competence_id for b in content.iter_blocks()
              if b.role.value == "task" for s in b.serves}
    spr = [c for c in res.competences if "SPR" in (c.dimensions or [])]
    if not spr:
        return None
    c = next((c for c in spr if c.id not in served), spr[0])
    return CompetenceAnchor(competence_id=c.id, dimension=(c.dimensions or ["SPR"])[0],
                            served_by="interaction")


def build_arrangement(at: AnnotatedText, *, today: date | None = None) -> Lernarrangement:
    """An AnnotatedText (a communicative Realie) → a `Lernarrangement`, stage-ready."""
    content, res = build_worksheet(at, today=today)
    scene = at.scene or at.title
    level = at.cefr or "A2"
    meta = ArrangementMeta(
        title=at.title, subtitle=f"{scene} — eine kommunikative Realie ({level})",
        subject=at.subject, stufe="Unterstufe", klasse=at.klasse,
        kernfrage=f"{scene}: verstehen, schreiben und sprechen",
        fassung=res.fassung, format="simulation_game",
        lehrplan_label=f"{at.subject} · {at.klasse}. Kl. · {level}"
        + (f" · {at.genre}" if at.genre else ""))
    anchor = _anchor_competence(content, res)
    return Lernarrangement(
        meta=meta,
        common_material=[InfoBlock(
            id="brief", kind="prose",
            content=(f"{scene}: Lies zuerst den Text und löse die Aufgaben. Danach spielt ihr zu "
                     f"zweit die Szene — eine Person übernimmt Rolle A, die andere Rolle B "
                     f"(siehe Sprechkarte auf dem Arbeitsblatt), dann tauscht ihr die Rollen."))],
        roles=[ArrangementRole(id="lernende", label="Lernende", share="all", material=content)],
        phases=[
            ArrangementPhase(id="p1", label="Lesen & Schreiben (einzeln)", grouping="individual",
                             minutes=15, what_happens=("Den Text lesen und die Lese- und "
                             "Schreibaufgaben des Arbeitsblatts bearbeiten.")),
            ArrangementPhase(id="p2", label="Rollenspiel (zu zweit)", grouping="role_group",
                             minutes=10, what_happens=("Mit der Sprechkarte die Szene zu zweit "
                             "spielen (Rolle A und B), danach die Rollen tauschen.")),
            ArrangementPhase(id="p3", label="Reflexion (Plenum)", grouping="plenary",
                             minutes=5, what_happens=("Nützliche Wendungen gemeinsam sammeln; "
                             "siehe Debrief.")),
        ],
        shared_product=SharedProduct(
            description=("Spielt euren Dialog der Gruppe oder der Klasse vor — frei, nicht "
                         "abgelesen."),
            rubric=[
                {"criterion": "Kommunikation",
                 "levels": ["kommt nicht zustande", "gelingt mit Hilfe",
                            "flüssig genug für die Situation"]},
                {"criterion": "Wendungen",
                 "levels": ["kaum passende Wendungen", "einige passende Wendungen",
                            "passende Frage- und Höflichkeitswendungen"]},
            ]),
        debrief=[InfoBlock(
            id="db", kind="prose",
            content=("Tretet aus der Rolle heraus: Welche Wendungen waren am nützlichsten? "
                     "Was würdest du beim nächsten Mal anders oder höflicher sagen?"))],
        competence_anchors=[anchor] if anchor else [],
    )
