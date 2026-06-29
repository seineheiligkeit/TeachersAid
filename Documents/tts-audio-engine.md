# TTS / Audio engine — build notes & handover

**Status: the real `audio:` backend is WIRED and proven end-to-end (28 Jun 2026).**
A `WorksheetContent` audio asset now renders to a multi-voice German/English mp3 on the
local GPU, through the existing seam, with voices selected from a curated, rights-gated
reference library. This doc is the clean-state record for the next session: what was
decided, what was built, how the environment is set up (there are real gotchas), and
what's left.

Companion context: `feature-roadmap.md` (Languages/Audio), CLAUDE.md (the audio seam),
`schema/voices.py` (the voice model). The throwaway evaluation lives in `runs/tts_eval/`
(git-ignored).

---

## 1. The decisions (settled)

- **Engine: F5-TTS**, run **locally on the GPU** (RTX 4070, 12 GB — *not* the 3060 the
  hardware was misremembered as). Voice-cloning gives the control levers (which voice,
  which age) that a fixed-voice engine (Piper) lacks. **Piper-Thorsten** stays as a
  zero-dependency, CC0 fallback for single-narrator German.
- **Multilingual, ENGLISH-FIRST.** German treats Hören/Sprechen as *integrated* (not a
  tested skill), so DEU Hörverstehen is low-priority; the real demand is **FS1 (English)**,
  then **FS2 (French/Italian/Spanish)** + Latein. The engine loads a **per-language
  checkpoint**; each checkpoint is its own quality + licence decision.
- **Multi-voice dialogues are the v1 capability** (not single narration).
- **Voices are SELECTED, never authored** — the same discipline as the data/text layers.
  A voice clones a real, openly-licensed **reference clip** from a curated corpus.
- **Ethics line:** clone consenting, openly-licensed **young adults (~22–23)**, *never
  minors* — even where a CC0 clip of a child exists. Youthful-young-adult is the rights-
  clean ceiling and matches real exam-audio convention. Pitch-shaping a reference up a
  little is the only lever past that (a knob, default off).
- **Licence reality:** the textbook CC0 source (Common Voice, age-tagged, multilingual) is
  **no longer scriptable** — Mozilla moved the data off HuggingFace and `datasets 5.0`
  dropped the script loaders the mirrors used. The working streamable sources are **CC-BY**
  (VCTK for English with ages; FLEURS for the FS languages, no age). CC-BY means the
  attribution must propagate into the product — a string, but acceptable. A CC0 path needs
  a manual Common Voice download from the user's Mozilla account (deferred).

---

## 2. Architecture — the two-process split (and WHY)

```
3.14 core (the package)                    3.12 GPU process (separate interpreter)
─────────────────────────                  ──────────────────────────────────────
pipeline/assets.build_audio(asset)
  └─ audio/f5_backend.render(asset, path)   ── subprocess ──►  audio/f5_render.py
       • spec → turns (normalize)                                • F5TTS(model=…, device=cuda)
       • resolve_voice(lang, persona)  ◄── grounding/voice_store • clone each turn's ref
       • build request JSON                                      • stitch turns + gaps
       • ffmpeg WAV → mp3  ◄──────────────── writes WAV ─────────• write one WAV
```

**Why two processes:** CUDA PyTorch has **no Python-3.14 wheel** (only `torch+cpu`). The
3.14 core therefore *cannot host* the GPU stack; it drives a **separate 3.12 interpreter**
as a subprocess. `f5_render.py` is the only file that imports torch/f5_tts/librosa and is
**never imported** by the core — it is only *executed* by the 3.12 interpreter. This keeps
the offline test suite and the core import graph clean (no heavy deps leak in).

The seam is the pre-existing one: `assets.register_audio_backend(fn)` /
`assets.build_audio(asset)`. Until `register()` is called, `build_audio` raises
`AudioNotConfigured` and the **printable teacher-only transcript is the fallback** — no
silent slop.

