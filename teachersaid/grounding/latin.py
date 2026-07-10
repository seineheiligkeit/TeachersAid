"""Latin word-formation grounding — curated morphology facts (Wortbildung).

The Latein analogue of the qualitative chemistry tables (``grounding/chemistry.py``):
curated **facts** the Wortbildung recipes (``pipeline/latin.py``) read. The discipline is
identical — *select, never author*:

- **Every entry in ``DERIVED_WORDS`` is a real, attested, textbook-standard classical
  Latin word** (Stowasser-level school vocabulary) with its standard German school
  meaning. The recipe layer only ever SELECTS an entry; it never synthesizes a
  prefix+base combination that is not curated here — **no invented Latin, ever**. (A
  mechanical ``prefix + base`` string join would happily produce unattested or
  wrongly-assimilated forms; this table is exactly what forbids that failure.)
- **Composition is recorded explicitly.** Where the surface form differs from the
  citation forms (assimilation: ad+capere → *accipere*; vowel weakening: capere →
  ``-cipere`` in Komposita), the entry carries the assimilated ``surface`` prefix and
  the ``base_form`` — so ``word == surface_prefix() + surface_base()`` holds for EVERY
  row (a test locks this structural identity; an invented form cannot hide).
- **Meaning is curated, not derived.** ``transparent=False`` flags entries whose school
  meaning is NOT directly compositional (*amittere* = verlieren, not "wegschicken") —
  the "erschließe die Bedeutung" ask draws only transparent entries; the answer shown
  is always the curated one, with the meaning shift explained in ``note``.

Why this exists: *trennen (Wortbildung)* is the most frequent IT-Arbeitsaufgaben family
in the SRDP Latein corpus (``Documents/matura-latein-coverage.md``), and the Lehrplan's
Klasse-3 Anwendungsbereich names "Wortbildungselemente" explicitly. Each row is one
SME-reviewable datum (the SME fact-checks the Latin and the German at the review gate);
add a word = add one curated row.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prefix:
    """A Latin verbal prefix (Präverb) with its German school meaning.

    ``assimilation`` is a German display note on the sound changes the prefix undergoes
    before certain consonants ("" if it never changes)."""
    form: str          # citation form, e.g. "ad-"
    meaning: str       # German meaning(s), e.g. "zu, heran, hinzu"
    assimilation: str = ""


PREFIXES: dict[str, Prefix] = {
    "ab-": Prefix("ab-", "weg, fort",
                  "vor f zu au- (auferre), vor m zu a- (amittere)"),
    "ad-": Prefix("ad-", "zu, heran, hinzu",
                  "das d gleicht sich oft an den Folgekonsonanten an: ad+c → acc- "
                  "(accipere), ad+f → aff- (afferre), ad+p → app-, ad+t → att-"),
    "con-": Prefix("con-", "zusammen, mit",
                   "vor b/m/p zu com- (componere), vor l zu col-, vor r zu cor-, "
                   "vor Vokal und h zu co-"),
    "de-": Prefix("de-", "herab, weg"),
    "ex-": Prefix("ex-", "heraus, hinaus",
                  "vor f zu ef- (efferre); vor stimmhaften Konsonanten meist e- (educere)"),
    "in-": Prefix("in-", "hinein, in, an",
                  "vor b/m/p zu im- (importare), vor l zu il-, vor r zu ir-"),
    "per-": Prefix("per-", "durch, hindurch; (verstärkend) ganz, zu Ende"),
    "prae-": Prefix("prae-", "voraus, voran, vorher"),
    "pro-": Prefix("pro-", "vor, vorwärts, hervor"),
    "re-": Prefix("re-", "zurück, wieder",
                  "vor Vokal zu red- (redire)"),
    "sub-": Prefix("sub-", "unter; von unten heran",
                   "vor c zu suc- (succedere), vor f zu suf-, vor g zu sug-, vor p zu sup-"),
    "trans-": Prefix("trans-", "hinüber, über … hin",
                     "vor manchen Konsonanten verkürzt zu tra- (tradere, traducere)"),
}

# Base verb (citation infinitive) → German school meaning.
BASE_VERBS: dict[str, str] = {
    "ducere": "führen",
    "ferre": "tragen, bringen",
    "mittere": "schicken",
    "ponere": "setzen, stellen, legen",
    "venire": "kommen",
    "capere": "nehmen, fassen",
    "cedere": "gehen, weichen",
    "ire": "gehen",
    "portare": "tragen, bringen",
}


@dataclass(frozen=True)
class DerivedWord:
    """One curated, attested compound. The structural identity every row satisfies:
    ``word == surface_prefix() + surface_base()`` (locked by a test)."""
    word: str            # attested surface form, e.g. "accipere"
    prefix: str          # key into PREFIXES, e.g. "ad-"
    base: str            # key into BASE_VERBS, e.g. "capere"
    meaning: str         # German school meaning of the compound (curated truth)
    surface: str = ""    # assimilated prefix surface in this word, if ≠ the prefix stem
    base_form: str = ""  # base surface in this word, if ≠ the citation form
    note: str = ""       # curated meaning-shift note (German, display), "" if plain
    transparent: bool = True  # meaning directly derivable from prefix+base? (False →
                              # excluded from the "erschließe die Bedeutung" ask)

    def surface_prefix(self) -> str:
        return self.surface or self.prefix.rstrip("-")

    def surface_base(self) -> str:
        return self.base_form or self.base


# Every row: a real, attested, school-standard Latin verb. SME-reviewable data.
DERIVED_WORDS: list[DerivedWord] = [
    # --- ducere (führen) ---------------------------------------------------------
    DerivedWord("abducere", "ab-", "ducere", "wegführen"),
    DerivedWord("deducere", "de-", "ducere", "hinabführen, geleiten"),
    DerivedWord("educere", "ex-", "ducere", "herausführen", surface="e"),
    DerivedWord("reducere", "re-", "ducere", "zurückführen"),
    # --- ferre (tragen, bringen) -------------------------------------------------
    DerivedWord("afferre", "ad-", "ferre", "herbeitragen, herbeibringen", surface="af"),
    DerivedWord("auferre", "ab-", "ferre", "wegtragen, wegbringen", surface="au"),
    DerivedWord("conferre", "con-", "ferre", "zusammentragen; vergleichen"),
    DerivedWord("efferre", "ex-", "ferre", "hinaustragen, heraustragen", surface="ef"),
    DerivedWord("referre", "re-", "ferre", "zurückbringen; berichten"),
    DerivedWord("transferre", "trans-", "ferre", "hinübertragen, übertragen"),
    # --- mittere (schicken) ------------------------------------------------------
    DerivedWord("amittere", "ab-", "mittere", "verlieren", surface="a",
                note="Bedeutungswandel: „wegschicken, aus der Hand geben“ → „verlieren“",
                transparent=False),
    DerivedWord("permittere", "per-", "mittere", "erlauben, überlassen",
                note="Bedeutungswandel: „hindurchlassen“ → „zulassen, erlauben“",
                transparent=False),
    DerivedWord("praemittere", "prae-", "mittere", "vorausschicken"),
    DerivedWord("promittere", "pro-", "mittere", "versprechen",
                note="Bedeutungswandel: „hervor-, in Aussicht stellen“ → „versprechen“",
                transparent=False),
    DerivedWord("remittere", "re-", "mittere", "zurückschicken"),
    # --- ponere (setzen, stellen, legen) -----------------------------------------
    DerivedWord("componere", "con-", "ponere", "zusammensetzen, zusammenstellen",
                surface="com"),
    DerivedWord("deponere", "de-", "ponere", "ablegen, niederlegen"),
    DerivedWord("exponere", "ex-", "ponere", "herausstellen, darlegen"),
    DerivedWord("proponere", "pro-", "ponere", "vor Augen stellen, vorschlagen"),
    # --- venire (kommen) ---------------------------------------------------------
    DerivedWord("convenire", "con-", "venire", "zusammenkommen"),
    DerivedWord("invenire", "in-", "venire", "finden, erfinden",
                note="Bedeutungswandel: „auf etwas kommen“ → „finden“", transparent=False),
    DerivedWord("pervenire", "per-", "venire", "hingelangen, ankommen"),
    DerivedWord("subvenire", "sub-", "venire", "zu Hilfe kommen",
                note="Bedeutungswandel: „von unten heran-, unterstützend herbeikommen“ → "
                     "„zu Hilfe kommen“", transparent=False),
    # --- capere (nehmen, fassen) — in Komposita -cipere --------------------------
    DerivedWord("accipere", "ad-", "capere", "annehmen, empfangen",
                surface="ac", base_form="cipere"),
    DerivedWord("decipere", "de-", "capere", "täuschen", base_form="cipere",
                note="Bedeutungswandel: „wegfangen, abfangen“ → „täuschen“",
                transparent=False),
    DerivedWord("incipere", "in-", "capere", "anfangen, beginnen", base_form="cipere",
                note="Bedeutungswandel: „etwas in die Hand nehmen“ → „anfangen“",
                transparent=False),
    DerivedWord("recipere", "re-", "capere", "zurücknehmen, aufnehmen", base_form="cipere"),
    # --- cedere (gehen, weichen) --------------------------------------------------
    DerivedWord("accedere", "ad-", "cedere", "herangehen, sich nähern", surface="ac"),
    DerivedWord("concedere", "con-", "cedere", "nachgeben, zugestehen",
                note="Bedeutungswandel: „(gemeinsam) weichen“ → „nachgeben, zugestehen“",
                transparent=False),
    DerivedWord("procedere", "pro-", "cedere", "vorrücken, vorangehen"),
    DerivedWord("succedere", "sub-", "cedere", "nachrücken, nachfolgen", surface="suc"),
    # --- ire (gehen) ---------------------------------------------------------------
    DerivedWord("abire", "ab-", "ire", "weggehen"),
    DerivedWord("adire", "ad-", "ire", "herangehen, aufsuchen"),
    DerivedWord("perire", "per-", "ire", "zugrunde gehen, umkommen",
                note="Bedeutungswandel: „ganz dahingehen“ → „zugrunde gehen“",
                transparent=False),
    DerivedWord("redire", "re-", "ire", "zurückgehen, zurückkehren", surface="red"),
    DerivedWord("transire", "trans-", "ire", "hinübergehen, überqueren"),
    # --- portare (tragen, bringen) -------------------------------------------------
    DerivedWord("exportare", "ex-", "portare", "ausführen, hinausschaffen"),
    DerivedWord("importare", "in-", "portare", "einführen, hineinbringen", surface="im"),
    DerivedWord("transportare", "trans-", "portare", "hinüberschaffen, befördern"),
]
