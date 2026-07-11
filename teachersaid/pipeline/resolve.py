"""Resolve (deterministic) — schema §7 step 1.

Pure data lookup against the curated grounding. grade_check is the trust feature:
a topic only resolves if its Kompetenzbereich actually belongs to the requested
Klasse. Anything outside the curated catalogue produces honest gap notes, not a
hallucinated resolution.
"""

from __future__ import annotations

from datetime import date

from ..grounding import lehrplan_store as store
from ..schema.worksheet import (
    BundleRequest,
    FassungRef,
    LehrplanResolution,
    ResolvedCompetence,
)
from ..schema.enums import AnchorMode


def _matches_topic(kompetenzbereich: str, topic_raw: str) -> bool:
    t = topic_raw.casefold()
    kb = kompetenzbereich.casefold()
    if kb in t or t in kb:
        return True
    # token overlap on significant words (e.g. "Strahlung" matches the KB)
    kb_tokens = {w for w in kb.replace("und", " ").split() if len(w) > 4}
    return any(tok in t for tok in kb_tokens)


def _resolution_preamble(
    subject: str, klasse: int, today: date, stufe: str
) -> tuple[FassungRef, list[str], list[ResolvedCompetence] | None]:
    """Shared trust-checks for any resolution: Fassung window (handoff §2) + that the
    subject and grade are actually in the catalog (of the right stage). Returns (fassung,
    notes, all_for_grade); all_for_grade is None when resolution cannot proceed — the
    caller then returns an empty, grade_check=False resolution carrying the notes."""
    fassung = store.get_fassung()
    notes: list[str] = []

    if not (
        date.fromisoformat(fassung.valid_from)
        <= today
        <= date.fromisoformat(fassung.valid_to)
    ):
        notes.append(
            f"Achtung: heutiges Datum {today.isoformat()} liegt außerhalb des "
            f"Fassungsfensters ({fassung.valid_from}…{fassung.valid_to}). "
            "Eine neue Fassung wird benötigt."
        )

    if store.get_subject_model(subject, stufe) is None:
        notes.append(
            f"Fach '{subject}' ist im {stufe}-Katalog nicht hinterlegt "
            f"(verfügbar: {', '.join(store.list_subjects(stufe))})."
        )
        return fassung, notes, None

    all_for_grade = store.competences_for(subject, klasse, stufe)
    if not all_for_grade:
        gmap = store.grade_map(subject, stufe)
        if gmap:
            notes.append(
                f"Für {subject} {klasse}. Kl. sind im Katalog keine "
                f"Kompetenzen hinterlegt (das Fach umfasst die Klassen "
                f"{', '.join(str(k) for k in sorted(gmap))})."
            )
        else:
            notes.append(
                f"Für {subject} ist nur das Kompetenzmodell hinterlegt, "
                "noch keine verbatim Kompetenzen (Demo-Grenze)."
            )
        return fassung, notes, None

    return fassung, notes, all_for_grade