### The asset spec
```python
# multi-voice dialogue (the v1 capability)
spec = {"lang": "en", "turns": [
          {"persona": "youth_m", "text": "Hi Mia! …"},
          {"persona": "youth_f", "text": "Hi Tom! …", "pitch": 0.0},
       ]}
# single narrator (fallback)
spec = {"lang": "en", "script": "…", "voice": "youth_f"}
```
`(lang, persona)` resolves to a `VoiceRef` in the library. Per-language checkpoints live in
`f5_backend._CHECKPOINTS` (`en` = `F5TTS_v1_Base`, auto-downloaded; `de/fr/it/es` via env
`TEACHERSAID_TTS_<L>_CKPT`). An unwired language fails loudly, never silently.

---

## 3. Environment setup — READ THIS before running (real gotchas)

The build hit two environment traps; both are solved, but a new session must understand them.

1. **No CUDA torch on Python 3.14** → the GPU engine runs on a **separate Python 3.12**.
2. **Claude Code runs inside an MSIX app-container** that virtualizes `%APPDATA%\Roaming`
   to `…\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\`. A venv created by
   **uv inside that container** has its base interpreter *trapped in the container*: the
   venv's trampoline `python.exe` mis-resolves under `subprocess` (it only works when
   launched from PowerShell `&`) and **would not exist in the user's own shell**. The
   python.org **GUI installer also fails in-container** (exit 3).

**The working setup (durable, normal locations, no container dependency):**
- **GPU packages** (torch 2.6.0+cu124, f5-tts, etc., ~3 GB) live in
  `.venv-tts-gpu/Lib/site-packages` — a *normal* project path (only the uv *base
  interpreter* was trapped; the packages are fine).
- **Interpreter** = a python.org **embeddable 3.12.8** unzipped to `C:\Users\Sebas\Python312`
  (no installer needed). Its `python312._pth` is edited to append the GPU `site-packages`
  path, so it imports torch/f5 with **no re-download**.
- **ffmpeg** installed via winget (`Gyan.FFmpeg`); used for WAV→mp3.
- **Config knobs** (`teachersaid/config.py`, all env-overridable):
  `TTS_PYTHON` (default `~/Python312/python.exe`), `TTS_PYTHON_SITE` (optional extra
  PYTHONPATH), `TTS_FFMPEG`.

If `TTS_PYTHON` is absent, `audio.register()` returns `False` and the engine stays unwired
(transcript fallback). To rebuild the interpreter from scratch: re-unzip the embeddable to a
normal path and point its `._pth` at `.venv-tts-gpu/Lib/site-packages` (or set the env vars).

> Note for a fully Claude-independent setup: the embeddable + project venv are both in normal
> locations, so this already works from the user's own shell. The only remaining container
> artifact is the original uv base interpreter, which we no longer use.

### Voice reference audio
The catalog (`grounding/voices/_catalog.json` + per-voice JSON) is **committed**; the audio
binaries are **git-ignored and re-fetchable**:
```
python tools/fetch_vctk_voices.py        # repopulates grounding/voices/audio/ from VCTK
```

---

## 4. The voice reference library (`grounding/voices/`)

Mirrors the grounded-facts data layer exactly (schema → fetch tool → committed catalog +
re-fetchable binaries → rights gate).

- **Schema** `schema/voices.py`: `VoiceSourceRef` (licence/attribution stamp) + `VoiceRef`
  (language/gender/age/accent/persona/ref_text/audio_file/source). Ethics line in the docstring.
- **Fetch tool** `tools/fetch_vctk_voices.py`: deterministic stream of `sanchit-gandhi/vctk`
  (parquet VCTK), pins the elicitation sentence so only timbre varies, applies the
  **`_rights_gate`** (redistributable + attribution required), writes audio + provenance.
- **Starter set (6, all CC-BY, validated):** 3 female (`p225`, `p228`, `p230`) + 3 male
  (`p226`, `p232` English, `p237` Scottish), young adults 22–23, personas `youth_f`/`youth_m`.
- **Resolver** `grounding/voice_store.py`: `resolve_voice(language, persona)` → `VoiceRef`,
  honest gap (note, not crash) for an unsourced language; `audio_path()`, `missing_audio()`.

---

## 5. File map (what to read first)

| File | What |
|---|---|
| `teachersaid/schema/voices.py` | `VoiceRef` / `VoiceSourceRef` |
| `teachersaid/grounding/voice_store.py` | the casting resolver (data_store twin) |
| `teachersaid/grounding/voices/` | committed catalog + per-voice provenance (audio git-ignored) |
| `teachersaid/audio/f5_backend.py` | **core-side** backend (no torch): spec→turns, resolve, subprocess, ffmpeg, `register()` |
| `teachersaid/audio/f5_render.py` | **GPU-side** worker (torch/f5) — executed in the 3.12 interp, never imported |
| `teachersaid/config.py` | `TTS_PYTHON` / `TTS_PYTHON_SITE` / `TTS_FFMPEG` / `GROUNDING_VOICES` |
| `tools/fetch_vctk_voices.py` | deterministic VCTK fetch + rights gate |
| `tests/test_audio.py` | 8 offline tests (resolution, normalization, gate, request) |
| `runs/tts_eval/` | throwaway evaluation (Piper/F5 samples, scripts) — git-ignored |

---

## 6. How to run / verify

```python
from teachersaid.pipeline import assets
from teachersaid.schema.assets import Asset
from teachersaid.schema.enums import Medium
import teachersaid.audio as audio

