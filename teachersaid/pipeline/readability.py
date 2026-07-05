"""Readability estimate - the Erste Wiener Sachtextformel (Bamberger/Vanecek) - DETERMINISTIC
(given the heuristics below), ADVISORY-ONLY (roadmap A6).

Source: Bamberger, R. / Vanecek, E. (1984), *Lesen - Verstehen - Lernen - Schreiben. Die
Schwierigkeitsstufen von Texten in deutscher Sprache*, Wien: Jugend & Volk. The formula
(WSTF1, the first of four Bamberger/Vanecek variants - this module implements only WSTF1,
the "no word-frequency lookup needed" one):

    WSTF1 = 0.1935*MS + 0.1672*SL + 0.1297*IW - 0.0327*ES - 0.875

    MS  = % of words with >= 3 syllables        ("Mehrsilbler")
    SL  = mean sentence length in words         ("Satzlaenge")
    IW  = % of words longer than 6 letters      ("Info-lastige Woerter")
    ES  = % of one-syllable words               ("Einsilbler")

    (percentages are 0..100, not 0..1 - this is the detail that trips up ports of the
    formula: MS/IW/ES are literally "times 100", so e.g. MS=50.0 means half the words are
    polysyllabic, not "0.5")

The result is a German **Schulstufe** estimate, roughly 4 (very easy) .. 15 (very hard /
academic). This is THE canonical German-language readability measure taught in Austrian
teacher education (there are newer variants - WSTF2..4 trade the IW/ES terms for a
word-frequency lookup, which needs a corpus we don't have - and the "Flesch" family is
English-calibrated and not used here).

Why this is advisory-lane only (see CLAUDE.md's lint-lane rule): German syllable counting
by vowel-group heuristics is provably imperfect (compounds, hiatus, foreign loanwords,
abbreviations) - there is no closed-form rule that is always right, only well-documented
approximations. A wrong syllable count shifts MS/ES by a few points, which shifts the
Schulstufe estimate by a fraction of a grade - useful as a directional flag for the SME,
never as a gate. See `_count_syllables` for the documented heuristic and its known misses.
"""

from __future__ import annotations

import re

from ..schema.blocks import BlockBase
from ..schema.richtext import InlineRun, RichText

# A block needs at least this many prose words before an estimate means anything - MS/SL/
# IW/ES on a 10-word snippet is noise, not signal (a single long compound noun can swing
# MS by 10 points). Named per the task brief ("constant with a name").
MIN_WORDS_FOR_ESTIMATE = 30

# Klasse -> Schulstufe: AHS-Klasse 1..4 (Unterstufe) = Schulstufe 5..8, Klasse 5..8
# (Oberstufe) = Schulstufe 9..12 - i.e. a flat +4 offset across both Stufen.
KLASSE_TO_SCHULSTUFE_OFFSET = 4

# verify.py warns when the estimate exceeds the worksheet's target Schulstufe by more
# than this many grade-levels (advisory threshold, not a gate).
SCHULSTUFE_OVERSHOOT_WARN = 2.0


# --- German syllable counting (heuristic; vowel-group + documented special cases) -------
#
# The approach: count maximal runs of vowel-like characters ("nuclei"), then apply a short
# list of German-specific corrections. Known, accepted misses (this is why the module is
# advisory-lane, not a guarantee):
#   * silent 'e' in French/English loanwords ("Cafe", "Team") is not corrected;
#   * some compounds with a genuine hiatus across the morpheme boundary undercount by one
#     if the two vowels are identical ("Seeelefant" is not attempted - rare in schoolbook
#     prose);
#   * 'y' as a consonant (e.g. "Yoga") is over-counted as a vowel-start - accepted, 'y' is
#     a vowel far more often in German schoolbook vocabulary ("Physik", "Symbol", "System").

_VOWELS = "aeiouyäöü"

# German has exactly THREE phonetic diphthongs (a single spoken nucleus written with two
# vowel letters): ei/ai (same sound, two spellings), au, eu/äu (same sound, two spellings).
# Every OTHER two-distinct-vowel-letter run that occurs in German words is a Latin/Greek/
# Romance loanword vowel sequence and is ALWAYS spoken as two separate nuclei (hiatus) -
# "eo" (Video), "io" (Nation, Podium's -iu is the same family), "iu" (Podium), etc. So the
# default for an unrecognised 2-letter run is HIATUS, with the closed diphthong set as the
# listed exception - the inverse of what a naive port of this heuristic usually assumes,
# and the reason the brief's Nation/Familie/Museum examples exist as named test cases.
_DIPHTHONGS = ("äu", "eu", "ei", "ai", "au")

# 'ie' is the tricky one: it is not phonetically a diphthong at all but the SPELLING of a
# long simple "i:" sound (Wiese, Liebe, Tier) - which is exactly why it doubles as the
# hiatus spelling in the unstressed Latin/Greek -ie loanword ending (Familie, Chemie,
# Serie, Studie). A bare substring match can't tell the two apart; they are disambiguated
# by POSITION instead: 'ie' is hiatus when the run is the WORD-FINAL run, and the long-i
# reading (one nucleus) otherwise. This is a genuine, well-known German orthographic
# regularity (the -ie ending is always unstressed and syllabic), not a guess.
_IE_HIATUS_IF_WORD_FINAL = "ie"

