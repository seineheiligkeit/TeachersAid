"""Offline tests for the audio: backend core-side logic — voice resolution, the
spec→turns normalizer, request building, and the licence gate. No GPU / no
subprocess (the actual F5 render is exercised manually, like other asset images)."""

from __future__ import annotations

import pytest

from teachersaid.audio import f5_backend
from teachersaid.grounding import voice_store
from teachersaid.schema.voices import VoiceRef


# --- the curated voice library + resolver ------------------------------------

def test_catalog_validates_and_gate_holds():
    voices = voice_store.list_voices()
    assert voices, "expected the seeded VCTK voice references"
    for v in voices:
        assert isinstance(v, VoiceRef)
        # the rights gate: every library voice is redistributable + attributed
        assert v.source.redistributable and v.source.attribution
        assert v.credit()  # the attribution that must propagate to the product


def test_resolve_voice_by_persona_and_gender():
    m, notes = voice_store.resolve_voice("en", "youth_m")
    assert m is not None and m.gender == "M" and m.persona == "youth_m" and not notes
    f, notes = voice_store.resolve_voice("en", "youth_f")
    assert f is not None and f.gender == "F" and f.persona == "youth_f" and not notes


def test_resolve_voice_honest_gap_for_unsourced_language():
    # French references aren't sourced yet → a note, not a wrong-language substitution
    v, notes = voice_store.resolve_voice("fr", "youth_m")
    assert v is None and notes and "fr" in notes[0]


# --- spec → turns normalization ----------------------------------------------

def test_turns_from_explicit_turns():
    spec = {"lang": "en", "turns": [
        {"persona": "youth_m", "text": "Hi!"},
        {"persona": "youth_f", "text": "Hello!", "pitch": 2.0},
    ]}
    turns = f5_backend._turns_from_spec(spec)
    assert [t["persona"] for t in turns] == ["youth_m", "youth_f"]
    assert turns[1]["pitch"] == 2.0


def test_turns_from_single_script():
    turns = f5_backend._turns_from_spec({"lang": "en", "script": "One voice.", "voice": "youth_f"})
    assert len(turns) == 1 and turns[0]["persona"] == "youth_f" and turns[0]["text"] == "One voice."


def test_turns_empty_spec():
    assert f5_backend._turns_from_spec({}) == []


# --- request building (resolves voices; needs no GPU) ------------------------

def test_build_request_unwired_language_raises():
    # no F5 checkpoint configured for Italian → loud failure, never silent slop
    with pytest.raises(f5_backend.AudioRenderError, match="checkpoint"):
        f5_backend._build_request({"lang": "it", "script": "Ciao."}, out_wav=_tmp())


def test_build_request_english_structure():
    if voice_store.missing_audio():
        pytest.skip("voice reference audio not fetched (tools/fetch_vctk_voices.py)")
    req = f5_backend._build_request(
        {"lang": "en", "turns": [{"persona": "youth_m", "text": "Hi Mia!"},
                                 {"persona": "youth_f", "text": "Hi Tom!"}]},
        out_wav=_tmp())
    assert req["model"] == "F5TTS_v1_Base"
    assert len(req["turns"]) == 2
    for t in req["turns"]:
        assert t["ref_audio"] and t["ref_text"] and t["gen_text"]


def _tmp():
    from pathlib import Path
    import tempfile
    return Path(tempfile.gettempdir()) / "ta_audio_test.wav"
