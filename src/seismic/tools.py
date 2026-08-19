"""Seismic service implementing repository ingestion and graph-native MCP operations."""

from __future__ import annotations

import json
import re
import time
import uuid
from collections import Counter
from datetime import UTC, datetime

from neo4j.graph import Node, Path

from seismic.config import SeismicConfig
from seismic.db import HydraDB
from seismic.diffing import ChangedFile, parse_unified_diff
from seismic.gate import build_change_gate
from seismic.identity import relationship_id, stable_id
from seismic.ingest import SnapshotWriter, repository_index_lock
from seismic.models import (
    ChangeImpactReport,
    ContextPack,
    DecisionReceipt,
    DiffImpactReport,
    EvidenceCoverage,
    EvidenceHop,
    EvidenceNode,
    EvidenceStatus,
    GateDecision,
    ImpactExplanation,
    ImpactResult,
    IngestSummary,
)
from seismic.parser import RepositoryParser
from seismic.risk import risk_reason, score_risk

RELATIONSHIP_TYPES = ["PART_OF", "IMPORTS", "CALLS", "TESTS", "STARTS_AT", "DEPENDS_ON"]
MAX_QUERY_LENGTH = 2_000
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "change",
    "code",
    "for",
    "how",
    "in",
    "is",
    "of",
    "on",
    "the",
    "this",
    "to",
    "what",
    "which",
}


