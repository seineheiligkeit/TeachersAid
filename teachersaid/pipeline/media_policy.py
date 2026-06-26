"""MediaPolicy — the library-entry gate for assets (schema §6 / v0.4 A3).

The load-bearing product principle: the platform *consolidates a human-vetted
library*, it does not live-generate. So discipline about asset sources is a
**library-entry gate, not a generation ban**. The durable invariant this gate
enforces (the 3-class table in `Documents/schema-roadmap-v0.4-v0.5.md`):

    content-bearing visuals must be CORRECT  → code-generated (correct by
        construction, beats review) or vetted-sourced (external file + rights);
    decorative visuals must be CONTENT-FREE  → then any source (incl. diffusion,
        vetted once) is fine.

`MediaPolicy` is the per-subject config: per medium, it partitions asset *roles*
into `must_be_code` / `must_be_sourced` / `diffusion_ok`. `check_content` runs in
`verify` (the one rules place every entry path passes through), so a mis-sourced
content asset — or a decorative asset masquerading as content — blocks library
entry exactly like any other verify problem. It also *steers generation*: an LLM
may only request the code recipes (`GENERATION_RECIPES`), which are the
`must_be_code` roles.

Adding a `diffusion:` backend (the SME's image-gen agent, Phase 4 #4) needs no
change here: this gate already *admits* a decorative, content-free diffusion asset.
"""
from __future__ import annotations

from ..schema.assets import Asset, MediaPolicy, MediaPolicyEntry
from ..schema.enums import Medium

# Backends that are correct-by-construction (the asset is right because the code
# built it). `diffusion:` is deliberately NOT here — it can only ever be decorative.
CODE_BACKENDS = frozenset({"matplotlib", "svg"})
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


def classify_source(asset: Asset) -> str:
    """How the asset is produced: 'code' (correct-by-construction backend),
    'diffusion' (image-gen), 'sourced' (external file + provenance), or 'none'."""
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


def check_asset(asset: Asset, policy: MediaPolicy = DEFAULT_MEDIA_POLICY) -> tuple[list[str], list[str]]:
    """Gate one asset against the policy. Returns (problems, warnings): a problem
    blocks library entry (the invariant is violated); a warning flags something a
    human should classify but doesn't block."""
    problems: list[str] = []
    warnings: list[str] = []
    entry = _entry(policy, asset.medium)
    if entry is None:
        warnings.append(f"asset '{asset.id}': no media policy for medium '{asset.medium}'")
        return problems, warnings

    role, src = asset.role, classify_source(asset)
    if role in entry.must_be_code:
        if src != "code":
            problems.append(
                f"asset '{asset.id}': content role '{role}' must be code-generated "
                f"(correct by construction), but its source is '{src}'"
            )
    elif role in entry.must_be_sourced:
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
    elif role in entry.diffusion_ok:
        # decorative: any source is fine, but it must carry NO content claim
        if asset.correctness_surface or asset.intentionally_flawed:
            problems.append(
                f"asset '{asset.id}': decorative role '{role}' must be content-free, "
                f"but it carries a correctness/flaw claim"
            )
    else:
        # role not covered by the policy: fine if already vetted, else flag for triage
        if src in ("diffusion", "none"):
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
