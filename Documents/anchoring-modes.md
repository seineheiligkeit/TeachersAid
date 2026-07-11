# Three-tier anchoring — Kompetenz · ÜT · Horizont

**Status: BUILT, 11 Jul 2026.** This is the trust-layer enabler from the live roadmap.

## The claim

A worksheet must say what authorizes its place in the corpus. There are exactly three
primary modes:

| mode | honest claim | allowed evidence |
|---|---|---|
| `competence` | exercises resolved verbatim subject competences | full coverage table + automatic gaps |
| `uet` | is primarily anchored to one numbered übergreifendes Thema | exact ÜT number/name; optional genuinely hooked secondary competences, no completeness claim |
| `horizont` | is teacher-choice enrichment beyond the Lehrplan | no `serves`, no competence table, explicit beyond-Lehrplan statement |

The modes are not quality levels. They are mutually honest descriptions of curricular
placement. Horizont is not a failed resolution; ÜT is not a loose keyword tag.

## Schema

`AnchorMode` is a closed enum in `schema/enums.py`. `WorksheetContent` and
`BundleRequest` carry:

```python
anchor_mode: AnchorMode = AnchorMode.COMPETENCE
anchor_uet: int | None = None
```

`anchor_uet` is required exactly for `uet` and constrained to 1–13. The competence
default makes all old corpus JSON backward-compatible. `Nachweis` is derived and stores
the selected mode plus its rendered label; neither the LLM nor an author may supply it.

## Deterministic path

1. `resolve(BundleRequest)` dispatches by mode.
   - Kompetenz: the existing topic/grade resolver, unchanged.
   - ÜT: the exact subject/grade catalog is filtered to competences carrying that numbered
     hook. A legend number that the subject does not carry fails honestly.
   - Horizont: validates the subject/grade but deliberately returns zero competences and an
     explicit note that no competence relation is claimed.
2. `plan` keeps the established competence skeleton for Kompetenz. ÜT/Horizont receive a
   useful three-step subject-dimension skeleton whose specs have no `serves` id.
3. The corpus-loop prompt changes with the mode. ÜT/Horizont require `serves: []`; student
   wording still never mentions internal anchoring metadata.
4. `verify` checks the exact ÜT hook and restricts any optional secondary `serves` to
   competences that actually carry it. Horizont with any `serves` is a hard problem.
5. `derive_nachweis` is the only producer of the claim:
   - Kompetenz: full universe, coverage and gaps (existing behavior).
   - ÜT: verbatim numbered hook; only explicitly served secondary competences; no false gaps.
   - Horizont: explicit voluntary enrichment; empty competence evidence.
6. The teacher PDF renders `Verankerungsmodus` before any evidence. Queue summaries expose
   `anchor_mode` and the derived human label.

## Authoring surfaces

The idea form and `POST /api/brainstorm` accept the mode and optional ÜT number. Curated
builders set the two `WorksheetContent` fields directly and use ordinary `stage_worksheet`;
the staged review request inherits the same anchor fields. Existing callers need no change.

```python
WorksheetContent(..., anchor_mode="uet", anchor_uet=13)
```

## Boundaries

- ÜT anchoring does not claim that every competence carrying the hook is covered.
- Horizont still uses a real subject model for legal task kinds/dimensions; only the
  curricular coverage claim is absent.
- The mode does not weaken factual provenance, rights, media-policy, readability,
  difficulty, or other verification gates.
- Lernarrangements retain their cross-subject ÜT resolution. This feature governs each
  `WorksheetContent`; it does not redesign the arrangement object.

## Tests

`tests/test_anchor_modes.py` locks old-JSON defaults, schema coherence, exact ÜT resolution,
non-empty ÜT/Horizont planning, prompt discipline, derived Nachweis semantics, forbidden
Horizont `serves`, PDF text, and API carriage. Full suite: **793 passed, 1 skipped**.
