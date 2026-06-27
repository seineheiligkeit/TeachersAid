"""Central human-feedback log (the HITL loop's backbone).

ONE append-only store keyed by (target_kind, target_id) holds rich feedback — a
rating (1-5) + free comment + quick tags — on ANY reviewable entity (a block, a
worksheet item, an arrangement, an asset). It is **decoupled from approve/reject**:
you can rate or comment on something without deciding its fate, so partial review
still accumulates signal. Centralising it (rather than a field on each of four
models) makes the aggregated `digest()` — the thing the AI consumes to drive
refinement — a single read.
"""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from .base import JsonStore, now

TARGET_KINDS = ("block", "item", "arrangement", "asset", "dataset")
# the offered quick-tag vocabulary (free comments cover anything else)
FEEDBACK_TAGS = (
    "zu leicht", "zu schwer", "Sachfehler", "Sprache/Wortwahl", "unklar",
    "didaktisch stark", "Bild/Abbildung nötig", "super",
)
# tags that, like a low rating or a revise flag, mark something for attention
_ATTENTION_TAGS = {"sachfehler", "unklar", "zu leicht", "zu schwer", "bild/abbildung nötig"}


class FeedbackEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = ""
    target_kind: str                      # block | item | arrangement | asset
    target_id: str
    subject: str = ""                     # denormalised at write time, for the digest
    label: str = ""                       # denormalised human label
    rating: int | None = None             # 1-5 (optional)
    comment: str = ""
    tags: list[str] = Field(default_factory=list)
    revise: bool = False                  # an explicit "please rework this" flag
    at: str = ""

    def is_attention(self) -> bool:
        return (self.revise or (self.rating is not None and self.rating <= 2)
                or any(t.lower() in _ATTENTION_TAGS for t in self.tags))


class FeedbackStore(JsonStore[FeedbackEntry]):
    """Append-only: `add` (not upsert) with a generated id; one central log keyed by
    (target_kind, target_id) over ANY reviewable entity."""

    model = FeedbackEntry
    subdir = "feedback"

    def add(self, entry: FeedbackEntry) -> FeedbackEntry:
        entry.id = entry.id or self._next_seq("f")
        entry.at = entry.at or now()
        return self._write(entry)

    def list(self) -> list[FeedbackEntry]:
        return self._list(sort_key=lambda e: e.at, reverse=True, pattern="f*.json")

    def for_target(self, target_kind: str, target_id: str) -> list[FeedbackEntry]:
        return [e for e in self.list()
                if e.target_kind == target_kind and e.target_id == target_id]

    def digest(self) -> dict:
        """Aggregate the human feedback into actionable signal — the report the AI
        reads to plan refinements (and the Insights view renders)."""
        allfb = self.list()
        rated = [e for e in allfb if e.rating is not None]
        by_kind = Counter(e.target_kind for e in allfb)
        tagfreq = Counter(t for e in allfb for t in e.tags)

        by_subject: dict[str, dict] = {}
        for e in allfb:
            s = by_subject.setdefault(e.subject or "—", {"n": 0, "rating_sum": 0, "rated": 0})
            s["n"] += 1
            if e.rating is not None:
                s["rating_sum"] += e.rating
                s["rated"] += 1
        subjects = sorted(
            ({"subject": s, "n": d["n"],
              "avg_rating": round(d["rating_sum"] / d["rated"], 2) if d["rated"] else None}
             for s, d in by_subject.items()),
            key=lambda x: (x["avg_rating"] is None, x["avg_rating"] if x["avg_rating"] is not None else 9))

        def _entry(e: FeedbackEntry) -> dict:
            return {"target_kind": e.target_kind, "target_id": e.target_id, "subject": e.subject,
                    "label": e.label, "rating": e.rating, "comment": e.comment, "tags": e.tags,
                    "revise": e.revise, "at": e.at}

        attention = [_entry(e) for e in allfb if e.is_attention()]
        praise = [_entry(e) for e in allfb if e.rating is not None and e.rating >= 4]
        return {
            "total": len(allfb),
            "by_kind": dict(by_kind),
            "avg_rating": round(sum(e.rating for e in rated) / len(rated), 2) if rated else None,
            "tags": tagfreq.most_common(),
            "by_subject": subjects,
            "attention": attention,          # the priority worklist (low / flagged / Sachfehler)
            "praise": praise,                # what's working — keep doing it
            "recent": [_entry(e) for e in allfb[:12]],
        }
