"""Build the adversarial review-triage brief over the live Prüfen queue (Track 1 #3c).

The triage twin of `tools/breadth_prompt.py`: where the breadth brief asks a subagent to
GENERATE, this one asks it to JUDGE — a strenger Fachdidaktiker reads every staged entry
and estimates where the SME's reading time is best spent. The brief carries the queue
envelope (kind/id/title/tier/warnings) and, for worksheet items, the Kernfrage + the
first tasks with their answer keys — enough to judge didactics, register, and answer-key
consistency without touching the stores. Triage never decides: no approve, no reject —
the SME remains the gate (invariants §7); the verdicts only re-rank the queue
(`tools/ingest_triage.py` → `FeedbackStore` → `pipeline/triage.py::attention`). Run with
the venv:

    python tools/triage_prompt.py

A subagent reads `runs/triage/brief.md` and writes `runs/triage/verdicts.json`.
"""
from __future__ import annotations

from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.schema.enums import Role
from teachersaid.schema.richtext import plain_text
from teachersaid.store.arrangementstore import ArrangementStore
from teachersaid.store.assetstore import AssetStore
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.datasetstore import DatasetStore
from teachersaid.store.repository import ReviewStore
from teachersaid.store.reviewqueue import queue
from teachersaid.store.sachverhaltstore import SachverhaltStore
from teachersaid.store.textstore import TextStore

MAX_TASKS = 6  # tasks shown per worksheet item
CLIP = 300     # ~chars per prompt/answer_key (the judge skims; the SME reads in full)

_TEMPLATE = """# Review-Triage: adversarialer Durchgang über die Prüf-Warteschlange

Du bist ein **strenger Fachdidaktiker / eine strenge Fachdidaktikerin** (AHS, Österreich).
Unten stehen **{n} Einträge**, die zur fachlichen Prüfung anstehen. Beurteile jeden
Eintrag kritisch — du suchst Schwächen, nicht Bestätigung.

**Du gibst NICHTS frei und lehnst NICHTS ab.** Das ist reine Triage: Deine Einschätzung
lenkt nur, was zuerst gelesen wird — die fachliche Endabnahme (SME) bleibt das Gate
(invariants §7).

## Prüfkriterien (je Eintrag)
1. **Didaktik** — steigt die kognitive Leiter (remember → … → create), statt alles auf
   einer Stufe zu bleiben? Sind die Aufgaben klar, eindeutig und schülergerecht gestellt?
2. **Sprachliches Register** — AHS-angemessenes Deutsch (bzw. Zielsprache): altersgerecht,
   präzise Fachsprache, keine Stilbrüche?
3. **Lösungs-Konsistenz** — beantwortet der `answer_key` TATSÄCHLICH die gestellte Frage
   (nicht eine benachbarte)? Passt die Musterlösung zur Aufgabenform?

## Ausgabe
Schreibe **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune) nach
`runs/triage/verdicts.json` — eine Liste, ein Objekt pro beurteiltem Eintrag:

```json
[
  {{"kind": "item", "id": "c0001", "rating": 2, "attention": "hoch",
    "reasons": ["Kognitive Leiter flach", "Lösung zu Aufgabe 3 beantwortet die Frage nicht"],
    "watch": "answer_key von Aufgabe 3 gegen den Prompt lesen"}}
]
```

- `rating` 1–5 — erwartete Qualität (1 = gravierende Mängel erwartet, 5 = sehr wahrscheinlich solide)
- `attention` ∈ `"hoch"` | `"mittel"` | `"niedrig"` — wie dringend das gelesen werden muss
- `reasons` — höchstens 3 kurze deutsche Begründungen
- `watch` — eine Zeile: worauf beim Lesen zuerst zu achten ist

## Einträge ({n})

{entries}
"""


def _clip(rt, n: int = CLIP) -> str:
    """RichText → one plain line, truncated to ~n chars."""
    text = " ".join(plain_text(rt).split()) if rt else ""
    return text if len(text) <= n else text[: n - 1] + "…"


def _item_detail(item) -> list[str]:
    """Kernfrage + the first tasks (prompt + answer_key) of a staged worksheet item —
    the material the didactics/register/answer-key judgment actually needs."""
    content = getattr(item, "content", None)
    if content is None:
        return ["- (kein Inhalt vorhanden — Generierung prüfen)"]
    lines: list[str] = []
    kernfrage = _clip(content.meta.kernfrage)
    if kernfrage:
        lines.append(f"- Kernfrage: {kernfrage}")
    tasks = [b for b in content.iter_blocks() if b.role == Role.TASK]
    if tasks:
        lines.append("- Aufgaben:")
    for i, t in enumerate(tasks[:MAX_TASKS], start=1):
        lines.append(f"  {i}. [{t.kind} · {t.cognitive_level}] {_clip(t.prompt)}")
        lines.append(f"     Lösung: {_clip(t.answer_key) or '—'}")
    if len(tasks) > MAX_TASKS:
        lines.append(f"  … + {len(tasks) - MAX_TASKS} weitere Aufgaben")
    return lines


def _entry_lines(e: dict, items) -> str:
    """One queue entry as a markdown block (envelope + item detail where available)."""
    klasse = f", {e['klasse']}. Kl." if e.get("klasse") else ""
    lines = [f"### {e['kind']} `{e['id']}` — „{e.get('title') or e['id']}“ "
             f"({e.get('subject') or '—'}{klasse} · Stufe {e['tier']})"]
    shown = e.get("warnings") or []
    for w in shown:
        lines.append(f"- ⚠ {w}")
    if (e.get("n_warnings") or 0) > len(shown):
        lines.append(f"- … + {e['n_warnings'] - len(shown)} weitere Hinweise")
    if e["kind"] == "item":
        rec = items.get(e["id"])
        if rec is not None:
            lines += _item_detail(rec)
    return "\n".join(lines)


def render_brief(q: dict, items) -> str:
    """The brief text for a queue envelope (pure; `build` wires the real stores)."""
    entries = "\n\n".join(_entry_lines(e, items) for e in q["entries"]) or "(leer)"
    return _TEMPLATE.format(n=q["total"], entries=entries)


def build() -> Path:
    items = ReviewStore()
    q = queue(items=items, blocks=BlockStore(), assets=AssetStore(),
              datasets=DatasetStore(), texts=TextStore(),
              sachverhalte=SachverhaltStore(), arrangements=ArrangementStore())
    out = RUNS_DIR / "triage" / "brief.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_brief(q, items), encoding="utf-8")
    lanes = ", ".join(f"{t}={n}" for t, n in q["lanes"].items())
    print(f"{q['total']} Einträge (Lanes: {lanes}) -> {out}")
    return out


if __name__ == "__main__":
    build()
