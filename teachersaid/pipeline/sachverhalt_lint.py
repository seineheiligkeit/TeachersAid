"""The Sachverhalt entity-lint — DETERMINISTIC, the correct-by-construction guard on AUTHORING.

The Darstellung pass authors prose freely *over the frozen, sourced fact-set* (`invariants.md`
§3, the "re-expressed under constraint" mechanism). This lint is what makes that authoring
correct-by-construction rather than merely trusted: every load-bearing entity in the prose must
already appear in the fact-set, so no out-of-set fact can survive — the same discipline as the
rendering layer (a projection that cannot reach back and invent content).

Honest scope (the German wrinkle, stated plainly):

* **Years — the HARD guarantee (problem).** Every 3–4 digit year in a Darstellung section must
  appear in the fact-set's number vocabulary (timeline `at` values + numbers inside the facts).
  Regex-clean; this is what catches the 1815→1851 garble the design names.
* **Proper names — ADVISORY (warning).** German capitalises *every* noun, so the English
  "capitalised token = proper name" heuristic is useless. We flag only a *multi-word* capitalised
  phrase ("Wiener Kongress", "Klemens von Metternich") *none* of whose significant tokens appear
  anywhere in the fact-set — a strong signal of a wholly-invented entity, low false-positive rate.
  Names lean on the SME gate; numbers are machine-guaranteed.
* **Quoted spans — ADVISORY (warning).** A long „…" span absent from the fact-set is flagged
  (could be an uncited citation, or mere emphasis — hence advisory).
* **grounded_by audit — ADVISORY (warning).** A `grounded_by` key matching no fact is flagged.

Runs at ingest/derivation time on the `Sachverhalt` object (not in worksheet `verify`, where the
fact-set is already projected away). The derived worksheet's prose blocks carry `role="facts"`
provenance, so the existing `prose_lint` covers them at the worksheet level.
"""

from __future__ import annotations

import re

from ..schema.richtext import plain_text
from ..schema.sachverhalt import Sachverhalt


def _p(rt) -> str:
    """plain_text that tolerates empty RichText (an empty InlineRun fails validation)."""
    return plain_text(rt) if rt else ""


_YEAR_RE = re.compile(r"\b\d{3,4}\b")
# a multi-word capitalised phrase (allowing lowercase nobiliary/relator particles) — a strong
# proper-name signal in German, unlike a single capitalised noun.
_NAME_RE = re.compile(
    r"[A-ZÄÖÜ][\wäöüß]+(?:\s+(?:von|van|zu|zur|de|del|der|den|of|the|el|al)\s+[A-ZÄÖÜ][\wäöüß]+"
    r"|\s+[A-ZÄÖÜ][\wäöüß]+)+")
_QUOTE_RE = re.compile(r"„([^“”\"]{1,})[“”\"]")
_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+")
_PARTICLES = {"von", "van", "zu", "zur", "de", "del", "der", "den", "of", "the", "el", "al"}
# common German function/numeral words that, capitalised at a sentence start, masquerade as a
# proper-name head ("Die Karte", "Drei Arten") — excluded so the advisory name check only fires on
# a genuine multi-token proper name (German capitalises every noun, so this must stay conservative).
_NAME_STOP = _PARTICLES | {
    "der", "die", "das", "dem", "den", "ein", "eine", "einen", "einem", "einer", "und", "oder",
    "aber", "auf", "aus", "bei", "mit", "nach", "vor", "für", "über", "unter", "durch", "gegen",
    "ohne", "beim", "drei", "zwei", "vier", "fünf", "viele", "manche", "diese", "dieser",
    "dieses", "jede", "jeder", "jedes", "alle", "auch", "dann", "noch", "schon", "sehr", "mehr",
    "etwa", "heute", "damals", "dort", "hier", "wenn", "weil", "dass",
}


