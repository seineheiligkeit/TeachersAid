"""MediaPolicy — the library-entry gate for assets (schema §6 / v0.4 A3).

The load-bearing product principle: the platform *consolidates a human-vetted
library*, it does not live-generate. So discipline about asset sources is a
**library-entry gate, not a generation ban**. The durable invariant this gate
enforces three claim lanes (`Documents/illustration-design.md`):

    content-bearing visuals must be CORRECT  → code-generated (correct by
        construction, beats review) or vetted-sourced (external file + rights);
    depictive visuals carry one declared, SME-checkable intended claim and no
        baked-in text, labels, numbers or task structure;
    decorative visuals must be CONTENT-FREE  → then any source (incl. diffusion,
        vetted once) is fine.

`MediaPolicy` is the per-subject config: per medium, it partitions asset *roles*
into `must_be_code` / `must_be_sourced` / `depictive_ok` / `diffusion_ok`.
`check_content` runs in
`verify` (the one rules place every entry path passes through), so a mis-sourced
content asset — or a decorative asset masquerading as content — blocks library
entry exactly like any other verify problem. It also *steers generation*: an LLM
may only request the code recipes (`GENERATION_RECIPES`), which are the
`must_be_code` roles.

Adding a `diffusion:` backend (the SME's image-gen agent, Phase 4 #4) needs no
change here: this gate already *admits* a decorative, content-free diffusion asset.
Agent-time generations additionally pass `origin="synthetic"` to `check_asset`,
so a materialised file cannot conceal a generated source. Synthetic content is
always rejected.
"""
from __future__ import annotations

from ..schema.assets import Asset, MediaPolicy, MediaPolicyEntry
from ..schema.enums import Medium

# Backends that are correct-by-construction (the asset is right because the code
# built it) — incl. `audio:` (TTS from a vetted script, the machine path for Hören).
# `diffusion:` is deliberately NOT here — it can only ever be decorative.
CODE_BACKENDS = frozenset({"matplotlib", "svg", "audio"})
# Rights that count as cleared for a sourced asset ("unverified" does not).
VETTED_RIGHTS = frozenset({"public_domain", "licensed", "cleared", "original"})

# The default gate, applied to every subject until one overrides it. Roles are
# partitioned by the discipline they require; the invariant lives in this table.
DEFAULT_MEDIA_POLICY = MediaPolicy(
    subject="*",
    per_medium=[
        MediaPolicyEntry(
            medium=Medium.VISUAL,
            must_be_code=[
                "figure", "diagram", "chart", "graph", "plot", "data", "dataset",
                "number_line", "timeline", "geometry", "table", "schematic",
            ],
            must_be_sourced=[
                "photo", "photograph", "source", "artwork", "map", "scan", "screenshot",
            ],
            depictive_ok=[
                "depiction", "depictive", "backdrop", "scene_illustration",
                "object_illustration", "anatomy_base", "apparatus_base",
            ],
            diffusion_ok=[
                "decoration", "decorative", "mascot", "motif", "icon", "illustration",
                "spot_illustration", "background", "ornament", "header",
            ],
        ),
        MediaPolicyEntry(
            medium=Medium.AUDIO,
            machine_generatable=False,  # music/speech is NOT machine-generatable…
            must_be_code=["tts", "synth"],  # …but a language TTS prompt IS
            must_be_sourced=["recording", "song", "music", "audio", "soundscape"],
            diffusion_ok=[],
        ),
        MediaPolicyEntry(
            medium=Medium.INTERACTIVE,
            must_be_code=["widget", "applet", "simulation", "interactive"],
            must_be_sourced=[],
            diffusion_ok=[],
        ),
    ],
)

# Per-subject overrides plug in here later; for now every subject uses the default.
_SUBJECT_POLICIES: dict[str, MediaPolicy] = {}


def policy_for(subject: str | None) -> MediaPolicy:
    return _SUBJECT_POLICIES.get(subject or "", DEFAULT_MEDIA_POLICY)


def _backend(generator: str | None) -> str | None:
    return generator.split(":", 1)[0] if generator else None