# 'eu' is the other ambiguous pair: diphthong in Feuer/Freund/neu, but hiatus in the Latin
# -eum suffix (Museum, Mausoleum) - there the 'u' of "-um" belongs to the NEXT vowel run,
# so the 'eu' run's tail is just a bare trailing "m" (never the case for the genuine
# diphthong reading, whose tail is a full syllable or empty).
_EU_HIATUS_BEFORE_TAIL = "m"


def _count_syllables(word: str) -> int:
    """Heuristic German syllable count for one word (letters only, case-insensitive).

    Algorithm: scan for maximal vowel-letter runs ("nuclei candidates"); a bare run of
    2+ vowel letters is normally ONE nucleus (long vowel or diphthong: "Boot", "Haus"),
    UNLESS the run matches a known hiatus pattern (Familie/Nation/Museum-type), in which
    case it splits into two. Consonant runs (incl. 'qu' treated as one leading consonant)
    are skipped between nuclei. A word with zero vowel letters (e.g. a bare abbreviation
    "usw") counts as 1 syllable - every spoken word has at least one nucleus.
    """
    w = word.lower()
    w = re.sub(r"[^a-zäöüß]", "", w)  # letters only; sz behaves as a consonant
    if not w:
        return 0
    w = w.replace("qu", "kw")  # 'qu' is one consonant sound, not a vowel-adjacent 'u'

    count = 0
    seen_a_run = False  # tracks whether an earlier vowel-letter run preceded this one
                        # (NOT the same as "this run starts at character index 0" - a
                        # word can start with a consonant, as "die" does)
    i = 0
    n = len(w)
    while i < n:
        if w[i] not in _VOWELS:
            i += 1
            continue
        # found the start of a vowel-letter run
        j = i
        while j < n and w[j] in _VOWELS:
            j += 1
        run = w[i:j]
        tail = w[j:]  # what follows the run: the -eum suffix check + word-final test
        count += _nuclei_in_run(run, tail, at_word_start=not seen_a_run)
        seen_a_run = True
        i = j
    return max(count, 1)


def _nuclei_in_run(run: str, tail: str, *, at_word_start: bool) -> int:
    """How many syllable nuclei a maximal vowel-letter run represents.

    `tail` is the (lowercased) remainder of the word after this run - used to decide
    word-final position (the -ie ending) and the -eum suffix trigger; `tail == ""` means
    the run reaches the end of the word. `at_word_start` says this run is the word's
    FIRST vowel-letter run - needed so the closed-class monosyllables "die/sie/wie/nie"
    (a single consonant + a word-final "ie" with nothing before it - the whole word IS
    the long-i sound, so hiatus is not even a possible reading) don't get mistaken for
    the genuine polysyllabic -ie loanword ending (Famil-ie, Ser-ie, Stud-ie: those always
    have at least one syllable BEFORE the trailing -ie)."""
    if len(run) == 1:
        return 1
    # a doubled identical vowel ("Boot", "Idee", "Haar") is one long nucleus, never hiatus
    if len(run) == 2 and run[0] == run[1]:
        return 1
    if len(run) == 2:
        if run == _IE_HIATUS_IF_WORD_FINAL:
            # Famil-ie/Ser-ie (hiatus) needs BOTH word-final AND something before it;
            # Wies-e (long i, mid-word) and Sie/Wie/Die/Nie (long i, nothing before it)
            # both read as one nucleus.
            return 2 if (tail == "" and not at_word_start) else 1
        if run == "eu" and tail == _EU_HIATUS_BEFORE_TAIL:
            return 2                               # Mus-eu-m (hiatus, the -eum suffix)
        if run in _DIPHTHONGS:
            return 1
        return 2  # default for an unrecognised 2-vowel run: hiatus (Nation, Video, Podium)
    # length >= 3: walk it as (one nucleus, using the same rules on its 2-letter prefix)
    # + recurse on the remainder, so a genuine 3+ vowel run resolves letter-by-letter
    # (rare in practice - most German runs of 3+ vowel LETTERS already split at a
    # consonant boundary before reaching this branch).
    head, rest = run[:2], run[2:]
    # rebuild context for the head: if there's a rest, the head is not word-final and
    # (since a whole run only counts as at_word_start when the ENTIRE run starts at 0)
    # a non-empty rest means there IS something after the head, which is irrelevant to
    # at_word_start (unchanged) but means the head is not the tail-word-final position
    head_tail = tail if not rest else "x"  # "x" is any non-empty marker: head is mid-run
    return (_nuclei_in_run(head, head_tail, at_word_start=at_word_start)
            + (_nuclei_in_run(rest, tail, at_word_start=False) if rest else 0))


# --- sentence splitting (simple, documented abbreviation guards) ------------------------