def _fact_text(sv: Sachverhalt) -> str:
    """All fact-set strings concatenated (lowercased) — the allowed entity vocabulary."""
    parts: list[str] = [sv.topic, _p(sv.leitfrage), _p(sv.bedeutung),
                        _p(sv.gegenwartsbezug), _p(sv.urteilsfrage)]
    parts += list(sv.keywords)
    for e in sv.timeline:
        parts += [str(e.at), e.label, _p(e.text)]
    for a in sv.actors:
        parts += [a.name, _p(a.role)]
    for c in sv.causes:
        parts += [c.cause, c.effect]
    for c in sv.concepts:
        parts += [c.term, _p(c.definition)]
    parts.append(sv.process_name)
    for st in sv.process:
        parts += [st.name, _p(st.text)]
    for r in sv.regions:
        parts += [r.name, _p(r.note)]
    for s in sv.sources:
        parts += [s.title or "", s.quote_span or ""]
    return "  ".join(p for p in parts if p).lower()


def _fact_years(vocab: str, sv: Sachverhalt) -> set[str]:
    years = set(_YEAR_RE.findall(vocab))
    for e in sv.timeline:
        years |= set(_YEAR_RE.findall(str(e.at)))
    return years


def _fact_keys(sv: Sachverhalt) -> set[str]:
    keys: set[str] = set()
    for e in sv.timeline:
        keys.add(e.label.lower())
    for a in sv.actors:
        keys.add(a.name.lower())
    for c in sv.concepts:
        keys.add(c.term.lower())
    for c in sv.causes:
        keys.update({c.cause.lower(), c.effect.lower(), f"{c.cause} → {c.effect}".lower()})
    for st in sv.process:
        keys.add(st.name.lower())
    for r in sv.regions:
        keys.add(r.name.lower())
    return keys


def lint(sv: Sachverhalt) -> tuple[list[str], list[str]]:
    """(problems, warnings). Years out-of-set → problem; names/quotes/grounded_by → warnings."""
    problems: list[str] = []
    warnings: list[str] = []
    vocab = _fact_text(sv)
    fact_years = _fact_years(vocab, sv)
    fact_keys = _fact_keys(sv)
    seen_names: set[str] = set()

    for i, sec in enumerate(sv.darstellung, 1):
        body = _p(sec.body)
        loc = f"darstellung[{i}] „{sec.heading}“"

        # (1) years — the HARD guarantee
        for y in _YEAR_RE.findall(body):
            if y not in fact_years:
                problems.append(
                    f"{loc}: Jahreszahl {y} steht nicht im Faktenset — die Darstellung darf nur "
                    f"Daten aus den kuratierten Fakten verwenden (select-never-author).")

        # (2) proper names — ADVISORY (multi-word; flag only if NO token is known)
        for m in _NAME_RE.finditer(body):
            toks = [t for t in _WORD_RE.findall(m.group(0))
                    if len(t) >= 4 and t.lower() not in _NAME_STOP]
            # only a genuine multi-token proper name (>=2 significant tokens, none known) is flagged
            if len(toks) >= 2 and all(t.lower() not in vocab for t in toks):
                key = " ".join(toks).lower()
                if key not in seen_names:
                    seen_names.add(key)
                    warnings.append(
                        f"{loc}: „{m.group(0).strip()}“ wirkt wie ein Eigenname, steht aber nicht "
                        f"im Faktenset (heuristische Namensprüfung, Deutsch — am Gate prüfen).")

        # (3) quoted spans — ADVISORY
        for q in _QUOTE_RE.findall(body):
            if len(q) > 12 and q.lower() not in vocab:
                warnings.append(
                    f"{loc}: wörtliches Zitat „{q[:40]}…“ nicht im Faktenset — als Quelle "
                    f"eintragen (role='facts'/'expression') oder umformulieren.")

        # (4) grounded_by audit — ADVISORY
        for key in sec.grounded_by:
            if key.lower() not in fact_keys:
                warnings.append(f"{loc}: grounded_by-Verweis „{key}“ passt zu keinem Fakt im Set.")

    return problems, warnings
