"""P1 Tiefenregler for deterministic parametric worksheets.

Every transformation is a pure projection of one seeded master.  Unsupported controls
raise instead of silently doing nothing.  The accompanying lint measures both endpoints
of each enabled fader and proves that competence coverage is unchanged.
"""

from __future__ import annotations

import math

from ..schema.assets import Asset
from ..schema.blocks import TaskBlock
from ..schema.enums import COGNITIVE_RANK
from ..schema.mixer import (
    Abstraktion,
    ENDPOINT_LABELS,
    FADER_LABELS,
    FaderCapability,
    FaderMovement,
    FaderOption,
    Geruest,
    MixerLintReport,
    MixerMetricSnapshot,
    Offenheit,
    ParametricMixerProfile,
    TemplateCapabilities,
    Textlast,
    Tiefe,
    Umfang,
)
from ..schema.parametric import ParametricTask
from ..schema.response import LinesResponse
from ..schema.richtext import InlineRun
from .parametrize import make_variants_with_assets


def adjusted_variant_count(base_n: int, umfang: Umfang) -> int:
    """Map the Umfang endpoint around an explicit neutral count (bounded like the API)."""
    if not 1 <= base_n <= 30:
        raise ValueError("base variant count must be between 1 and 30")
    if umfang == Umfang.KOMPAKT:
        return max(1, math.ceil(base_n * 2 / 3))
    if umfang == Umfang.ERWEITERT:
        return min(30, math.ceil(base_n * 4 / 3))
    return base_n


def projected_title(title: str, profile: ParametricMixerProfile | None) -> str:
    """Remove an MC-only genre suffix when the same master is projected openly."""
    if profile and profile.offenheit == Offenheit.OFFEN:
        return title.replace(" (Multiple Choice)", "")
    return title


def _append_prompt(block: TaskBlock, suffix: str) -> None:
    if isinstance(block.prompt, str):
        block.prompt = f"{block.prompt} {suffix}"
    else:
        block.prompt = [*block.prompt, InlineRun(text=" " + suffix)]


def _strategy_depth(blocks: list[TaskBlock]) -> list[TaskBlock]:
    out = [b.model_copy(deep=True) for b in blocks]
    unsupported = [b.id for b in out if not b.solution_paths]
    if unsupported:
        raise ValueError(
            "Tiefenregler Tiefe is unsupported: the recipe emits no alternative "
            f"computed solution paths ({unsupported[0]})"
        )
    for block in out:
        names = ", ".join(path.strategy for path in block.solution_paths)
        _append_prompt(
            block,
            "Löse die Aufgabe auf mindestens zwei unterschiedlichen Wegen "
            f"(darunter {names}). Vergleiche die Wege und begründe, welcher für "
            "diesen Zahlensatz günstig ist.",
        )
        block.cognitive_level = "evaluate"
        block.est_minutes += max(3, 2 * len(block.solution_paths))
        if not getattr(block.response, "mode", None) == "lines" or block.response.n < 6:
            block.response = LinesResponse(n=6)
    return out


def _formal_projection(
    blocks: list[TaskBlock], assets: list[Asset],
) -> tuple[list[TaskBlock], list[Asset]]:
    out = [b.model_copy(deep=True) for b in blocks]
    student_refs = {ref for b in out for ref in b.asset_refs}
    if not student_refs:
        raise ValueError(
            "Tiefenregler Abstraktion is unsupported: the recipe emits no "
            "computed student figure"
        )
    for block in out:
        block.asset_refs = []
    # Keep solution-only figures: formalising the student projection must not discard
    # computed teacher evidence that travels through a separate reference channel.
    return out, [a.model_copy(deep=True) for a in assets if a.id not in student_refs]


def _coverage_ids(blocks: list[TaskBlock]) -> list[str]:
    return sorted({s.competence_id for b in blocks for s in b.serves})


def _afb_band(level: str) -> str:
    rank = COGNITIVE_RANK.get(level, 1)
    return "1" if rank <= 1 else "2" if rank <= 3 else "3"