audio.register()                              # wires the backend (False if TTS_PYTHON absent)
asset = Asset(id="demo", role="tts", medium=Medium.AUDIO, generator="audio:tts",
              spec={"lang": "en", "turns": [
                  {"persona": "youth_m", "text": "Hi Mia! How was school?"},
                  {"persona": "youth_f", "text": "Hi Tom! It was good, thanks."}]})
print(assets.build_audio(asset))              # → runs/audio/demo.mp3
```
Tests: `python -m pytest tests/test_audio.py -q` (offline). Full suite: **265 passed**
(was 204 at the audio milestone; +Matura archive/figures since). Performance: F5 on the 4070
≈ **4× real-time** (~1.2 s per turn).

---

## 7. Next steps (in priority order)

1. **HITL "Stimmen" review tab** — a `VoiceStore` (subclass `store/base.py::JsonStore`) +
   a dashboard tab mirroring *Datensätze*/*Abbildungen* (play the reference + a cloned sample,
   approve/reject, show licence/attribution). Call `audio.register()` at dashboard startup so
   generated worksheets actually render audio. **This makes it real in the product.**
2. **`text_tasks` → turns** — today an audio `AnnotatedText` emits a single `script`; to get
   *dialogue* audio it needs a **speaker/turn model** on `AnnotatedText` (a list of
   `(speaker, line)` with a persona mapping) so `build_worksheet` emits a `turns` spec.
3. **Multilingual references + checkpoints** — FLEURS (`google/fleurs`, CC-BY, EN/DE/FR/IT/ES;
   no age, pick clear young-sounding voices by ear) into the library via a `fetch_fleurs_voices.py`;
   wire `de/fr/it/es` checkpoints (German `hvoss-techfak/F5-TTS-German`, CC0-trained, already
   evaluated; others are community finetunes to vet). The `_CHECKPOINTS` map + env hooks exist.
4. **Pitch-youthen knob** — already plumbed (`turn.pitch`); expose it where casting is chosen,
   if a voice needs to read a touch younger.
5. **Sourced-audio path** (deferred) — real recordings + rights, the audio analogue of sourced images.

### Known loose ends / cleanups
- `pipeline/assets.build_audio` hard-codes the `.mp3` extension — fine (ffmpeg encodes mp3),
  but if a non-mp3 format is ever wanted, relax it.
- The German checkpoint used in evaluation sits in `runs/tts_eval/f5model/` (git-ignored scratch);
  when wiring `de` for real, resolve it from HF (`hvoss-techfak/F5-TTS-German`) rather than scratch.
- English base checkpoint (`F5TTS_v1_Base`) is trained on **Emilia (non-commercial)** — for a
  commercial-clean product, find a LibriTTS/Common-Voice-trained English checkpoint.
