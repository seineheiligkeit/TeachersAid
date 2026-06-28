"""Optional GPU TTS backend for the `audio:` seam (F5-TTS multi-voice).

Importing this package is cheap and core-safe (no torch); the heavy ML stack lives
only in `f5_render.py`, which is executed in the 3.12 venv, never imported here.
Wire it once with `register()`; until then `build_audio` raises `AudioNotConfigured`.
"""

from .f5_backend import AudioRenderError, available, register, render

__all__ = ["register", "render", "available", "AudioRenderError"]
