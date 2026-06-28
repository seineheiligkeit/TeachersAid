"""Reads the curated voice-reference library at `grounding/voices/`.

The voice twin of `data_store.py`: it reads the deterministic fetch-tool output
(`grounding/voices/_catalog.json` + per-voice `<id>.json`, written by
`tools/fetch_vctk_voices.py` and gated by HITL review + the licence gate) and
adapts it to `schema.voices.VoiceRef`. It is the *resolver* for casting — given a
`(language, persona)` it selects a reference voice; it never authors a voice, only
looks one up. Honest gaps (no voice for a language/persona) are notes, not crashes.
"""

from __future__ import annotations

import json
from functools import lru_cache

from ..config import GROUNDING_VOICES
from ..schema.voices import VoiceRef


@lru_cache(maxsize=1)
def _catalog() -> dict:
    p = GROUNDING_VOICES / "_catalog.json"
    if not p.exists():
        return {"voices": []}
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def get_voice(voice_id: str) -> VoiceRef | None:
    entry = next((v for v in _catalog().get("voices", []) if v.get("id") == voice_id), None)
    fname = (entry or {}).get("file") or f"{voice_id}.json"
    p = GROUNDING_VOICES / fname
    if not p.exists():
        return None
    return VoiceRef.model_validate_json(p.read_text(encoding="utf-8"))


def list_voices(*, language: str | None = None) -> list[VoiceRef]:
    out = [get_voice(v["id"]) for v in _catalog().get("voices", [])]
    voices = [v for v in out if v is not None]
    if language:
        voices = [v for v in voices if v.language == language]
    return voices


def audio_path(voice: VoiceRef):
    """Absolute path to the reference clip (re-fetchable; git-ignored)."""
    return GROUNDING_VOICES / voice.audio_file


def resolve_voice(
    language: str, persona: str | None = None, *, gender: str | None = None,
) -> tuple[VoiceRef | None, list[str]]:
    """Select a reference voice for a dialogue turn — *select, never author*.

    Preference: exact (language, persona) → (language, gender) → any voice in the
    language. No voice in the language at all is an honest gap (a note), so the
    caller fails loudly rather than substituting a wrong-language voice.
    """
    pool = list_voices(language=language)
    if not pool:
        return None, [f"keine Stimme für Sprache '{language}' im Katalog "
                      f"(tools/fetch_vctk_voices.py / fetch_fleurs_voices.py)"]
    if persona:
        exact = [v for v in pool if v.persona == persona]
        if exact:
            return exact[0], []
    if gender:
        bygender = [v for v in pool if v.gender == gender.upper()[:1]]
        if bygender:
            return bygender[0], []
    note = []
    if persona or gender:
        note = [f"keine exakte Stimme für persona={persona!r}/gender={gender!r} "
                f"in '{language}' — Fallback auf {pool[0].id}"]
    return pool[0], note


def missing_audio() -> list[str]:
    """Voice ids whose reference clip isn't present locally (need a re-fetch)."""
    return [v.id for v in list_voices() if not audio_path(v).exists()]