# Abbreviations that end in a period WITHOUT ending a sentence - guarded so ". " after
# one of these doesn't split. German abbreviations are fixed-case; matched literally.
_ABBREVIATIONS = (
    "z. B.", "z.B.", "u. a.", "u.a.", "bzw.", "ca.", "Dr.", "Prof.", "usw.", "etc.",
    "d. h.", "d.h.", "Nr.", "Abb.", "Jh.", "v. Chr.", "n. Chr.", "u. v. m.", "u.v.m.",
    "Mag.", "Ing.", "St.",
)

_SENTENCE_END = re.compile(r"[.!?:]+")

# An internal marker swapped in for the period of a protected abbreviation, so the
# sentence-boundary regex doesn't split there; restored to '.' afterwards. Chosen to be
# something that cannot occur in ordinary German prose (letters, no punctuation).
_DOT_MARKER = "ZZDOTZZ"


def _split_sentences(text: str) -> list[str]:
    """Split on . ! ? : with a simple abbreviation guard: a candidate split point is
    skipped if the text immediately before it ends with a known abbreviation. This is
    intentionally simple (documented heuristic, not a full tokenizer) - a name that
    happens to end in one of these strings ("usw." mid-sentence is the only realistic
    case) is the accepted, rare miss."""
    protected = text
    for abbr in _ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", _DOT_MARKER))
    parts = _SENTENCE_END.split(protected)
    out = []
    for p in parts:
        p = p.replace(_DOT_MARKER, ".").strip()
        if p:
            out.append(p)
    return out


# --- word extraction ---------------------------------------------------------------------

_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+"
                   r"(?:[-'][A-Za-zÀ-ÖØ-öø-ÿ]+)*")


def _words(text: str) -> list[str]:
    """Tokenise into words - letters (+ internal hyphen/apostrophe for compounds like
    'Erste-Hilfe'), no digits/punctuation-only tokens."""
    return _WORD.findall(text)


# --- RichText -> plain prose, skipping math runs -------------------------------------------

def extract_prose(value: RichText | None) -> str:
    """Flatten a schema RichText value to plain prose for readability analysis,
    explicitly SKIPPING any run with `math=True` (LaTeX would corrupt syllable/word
    counts - a fraction like a LaTeX \\frac{1}{2} is not German prose)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for run in value:
            if isinstance(run, InlineRun):
                if run.math or run.ref_block is not None:
                    continue
                parts.append(run.text)
            elif isinstance(run, dict):
                if run.get("math") or run.get("ref_block") is not None:
                    continue
                parts.append(run.get("text", ""))
        return " ".join(p for p in parts if p)
    return str(value)


# --- the formula --------------------------------------------------------------------------

def wstf(text: str) -> float | None:
    """Erste Wiener Sachtextformel (WSTF1) for a plain-text prose passage.

    Returns None if there are too few words (see MIN_WORDS_FOR_ESTIMATE) or no sentences
    to measure a sentence length from - a short snippet is statistical noise, not signal.
    """
    words = _words(text)
    if len(words) < MIN_WORDS_FOR_ESTIMATE:
        return None
    sentences = _split_sentences(text)
    if not sentences:
        return None

    syll_counts = [_count_syllables(w) for w in words]
    n = len(words)
    ms = 100.0 * sum(1 for s in syll_counts if s >= 3) / n   # Mehrsilbler %
    es = 100.0 * sum(1 for s in syll_counts if s == 1) / n   # Einsilbler %
    iw = 100.0 * sum(1 for w in words if len(w) > 6) / n     # info-lastige Woerter %
    sl = n / len(sentences)                                   # mean sentence length

    return 0.1935 * ms + 0.1672 * sl + 0.1297 * iw - 0.0327 * es - 0.875


def estimate_block(block: BlockBase) -> float | None:
    """WSTF1 estimate for one schema block's prose, or None when there isn't enough of
    it (< MIN_WORDS_FOR_ESTIMATE words) to mean anything. Pulls `content` (InfoBlock) or
    `prompt` (TaskBlock) - the block's principal prose field - via `extract_prose` (math
    runs skipped). Does not look at `answer_key`/`acceptable_reasoning`/`teacher_note`:
    those are teacher-only and not what a *student* reads off the sheet."""
    raw = getattr(block, "content", None)
    if raw is None:
        raw = getattr(block, "prompt", None)
    return wstf(extract_prose(raw))


def klasse_to_schulstufe(klasse: int) -> int:
    """AHS Klasse (1..8, Unter- and Oberstufe alike) -> Schulstufe (5..12)."""
    return klasse + KLASSE_TO_SCHULSTUFE_OFFSET


def advisory_exempt(block: BlockBase) -> bool:
    """True when the "Text ggf. vereinfachen" advisory is inapplicable BY CONSTRUCTION:
    verbatim selected material (a `quoted` expression, a `source_text` block) is not ours
    to simplify - an 1815 legal text or an authentic PD Lesetext is deliberately hard;
    its difficulty is the Quellenarbeit/Lesekompetenz point, not a defect. The ESTIMATE
    itself stays available (dashboard cards may still show it - knowing a source reads at
    Schulstufe 14 is useful); only the verify warning is suppressed."""
    if getattr(block, "kind", None) == "source_text":
        return True
    provenance = getattr(block, "provenance", None)
    return getattr(provenance, "expression_origin", None) == "quoted"
