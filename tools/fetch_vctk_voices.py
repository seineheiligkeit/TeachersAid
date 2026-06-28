"""Deterministic fetch of youthful voice references from VCTK → grounding/voices/.

VCTK (CSTR, University of Edinburgh) is CC BY 4.0 (redistribution permitted with
attribution) and `sanchit-gandhi/vctk` mirrors it as parquet with per-speaker
`age`/`gender`/`accent`, so it's the cleanest age-tagged English reference source.
No LLM in the path — a curated (speaker_id, reference-sentence) pair is streamed,
decoded, written as a clip, and stamped with its citation + the rights gate.

The committed artifact is the provenance (`<id>.json` + `_catalog.json`); the audio
binary is re-fetchable and git-ignored (cf. the RIS Lehrplan source).

    python tools/fetch_vctk_voices.py            # fetch the curated starter set
    python tools/fetch_vctk_voices.py --limit 8000   # widen the stream scan if a speaker is missed
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import io
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "teachersaid" / "grounding" / "voices"
AUDIO_DIR = OUT_DIR / "audio"
HF_DATASET = "sanchit-gandhi/vctk"

# The VCTK elicitation sentence every speaker reads (text_id 003) — a consistent,
# ~7-8s reference across speakers, so the only variable is timbre.
REF_SENTENCE = "Six spoons of fresh snow peas"

# Curated young-adult starter set (balanced gender), all early-streaming speakers.
# (speaker_id, persona) — language/age/accent are read from the corpus, not asserted.
CURATED = [
    ("p225", "youth_f"),
    ("p228", "youth_f"),
    ("p230", "youth_f"),
    ("p226", "youth_m"),
    ("p232", "youth_m"),
    ("p237", "youth_m"),
]

# VCTK licence is CC BY 4.0 — redistributable WITH attribution (the gate).
VCTK_SOURCE = {
    "publisher": "CSTR, University of Edinburgh",
    "title": "CSTR VCTK Corpus (version 0.92)",
    "url": "https://datashare.ed.ac.uk/handle/10283/3443",
    "corpus_code": HF_DATASET,
    "licence": "CC BY 4.0",
    "licence_url": "https://creativecommons.org/licenses/by/4.0/",
    "redistributable": True,
    "attribution": ("Stimme: CSTR VCTK Corpus, University of Edinburgh "
                    "(Veaux, Yamagishi, MacDonald), CC BY 4.0 — Sprecher/in {spk}"),
}


def _rights_gate(source: dict) -> None:
    """Only redistributable, attributed licences may enter the library."""
    if not source.get("redistributable"):
        raise SystemExit(f"licence gate: {source.get('licence')!r} is not redistributable")
    if not source.get("attribution"):
        raise SystemExit("licence gate: an attribution string is required")


def fetch(retrieved: str, limit: int) -> list[dict]:
    from datasets import load_dataset, Audio
    import soundfile as sf

    _rights_gate(VCTK_SOURCE)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    wanted = dict(CURATED)
    found: dict[str, dict] = {}

    ds = load_dataset(HF_DATASET, split="train", streaming=True)
    ds = ds.cast_column("audio", Audio(decode=False))
    for i, ex in enumerate(ds):
        if i > limit or len(found) == len(wanted):
            break
        spk = ex.get("speaker_id")
        if spk not in wanted or spk in found:
            continue
        text = (ex.get("text") or "").strip()
        if not text.startswith(REF_SENTENCE):
            continue
        data, sr = sf.read(io.BytesIO(ex["audio"]["bytes"]))
        if getattr(data, "ndim", 1) > 1:
            data = data[:, 0]
        vid = f"vctk_{spk}"
        rel = f"audio/{vid}.wav"
        sf.write(str(AUDIO_DIR / f"{vid}.wav"), data, sr)
        sha = hashlib.sha256((AUDIO_DIR / f"{vid}.wav").read_bytes()).hexdigest()
        src = dict(VCTK_SOURCE, attribution=VCTK_SOURCE["attribution"].format(spk=spk),
                   retrieved=retrieved)
        try:
            age = int(ex.get("age"))
        except (TypeError, ValueError):
            age = None
        found[spk] = {
            "id": vid, "language": "en", "gender": (ex.get("gender") or "").upper()[:1],
            "age": age, "accent": ex.get("accent"), "speaker_id": spk,
            "persona": wanted[spk], "ref_text": text, "audio_file": rel,
            "duration_s": round(len(data) / sr, 2), "audio_sha256": sha,
            "source": src, "tags": ["youthful", wanted[spk], "en"],
        }
        print(f"  [{len(found)}/{len(wanted)}] {vid} age={age} "
              f"{found[spk]['gender']} {found[spk]['duration_s']}s {ex.get('accent')!r}")
    missing = [s for s in wanted if s not in found]
    if missing:
        print(f"  ! not reached within {limit} rows (raise --limit): {missing}")
    return list(found.values())


def write(voices: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cat_path = OUT_DIR / "_catalog.json"
    catalog = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {"voices": []}
    by_id = {v["id"]: v for v in catalog.get("voices", [])}
    for v in voices:
        (OUT_DIR / f"{v['id']}.json").write_text(
            json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")
        by_id[v["id"]] = {"id": v["id"], "language": v["language"], "gender": v["gender"],
                          "age": v["age"], "persona": v["persona"], "file": f"{v['id']}.json",
                          "audio_file": v["audio_file"], "licence": v["source"]["licence"]}
    catalog["voices"] = sorted(by_id.values(), key=lambda v: v["id"])
    cat_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[write] {len(voices)} voice refs -> {OUT_DIR}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--retrieved", default=_dt.date.today().isoformat())
    ap.add_argument("--limit", type=int, default=8000, help="max stream rows to scan")
    args = ap.parse_args()
    write(fetch(args.retrieved, args.limit))


if __name__ == "__main__":
    main()
