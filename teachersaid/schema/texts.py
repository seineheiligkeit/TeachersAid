"""Annotated authentic texts (the Deutsch "asset class").

The reading/writing analogue of the grounded-facts data layer: a real, rights-cleared
text + a *curated annotation layer*. The discipline mirrors the data layer — the text is
**select, never author** (an actual PD/licensed text, cited), and each task's answer is
**derived from a vetted annotation, never authored at task time** (no hallucinated
Erwartungshorizont). One annotated text → many aligned tasks (comprehension, close-reading,
Medienkritik, materialgestütztes Schreiben) across grades. "Correct by *curation*" (HITL),
not by computation — there is no sympy for German — but far more trustworthy than free
LLM authoring, and it compounds like the dataset/competence catalogs.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .blocks import Serves
from .richtext import RichText

# annotation kinds → the tasks they license (see pipeline/text_tasks.py)
AnnotationKind = Literal[
    "vocab",            # a hard word + gloss (reading scaffold; Latin: Vokabel → Bedeutung)
    "comprehension",    # a question answerable from the text + its answer (Realien: the scan warm-up)
    "structure",        # a structural part (Einleitung/Strophe/Argumentationsgang)
    "stilmittel",       # a rhetorical/poetic device at a span + its Wirkung
    "argument_move",    # These/Beleg/Gegenargument (argumentative texts)
    "media_technique",  # how the text persuades/constructs (Medienkompetenz)
    "erwartungshorizont",  # expected-answer points for an open interpretation/Stellungnahme
    "translation",      # (Latin) translate a line/passage → the model translation is the answer
    "grammar",          # (Latin) determine a form/construction → the answer (SPR analysis)
    "culture",          # (Latin) content/cultural question → the answer (INH dimension)
    "communicative",    # (Realien/FS) a productive written task (write a reply/message) + model answer
    "roleplay",         # (Realien/FS) a Sprechkarte: an oral pair task; `roles` = the per-partner cues
]

RightsBasis = Literal["public_domain_pma", "public_domain_mark", "cc_by", "cc0", "cleared"]

# Realien honesty mode (see Documents/realien-design.md §5). "constructed" is the DEFAULT for the
# modern-FS Sprechanlass — invented-coherent pedagogical fiction, no source/rights gate; the
# language (not the facts) is what the SME vets. "sourced"/"adapted" re-acquire the rights gate.
RealieOrigin = Literal["constructed", "sourced", "adapted"]


class RealieFact(BaseModel):
    """One row of a Realie's light internal fact-set (a timetable row, a menu item). Pure
    scaffold for INTERNAL CONSISTENCY (`pipeline/realie_lint.py`) — invented-coherent, never
    world-grounded. The lint checks that a task answer's data tokens appear here or in the text."""
    model_config = ConfigDict(extra="forbid")
    label: str                               # e.g. "08:14 to London" / "Tagesmenü"
    value: str | None = None                 # e.g. "Platform 3" / "€9,50"


class TextSourceRef(BaseModel):
    """Provenance + rights for an authentic text — the text analogue of `SourceRef`,
    with the copyright nuances the roadmap flagged: a work PD in the US may still be in
    copyright in Austria (70 Jahre p.m.a.), and a PD work ≠ a PD reproduction."""
    model_config = ConfigDict(extra="forbid")
    author: str
    title: str
    year: str | None = None                  # year of the work
    author_death_year: int | None = None     # for the AT 70-Jahre-post-mortem-auctoris rule
    rights_basis: RightsBasis = "public_domain_pma"
    licence: str | None = None
    repository: str                          # Projekt Gutenberg-DE · Wikisource · ANNO/ÖNB …
    url: str | None = None
    retrieved: str | None = None
    attribution: str                         # the citation string rendered under the text

    def is_clear(self, today_year: int) -> tuple[bool, list[str]]:
        """Whether the text may be redistributed; returns (ok, reasons-if-not)."""
        if self.rights_basis in ("cc_by", "cc0", "cleared"):
            return True, []
        if self.rights_basis == "public_domain_mark":
            if not self.licence or "public domain mark" not in self.licence.casefold():
                return False, ["public_domain_mark but no Public Domain Mark recorded in licence"]
            return True, []
        if self.rights_basis == "public_domain_pma":
            if self.author_death_year is None:
                return False, ["public_domain_pma but no author_death_year recorded"]
            if today_year - self.author_death_year < 70:
                return False, [f"author died {self.author_death_year}: not yet 70 Jahre p.m.a."]
            return True, []
        return False, [f"unknown rights_basis {self.rights_basis!r}"]


class Annotation(BaseModel):
    """One curated annotation on the text. Task-bearing kinds carry the vetted `answer`,
    so a derived task's `answer_key` is the curation, never authored at task time."""
    model_config = ConfigDict(extra="forbid")
    kind: AnnotationKind
    zeile: str | None = None                 # line ref, e.g. "5" or "5-7"
    span: str | None = None                  # the quoted snippet it refers to
    label: str                               # the word / question / device name / claim
    answer: RichText | None = None           # gloss / answer / Wirkung / expected points
    cognitive_level: str = "understand"      # for the derived task
    dimensions: list[str] = Field(default_factory=list)   # DEU dims (LES/SCH/SPR)
    roles: list[str] = Field(default_factory=list)        # (roleplay) per-partner Sprechkarte cues


class AnnotatedText(BaseModel):
    """A real text + its curated annotation layer (the curated in-repo record)."""
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    subject: str = "Deutsch"
    klasse: int
    text: str                                # the actual text (audio: the transcript), newline-sep
    genre: str | None = None                 # Märchen · Gedicht · Fabel · Speisekarte · Fahrplan
    textsorte: str | None = None
    # `source` is OPTIONAL: a constructed Realie (invented-coherent fiction) has no source and
    # rides no rights gate — only a `sourced`/`adapted` text must cite + clear (see ingest_text).
    source: TextSourceRef | None = None
    # --- Realien (modern-FS communicative reading; Documents/realien-design.md) ---
    cefr: Literal["A1", "A2", "B1", "B2"] | None = None    # the controlled-input level (SME-judged)
    origin: RealieOrigin = "constructed"     # honesty mode; "constructed" is the FS default (§5)
    scene: str | None = None                 # the communicative situation ("At the station")
    facts: list[RealieFact] = Field(default_factory=list)  # the light internal fact-set (scaffold)
    # Optional, SME-approved file-backed asset id. The backdrop is atmospheric only: the Realie's
    # task-bearing timetable/menu remains text in the content object and is rendered by code.
    backdrop_asset: str | None = None
    # --- audio (Hörverstehen, FS): a spoken text with a transcript ---
    medium: str = "text"                     # "text" | "audio" (a listening text)
    show_transcript: bool = False            # audio: also show the transcript to students (A1: listen-and-read)
    lang: str | None = None                  # BCP-47 hint for TTS, e.g. "en"
    voice: str | None = None                 # optional TTS voice id
    annotations: list[Annotation] = Field(default_factory=list)
    serves: list[Serves] = Field(default_factory=list)    # DEU competences text+tasks target
    keywords: list[str] = Field(default_factory=list)

    def line_count(self) -> int:
        return len(self.text.splitlines())
