"""Typed data exchanged by Seismic's parser, service, MCP, and dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypedDict

ArtifactKind = Literal["file", "function", "class", "test", "entrypoint", "package_version"]
RelationshipKind = Literal["PART_OF", "IMPORTS", "CALLS", "TESTS", "STARTS_AT", "DEPENDS_ON"]
GateDecision = Literal["safe", "review", "block"]
EvidenceStatus = Literal["supported", "bounded-empty", "incomplete"]


@dataclass(slots=True)
class ArtifactRecord:
    """One snapshot-scoped code, test, entrypoint, or package artifact."""

    id: int
    key: str
    identity_id: int
    identity_key: str
    repo_key: str
    snapshot_key: str
    logical_key: str
    kind: ArtifactKind
    path: str
    qualified_name: str
    language: str
    line_start: int = 0
    line_end: int = 0
    content_hash: str = ""
    last_author: str = ""
    last_modified: str = ""
    owner: str = ""
    owner_source: str = ""
    resolution_confidence: float = 1.0
    text: str = ""


@dataclass(slots=True)
class RelationshipRecord:
    """One deterministic dependency relationship inside a repository snapshot."""

    id: int
    kind: RelationshipKind
    source_id: int
    target_id: int
    confidence: float = 1.0
    evidence_count: int = 1
    first_evidence_line: int = 0
    source: str = "ast"
    requirement: str = ""


@dataclass(slots=True)
class RepositoryGraph:
    """A fully parsed immutable repository snapshot ready for validation and storage."""

    repo_key: str
    snapshot_key: str
    commit_sha: str
    root_name: str
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    relationships: list[RelationshipRecord] = field(default_factory=list)
    unresolved_imports: int = 0
    unresolved_calls: int = 0
    skipped_files: int = 0
    warnings: list[str] = field(default_factory=list)


class IngestSummary(TypedDict):
    """Serializable outcome of one repository snapshot activation."""

    repo_id: str
    snapshot_id: str
    commit_sha: str
    files: int
    artifacts: int
    packages: int
    relationships: int
    unresolved_imports: int
    unresolved_calls: int
    skipped_files: int
    duration_ms: float
    activated: bool
    warnings: list[str]


class EvidenceNode(TypedDict):
    """One artifact in a user-facing evidence path."""

    key: str
    logical_key: str
    kind: str
    path: str
    qualified_name: str


class EvidenceHop(TypedDict):
    """One relationship hop in an evidence path."""

    type: str
    source: str
    target: str
    evidence_line: int
    confidence: float


class ImpactResult(TypedDict):
    """One affected artifact with path evidence and transparent risk components."""

    target: str
    artifact_key: str
    logical_key: str
    kind: str
    path: str
    qualified_name: str
    hop_distance: int
    risk_score: float
    score_components: dict[str, float]
    resolution_confidence: float
    owner: str
    owner_source: str
    last_author: str
    last_modified: str
    incident_count: int
    incident_pair_count: int
    reason: str
    nodes: list[EvidenceNode]
    hops: list[EvidenceHop]


class ChangeGate(TypedDict):
    """Deterministic action an agent can take from the supported graph evidence."""

    policy: str
    decision: GateDecision
    headline: str
    summary: str
    max_risk_score: float
    impacted_artifacts: int
    required_tests: list[str]
    verification_commands: list[str]
    affected_entrypoints: list[str]
    affected_owners: list[str]
    reasons: list[str]


class EvidenceCoverage(TypedDict):
    """Explain whether the graph supports, bounds, or cannot justify a decision."""

    status: EvidenceStatus
    complete: bool
    fallback: bool
    reason: str
    unresolved_imports: int
    unresolved_calls: int
    skipped_files: int


class DecisionReceipt(TypedDict):
    """Durable HydraDB audit record for one agent-facing change decision."""

    id: str
    repo_id: str
    snapshot_id: str
    analysis_kind: str
    created_at: str
    decision: GateDecision
    evidence_status: EvidenceStatus
    fallback: bool
    reason: str
    targets: list[str]
    unresolved_targets: list[str]
    supported_impacts: int
    max_risk_score: float


class ChangeImpactReport(TypedDict):
    """Complete result of analyzing one planned repository change."""

    repo_id: str
    snapshot_id: str
    targets: list[str]
    engine: str
    gate: ChangeGate
    results: list[ImpactResult]
    unresolved_targets: list[str]
    warnings: list[str]
    evidence: EvidenceCoverage
    receipt_id: str


class DiffImpactReport(ChangeImpactReport):
    """Change impact plus the files discovered from a bounded unified diff."""

    diff_files: list[str]


class ContextPack(TypedDict):
    """Lexical seeds plus graph-expanded evidence for an agent task."""

    repo_id: str
    snapshot_id: str
    query: str
    seeds: list[dict[str, object]]
    graph_context: list[ImpactResult]
    abstained: bool
    warnings: list[str]


class ImpactExplanation(TypedDict):
    """Exact native path evidence between a change and one affected artifact."""

    repo_id: str
    snapshot_id: str
    changed_target: str
    affected_target: str
    engine: str
    supported: bool
    summary: str
    nodes: list[EvidenceNode]
    hops: list[EvidenceHop]
