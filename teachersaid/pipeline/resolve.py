"""Resolve (deterministic) — schema §7 step 1.

Pure data lookup against the curated grounding. grade_check is the trust feature:
a topic only resolves if its Kompetenzbereich actually belongs to the requested
Klasse. Anything outside the curated catalogue produces honest gap notes, not a
hallucinated resolution.
"""

from __future__ import annotations

from datetime import date

from ..grounding import lehrplan_store as store
from ..schema.worksheet import BundleRequest, LehrplanResolution


def _matches_topic(kompetenzbereich: str, topic_raw: str) -> bool:
    t = topic_raw.casefold()
    kb = kompetenzbereich.casefold()
    if kb in t or t in kb:
        return True
    # token overlap on significant words (e.g. "Strahlung" matches the KB)
    kb_tokens = {w for w in kb.replace("und", " ").split() if len(w) > 4}
    return any(tok in t for tok in kb_tokens)


def resolve(req: BundleRequest, *, today: date | None = None) -> LehrplanResolution:
    today = today or date.today()
    fassung = store.get_fassung()
    notes: list[str] = []

    # Fassung window check (handoff §2: versioning against Fassung windows).
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

    model = store.get_subject_model(req.subject)
    if model is None:
        notes.append(
            f"Fach '{req.subject}' ist im Demo-Katalog nicht hinterlegt "
            f"(verfügbar: {', '.join(store.list_subjects())})."
        )
        return LehrplanResolution(
            fassung=fassung, subject=req.subject, klasse=req.klasse,
            grade_check=False, competences=[], notes=notes,
        )

    all_for_grade = store.competences_for(req.subject, req.klasse)
    if not all_for_grade:
        gmap = store.grade_map(req.subject)
        if gmap:
            notes.append(
                f"Für {req.subject} {req.klasse}. Kl. sind im Demo-Katalog keine "
                "Kompetenzen hinterlegt. Kuratiert ist nur Physik 4. Kl. "
                "(Strahlung und Radioaktivität)."
            )
        else:
            notes.append(
                f"Für {req.subject} ist nur das Kompetenzmodell hinterlegt, "
                "noch keine verbatim Kompetenzen (Demo-Grenze)."
            )
        return LehrplanResolution(
            fassung=fassung, subject=req.subject, klasse=req.klasse,
            grade_check=False, competences=[], notes=notes,
        )

    matched = [c for c in all_for_grade if _matches_topic(c.kompetenzbereich, req.topic_raw)]
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