def resolve(req: BundleRequest, *, today: date | None = None) -> LehrplanResolution:
    today = today or date.today()
    stufe = store.stufe_for_klasse(req.klasse)  # Klasse fixes the stage (1–4 / 5–8)
    fassung, notes, all_for_grade = _resolution_preamble(req.subject, req.klasse, today, stufe)
    if all_for_grade is None:
        return LehrplanResolution(
            fassung=fassung, subject=req.subject, klasse=req.klasse,
            grade_check=False, competences=[], notes=notes,
        )

    if req.anchor_mode == AnchorMode.HORIZONT:
        notes.append(
            "Verankerungsmodus Horizont: ausdrücklich freiwillige Vertiefung nach "
            "Wahl der Lehrkraft; es wird kein Lehrplan-Kompetenzbezug behauptet."
        )
        return LehrplanResolution(
            fassung=fassung, subject=req.subject, klasse=req.klasse,
            grade_check=True, competences=[], notes=notes,
        )

    if req.anchor_mode == AnchorMode.UET:
        legend = store.uebergreifende_themen(stufe)
        label = legend.get(req.anchor_uet)
        if label is None:
            notes.append(
                f"Übergreifendes Thema {req.anchor_uet} ist im {stufe}-Katalog nicht definiert."
            )
            return LehrplanResolution(
                fassung=fassung, subject=req.subject, klasse=req.klasse,
                grade_check=False, competences=[], notes=notes,
            )
        matched = [c for c in all_for_grade if req.anchor_uet in c.uebergreifende_themen]
        if not matched:
            notes.append(
                f"{req.subject} führt das übergreifende Thema „{label}“ in der "
                f"{req.klasse}. Klasse nicht als verbatim Hook."
            )
        else:
            notes.append(
                f"ÜT {req.anchor_uet}: „{label}“ ist für {req.subject} in der "
                f"{req.klasse}. Klasse verbatim im Katalog verankert."
            )
        return LehrplanResolution(
            fassung=fassung, subject=req.subject, klasse=req.klasse,
            matched_kompetenzbereiche=sorted({c.kompetenzbereich for c in matched}),
            grade_check=bool(matched), competences=matched, notes=notes,
        )

    matched = [c for c in all_for_grade if _matches_topic(c.kompetenzbereich, req.topic_raw)]
    if not matched:
        # Many subjects (sciences, GPB) name their Kompetenzbereiche after the
        # W/E/S dimensions or competence strands, not the topic — the thematic
        # content lives in the Anwendungsbereiche. Match there and resolve the
        # (cross-cutting) competences for the grade.
        ab = store.anwendungsbereiche_for(req.subject, req.klasse, stufe)
        if any(_matches_topic(item, req.topic_raw) for item in ab):
            matched = all_for_grade
            notes.append(
                f"Thema '{req.topic_raw}' über die Anwendungsbereiche aufgelöst; "
                "die Kompetenzen dieses Fachs sind fachübergreifend formuliert."
            )
    if not matched:
        kbs = sorted({c.kompetenzbereich for c in all_for_grade})
        notes.append(
            f"Thema '{req.topic_raw}' passt zu keinem Kompetenzbereich der "
            f"{req.klasse}. Kl. {req.subject}. Vorhanden: {', '.join(kbs)}."
        )
        # grade_check still passes (the grade is valid); the topic just didn't match.
        return LehrplanResolution(
            fassung=fassung, subject=req.subject, klasse=req.klasse,
            grade_check=True, competences=[], notes=notes,
        )

    kompetenzbereiche = sorted({c.kompetenzbereich for c in matched})
    return LehrplanResolution(
        fassung=fassung,
        subject=req.subject,
        klasse=req.klasse,
        matched_kompetenzbereiche=kompetenzbereiche,
        grade_check=True,
        competences=matched,
        notes=notes,
    )


def resolve_kompetenzbereich(
    subject: str, klasse: int, kompetenzbereich: str, *, today: date | None = None
) -> LehrplanResolution:
    """Deterministic resolution for an explicitly chosen Kompetenzbereich — no topic
    guessing. The composer targets competences directly (the block library is
    competence-anchored), so a worksheet's *title* need not textually match the
    catalog's KB name — which `resolve()` requires and which fails for subjects whose
    KBs are numbered content areas (MAT) or W/E/S strands (BIO). Falls back to a loose
    label match so a slightly-off KB string still lands."""
    today = today or date.today()
    stufe = store.stufe_for_klasse(klasse)
    fassung, notes, all_for_grade = _resolution_preamble(subject, klasse, today, stufe)
    if all_for_grade is None:
        return LehrplanResolution(
            fassung=fassung, subject=subject, klasse=klasse,
            grade_check=False, competences=[], notes=notes,
        )

    kbf = kompetenzbereich.casefold()
    matched = [c for c in all_for_grade if c.kompetenzbereich.casefold() == kbf]
    if not matched:  # tolerate a slightly-off label via token overlap
        matched = [c for c in all_for_grade if _matches_topic(c.kompetenzbereich, kompetenzbereich)]
    if not matched:
        kbs = sorted({c.kompetenzbereich for c in all_for_grade})
        notes.append(
            f"Kompetenzbereich '{kompetenzbereich}' nicht in {subject} "
            f"{klasse}. Kl. gefunden. Vorhanden: {', '.join(kbs)}."
        )
        return LehrplanResolution(
            fassung=fassung, subject=subject, klasse=klasse,
            grade_check=True, competences=[], notes=notes,
        )

    kompetenzbereiche = sorted({c.kompetenzbereich for c in matched})
    return LehrplanResolution(
        fassung=fassung,
        subject=subject,
        klasse=klasse,
        matched_kompetenzbereiche=kompetenzbereiche,
        grade_check=True,
        competences=matched,
        notes=notes,
    )


