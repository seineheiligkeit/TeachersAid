"""Typed data model: schema v0.3 + the additive v0.4 deltas (Pydantic v2)."""

from __future__ import annotations

from .arrangement import (
    ArrangementMeta,
    ArrangementPhase,
    ArrangementRole,
    CompetenceAnchor,
    Lernarrangement,
    SharedProduct,
)
from .assets import Asset, AssetProvenance, IntentionallyFlawed, MediaPolicy
from .blocks import (
    Block,
    BlockBase,
    ContentFlags,
    InfoBlock,
    RubricCriterion,
    Serves,
    TaskBlock,
    TaskPayload,
)
from .competence import (
    CompetenceDimension,
    DimensionRef,
    SubjectCompetenceModel,
    SubjectCompetenceModelRef,
    printable_coverage,
)
from .derived import (
    CompetenceCoverage,
    DepthProfile,
    DepthTarget,
    Nachweis,
)
from .enums import (
    CognitiveLevel,
    CoreTaskKind,
    CoverageRelation,
    InfoKind,
    Medium,
    Modality,
    Role,
    Stufe,
)
from .response import ResponseSpec
from .richtext import InlineRun, RichText, plain_text, to_runs
from .verification import Thread, ThreadRack, VerificationItem
from .worksheet import (
    Baustein,
    Bundle,
    BundleRequest,
    FassungRef,
    LehrplanResolution,
    ResolvedCompetence,
    WorksheetContent,
    WorksheetMeta,
)

__all__ = [
    "Lernarrangement",
    "ArrangementMeta",
    "ArrangementRole",
    "ArrangementPhase",
    "SharedProduct",
    "CompetenceAnchor",
    "Asset",
    "AssetProvenance",
    "IntentionallyFlawed",
    "MediaPolicy",
    "Block",
    "BlockBase",
    "ContentFlags",
    "InfoBlock",
    "RubricCriterion",
    "Serves",
    "TaskBlock",
    "TaskPayload",
    "CompetenceDimension",
    "DimensionRef",
    "SubjectCompetenceModel",
    "SubjectCompetenceModelRef",
    "printable_coverage",
    "CompetenceCoverage",
    "DepthProfile",
    "DepthTarget",
    "Nachweis",
    "CognitiveLevel",
    "CoreTaskKind",
    "CoverageRelation",
    "InfoKind",
    "Medium",
    "Modality",
    "Role",
    "Stufe",
    "ResponseSpec",
    "InlineRun",
    "RichText",
    "plain_text",
    "to_runs",
    "Thread",
    "ThreadRack",
    "VerificationItem",
    "Baustein",
    "Bundle",
    "BundleRequest",
    "FassungRef",
    "LehrplanResolution",
    "ResolvedCompetence",
    "WorksheetContent",
    "WorksheetMeta",
]