def classify_source(asset: Asset, *, origin: str | None = None) -> str:
    """How the asset is produced: 'code' (correct-by-construction backend),
    'diffusion' (runtime image-gen), 'synthetic' (agent-time image-gen),
    'sourced' (external file + provenance), or 'none'."""
    if origin == "synthetic":
        return "synthetic"
    backend = _backend(asset.generator)
    if backend in CODE_BACKENDS:
        return "code"
    if backend == "diffusion":
        return "diffusion"
    if asset.provenance is not None:
        return "sourced"
    return "none"


def _entry(policy: MediaPolicy, medium) -> MediaPolicyEntry | None:
    for e in policy.per_medium:
        if e.medium == medium:
            return e
    return None


def check_asset(
    asset: Asset,
    policy: MediaPolicy = DEFAULT_MEDIA_POLICY,
    *,
    origin: str | None = None,
) -> tuple[list[str], list[str]]:
    """Gate one asset against the policy. Returns (problems, warnings): a problem
    blocks library entry (the invariant is violated); a warning flags something a
    human should classify but doesn't block."""
    problems: list[str] = []
    warnings: list[str] = []
    entry = _entry(policy, asset.medium)
    if entry is None:
        warnings.append(f"asset '{asset.id}': no media policy for medium '{asset.medium}'")
        return problems, warnings

    role, src = asset.role, classify_source(asset, origin=origin)
    declared_lane = asset.lane
    if role in entry.must_be_code:
        if declared_lane not in (None, "content"):
            problems.append(
                f"asset '{asset.id}': content role '{role}' cannot declare lane "
                f"'{declared_lane}'"
            )
        if src != "code":
            problems.append(
                f"asset '{asset.id}': content role '{role}' must be code-generated "
                f"(correct by construction), but its source is '{src}'"
            )
    elif role in entry.must_be_sourced:
        if declared_lane not in (None, "content"):
            problems.append(
                f"asset '{asset.id}': content role '{role}' cannot declare lane "
                f"'{declared_lane}'"
            )
        if src != "sourced":
            problems.append(
                f"asset '{asset.id}': content role '{role}' must be sourced "
                f"(external file + provenance), but its source is '{src}'"
            )
        elif asset.provenance.rights not in VETTED_RIGHTS:
            problems.append(
                f"asset '{asset.id}': sourced '{role}' has unverified rights "
                f"'{asset.provenance.rights}'"
            )
    elif role in entry.depictive_ok or declared_lane == "depictive":
        if not (asset.intended_claim or "").strip():
            problems.append(
                f"asset '{asset.id}': depictive lane requires an intended_claim"
            )
        if asset.correctness_surface or asset.intentionally_flawed:
            problems.append(
                f"asset '{asset.id}': depictive pixels may carry only the declared "
                "intended_claim, never a correctness/flaw task surface"
            )
        if src == "sourced" and asset.provenance.rights not in VETTED_RIGHTS:
            problems.append(
                f"asset '{asset.id}': sourced depictive asset has unverified rights "
                f"'{asset.provenance.rights}'"
            )
    elif role in entry.diffusion_ok or declared_lane == "decorative":
        # decorative: any source is fine, but it must carry NO content claim
        if asset.intended_claim or asset.correctness_surface or asset.intentionally_flawed:
            problems.append(
                f"asset '{asset.id}': decorative role '{role}' must be content-free, "
                f"but it carries a correctness/flaw claim"
            )
    elif declared_lane == "content":
        # Unknown content roles still cannot use generated/unvetted pixels.
        if src in {"diffusion", "synthetic", "none"}:
            problems.append(
                f"asset '{asset.id}': content lane hard-rejects generated/unvetted "
                f"source '{src}'"
            )
    else:
        # role not covered by the policy: fine if already vetted, else flag for triage
        if src in ("diffusion", "synthetic", "none"):
            warnings.append(
                f"asset '{asset.id}': role '{role}' is not covered by the media policy "
                f"and its source '{src}' is unvetted — classify it"
            )
    return problems, warnings


def check_content(content, policy: MediaPolicy | None = None) -> tuple[list[str], list[str]]:
    """Gate every asset on a worksheet. Resolves the per-subject policy."""
    pol = policy or policy_for(getattr(content.meta, "subject", None))
    problems: list[str] = []
    warnings: list[str] = []
    for a in content.assets:
        p, w = check_asset(a, pol)
        problems += p
        warnings += w
    return problems, warnings
