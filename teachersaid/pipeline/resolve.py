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


def _matches_topic(kompetenzbereich: str, topic_raw: str) -> bool:
    t = topic_raw.casefold()
    kb = kompetenzbereich.casefold()
    if kb in t or t in kb:
        return True
    # token overlap on significant words (e.g. "Strahlung" matches the KB)
    kb_tokens = {w for w in kb.replace("und", " ").split() if len(w) > 4}
    return any(tok in t for tok in kb_tokens)


def _resolution_preamble(
    subject: str, klasse: int, today: date
) -> tuple[FassungRef, list[str], list[ResolvedCompetence] | None]:
    """Shared trust-checks for any resolution: Fassung window (handoff §2) + that the
    subject and grade are actually in the catalog. Returns (fassung, notes,
    all_for_grade); all_for_grade is None when resolution cannot proceed — the caller
    then returns an empty, grade_check=False resolution carrying the notes."""
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

    if store.get_subject_model(subject) is None:
        notes.append(
            f"Fach '{subject}' ist im Katalog nicht hinterlegt "
            f"(verfügbar: {', '.join(store.list_subjects())})."
        )
        return fassung, notes, None

    all_for_grade = store.competences_for(subject, klasse)
    if not all_for_grade:
        gmap = store.grade_map(subject)
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
    fassung, notes, all_for_grade = _resolution_preamble(req.subject, req.klasse, today)
    if all_for_grade is None:
        return LehrplanResolution(
            fassung=fassung, subject=req.subject, klasse=req.klasse,
            grade_check=False, competences=[], notes=notes,
        )

    matched = [c for c in all_for_grade if _matches_topic(c.kompetenzbereich, req.topic_raw)]
    if not matched:
        # Many subjects (sciences, GPB) name their Kompetenzbereiche after the
        # W/E/S dimensions or competence strands, not the topic — the thematic
        # content lives in the Anwendungsbereiche. Match there and resolve the
        # (cross-cutting) competences for the grade.
        ab = store.anwendungsbereiche_for(req.subject, req.klasse)
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
    fassung, notes, all_for_grade = _resolution_preamble(subject, klasse, today)
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
    subject: str, klasse: int, *, today: date | None = None
) -> LehrplanResolution:
    """Resolution over ALL competences of a subject+grade — no topic/KB focus. Used to
    ingest a generated worksheet whose tasks may serve competences across the W/E/S
    strands (sciences, GPB), where the thematic focus lives in the Anwendungsbereiche
    rather than a single Kompetenzbereich (the same all-grade scope `resolve()` reaches
    via its Anwendungsbereiche fallback)."""
    today = today or date.today()
    fassung, notes, all_for_grade = _resolution_preamble(subject, klasse, today)
    if all_for_grade is None:
        return LehrplanResolution(
            fassung=fassung, subject=subject, klasse=klasse,
            grade_check=False, competences=[], notes=notes,
        )
    kbs = sorted({c.kompetenzbereich for c in all_for_grade})
    return LehrplanResolution(
        fassung=fassung, subject=subject, klasse=klasse,
        matched_kompetenzbereiche=kbs, grade_check=True,
        competences=all_for_grade, notes=notes,
    )