def metric_snapshot(blocks: list[TaskBlock]) -> MixerMetricSnapshot:
    """Measure only stable, already-computed task properties (no rendering heuristics)."""
    afb: dict[str, int] = {}
    c4_scores: list[float] = []
    from .difficulty_model import estimate
    from .scaffold import scaffold_size
    from .textlast import measure_wstf

    for block in blocks:
        band = _afb_band(block.cognitive_level)
        afb[band] = afb.get(band, 0) + 1
        est = estimate(block)
        if est is not None:
            c4_scores.append(est.score)
    return MixerMetricSnapshot(
        task_count=len(blocks),
        minutes_total=sum(b.est_minutes for b in blocks),
        afb_mix=afb,
        figure_tasks=sum(bool(b.asset_refs) for b in blocks),
        multiple_choice_tasks=sum(
            getattr(b.payload, "kind", None) == "multiple_choice" for b in blocks
        ),
        open_response_tasks=sum(b.kind == "open_response" for b in blocks),
        scaffolded_tasks=sum(bool(b.scaffold) for b in blocks),
        scaffold_elements=sum(scaffold_size(b.scaffold) for b in blocks),
        wstf=(round(w, 4) if (w := measure_wstf(blocks)) is not None else None),
        c4_mean=(round(sum(c4_scores) / len(c4_scores), 4) if c4_scores else None),
        coverage_ids=_coverage_ids(blocks),
    )


def _afb_mean(snapshot: MixerMetricSnapshot) -> float:
    total = sum(snapshot.afb_mix.values())
    return (sum(int(band) * count for band, count in snapshot.afb_mix.items()) / total
            if total else 0.0)


def _movement(
    fader: str,
    low_label: str,
    high_label: str,
    metric: str,
    low_value: float,
    high_value: float,
    low: MixerMetricSnapshot,
    high: MixerMetricSnapshot,
) -> FaderMovement:
    return FaderMovement(
        fader=fader,
        low_label=low_label,
        high_label=high_label,
        metric=metric,
        low_value=round(float(low_value), 4),
        high_value=round(float(high_value), 4),
        moved=low_value != high_value,
        coverage_intact=low.coverage_ids == high.coverage_ids,
    )


