"""Compose a fächerübergreifendes Lernarrangement for one übergreifendes Thema (Wave C3).

The **Projektwoche bundle**: one übergreifendes Thema (ÜT — Umweltbildung, Medienbildung, …)
at one Klasse, approached from EACH subject that carries it in the Lehrplan. Deterministic +
LLM-free — the delivery-loop discipline exactly (approved blocks only, template framing, an
honest gap on failure). Each participating subject becomes an `ArrangementRole` whose material
is a small worksheet built from that subject's approved ÜT-tagged blocks (reusing the worksheet
engine whole); the shared Projektwoche product anchors a ÜT competence no single printable sheet
reaches — the v0.5 payoff (`competence_anchor` served by the `shared_product`).

Two halves, cleanly split: `resolve_uet` (pipeline/resolve.py) is the **catalog** side — which
competences carry the ÜT; this module is the **corpus** side — which subjects actually have
approved blocks. Honest failure: fewer than `MIN_SUBJECTS` subjects with approved ÜT task blocks
→ a structured `UetResult` gap (the orchestrator feeds it to the demand queue), never a thin
one-subject bundle dressed up as fächerübergreifend.

Cross-subject wrinkle: the roles span subjects, so each role's material is assembled/verified
against its OWN subject-grade resolution (via `arrange`'s `role_resolutions`), while the
arrangement-level Nachweis is derived against the shared ÜT resolution. See
`pipeline/arrange.py::assemble_arrangement`.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date

from ..grounding import lehrplan_store as ls
from ..schema.arrangement import (
    ArrangementMeta,
    ArrangementPhase,
    ArrangementRole,
    CompetenceAnchor,
    Lernarrangement,
    SharedProduct,
)
from ..schema.blocks import InfoBlock
from ..schema.enums import COGNITIVE_RANK, Role
from ..schema.worksheet import (
    Baustein,
    LehrplanResolution,
    WorksheetContent,
    WorksheetMeta,
)
from .plan import _ENVELOPE_MINUTES
from .resolve import resolve_grade, resolve_uet

MIN_SUBJECTS = 2            # a fächerübergreifendes bundle needs at least two subjects
MAX_SUBJECTS = 6           # cap the station count so the bundle stays a sane Projektwoche
MAX_TASKS_PER_ROLE = 4     # each station is a small, focused worksheet


@dataclass
class UetResult:
    """The outcome of `compose_uet`: either a staged-ready arrangement or an honest gap.

    On success `arrangement`/`resolution`/`role_resolutions` are set (feed them straight to
    `arrange.stage_arrangement`). On failure `gap` carries the honest reason and `arrangement`
    is None (`subjects` lists whichever subjects DID have approved ÜT blocks — 0 or 1)."""
    uet: int
    uet_label: str
    klasse: int
    envelope: str
    subjects: list[str] = field(default_factory=list)
    arrangement: Lernarrangement | None = None
    resolution: LehrplanResolution | None = None
    role_resolutions: dict[str, LehrplanResolution] = field(default_factory=dict)
    gap: str | None = None

    @property
    def ok(self) -> bool:
        return self.arrangement is not None


def _carries_asset(block) -> bool:
    """A task wired to a figure/solution asset — skipped for ÜT stations (they are text-first;
    carrying figures across an auto-composed cross-subject bundle is a later seam)."""
    return bool(getattr(block, "asset_refs", None) or getattr(block, "solution_asset_refs", None))


def _select_tasks(libblocks, budget: int, max_tasks: int):
    """One representative per family, climbing the cognitive ladder, greedy time-fit to the
    per-role budget, capped at `max_tasks` (and deduped by inner block id). Returns
    (chosen LibraryBlocks, minutes)."""
    seen_fam: set[str] = set()
    seen_ids: set[str] = set()
    uniq = []
    for lb in sorted(libblocks, key=lambda l: (COGNITIVE_RANK.get(l.cognitive_level or "", 9), l.id)):
        if lb.block.id in seen_ids:
            continue
        if lb.family and lb.family in seen_fam:
            continue
        if lb.family:
            seen_fam.add(lb.family)
        seen_ids.add(lb.block.id)
        uniq.append(lb)
    chosen, spent = [], 0
    for lb in uniq:
        if len(chosen) >= max_tasks:
            break
        m = getattr(lb.block, "est_minutes", 0) or 0
        if not chosen or spent + m <= budget:
            chosen.append(lb)
            spent += m
    return chosen, spent


def _role_material(subject: str, code: str, klasse: int, stufe: str, label: str, uet: int,
                   chosen, fassung) -> WorksheetContent:
    """A single subject's station: a small worksheet (template intro + the chosen tasks)."""
    model = ls.get_subject_model(subject, stufe)
    intro = InfoBlock(
        id=f"{code.lower()}.i", kind="prose",
        content=(f"Station {subject}. Untersucht „{label}“ aus der Sicht eures Fachs. "
                 f"Löst die Aufgaben. Haltet eure Ergebnisse für das gemeinsame Produkt fest."),
    )
    section = Baustein(
        id=f"{code.lower()}.kern", title=f"Station {subject}",
        blocks=[lb.block for lb in chosen],
    )
    return WorksheetContent(
        meta=WorksheetMeta(
            title=f"Station {subject}: {label}",
            subtitle=f"Projektwoche „{label}“ — fächerübergreifendes Lernarrangement",
            subject=subject, stufe=stufe, klasse=klasse,
            kernfrage=f"Was trägt {subject} zum Verständnis von „{label}“ bei?",
            fassung=fassung, lehrplan_label=f"{subject} · {klasse}. Kl. · ÜT {uet}: {label}",
        ),
        subject_model=model, intro=[intro], sections=[section],
    )


