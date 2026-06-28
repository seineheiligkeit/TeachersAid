"""GPU-side F5-TTS render worker — runs in the 3.12 venv (.venv-tts-gpu), invoked
as a subprocess by f5_backend (the 3.14 core can't host CUDA torch).

Reads a request JSON (argv[1]), renders each dialogue turn by cloning its reference
voice, stitches them with gaps, and writes a single WAV to request["out_wav"].
This file is NEVER imported by the core — only executed by the GPU interpreter — so
its torch/f5_tts/librosa imports stay isolated.

Request shape:
{
  "out_wav": "<path>", "model": "F5TTS_v1_Base",
  "ckpt": "<path|null>", "vocab": "<path|null>",
  "nfe_step": 32, "gap_ms": 450, "seed": 1234,
  "turns": [{"ref_audio": "<wav>", "ref_text": "...", "gen_text": "...", "pitch": 0.0}, ...]
}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import librosa
from f5_tts.api import F5TTS

_quiet = lambda *a, **k: None  # noqa: E731  (silence F5's per-call prints)


def _ref(path: str, pitch: float, tmp: Path) -> str:
    if not pitch:
        return path
    y, sr = librosa.load(path, sr=None)
    out = tmp / (Path(path).stem + f"_p{pitch:+.1f}.wav")
    sf.write(str(out), librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch), sr)
    return str(out)


def main() -> None:
    req = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_wav = Path(req["out_wav"])
    tmp = out_wav.parent
    tmp.mkdir(parents=True, exist_ok=True)

    kwargs = {"model": req.get("model", "F5TTS_v1_Base"), "device": "cuda"}
    if req.get("ckpt"):
        kwargs["ckpt_file"] = req["ckpt"]
    if req.get("vocab"):
        kwargs["vocab_file"] = req["vocab"]
    f5 = F5TTS(**kwargs)

    sr_out, segments, gap = None, [], None
    for i, t in enumerate(req["turns"]):
        ref = _ref(t["ref_audio"], float(t.get("pitch", 0.0)), tmp)
        wav, sr, _ = f5.infer(
            ref_file=ref, ref_text=t["ref_text"], gen_text=t["gen_text"],
            nfe_step=int(req.get("nfe_step", 32)), speed=float(req.get("speed", 1.0)),
            seed=int(req.get("seed", 1234)), show_info=_quiet)
        wav = np.asarray(wav, dtype=np.float32)
        if sr_out is None:
            sr_out = sr
            gap = np.zeros(int(sr * int(req.get("gap_ms", 450)) / 1000), dtype=np.float32)
        segments += [wav, gap]
        print(f"turn {i + 1}/{len(req['turns'])} {len(wav) / sr:.1f}s", flush=True)

    combined = np.concatenate(segments) if segments else np.zeros(1, dtype=np.float32)
    sf.write(str(out_wav), combined, sr_out or 24000)
    print(f"OK {len(combined) / (sr_out or 24000):.1f}s -> {out_wav}", flush=True)


if __name__ == "__main__":
    main()