def make_mixed_variants(
    task: ParametricTask,
    base_n: int,
    profile: ParametricMixerProfile,
    *,
    seed0: int = 1,
    ramp: bool = False,
) -> tuple[list[TaskBlock], list[Asset], MixerLintReport, int]:
    """Apply a P1/P2 profile and return blocks, assets, Regler-Lint, and actual count."""
    actual_n = adjusted_variant_count(base_n, profile.umfang)

    scaffold_on = profile.geruest == Geruest.GESTUETZT
    blocks, assets = make_variants_with_assets(
        task, actual_n, seed0=seed0, ramp=ramp, openness=profile.offenheit,
        scaffold=scaffold_on, textlast=profile.textlast,
    )
    if profile.textlast is not None and task.prompt_simple is None:
        # Textlast capability (fail loudly, like the P1/P2 faders): the fader exists only
        # where the template carries an approved simplified twin — never a decorative knob.
        raise ValueError(
            "Tiefenregler Textlast is unsupported by template "
            f"'{task.id}': no approved simplified prompt twin (prompt_simple)"
        )
    if profile.geruest is not None:
        # Gerüst capability (fail loudly, like the P1 faders): the template must expose
        # scaffoldable data on at least one variant, else this is a no-op control.
        probe = blocks if scaffold_on else make_variants_with_assets(
            task, actual_n, seed0=seed0, ramp=ramp, openness=profile.offenheit,
            scaffold=True,
        )[0]
        if not any(b.scaffold for b in probe):
            raise ValueError(
                "Tiefenregler Gerüst is unsupported by template "
                f"'{task.id}': no leak-free first step, misconception hint, or open "
                "response surface to scaffold"
            )
    if profile.tiefe == Tiefe.STRATEGIEN_VERGLEICHEN:
        blocks = _strategy_depth(blocks)
    elif profile.tiefe == Tiefe.UEBEN:
        # Prove the high endpoint exists even when the requested projection is the low one.
        _strategy_depth(blocks)
    if profile.abstraktion == Abstraktion.FORMAL:
        blocks, assets = _formal_projection(blocks, assets)
    elif profile.abstraktion == Abstraktion.ANSCHAULICH and not any(b.asset_refs for b in blocks):
        raise ValueError(
            "Tiefenregler Abstraktion is unsupported: the recipe emits no "
            "computed student figure"
        )

    movements: list[FaderMovement] = []

    # Umfang is universal.  Measure its endpoints from the same template and seed stream.
    compact_n = adjusted_variant_count(base_n, Umfang.KOMPAKT)
    extended_n = adjusted_variant_count(base_n, Umfang.ERWEITERT)
    compact, _ = make_variants_with_assets(task, compact_n, seed0=seed0, ramp=ramp)
    extended, _ = make_variants_with_assets(task, extended_n, seed0=seed0, ramp=ramp)
    compact_m, extended_m = metric_snapshot(compact), metric_snapshot(extended)
    movements.append(_movement(
        "umfang", "kompakt", "erweitert", "task_count",
        compact_m.task_count, extended_m.task_count, compact_m, extended_m,
    ))

    if profile.tiefe is not None:
        native, _ = make_variants_with_assets(task, actual_n, seed0=seed0, ramp=ramp)
        deep = _strategy_depth(native)
        low, high = metric_snapshot(native), metric_snapshot(deep)
        movements.append(_movement(
            "tiefe", "üben", "Strategien vergleichen", "afb_mean",
            _afb_mean(low), _afb_mean(high), low, high,
        ))

    if profile.abstraktion is not None:
        visual, visual_assets = make_variants_with_assets(
            task, actual_n, seed0=seed0, ramp=ramp,
        )
        formal, _ = _formal_projection(visual, visual_assets)
        low, high = metric_snapshot(visual), metric_snapshot(formal)
        movements.append(_movement(
            "abstraktion", "anschaulich", "formal", "figure_tasks",
            low.figure_tasks, high.figure_tasks, low, high,
        ))

    if profile.offenheit is not None:
        closed, _ = make_variants_with_assets(
            task, actual_n, seed0=seed0, ramp=ramp,
            openness=Offenheit.GESCHLOSSEN,
        )
        opened, _ = make_variants_with_assets(
            task, actual_n, seed0=seed0, ramp=ramp,
            openness=Offenheit.OFFEN,
        )
        low, high = metric_snapshot(closed), metric_snapshot(opened)
        movements.append(_movement(
            "offenheit", "geschlossen", "offen", "multiple_choice_tasks",
            low.multiple_choice_tasks, high.multiple_choice_tasks, low, high,
        ))

    if profile.geruest is not None:
        # Gerüst (P2): measure the two endpoints from the same template + seed stream.
        # Scaffolding never touches serves/kind/minutes, so only the scaffold count moves —
        # coverage is intact by construction.
        bare, _ = make_variants_with_assets(
            task, actual_n, seed0=seed0, ramp=ramp, openness=profile.offenheit,
            scaffold=False,
        )
        scaffolded, _ = make_variants_with_assets(
            task, actual_n, seed0=seed0, ramp=ramp, openness=profile.offenheit,
            scaffold=True,
        )
        low, high = metric_snapshot(bare), metric_snapshot(scaffolded)
        movements.append(_movement(
            "geruest", "ohne", "gestützt", "scaffolded_tasks",
            low.scaffolded_tasks, high.scaffolded_tasks, low, high,
        ))

    if profile.textlast is not None:
        # Textlast (P3): measure the Wiener Sachtextformel of the student-facing prompt prose
        # at both CURATED endpoints from the same template + seed stream (same numbers; only
        # the prose register differs).  The lint passes iff `einfach` STRICTLY lowers the WSTF
        # Schulstufe — a twin that fails to simplify is a bad twin the SME must see (it lands
        # in this SAME report as `moved=False`, not a parallel lint).  Scaffolding/serves are
        # untouched, so competence coverage is identical by construction.
        full, _ = make_variants_with_assets(
            task, actual_n, seed0=seed0, ramp=ramp, openness=profile.offenheit,
            textlast=Textlast.VOLL,
        )
        simple, _ = make_variants_with_assets(
            task, actual_n, seed0=seed0, ramp=ramp, openness=profile.offenheit,
            textlast=Textlast.EINFACH,
        )
        low, high = metric_snapshot(full), metric_snapshot(simple)
        if low.wstf is None or high.wstf is None:
            raise ValueError(
                "Tiefenregler Textlast is unmeasurable for template "
                f"'{task.id}': too little student-facing prompt prose to compute the WSTF"
            )
        movements.append(FaderMovement(
            fader="textlast", low_label="voll", high_label="einfach", metric="wstf",
            low_value=round(float(low.wstf), 4), high_value=round(float(high.wstf), 4),
            moved=high.wstf < low.wstf,      # a genuine, measurable simplification (strict ↓)
            coverage_intact=low.coverage_ids == high.coverage_ids,
        ))

    report = MixerLintReport(
        passed=all(m.moved and m.coverage_intact for m in movements),
        output=metric_snapshot(blocks),
        movements=movements,
    )
    if not report.passed:
        failed = ", ".join(m.fader for m in movements
                           if not (m.moved and m.coverage_intact))
        raise ValueError(f"Regler-Lint failed for: {failed}")
    return blocks, assets, report, actual_n