def _anchor_dimension(comp, stufe: str) -> str:
    """A DimensionRef for the anchor competence: its own primary dimension where the catalog
    gives one, else the subject model's first dimension (informational — never validated)."""
    if comp.dimensions:
        return comp.dimensions[0]
    meta = ls.competence_meta(comp.id) or {}
    model = ls.get_subject_model(meta.get("subject_code") or "", stufe)
    if model and model.dimensions:
        return model.dimensions[0].id
    return "—"


def compose_uet(uet: int, klasse: int, envelope: str = "doppelstunde", *,
                block_store, today: date | None = None,
                max_subjects: int = MAX_SUBJECTS) -> UetResult:
    """Compose a cross-subject `Lernarrangement` for übergreifendes Thema `uet` at `klasse`
    from APPROVED blocks. Returns a `UetResult`: `.arrangement` set on success (≥ MIN_SUBJECTS
    subjects contribute), else `.gap` with an honest reason. Deterministic + LLM-free."""
    stufe = ls.stufe_for_klasse(klasse)
    label = ls.uebergreifende_themen(stufe).get(uet) or f"ÜT {uet}"
    result = UetResult(uet=uet, uet_label=label, klasse=klasse, envelope=envelope)

    combined = resolve_uet(uet, klasse, today=today)
    if not combined.competences:
        result.gap = (f"Kein Lehrplan-Fach führt das übergreifende Thema „{label}“ in der "
                      f"{klasse}. Klasse — es lässt sich kein fächerübergreifendes Bündel bilden.")
        return result
    uet_ids = {c.id for c in combined.competences}

    # group APPROVED, printable, text-first task blocks that serve a ÜT competence, by
    # canonical subject code (the corpus uses several display strings per code, e.g. Biologie /
    # Biologie und Umweltbildung → BIO)
    by_code: dict[str, list] = defaultdict(list)
    display: dict[str, Counter] = defaultdict(Counter)
    for b in block_store.approved():
        if b.klasse != klasse or b.role != "task" or b.modality != "printable":
            continue
        if _carries_asset(b.block) or not (set(b.competences) & uet_ids):
            continue
        code = ls._code_for(b.subject, stufe)
        if code is None:
            continue
        by_code[code].append(b)
        display[code][b.subject] += 1

    participating = {code: libs for code, libs in by_code.items() if libs}
    if len(participating) < MIN_SUBJECTS:
        result.subjects = [display[c].most_common(1)[0][0] for c in participating]
        n = len(participating)
        wieviele = "Kein Fach hat" if n == 0 else "Nur ein Fach hat"
        result.gap = (f"{wieviele} freigegebene Bausteine für das übergreifende Thema "
                      f"„{label}“ (Kl. {klasse}); ein fächerübergreifendes Bündel braucht "
                      f"mindestens {MIN_SUBJECTS} Fächer. Die Lücke wird über eine "
                      f"Korpus-Kampagne gefüllt.")
        return result

    # rank subjects by task richness (ties by code for determinism) and cap the station count
    ranked = sorted(participating.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    chosen_codes = [code for code, _ in ranked[:max_subjects]]

    budget = _ENVELOPE_MINUTES.get(envelope, 100)
    roles: list[ArrangementRole] = []
    role_resolutions: dict[str, LehrplanResolution] = {}
    subjects: list[str] = []
    for code in chosen_codes:
        subject = display[code].most_common(1)[0][0]   # representative display string
        chosen, _spent = _select_tasks(participating[code], budget, MAX_TASKS_PER_ROLE)
        if not chosen:
            continue
        material = _role_material(subject, code, klasse, stufe, label, uet, chosen,
                                  combined.fassung)
        rid = code.lower()
        roles.append(ArrangementRole(id=rid, label=subject, material=material))
        role_resolutions[rid] = resolve_grade(subject, klasse, today=today)
        subjects.append(subject)

    if len(roles) < MIN_SUBJECTS:  # defensive — selection thinned below the floor
        result.subjects = subjects
        result.gap = (f"Nach der Auswahl blieben weniger als {MIN_SUBJECTS} Stationen für "
                      f"„{label}“ (Kl. {klasse}) übrig.")
        return result

    # the shared-product anchor: a ÜT competence NO printable role task exercises (anchor-only —
    # the v0.5 payoff), preferring a participating subject so it stays thematically connected
    exercised = {s.competence_id for role in roles for b in role.material.iter_blocks()
                 if b.role == Role.TASK for s in b.serves}
    chosen_set = set(chosen_codes)

    def _subj_code(cid: str) -> str | None:
        m = ls.competence_meta(cid)
        return m.get("subject_code") if m else None

    anchor_comp = next((c for c in combined.competences
                        if c.id not in exercised and _subj_code(c.id) in chosen_set), None)
    anchor_comp = anchor_comp or next((c for c in combined.competences
                                       if c.id not in exercised), None) or combined.competences[0]
    anchor = CompetenceAnchor(
        competence_id=anchor_comp.id, dimension=_anchor_dimension(anchor_comp, stufe),
        served_by="shared_product")

    faecher = ", ".join(subjects)
    arr = Lernarrangement(
        meta=ArrangementMeta(
            title=f"Projektwoche: {label}",
            subtitle=f"Fächerübergreifendes Lernarrangement · {len(roles)} Fächer · {klasse}. Klasse",
            subject=f"Fächerübergreifend ({label})", stufe=stufe, klasse=klasse,
            kernfrage=(f"Wie lässt sich „{label}“ aus der Sicht verschiedener Fächer verstehen "
                       f"und gestalten?"),
            fassung=combined.fassung, format="stations",
            lehrplan_label=f"Fächerübergreifend · {klasse}. Kl. · ÜT {uet}: {label}",
        ),
        common_material=[
            InfoBlock(id="auftakt", kind="prose",
                      content=(f"Projektwoche „{label}“: Ihr untersucht dieses Thema aus der "
                               f"Sicht mehrerer Fächer ({faecher}). In Fachgruppen bearbeitet ihr "
                               f"je eine Station; am Ende führt ihr eure Ergebnisse zu einem "
                               f"gemeinsamen Produkt zusammen (siehe unten).")),
            InfoBlock(id="ablauf", kind="procedure",
                      content=("Ablauf: (1) Gemeinsamer Themeneinstieg im Plenum. (2) Arbeit in "
                               "Fachgruppen an den Stationen. (3) Zusammenführung der Ergebnisse "
                               "zum gemeinsamen Produkt. (4) Präsentation und Reflexion.")),
        ],
        roles=roles,
        phases=[
            ArrangementPhase(id="p1", label="Auftakt & Themeneinstieg", grouping="plenary",
                             minutes=30,
                             what_happens=(f"Die Lehrkraft führt in das Thema „{label}“ und die "
                                           f"Kernfrage ein, stellt das gemeinsame Produkt vor und "
                                           f"teilt die Fachgruppen ein.")),
            ArrangementPhase(id="p2", label="Stationenarbeit in Fachgruppen", grouping="role_group",
                             minutes=90,
                             what_happens=("Jede Fachgruppe bearbeitet ihr Stationsblatt, klärt "
                                           "die fachliche Perspektive und hält Ergebnisse für das "
                                           "gemeinsame Produkt fest.")),
            ArrangementPhase(id="p3", label="Zusammenführung: gemeinsames Produkt", grouping="plenary",
                             minutes=60,
                             what_happens=("Die Fachgruppen bringen ihre Ergebnisse zusammen und "
                                           "erstellen das gemeinsame Produkt (Ausstellung, Plakat "
                                           "oder Präsentation).")),
            ArrangementPhase(id="p4", label="Präsentation & Reflexion", grouping="plenary",
                             minutes=40,
                             what_happens=("Das Produkt wird vorgestellt; anschließend Reflexion "
                                           "über die Fächerperspektiven — siehe Debrief.")),
        ],
        shared_product=SharedProduct(
            description=(f"Führt die Ergebnisse aller Stationen zu einem gemeinsamen Produkt "
                         f"zusammen — einer Ausstellung, einem Plakat oder einer Präsentation "
                         f"zum Thema „{label}“. Jede Fachgruppe ({faecher}) bringt ihre fachliche "
                         f"Perspektive ein; formuliert am Ende gemeinsame Erkenntnisse und — wo "
                         f"möglich — konkrete Schlussfolgerungen oder Empfehlungen."),
            rubric=[
                {"criterion": "Fachliche Tiefe",
                 "levels": ["oberflächlich", "in Teilen fundiert", "fachlich fundiert"]},
                {"criterion": "Fächerverbindung",
                 "levels": ["Perspektiven nebeneinander", "teilweise verknüpft",
                            "Perspektiven sinnvoll verbunden"]},
                {"criterion": "Gemeinsames Ergebnis",
                 "levels": ["kein gemeinsames Fazit", "vages Fazit",
                            "klares, begründetes gemeinsames Fazit"]},
            ]),
        debrief=[InfoBlock(
            id="debrief", kind="prose",
            content=("Tretet einen Schritt zurück: Was habt ihr in eurem Fach herausgefunden? "
                     "Wo ergänzen oder widersprechen sich die Perspektiven der Fächer? Was nehmt "
                     "ihr persönlich aus der Projektwoche mit?"))],
        competence_anchors=[anchor],
    )

    result.arrangement = arr
    result.resolution = combined
    result.role_resolutions = role_resolutions
    result.subjects = subjects
    return result