class SeismicService:
    """Coordinate parsing, durable graph writes, traversal, and incident evidence."""

    def __init__(self, db: HydraDB, config: SeismicConfig | None = None) -> None:
        self.db = db
        self.config = config or db.config
        self.parser = RepositoryParser(self.config)
        self.writer = SnapshotWriter(db)

    def index_repository(self, repo_path: str, repo_id: str | None = None) -> IngestSummary:
        """Build and activate a validated immutable code-graph snapshot for agents."""

        activation_started_at = datetime.now(UTC).isoformat()
        started = time.perf_counter()
        graph = self.parser.parse(repo_path, explicit_repo_key=repo_id)
        elapsed = (time.perf_counter() - started) * 1_000
        with repository_index_lock(graph.repo_key):
            return self.writer.write(
                graph,
                elapsed,
                activation_started_at=activation_started_at,
            )

    def analyze_change(
        self,
        repo_id: str,
        targets: list[str],
        max_hops: int = 4,
        limit: int = 30,
        *,
        analysis_kind: str = "targets",
    ) -> ChangeImpactReport:
        """Rank exact reverse-dependency paths before an agent changes code."""

        repo_key, snapshot_key = self._active_snapshot(repo_id)
        coverage = self._snapshot_coverage(snapshot_key)
        clean_targets = _target_list(targets)
        max_hops = _bounded(max_hops, "max_hops", 1, self.config.max_hops)
        limit = _bounded(limit, "limit", 1, self.config.max_results)
        resolved: list[dict[str, object]] = []
        unresolved: list[str] = []
        warnings: list[str] = []
        for target in clean_targets:
            matches = self._resolve_target(snapshot_key, target)
            if len(matches) == 1:
                resolved.append(matches[0])
            else:
                unresolved.append(target)
                if len(matches) > 1:
                    alternatives = ", ".join(str(match["logical_key"]) for match in matches)
                    warnings.append(f"Ambiguous target {target}; candidates: {alternatives}")
        if not resolved:
            empty_results: list[ImpactResult] = []
            evidence = self._build_evidence_coverage(
                coverage=coverage,
                targets=clean_targets,
                results=empty_results,
                unresolved_targets=unresolved,
            )
            report: ChangeImpactReport = {
                "repo_id": repo_key,
                "snapshot_id": snapshot_key,
                "targets": clean_targets,
                "engine": "HydraDB native path procedures",
                "gate": build_change_gate(
                    targets=clean_targets,
                    results=empty_results,
                    unresolved_targets=unresolved,
                    evidence_complete=evidence["complete"],
                ),
                "results": empty_results,
                "unresolved_targets": unresolved,
                "warnings": warnings,
                "evidence": evidence,
                "receipt_id": "",
            }
            return self._finalize_analysis(report, analysis_kind)
        fetch_limit = min(2_000, max(limit * 8, limit))
        paths = self._impact_paths(resolved, max_hops, fetch_limit)
        best_paths: dict[int, tuple[Path, dict[str, object]]] = {}
        fan_in: Counter[int] = Counter()
        for path in paths:
            if not isinstance(path, Path) or len(path.nodes) < 2:
                continue
            if any(str(node.get("snapshot_key", "")) != snapshot_key for node in path.nodes):
                continue
            for traversed_node in path.nodes[1:]:
                fan_in[_native_node_id(traversed_node)] += 1
            endpoint = path.nodes[-1]
            endpoint_id = _native_node_id(endpoint)
            source = path.nodes[0]
            source_record = next(
                (item for item in resolved if _record_id(item["id"]) == _native_node_id(source)),
                resolved[0],
            )
            current = best_paths.get(endpoint_id)
            if current is None or len(path.relationships) < len(current[0].relationships):
                best_paths[endpoint_id] = (path, source_record)
        max_fan_in = max(fan_in.values(), default=1)
        results: list[ImpactResult] = []
        for endpoint_id, (path, source_record) in best_paths.items():
            endpoint = path.nodes[-1]
            logical_key = str(endpoint.get("logical_key", ""))
            identity_key = str(endpoint.get("identity_key", ""))
            source_identity = str(source_record["identity_key"])
            incident_count = self._incident_count(identity_key)
            incident_pair_count = self._incident_pair_count(source_identity, identity_key)
            score, components = score_risk(
                hop_distance=len(path.relationships),
                incident_pair_count=incident_pair_count,
                incident_count=incident_count,
                fan_in=fan_in[endpoint_id],
                max_fan_in=max_fan_in,
                kind=str(endpoint.get("kind", "")),
            )
            nodes, hops = _serialize_path(path)
            results.append(
                {
                    "target": str(source_record["logical_key"]),
                    "artifact_key": str(endpoint.get("key", "")),
                    "logical_key": logical_key,
                    "kind": str(endpoint.get("kind", "")),
                    "path": str(endpoint.get("path", "")),
                    "qualified_name": str(endpoint.get("qualified_name", "")),
                    "hop_distance": len(path.relationships),
                    "risk_score": score,
                    "score_components": components,
                    "resolution_confidence": float(endpoint.get("resolution_confidence", 1.0)),
                    "owner": str(endpoint.get("owner", "")),
                    "owner_source": str(endpoint.get("owner_source", "")),
                    "last_author": str(endpoint.get("last_author", "")),
                    "last_modified": str(endpoint.get("last_modified", "")),
                    "incident_count": incident_count,
                    "incident_pair_count": incident_pair_count,
                    "reason": risk_reason(
                        logical_key=logical_key,
                        hop_distance=len(path.relationships),
                        incident_pair_count=incident_pair_count,
                        incident_count=incident_count,
                    ),
                    "nodes": nodes,
                    "hops": hops,
                }
            )
        results.sort(
            key=lambda item: (-item["risk_score"], item["hop_distance"], item["artifact_key"])
        )
        ranked_results = results[:limit]
        evidence = self._build_evidence_coverage(
            coverage=coverage,
            targets=clean_targets,
            results=results,
            unresolved_targets=unresolved,
        )
        report = {
            "repo_id": repo_key,
            "snapshot_id": snapshot_key,
            "targets": clean_targets,
            "engine": "HydraDB algo.SSpaths" if len(resolved) == 1 else "HydraDB algo.MSpaths",
            "gate": build_change_gate(
                targets=clean_targets,
                results=results,
                unresolved_targets=unresolved,
                evidence_complete=evidence["complete"],
            ),
            "results": ranked_results,
            "unresolved_targets": unresolved,
            "warnings": warnings,
            "evidence": evidence,
            "receipt_id": "",
        }
        return self._finalize_analysis(report, analysis_kind)

    def analyze_diff(
        self,
        repo_id: str,
        diff: str,
        max_hops: int = 4,
        limit: int = 30,
    ) -> DiffImpactReport:
        """Resolve a unified diff and return an actionable, evidence-backed change gate."""

        repo_key, snapshot_key = self._active_snapshot(repo_id)
        coverage = self._snapshot_coverage(snapshot_key)
        changes = parse_unified_diff(diff)
        targets, warnings = self._diff_targets(snapshot_key, changes)
        if not targets:
            results: list[ImpactResult] = []
            evidence = self._build_evidence_coverage(
                coverage=coverage,
                targets=[],
                results=results,
                unresolved_targets=[],
            )
            empty_report: DiffImpactReport = {
                "repo_id": repo_key,
                "snapshot_id": snapshot_key,
                "targets": [],
                "diff_files": [change.path for change in changes],
                "engine": "HydraDB native path procedures",
                "gate": build_change_gate(
                    targets=[],
                    results=results,
                    unresolved_targets=[],
                    evidence_complete=evidence["complete"],
                ),
                "results": results,
                "unresolved_targets": [],
                "warnings": warnings or ["The diff did not touch an indexed artifact."],
                "evidence": evidence,
                "receipt_id": "",
            }
            empty_report["receipt_id"] = self._record_decision_receipt(empty_report, "diff")
            return empty_report
        raw_report = self.analyze_change(
            repo_key,
            targets,
            max_hops,
            limit,
            analysis_kind="diff",
        )
        report: DiffImpactReport = {
            **raw_report,
            "diff_files": [change.path for change in changes],
        }
        report["warnings"] = [*raw_report["warnings"], *warnings]
        return report

    def retrieve_context(
        self,
        repo_id: str,
        query: str,
        candidate_targets: list[str] | None = None,
        limit: int = 20,
    ) -> ContextPack:
        """Seed lexically, then expand through HydraDB to recover structural context."""

        repo_key, snapshot_key = self._active_snapshot(repo_id)
        clean_query = _text(query, "query", MAX_QUERY_LENGTH)
        limit = _bounded(limit, "limit", 1, min(100, self.config.max_results))
        if candidate_targets:
            seed_targets = _target_list(candidate_targets)[:8]
            seeds = [
                {"logical_key": target, "lexical_score": 1.0, "source": "candidate"}
                for target in seed_targets
            ]
        else:
            rows = self.db.query(
                "MATCH (snapshot:Snapshot {id: $snapshot_id})-[:CONTAINS]->"
                "(artifact:Artifact) "
                "RETURN artifact.logical_key AS logical_key, artifact.path AS path, "
                "artifact.qualified_name AS qualified_name, artifact.text AS text "
                "ORDER BY artifact.id LIMIT 5000",
                {"snapshot_id": stable_id("snapshot", snapshot_key)},
            )
            query_tokens = _tokens(clean_query)
            ranked: list[tuple[float, str]] = []
            for row in rows:
                haystack = " ".join(
                    str(row[name] or "")
                    for name in ("logical_key", "path", "qualified_name", "text")
                )
                artifact_tokens = _tokens(haystack)
                if not query_tokens or not artifact_tokens:
                    continue
                score = len(query_tokens & artifact_tokens) / len(query_tokens)
                if score > 0:
                    ranked.append((score, str(row["logical_key"])))
            ranked.sort(key=lambda item: (-item[0], item[1]))
            seeds = [
                {"logical_key": target, "lexical_score": round(score, 4), "source": "lexical"}
                for score, target in ranked[:5]
            ]
            seed_targets = [str(seed["logical_key"]) for seed in seeds]
        if not seed_targets:
            return {
                "repo_id": repo_key,
                "snapshot_id": snapshot_key,
                "query": clean_query,
                "seeds": [],
                "graph_context": [],
                "abstained": True,
                "warnings": ["No credible lexical or caller-provided seed was found."],
            }
        report = self.analyze_change(
            repo_key,
            seed_targets,
            max_hops=3,
            limit=limit,
            analysis_kind="context",
        )
        return {
            "repo_id": repo_key,
            "snapshot_id": snapshot_key,
            "query": clean_query,
            "seeds": seeds,
            "graph_context": report["results"],
            "abstained": not bool(report["results"]),
            "warnings": report["warnings"],
        }

    def explain_impact(
        self,
        repo_id: str,
        changed_target: str,
        affected_target: str,
        max_hops: int = 6,
    ) -> ImpactExplanation:
        """Return one exact native dependency path or explicitly report no support."""

        repo_key, snapshot_key = self._active_snapshot(repo_id)
        max_hops = _bounded(max_hops, "max_hops", 1, self.config.max_hops)
        changed = self._single_target(snapshot_key, changed_target)
        affected = self._single_target(snapshot_key, affected_target)
        rows = self.db.query(
            """
CALL algo.SPpaths({
  sourceNode: $affected_id,
  targetNode: $changed_id,
  relTypes: ['PART_OF', 'IMPORTS', 'CALLS', 'TESTS', 'STARTS_AT', 'DEPENDS_ON'],
  relDirection: 'outgoing',
  maxLen: $max_hops,
  pathCount: 1
})
YIELD path
RETURN path
""",
            {
                "affected_id": _record_id(affected["id"]),
                "changed_id": _record_id(changed["id"]),
                "max_hops": max_hops,
            },
        )
        path = rows[0]["path"] if rows else None
        if not isinstance(path, Path):
            return {
                "repo_id": repo_key,
                "snapshot_id": snapshot_key,
                "changed_target": str(changed["logical_key"]),
                "affected_target": str(affected["logical_key"]),
                "engine": "HydraDB algo.SPpaths",
                "supported": False,
                "summary": "No supported dependency path exists within the requested hop bound.",
                "nodes": [],
                "hops": [],
            }
        nodes, hops = _serialize_path(path, reverse=True)
        summary = (
            f"{changed['logical_key']} can affect {affected['logical_key']} through "
            f"{len(path.relationships)} graph hop"
            f"{'s' if len(path.relationships) != 1 else ''}."
        )
        return {
            "repo_id": repo_key,
            "snapshot_id": snapshot_key,
            "changed_target": str(changed["logical_key"]),
            "affected_target": str(affected["logical_key"]),
            "engine": "HydraDB algo.SPpaths",
            "supported": True,
            "summary": summary,
            "nodes": nodes,
            "hops": hops,
        }

    def record_incident(
        self,
        repo_id: str,
        trigger: str,
        description: str,
        impacted: list[str] | None = None,
        severity: str = "medium",
        source: str = "manual",
    ) -> str:
        """Persist change-history evidence so future risk ordering can use it."""

        repo_key, snapshot_key = self._active_snapshot(repo_id)
        description = _text(description, "description", 4_000)
        source = _text(source, "source", 120)
        severity = severity.strip().casefold()
        if severity not in {"low", "medium", "high", "critical"}:
            raise ValueError("severity must be low, medium, high, or critical")
        trigger_record = self._single_target(snapshot_key, trigger)
        impacted_records = [
            self._single_target(snapshot_key, target) for target in (impacted or [])[:20]
        ]
        incident_key = str(uuid.uuid4())
        incident_id = stable_id("incident", incident_key)
        now = datetime.now(UTC).isoformat()
        self.db.execute_write(
            "UNWIND $rows AS row MERGE (incident {id: row.id}) "
            "SET incident:Incident, incident.key = row.key, incident.repo_key = row.repo_key, "
            "incident.description = row.description, incident.severity = row.severity, "
            "incident.recorded_at = row.recorded_at, incident.source = row.source",
            {
                "rows": [
                    {
                        "id": incident_id,
                        "key": incident_key,
                        "repo_key": repo_key,
                        "description": description,
                        "severity": severity,
                        "recorded_at": now,
                        "source": source,
                    }
                ]
            },
        )
        trigger_identity = stable_id("artifact-identity", str(trigger_record["identity_key"]))
        self._merge_incident_edge("TRIGGERED_BY", incident_id, trigger_identity, incident_key)
        for record in impacted_records:
            self._merge_incident_edge(
                "IMPACTED",
                incident_id,
                stable_id("artifact-identity", str(record["identity_key"])),
                incident_key,
            )
        return incident_key

    def repository_status(self, repo_id: str) -> dict[str, object]:
        """Return the active immutable snapshot and its persisted graph counts."""

        repo_key, snapshot_key = self._active_snapshot(repo_id)
        rows = self.db.query(
            "MATCH (snapshot:Snapshot {id: $snapshot_id}) "
            "RETURN snapshot.commit_sha AS commit_sha, snapshot.status AS status, "
            "snapshot.artifact_count AS artifact_count, "
            "snapshot.relationship_count AS relationship_count, "
            "snapshot.unresolved_imports AS unresolved_imports, "
            "snapshot.unresolved_calls AS unresolved_calls, "
            "snapshot.skipped_files AS skipped_files, "
            "snapshot.coverage_recorded AS coverage_recorded, "
            "snapshot.created_at AS created_at",
            {"snapshot_id": stable_id("snapshot", snapshot_key)},
        )
        row = rows[0] if rows else {}
        unresolved_imports = int(row.get("unresolved_imports", 0) or 0)
        unresolved_calls = int(row.get("unresolved_calls", 0) or 0)
        skipped_files = int(row.get("skipped_files", 0) or 0)
        coverage_recorded = bool(row.get("coverage_recorded", False))
        return {
            "repo_id": repo_key,
            "snapshot_id": snapshot_key,
            "commit_sha": str(row.get("commit_sha", "")),
            "status": str(row.get("status", "unknown")),
            "artifact_count": int(row.get("artifact_count", 0) or 0),
            "relationship_count": int(row.get("relationship_count", 0) or 0),
            "unresolved_imports": unresolved_imports,
            "unresolved_calls": unresolved_calls,
            "skipped_files": skipped_files,
            "evidence_complete": coverage_recorded
            and unresolved_imports == 0
            and unresolved_calls == 0
            and skipped_files == 0,
            "created_at": str(row.get("created_at", "")),
        }

    def decision_history(self, repo_id: str, limit: int = 20) -> list[DecisionReceipt]:
        """Return durable agent decision receipts, including every conservative fallback."""

        repo_key = _repo_id(repo_id)
        limit = _bounded(limit, "limit", 1, 100)
        rows = self.db.query(
            "MATCH (receipt:DecisionReceipt)-[:EVALUATED_SNAPSHOT]->(snapshot:Snapshot) "
            "WHERE receipt.repo_key = $repo_key "
            "RETURN receipt.key AS id, receipt.repo_key AS repo_id, "
            "receipt.snapshot_key AS snapshot_id, receipt.analysis_kind AS analysis_kind, "
            "receipt.created_at AS created_at, receipt.decision AS decision, "
            "receipt.evidence_status AS evidence_status, receipt.fallback AS fallback, "
            "receipt.reason AS reason, receipt.targets_json AS targets_json, "
            "receipt.unresolved_targets_json AS unresolved_targets_json, "
            "receipt.supported_impacts AS supported_impacts, "
            "receipt.max_risk_score AS max_risk_score "
            "ORDER BY receipt.created_at DESC LIMIT $limit",
            {"repo_key": repo_key, "limit": limit},
        )
        return [
            {
                "id": str(row.get("id", "")),
                "repo_id": str(row.get("repo_id", repo_key)),
                "snapshot_id": str(row.get("snapshot_id", "")),
                "analysis_kind": str(row.get("analysis_kind", "")),
                "created_at": str(row.get("created_at", "")),
                "decision": _gate_decision(row.get("decision", "review")),
                "evidence_status": _evidence_status(row.get("evidence_status", "incomplete")),
                "fallback": bool(row.get("fallback", False)),
                "reason": str(row.get("reason", "")),
                "targets": _json_string_list(row.get("targets_json", "[]")),
                "unresolved_targets": _json_string_list(row.get("unresolved_targets_json", "[]")),
                "supported_impacts": int(row.get("supported_impacts", 0) or 0),
                "max_risk_score": float(row.get("max_risk_score", 0.0) or 0.0),
            }
            for row in rows
        ]

    def _snapshot_coverage(self, snapshot_key: str) -> dict[str, int | bool]:
        rows = self.db.query(
            "MATCH (snapshot:Snapshot {id: $snapshot_id}) "
            "RETURN snapshot.unresolved_imports AS unresolved_imports, "
            "snapshot.unresolved_calls AS unresolved_calls, "
            "snapshot.skipped_files AS skipped_files, "
            "snapshot.coverage_recorded AS coverage_recorded",
            {"snapshot_id": stable_id("snapshot", snapshot_key)},
        )
        row = rows[0] if rows else {}
        unresolved_imports = int(row.get("unresolved_imports", 0) or 0)
        unresolved_calls = int(row.get("unresolved_calls", 0) or 0)
        skipped_files = int(row.get("skipped_files", 0) or 0)
        recorded = bool(row.get("coverage_recorded", False))
        return {
            "recorded": recorded,
            "complete": recorded
            and unresolved_imports == 0
            and unresolved_calls == 0
            and skipped_files == 0,
            "unresolved_imports": unresolved_imports,
            "unresolved_calls": unresolved_calls,
            "skipped_files": skipped_files,
        }

    def _build_evidence_coverage(
        self,
        *,
        coverage: dict[str, int | bool],
        targets: list[str],
        results: list[ImpactResult],
        unresolved_targets: list[str],
    ) -> EvidenceCoverage:
        complete = bool(coverage["complete"])
        unresolved_imports = int(coverage["unresolved_imports"])
        unresolved_calls = int(coverage["unresolved_calls"])
        skipped_files = int(coverage["skipped_files"])
        status: EvidenceStatus
        if unresolved_targets:
            status = "incomplete"
            fallback = True
            reason = (
                f"{len(unresolved_targets)} change target"
                f"{'s could' if len(unresolved_targets) != 1 else ' could'} not be resolved. "
                "Seismic withheld a safe decision and logged this fallback."
            )
        elif not targets:
            status = "incomplete"
            fallback = True
            reason = (
                "No indexed symbol could be resolved from the supplied change. "
                "Seismic withheld a safe decision and logged this fallback."
            )
        elif not complete:
            status = "incomplete"
            fallback = True
            if not bool(coverage["recorded"]):
                reason = (
                    "The active snapshot predates evidence coverage receipts. "
                    "Re-index before relying on a safe decision."
                )
            else:
                reason = (
                    "The active snapshot contains "
                    f"{unresolved_imports} unresolved import"
                    f"{'s' if unresolved_imports != 1 else ''}, "
                    f"{unresolved_calls} unresolved call"
                    f"{'s' if unresolved_calls != 1 else ''} and "
                    f"{skipped_files} skipped file"
                    f"{'s' if skipped_files != 1 else ''}. "
                    "Seismic withheld a safe decision and logged this fallback."
                )
        elif results:
            status = "supported"
            fallback = False
            reason = (
                f"HydraDB supports {len(results)} downstream impact path"
                f"{'s' if len(results) != 1 else ''}."
            )
        else:
            status = "bounded-empty"
            fallback = False
            reason = (
                "The target resolved in a complete snapshot, but HydraDB found no supported "
                "downstream path within the requested bound."
            )
        return {
            "status": status,
            "complete": complete,
            "fallback": fallback,
            "reason": reason,
            "unresolved_imports": unresolved_imports,
            "unresolved_calls": unresolved_calls,
            "skipped_files": skipped_files,
        }

    def _finalize_analysis(
        self,
        report: ChangeImpactReport,
        analysis_kind: str,
    ) -> ChangeImpactReport:
        report["receipt_id"] = self._record_decision_receipt(report, analysis_kind)
        return report

    def _record_decision_receipt(
        self,
        report: ChangeImpactReport,
        analysis_kind: str,
    ) -> str:
        receipt_key = str(uuid.uuid4())
        receipt_id = stable_id("decision-receipt", receipt_key)
        snapshot_id = stable_id("snapshot", report["snapshot_id"])
        edge_id = relationship_id(
            receipt_key,
            "EVALUATED_SNAPSHOT",
            receipt_id,
            snapshot_id,
        )
        now = datetime.now(UTC).isoformat()
        row = {
            "snapshot_id": snapshot_id,
            "receipt_id": receipt_id,
            "receipt_key": receipt_key,
            "repo_key": report["repo_id"],
            "snapshot_key": report["snapshot_id"],
            "analysis_kind": _text(analysis_kind, "analysis_kind", 60),
            "created_at": now,
            "decision": report["gate"]["decision"],
            "evidence_status": report["evidence"]["status"],
            "fallback": report["evidence"]["fallback"],
            "reason": report["evidence"]["reason"],
            "targets_json": json.dumps(report["targets"], separators=(",", ":")),
            "unresolved_targets_json": json.dumps(
                report["unresolved_targets"], separators=(",", ":")
            ),
            "supported_impacts": report["gate"]["impacted_artifacts"],
            "max_risk_score": report["gate"]["max_risk_score"],
            "edge_id": edge_id,
        }
        self.db.execute_write(
            "UNWIND $rows AS row "
            "MERGE (receipt {id: row.receipt_id}) "
            "SET receipt:DecisionReceipt, receipt.key = row.receipt_key, "
            "receipt.repo_key = row.repo_key, receipt.snapshot_key = row.snapshot_key, "
            "receipt.analysis_kind = row.analysis_kind, receipt.created_at = row.created_at, "
            "receipt.decision = row.decision, "
            "receipt.evidence_status = row.evidence_status, "
            "receipt.fallback = row.fallback, receipt.reason = row.reason, "
            "receipt.targets_json = row.targets_json, "
            "receipt.unresolved_targets_json = row.unresolved_targets_json, "
            "receipt.supported_impacts = row.supported_impacts, "
            "receipt.max_risk_score = row.max_risk_score",
            {"rows": [row]},
        )
        self.db.execute_write(
            "UNWIND $rows AS row "
            "MATCH (receipt:DecisionReceipt {id: row.receipt_id}), "
            "(snapshot:Snapshot {id: row.snapshot_id}) "
            "MERGE (receipt)-[edge:EVALUATED_SNAPSHOT {id: row.edge_id}]->(snapshot)",
            {"rows": [row]},
        )
        rows = self.db.query(
            "MATCH (receipt:DecisionReceipt {id: $receipt_id})"
            "-[:EVALUATED_SNAPSHOT]->(snapshot:Snapshot {id: $snapshot_id}) "
            "RETURN receipt.key AS key",
            {"receipt_id": receipt_id, "snapshot_id": snapshot_id},
        )
        if not rows or str(rows[0].get("key", "")) != receipt_key:
            raise RuntimeError("HydraDB did not confirm the decision receipt")
        return receipt_key

    def _active_snapshot(self, repo_id: str) -> tuple[str, str]:
        clean = _repo_id(repo_id)
        rows = self.db.query(
            "MATCH (repo:Repository {id: $repo_id}) "
            "RETURN repo.key AS key, repo.current_snapshot_key AS snapshot_key",
            {"repo_id": stable_id("repository", clean)},
        )
        if not rows or str(rows[0]["key"]) != clean or not rows[0]["snapshot_key"]:
            raise ValueError(f"repository {clean} has no active Seismic snapshot")
        return clean, str(rows[0]["snapshot_key"])

    def _diff_targets(
        self, snapshot_key: str, changes: list[ChangedFile]
    ) -> tuple[list[str], list[str]]:
        targets: list[str] = []
        warnings: list[str] = []
        for change in changes:
            rows = self.db.query(
                "MATCH (snapshot:Snapshot {id: $snapshot_id})-[:CONTAINS]->"
                "(artifact:Artifact) WHERE artifact.path = $path "
                "RETURN artifact.logical_key AS logical_key, artifact.kind AS kind, "
                "artifact.line_start AS line_start, artifact.line_end AS line_end "
                "ORDER BY artifact.line_start, artifact.line_end",
                {
                    "snapshot_id": stable_id("snapshot", snapshot_key),
                    "path": change.path,
                },
            )
            if not rows:
                warnings.append(f"{change.path} is not present in the active snapshot.")
                continue
            symbols = [
                row
                for row in rows
                if str(row["kind"]) in {"function", "test", "class"}
                and _ranges_overlap(
                    change.ranges,
                    int(row["line_start"] or 0),
                    int(row["line_end"] or 0),
                )
            ]
            selected = symbols or [row for row in rows if str(row["kind"]) == "file"]
            for row in selected:
                logical_key = str(row["logical_key"])
                if logical_key not in targets:
                    targets.append(logical_key)
        if len(targets) > 10:
            warnings.append("The diff resolved more than 10 artifacts; analysis used the first 10.")
        return targets[:10], warnings

    def _resolve_target(self, snapshot_key: str, target: str) -> list[dict[str, object]]:
        clean = _text(target, "target", 500)
        if clean.startswith(f"{snapshot_key}::"):
            exact_rows = self._artifact_by_id(stable_id("artifact", clean), snapshot_key, key=clean)
            if exact_rows:
                return exact_rows
        likely_kinds = (
            ("function", "test", "class", "entrypoint", "file", "package_version")
            if "::" in clean
            else ("file", "function", "test", "class", "entrypoint", "package_version")
        )
        for kind in likely_kinds:
            key = f"{snapshot_key}::{kind}::{clean}"
            exact_rows = self._artifact_by_id(
                stable_id("artifact", key), snapshot_key, logical_key=clean
            )
            if exact_rows:
                return exact_rows
        fallback_rows = self.db.query(
            "MATCH (snapshot:Snapshot {id: $snapshot_id})-[:CONTAINS]->"
            "(artifact:Artifact) WHERE artifact.qualified_name = $target "
            "RETURN artifact.id AS id, artifact.key AS key, "
            "artifact.logical_key AS logical_key, artifact.kind AS kind, "
            "artifact.path AS path, artifact.qualified_name AS qualified_name, "
            "artifact.identity_key AS identity_key "
            "ORDER BY artifact.key LIMIT 6",
            {
                "snapshot_id": stable_id("snapshot", snapshot_key),
                "target": clean,
            },
        )
        return [dict(row) for row in fallback_rows]

    def _artifact_by_id(
        self,
        artifact_id: int,
        snapshot_key: str,
        *,
        logical_key: str | None = None,
        key: str | None = None,
    ) -> list[dict[str, object]]:
        rows = self.db.query(
            "MATCH (artifact:Artifact {id: $artifact_id}) "
            "RETURN artifact.id AS id, artifact.key AS key, "
            "artifact.snapshot_key AS snapshot_key, "
            "artifact.logical_key AS logical_key, artifact.kind AS kind, "
            "artifact.path AS path, artifact.qualified_name AS qualified_name, "
            "artifact.identity_key AS identity_key",
            {"artifact_id": artifact_id},
        )
        matches: list[dict[str, object]] = []
        for row in rows:
            candidate = dict(row)
            if str(candidate["snapshot_key"]) != snapshot_key:
                continue
            if logical_key is not None and str(candidate["logical_key"]) != logical_key:
                continue
            if key is not None and str(candidate["key"]) != key:
                continue
            matches.append(candidate)
        return matches

    def _single_target(self, snapshot_key: str, target: str) -> dict[str, object]:
        rows = self._resolve_target(snapshot_key, target)
        if not rows:
            raise ValueError(f"target {target!r} was not found in the active snapshot")
        if len(rows) != 1:
            alternatives = ", ".join(str(row["logical_key"]) for row in rows)
            raise ValueError(f"target {target!r} is ambiguous: {alternatives}")
        return rows[0]

    def _impact_paths(
        self,
        targets: list[dict[str, object]],
        max_hops: int,
        fetch_limit: int,
    ) -> list[Path]:
        if len(targets) == 1:
            rows = self.db.query(
                """
CALL algo.SSpaths({
  sourceNode: $source_id,
  relTypes: ['PART_OF', 'IMPORTS', 'CALLS', 'TESTS', 'STARTS_AT', 'DEPENDS_ON'],
  relDirection: 'incoming',
  maxLen: $max_hops,
  pathCount: $fetch_limit,
  resultLimit: $fetch_limit
})
YIELD path
RETURN path
""",
                {
                    "source_id": _record_id(targets[0]["id"]),
                    "max_hops": max_hops,
                    "fetch_limit": fetch_limit,
                },
            )
        else:
            # HydraDB requires selector lists to be query literals. Artifact
            # IDs are rendered as digit-only strings, so no user text enters
            # the statement.
            source_values = ", ".join(f"'{_record_id(target['id'])}'" for target in targets)
            rows = self.db.query(
                f"""
CALL algo.MSpaths({{
  sourceLabel: 'Artifact',
  sourceProperty: 'id_text',
  sourceValues: [{source_values}],
  relTypes: ['PART_OF', 'IMPORTS', 'CALLS', 'TESTS', 'STARTS_AT', 'DEPENDS_ON'],
  relDirection: 'incoming',
  maxLen: $max_hops,
  pathCount: $fetch_limit,
  resultLimit: $fetch_limit
}})
YIELD path
RETURN path
""",
                {
                    "max_hops": max_hops,
                    "fetch_limit": fetch_limit,
                },
            )
        return [row["path"] for row in rows if isinstance(row["path"], Path)]

    def _incident_count(self, identity_key: str) -> int:
        if not identity_key:
            return 0
        identity_id = stable_id("artifact-identity", identity_key)
        triggered = self.db.query(
            "MATCH (incident:Incident)-[:TRIGGERED_BY]->"
            "(identity:ArtifactIdentity {id: $identity_id}) "
            "RETURN count(*) AS total",
            {"identity_id": identity_id},
        )
        impacted = self.db.query(
            "MATCH (incident:Incident)-[:IMPACTED]->"
            "(identity:ArtifactIdentity {id: $identity_id}) "
            "RETURN count(*) AS total",
            {"identity_id": identity_id},
        )
        return int(triggered[0]["total"] if triggered else 0) + int(
            impacted[0]["total"] if impacted else 0
        )

    def _incident_pair_count(self, trigger_key: str, impacted_key: str) -> int:
        if not trigger_key or not impacted_key:
            return 0
        rows = self.db.query(
            "MATCH (incident:Incident)-[:TRIGGERED_BY]->"
            "(trigger:ArtifactIdentity {id: $trigger_id}) "
            "MATCH (incident)-[:IMPACTED]->"
            "(impacted:ArtifactIdentity {id: $impacted_id}) "
            "RETURN count(*) AS total",
            {
                "trigger_id": stable_id("artifact-identity", trigger_key),
                "impacted_id": stable_id("artifact-identity", impacted_key),
            },
        )
        return int(rows[0]["total"] if rows else 0)

    def _merge_incident_edge(
        self, kind: str, incident_id: int, identity_id: int, incident_key: str
    ) -> None:
        edge_id = relationship_id(incident_key, kind, incident_id, identity_id)
        query = (
            "UNWIND $rows AS row "
            "MATCH (incident:Incident {id: row.incident_id}), "
            "(identity:ArtifactIdentity {id: row.identity_id}) "
            f"MERGE (incident)-[edge:{kind} {{id: row.edge_id}}]->(identity)"
        )
        self.db.execute_write(
            query,
            {
                "rows": [
                    {
                        "incident_id": incident_id,
                        "identity_id": identity_id,
                        "edge_id": edge_id,
                    }
                ]
            },
        )