# --- P4: capability discovery ------------------------------------------------------------
# The dashboard Mischpult must show a teacher which faders a template supports — and, for the
# rest, an honest "warum nicht".  This is DERIVED by asking the SAME structural questions the
# mixer's own rejection paths ask (above), over the SAME variant builder — never a parallel,
# hand-maintained capability table that could drift.  `tests/test_mixer_capabilities.py` locks
# the discovery output against the mixer's actual accept/reject behaviour for every registered
# template × every fader (a registry-wide drift test).

DISCOVERY_N = 6   # a representative variant count for probing (the dashboard default). The
# structural capabilities (solution_paths / figure / MCSpec / scaffold / twin) are
# n-independent; the Textlast WSTF is aggregate-stable across n (tiefenregler-design §7), so
# the report is n-robust.

# Curated German "warum nicht" copy — ONE per capability fader (Austrian school register).
# Presentation only: the supported/unsupported DECISION is derived from the structural checks
# below (which mirror the mixer), never from this table.
_UNSUPPORTED_REASON: dict[str, str] = {
    "tiefe": "Kein alternativer Rechenweg im Rezept — es gibt keine zwei Strategien zum "
             "Vergleichen.",
    "abstraktion": "Keine Schüler-Abbildung im Rezept — es gibt nichts zum Weglassen.",
    "offenheit": "Keine Multiple-Choice-Grundlage — das Rezept erzeugt keine "
                 "Fehlvorstellungs-Antworten.",
    "geruest": "Nichts zum Stützen — kein leak-freier erster Schritt, kein Fehlerhinweis "
               "und keine Schreibfläche.",
    "textlast_no_twin": "Keine geprüfte vereinfachte Angabe hinterlegt.",
    "textlast_no_drop": "Die vereinfachte Angabe senkt die Lesbarkeit (WSTF) nicht messbar.",
}


def _is_mc(block: TaskBlock) -> bool:
    """The SAME multiple-choice test the metric snapshot uses (the payload discriminator)."""
    return getattr(block.payload, "kind", None) == "multiple_choice"


def _option(value) -> FaderOption:
    v = value.value if hasattr(value, "value") else str(value)
    return FaderOption(value=v, label=ENDPOINT_LABELS.get(v, v))


def _optional_capability(fader, low, high, supported, reason) -> FaderCapability:
    """A two-endpoint capability fader (neutral default = None)."""
    return FaderCapability(
        fader=fader, label=FADER_LABELS[fader], supported=supported, optional=True,
        options=[_option(low), _option(high)], default=None,
        reason=None if supported else reason,
    )


