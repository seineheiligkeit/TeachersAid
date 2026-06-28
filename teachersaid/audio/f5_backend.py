"""The `audio:` backend — F5-TTS multi-voice dialogue rendering wired to the seam.

Lives in the 3.14 core and imports NO heavy ML stack. It:
  1. parses an `audio:tts` asset's spec into dialogue **turns**;
  2. *resolves* each turn's voice from the curated library (`grounding/voice_store`)
     — select-never-author: the timbre is a vetted, rights-clean reference clip;
  3. drives the GPU worker (`f5_render.py`) in the 3.12 venv as a subprocess;
  4. encodes the stitched WAV → mp3 with ffmpeg.

Register it once via `register()` (or `assets.register_audio_backend(render)`); until
then `build_audio` raises `AudioNotConfigured` and the printable transcript stands.

Asset spec (in `Asset.spec`):
  multi-voice : {"lang":"en", "turns":[{"persona":"youth_m","text":"…","pitch":0}, …]}
  single-voice: {"lang":"en", "script":"…", "voice":"youth_f"}   # → one turn
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
from pathlib import Path

from ..config import RUNS_DIR, TTS_FFMPEG, TTS_PYTHON, TTS_PYTHON_SITE
from ..grounding import voice_store

# Per-language F5 checkpoints. English uses the HF-auto base; others are wired as
# their vetted checkpoints are added (env override e.g. TEACHERSAID_TTS_DE_CKPT).
_CHECKPOINTS: dict[str, dict] = {
    "en": {"model": "F5TTS_v1_Base"},
}
for _lang in ("de", "fr", "it", "es"):
    _ckpt = os.environ.get(f"TEACHERSAID_TTS_{_lang.upper()}_CKPT")
    if _ckpt:
        _CHECKPOINTS[_lang] = {
            "model": os.environ.get(f"TEACHERSAID_TTS_{_lang.upper()}_MODEL", "F5TTS_Base"),
            "ckpt": _ckpt,
            "vocab": os.environ.get(f"TEACHERSAID_TTS_{_lang.upper()}_VOCAB"),
        }

_RENDER_WORKER = Path(__file__).resolve().parent / "f5_render.py"


class AudioRenderError(RuntimeError):
    pass


def _resolve_interpreter() -> tuple[str, dict]:
    """Return (python_exe, extra_env) for the GPU worker.

    Preference order:
      1. `TTS_PYTHON` + `TTS_PYTHON_SITE` on PYTHONPATH (a plain interpreter pointed at a
         separate package dir) — or, for the default embeddable, no extra env (its
         `python312._pth` already carries the package path);
      2. a stdlib venv: launch its base interpreter (pyvenv.cfg `home`) with PYTHONPATH set
         to the venv site-packages — a uv-created venv's trampoline `python.exe` mis-resolves
         under subprocess, so we never launch it directly.
    """
    py = Path(TTS_PYTHON)
    if TTS_PYTHON_SITE:
        return str(py), {"PYTHONPATH": TTS_PYTHON_SITE}
    cfg = py.parent.parent / "pyvenv.cfg"
    if cfg.exists():
        home = next((ln.split("=", 1)[1].strip()
                     for ln in cfg.read_text(encoding="utf-8").splitlines()
                     if ln.strip().startswith("home")), None)
        base = Path(home) / "python.exe" if home else None
        site = py.parent.parent / "Lib" / "site-packages"
        if base and base.exists() and site.exists():
            return str(base), {"PYTHONPATH": str(site)}
    return str(py), {}


def _find_ffmpeg() -> str:
    """ffmpeg on PATH, else the winget (Gyan.FFmpeg) install location (PATH may be
    stale in a process started before install)."""
    if shutil.which(TTS_FFMPEG):
        return TTS_FFMPEG
    local = os.environ.get("LOCALAPPDATA", "")
    for pat in (
        os.path.join(local, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "**", "ffmpeg.exe"),
    ):
        hits = glob.glob(pat, recursive=True)
        if hits:
            return hits[0]
    raise AudioRenderError("ffmpeg not found (install Gyan.FFmpeg or set TEACHERSAID_FFMPEG)")


def _turns_from_spec(spec: dict) -> list[dict]:
    """Normalize a spec into a list of {persona, text, pitch}. A single `script`
    collapses to one turn; an explicit `turns` list is used as-is."""
    if spec.get("turns"):
        out = []
        for t in spec["turns"]:
            text = (t.get("text") or t.get("gen_text") or "").strip()
            if not text:
                continue
            out.append({"persona": t.get("persona") or t.get("voice"),
                        "text": text, "pitch": float(t.get("pitch", spec.get("pitch", 0.0)))})
        return out
    script = (spec.get("script") or "").strip()
    if not script:
        return []
    return [{"persona": spec.get("voice"), "text": script, "pitch": float(spec.get("pitch", 0.0))}]


def _build_request(spec: dict, out_wav: Path) -> dict:
    lang = (spec.get("lang") or "en").lower()[:2]
    ckpt = _CHECKPOINTS.get(lang)
    if ckpt is None:
        raise AudioRenderError(
            f"no F5 checkpoint wired for language '{lang}' — add one to _CHECKPOINTS "
            f"or set TEACHERSAID_TTS_{lang.upper()}_CKPT")
    turns_in = _turns_from_spec(spec)
    if not turns_in:
        raise AudioRenderError("asset spec carries no script/turns to speak")

    turns_out: list[dict] = []
    for t in turns_in:
        voice, notes = voice_store.resolve_voice(lang, t["persona"])
        if voice is None:
            raise AudioRenderError("; ".join(notes) or f"no voice for language '{lang}'")
        ref = voice_store.audio_path(voice)
        if not ref.exists():
            raise AudioRenderError(
                f"reference clip missing for {voice.id} ({ref}) — run tools/fetch_vctk_voices.py")
        turns_out.append({"ref_audio": str(ref), "ref_text": voice.ref_text,
                          "gen_text": t["text"], "pitch": t["pitch"]})

    return {"out_wav": str(out_wav), **ckpt,
            "nfe_step": int(spec.get("nfe_step", 32)), "gap_ms": int(spec.get("gap_ms", 450)),
            "seed": int(spec.get("seed", 1234)), "turns": turns_out}


def render(asset, path: Path) -> None:
    """The registered `audio:` backend: spec → GPU render → mp3 at `path`."""
    spec = asset.spec or {}
    work = RUNS_DIR / "audio" / "_work"
    work.mkdir(parents=True, exist_ok=True)
    out_wav = work / f"{asset.id}.wav"
    req_path = work / f"{asset.id}.request.json"
    req = _build_request(spec, out_wav)
    req_path.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")

    if not Path(TTS_PYTHON).exists():
        raise AudioRenderError(f"TTS interpreter not found: {TTS_PYTHON} (the .venv-tts-gpu venv)")
    py, extra_env = _resolve_interpreter()
    env = {**os.environ, **extra_env}
    proc = subprocess.run([py, str(_RENDER_WORKER), str(req_path)],
                          capture_output=True, text=True, env=env)
    if proc.returncode != 0 or not out_wav.exists():
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-8:]
        raise AudioRenderError("F5 render failed:\n" + "\n".join(tail))

    ffmpeg = _find_ffmpeg()
    enc = subprocess.run([ffmpeg, "-y", "-i", str(out_wav), "-codec:a", "libmp3lame",
                          "-q:a", "2", str(path)], capture_output=True, text=True)
    if enc.returncode != 0 or not Path(path).exists():
        raise AudioRenderError("ffmpeg mp3 encode failed:\n" + (enc.stderr or "")[-500:])


def available() -> bool:
    """True if the GPU venv interpreter is present (so registration is meaningful)."""
    return Path(TTS_PYTHON).exists()


def register() -> bool:
    """Wire `render` as the `audio:` backend. Returns False (and stays unwired, so
    build_audio → AudioNotConfigured) if the GPU venv isn't present."""
    from ..pipeline import assets
    if not available():
        return False
    assets.register_audio_backend(render)
    return True