def _serialize_path(
    path: Path, *, reverse: bool = False
) -> tuple[list[EvidenceNode], list[EvidenceHop]]:
    raw_nodes = list(path.nodes)
    raw_relationships = list(path.relationships)
    if reverse:
        raw_nodes.reverse()
        raw_relationships.reverse()
    nodes = [_serialize_node(node) for node in raw_nodes]
    hops: list[EvidenceHop] = []
    for index, relationship in enumerate(raw_relationships):
        hops.append(
            {
                "type": relationship.type,
                "source": nodes[index]["logical_key"],
                "target": nodes[index + 1]["logical_key"],
                "evidence_line": int(relationship.get("first_evidence_line", 0) or 0),
                "confidence": float(relationship.get("confidence", 1.0) or 1.0),
            }
        )
    return nodes, hops


def _serialize_node(node: Node) -> EvidenceNode:
    return {
        "key": str(node.get("key", "")),
        "logical_key": str(node.get("logical_key", "")),
        "kind": str(node.get("kind", "")),
        "path": str(node.get("path", "")),
        "qualified_name": str(node.get("qualified_name", "")),
    }


def _native_node_id(node: Node) -> int:
    """Return HydraDB's numeric vertex ID from official-driver hydration."""

    return int(node.element_id)


def _record_id(value: object) -> int:
    """Validate and normalize a numeric ID read from HydraDB."""

    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("HydraDB returned an invalid artifact ID")
    return int(value)