def discover_capabilities(
    task: ParametricTask, *, n: int = DISCOVERY_N, seed0: int = 1, ramp: bool = False,
) -> TemplateCapabilities:
    """Report which Mischpult faders `task` supports, and the honest German reason otherwise.

    Each capability is derived from the SAME structural condition the mixer's rejection code
    checks, over the SAME `make_variants_with_assets` builder — so discovery cannot drift from
    what `make_mixed_variants` will actually accept (locked registry-wide by the drift test).
    """
    caps: list[FaderCapability] = []

    # Umfang — universal: `adjusted_variant_count` always maps and, for n ≥ 1, the kompakt and
    # erweitert counts always differ, so the fader always moves.  Never left unset.
    caps.append(FaderCapability(
        fader="umfang", label=FADER_LABELS["umfang"], supported=True, optional=False,
        default=Umfang.STANDARD.value,
        options=[_option(u) for u in (Umfang.KOMPAKT, Umfang.STANDARD, Umfang.ERWEITERT)],
    ))

    # Build the neutral master ONCE — the same builder + defaults the mixer uses for the
    # Tiefe / Abstraktion / Offenheit capability checks.
    base, _ = make_variants_with_assets(task, n, seed0=seed0, ramp=ramp)

    # Tiefe — `_strategy_depth` rejects unless EVERY variant emits alternative solution paths.
    tiefe_ok = bool(base) and all(b.solution_paths for b in base)
    caps.append(_optional_capability(
        "tiefe", Tiefe.UEBEN, Tiefe.STRATEGIEN_VERGLEICHEN, tiefe_ok,
        _UNSUPPORTED_REASON["tiefe"]))

    # Abstraktion — `_formal_projection` rejects unless some variant carries a student figure.
    abstraktion_ok = any(b.asset_refs for b in base)
    caps.append(_optional_capability(
        "abstraktion", Abstraktion.ANSCHAULICH, Abstraktion.FORMAL, abstraktion_ok,
        _UNSUPPORTED_REASON["abstraktion"]))

    # Offenheit — the openness projection rejects unless every variant carries an MCSpec (i.e.
    # every base block is already a multiple_choice task).
    offenheit_ok = bool(base) and all(_is_mc(b) for b in base)
    caps.append(_optional_capability(
        "offenheit", Offenheit.GESCHLOSSEN, Offenheit.OFFEN, offenheit_ok,
        _UNSUPPORTED_REASON["offenheit"]))

    # Gerüst — the mixer builds a scaffolded probe and rejects unless ≥ 1 variant scaffolds.
    scaffolded, _ = make_variants_with_assets(task, n, seed0=seed0, ramp=ramp, scaffold=True)
    geruest_ok = any(b.scaffold for b in scaffolded)
    caps.append(_optional_capability(
        "geruest", Geruest.OHNE, Geruest.GESTUETZT, geruest_ok,
        _UNSUPPORTED_REASON["geruest"]))

    # Textlast — an approved twin (`prompt_simple`) whose student prose STRICTLY lowers the
    # WSTF Schulstufe (the exact rule the mixer's Textlast movement enforces).
    if task.prompt_simple is None:
        textlast_ok, reason = False, _UNSUPPORTED_REASON["textlast_no_twin"]
    else:
        from .textlast import measure_wstf
        full, _ = make_variants_with_assets(
            task, n, seed0=seed0, ramp=ramp, textlast=Textlast.VOLL)
        simple, _ = make_variants_with_assets(
            task, n, seed0=seed0, ramp=ramp, textlast=Textlast.EINFACH)
        wf, ws = measure_wstf(full), measure_wstf(simple)
        textlast_ok = wf is not None and ws is not None and ws < wf
        reason = _UNSUPPORTED_REASON["textlast_no_drop"]
    caps.append(_optional_capability(
        "textlast", Textlast.VOLL, Textlast.EINFACH, textlast_ok, reason))

    return TemplateCapabilities(
        template_id=task.id, subject=task.subject, klasse=task.klasse,
        title=task.title or task.id, capabilities=caps)