def resolve_grade(
    subject: str, klasse: int, *, today: date | None = None,
    kompetenzmodul: int | None = None, semester: int | None = None,
) -> LehrplanResolution:
    """Resolution over ALL competences of a subject+grade — no topic/KB focus. Used to
    ingest a generated worksheet whose tasks may serve competences across the W/E/S
    strands (sciences, GPB), where the thematic focus lives in the Anwendungsbereiche
    rather than a single Kompetenzbereich (the same all-grade scope `resolve()` reaches
    via its Anwendungsbereiche fallback).

    For the Oberstufe, `kompetenzmodul`/`semester` narrow to one semesterised module
    (grade-independent `descriptor` competences are always kept — they are exercised across
    every module)."""
    today = today or date.today()
    stufe = store.stufe_for_klasse(klasse)
    fassung, notes, all_for_grade = _resolution_preamble(subject, klasse, today, stufe)
    if all_for_grade is None:
        return LehrplanResolution(
            fassung=fassung, subject=subject, klasse=klasse,
            grade_check=False, competences=[], notes=notes,
        )
    comps = all_for_grade
    if kompetenzmodul is not None:
        comps = [c for c in comps if c.kind == "descriptor" or c.kompetenzmodul == kompetenzmodul]
        notes.append(f"Auf Kompetenzmodul {kompetenzmodul} eingegrenzt.")
    if semester is not None:
        comps = [c for c in comps if c.kind == "descriptor" or (c.semester and semester in c.semester)]
        notes.append(f"Auf das {semester}. Semester eingegrenzt.")
    if (kompetenzmodul is not None or semester is not None) and not any(
        c.kind != "descriptor" for c in comps
    ):
        notes.append(
            "Kein passendes Modul gefunden — nur fachübergreifende Kompetenzmodell-"
            "Deskriptoren resolved."
        )
    kbs = sorted({c.kompetenzbereich for c in comps})
    return LehrplanResolution(
        fassung=fassung, subject=subject, klasse=klasse,
        matched_kompetenzbereiche=kbs, grade_check=True,
        competences=comps, notes=notes,
    )


def resolve_kompetenzmodul(
    subject: str, klasse: int, kompetenzmodul: int, *, today: date | None = None
) -> LehrplanResolution:
    """Oberstufe convenience: resolve a subject+grade narrowed to one Kompetenzmodul."""
    return resolve_grade(subject, klasse, today=today, kompetenzmodul=kompetenzmodul)


def resolve_uet(uet: int, klasse: int, *, today: date | None = None) -> LehrplanResolution:
    """The cross-subject analogue of `resolve_grade`: every verbatim competence carrying
    übergreifendes Thema `uet` at `klasse`, across ALL Pflichtgegenstände of the stage
    (1–4 → Unterstufe, 5–8 → Oberstufe). This is the Lehrplan half of the fächerübergreifende
    Projektwoche bundle (Wave C3) — the shared competence ground several subjects stand on.

    The returned `competences` span subjects (each competence's subject is recoverable from
    its id via `lehrplan_store.competence_meta`); `subject` is the ÜT label, not a catalog
    subject. `grade_check` is True iff at least one subject carries the ÜT at the grade; an
    unknown ÜT number, or one no subject carries, yields an empty resolution + an honest note.
    Never asserts a bundle — it resolves the *catalog*; the corpus side (which subjects have
    approved blocks) is `compose_uet`'s concern."""
    today = today or date.today()
    stufe = store.stufe_for_klasse(klasse)  # Klasse fixes the stage (1–4 / 5–8)
    fassung = store.get_fassung()
    notes: list[str] = []
    if not (
        date.fromisoformat(fassung.valid_from) <= today <= date.fromisoformat(fassung.valid_to)
    ):
        notes.append(
            f"Achtung: heutiges Datum {today.isoformat()} liegt außerhalb des "
            f"Fassungsfensters ({fassung.valid_from}…{fassung.valid_to}). "
            "Eine neue Fassung wird benötigt."
        )

    legend = store.uebergreifende_themen(stufe)
    label = legend.get(uet)
    if label is None:
        notes.append(
            f"Übergreifendes Thema {uet} ist im {stufe}-Katalog nicht definiert "
            f"(gültig: {', '.join(str(n) for n in sorted(legend))})."
        )
        return LehrplanResolution(
            fassung=fassung, subject=f"ÜT {uet}", klasse=klasse,
            grade_check=False, competences=[], notes=notes,
        )

    competences: list[ResolvedCompetence] = []
    subjects_with = 0
    for subject in store.list_subjects(stufe):
        comps = [
            c for c in store.competences_for(subject, klasse, stufe)
            if uet in c.uebergreifende_themen
        ]
        if comps:
            competences.extend(comps)
            subjects_with += 1

    if not competences:
        notes.append(
            f"Kein Fach führt das übergreifende Thema „{label}“ in der {klasse}. "
            f"Klasse ({stufe})."
        )
    else:
        notes.append(
            f"{subjects_with} Fächer führen „{label}“ in der {klasse}. Klasse ({stufe})."
        )
    kbs = sorted({c.kompetenzbereich for c in competences})
    return LehrplanResolution(
        fassung=fassung, subject=f"ÜT {uet}: {label}", klasse=klasse,
        matched_kompetenzbereiche=kbs, grade_check=bool(competences),
        competences=competences, notes=notes,
    )