def _ranges_overlap(ranges: tuple[tuple[int, int], ...], start: int, end: int) -> bool:
    if start <= 0 or end < start:
        return False
    return any(range_start <= end and range_end >= start for range_start, range_end in ranges)


def _json_string_list(value: object) -> list[str]:
    """Decode a compact string-list property stored through HydraDB Bolt."""

    if not isinstance(value, str):
        return []
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return [item for item in decoded if isinstance(item, str)]


def _gate_decision(value: object) -> GateDecision:
    if value == "safe" or value == "review" or value == "block":
        return value
    return "review"


def _evidence_status(value: object) -> EvidenceStatus:
    if value == "supported" or value == "bounded-empty" or value == "incomplete":
        return value
    return "incomplete"


def _target_list(values: list[str]) -> list[str]:
    if not values:
        raise ValueError("targets must contain at least one file or symbol")
    if len(values) > 10:
        raise ValueError("targets may contain at most 10 files or symbols")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = _text(value, "target", 500)
        if clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def _repo_id(value: str) -> str:
    clean = _text(value, "repo_id", 120).casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", clean):
        raise ValueError("repo_id may contain lowercase letters, numbers, '.', '_', and '-'")
    return clean


def _text(value: str, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    clean = value.strip()
    if not clean:
        raise ValueError(f"{field} must not be empty")
    if len(clean) > maximum:
        raise ValueError(f"{field} must be at most {maximum} characters")
    return clean


def _bounded(value: int, field: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return value


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN.findall(value)
        if token.casefold() not in _STOPWORDS and len(token) > 1
    }
