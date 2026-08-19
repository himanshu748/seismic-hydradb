"""Validated immutable snapshot writes for parsed repository graphs."""

from __future__ import annotations

import fcntl
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from seismic.db import HydraDB
from seismic.identity import relationship_id, stable_id
from seismic.models import ArtifactRecord, IngestSummary, RelationshipRecord, RepositoryGraph

_UPSERT_REPOSITORY = """
UNWIND $rows AS row
MERGE (repo {id: row.id})
SET repo:Repository, repo.key = row.key, repo.root_name = row.root_name,
    repo.created_at = row.created_at, repo.updated_at = row.updated_at
"""

_UPSERT_SNAPSHOT = """
UNWIND $rows AS row
MERGE (snapshot {id: row.id})
SET snapshot:Snapshot, snapshot.key = row.key, snapshot.repo_key = row.repo_key,
    snapshot.commit_sha = row.commit_sha, snapshot.created_at = row.created_at,
    snapshot.status = row.status
"""

_UPSERT_IDENTITIES = """
UNWIND $rows AS row
MERGE (identity {id: row.id})
SET identity:ArtifactIdentity, identity.key = row.key, identity.repo_key = row.repo_key,
    identity.logical_key = row.logical_key, identity.kind = row.kind
"""

_UPSERT_ARTIFACTS = """
UNWIND $rows AS row
MERGE (artifact {id: row.id})
SET artifact:Artifact, artifact.key = row.key, artifact.repo_key = row.repo_key,
    artifact.id_text = row.id_text,
    artifact.snapshot_key = row.snapshot_key, artifact.logical_key = row.logical_key,
    artifact.identity_key = row.identity_key,
    artifact.kind = row.kind, artifact.path = row.path,
    artifact.qualified_name = row.qualified_name, artifact.language = row.language,
    artifact.line_start = row.line_start, artifact.line_end = row.line_end,
    artifact.content_hash = row.content_hash, artifact.last_author = row.last_author,
    artifact.last_modified = row.last_modified, artifact.owner = row.owner,
    artifact.owner_source = row.owner_source,
    artifact.resolution_confidence = row.resolution_confidence, artifact.text = row.text
"""

_UPSERT_GRAPH_EDGE = """
UNWIND $rows AS row
MATCH (source:Artifact {id: row.source_id}), (target:Artifact {id: row.target_id})
MERGE (source)-[edge:%s {id: row.id}]->(target)
SET edge.confidence = row.confidence, edge.evidence_count = row.evidence_count,
    edge.first_evidence_line = row.first_evidence_line, edge.source = row.source,
    edge.requirement = row.requirement
"""


class SnapshotWriter:
    """Persist and activate complete repository snapshots with a final pointer flip."""

    def __init__(self, db: HydraDB, batch_size: int = 500) -> None:
        self.db = db
        self.batch_size = batch_size

    def write(
        self,
        graph: RepositoryGraph,
        duration_ms: float,
        *,
        activation_started_at: str | None = None,
    ) -> IngestSummary:
        """Repair or create one snapshot, validate it, then make it current."""

        now = datetime.now(UTC).isoformat()
        activation_started_at = activation_started_at or now
        repo_id = stable_id("repository", graph.repo_key)
        snapshot_id = stable_id("snapshot", graph.snapshot_key)
        self.db.execute_write(
            _UPSERT_REPOSITORY,
            {
                "rows": [
                    {
                        "id": repo_id,
                        "key": graph.repo_key,
                        "root_name": graph.root_name,
                        "created_at": now,
                        "updated_at": now,
                    }
                ]
            },
        )
        self.db.execute_write(
            _UPSERT_SNAPSHOT,
            {
                "rows": [
                    {
                        "id": snapshot_id,
                        "key": graph.snapshot_key,
                        "repo_key": graph.repo_key,
                        "commit_sha": graph.commit_sha,
                        "created_at": now,
                        "status": "building",
                    }
                ]
            },
        )
        self._merge_simple_relationship(
            "HAS_SNAPSHOT",
            repo_id,
            snapshot_id,
            relationship_id(graph.snapshot_key, "HAS_SNAPSHOT", repo_id, snapshot_id),
            "Repository",
            "Snapshot",
        )
        identity_rows = {
            artifact.identity_id: {
                "id": artifact.identity_id,
                "key": artifact.identity_key,
                "repo_key": artifact.repo_key,
                "logical_key": artifact.logical_key,
                "kind": artifact.kind,
            }
            for artifact in graph.artifacts
        }
        for identity_batch in _batches(list(identity_rows.values()), self.batch_size):
            self.db.execute_write(_UPSERT_IDENTITIES, {"rows": identity_batch})
        for artifact_batch in _batches(
            [_artifact_row(value) for value in graph.artifacts], self.batch_size
        ):
            self.db.execute_write(_UPSERT_ARTIFACTS, {"rows": artifact_batch})
        contains_rows = [
            {
                "source_id": snapshot_id,
                "target_id": artifact.id,
                "id": relationship_id(graph.snapshot_key, "CONTAINS", snapshot_id, artifact.id),
            }
            for artifact in graph.artifacts
        ]
        instance_rows = [
            {
                "source_id": artifact.id,
                "target_id": artifact.identity_id,
                "id": relationship_id(
                    graph.snapshot_key, "INSTANCE_OF", artifact.id, artifact.identity_id
                ),
            }
            for artifact in graph.artifacts
        ]
        self._merge_relationship_batches("CONTAINS", "Snapshot", "Artifact", contains_rows)
        self._merge_relationship_batches(
            "INSTANCE_OF", "Artifact", "ArtifactIdentity", instance_rows
        )
        by_kind: dict[str, list[RelationshipRecord]] = {}
        for edge in graph.relationships:
            by_kind.setdefault(edge.kind, []).append(edge)
        for kind, edges in sorted(by_kind.items()):
            for relationship_batch in _batches(
                [_relationship_row(edge) for edge in edges], self.batch_size
            ):
                self.db.execute_write(_UPSERT_GRAPH_EDGE % kind, {"rows": relationship_batch})
        self._validate(graph)
        self.db.execute_write(
            "MATCH (snapshot:Snapshot) WHERE snapshot.id = $snapshot_id "
            "SET snapshot.status = $status, snapshot.artifact_count = $artifact_count, "
            "snapshot.relationship_count = $relationship_count, "
            "snapshot.unresolved_imports = $unresolved_imports, "
            "snapshot.unresolved_calls = $unresolved_calls, "
            "snapshot.skipped_files = $skipped_files, "
            "snapshot.coverage_recorded = $coverage_recorded",
            {
                "snapshot_id": snapshot_id,
                "status": "ready",
                "artifact_count": len(graph.artifacts),
                "relationship_count": len(graph.relationships),
                "unresolved_imports": graph.unresolved_imports,
                "unresolved_calls": graph.unresolved_calls,
                "skipped_files": graph.skipped_files,
                "coverage_recorded": True,
            },
        )
        activated = self._activate_snapshot(
            repo_id,
            graph.snapshot_key,
            now,
            activation_started_at,
        )
        return {
            "repo_id": graph.repo_key,
            "snapshot_id": graph.snapshot_key,
            "commit_sha": graph.commit_sha,
            "files": sum(artifact.kind == "file" for artifact in graph.artifacts),
            "artifacts": len(graph.artifacts),
            "packages": sum(artifact.kind == "package_version" for artifact in graph.artifacts),
            "relationships": len(graph.relationships),
            "unresolved_imports": graph.unresolved_imports,
            "unresolved_calls": graph.unresolved_calls,
            "skipped_files": graph.skipped_files,
            "duration_ms": round(duration_ms, 3),
            "activated": activated,
            "warnings": graph.warnings,
        }

    def _validate(self, graph: RepositoryGraph) -> None:
        rows = self.db.query(
            "MATCH (artifact:Artifact) WHERE artifact.snapshot_key = $snapshot_key "
            "RETURN count(*) AS total",
            {"snapshot_key": graph.snapshot_key},
        )
        actual = int(rows[0]["total"]) if rows else 0
        if actual != len(graph.artifacts):
            raise RuntimeError(
                "snapshot validation failed: expected "
                f"{len(graph.artifacts)} artifacts, found {actual}"
            )
        self._validate_relationships(graph)
        for edge in graph.relationships:
            if edge.source_id == edge.target_id:
                raise RuntimeError("snapshot validation failed: self relationship escaped parser")

    def _validate_relationships(self, graph: RepositoryGraph) -> None:
        expected_by_type: dict[str, set[tuple[int, int]]] = {}
        for edge in graph.relationships:
            expected_by_type.setdefault(edge.kind, set()).add((edge.source_id, edge.target_id))
        source_rows = [{"source_id": artifact.id} for artifact in graph.artifacts]
        actual_by_type: dict[str, set[tuple[int, int]]] = {}
        for relationship_type in sorted(expected_by_type):
            actual: set[tuple[int, int]] = set()
            for batch in _batches(source_rows, self.batch_size):
                rows = self.db.query(
                    "UNWIND $rows AS row "
                    f"MATCH (source {{id: row.source_id}})-[:{relationship_type}]->(target) "
                    "RETURN row.source_id AS source_id, target.id AS target_id",
                    {"rows": batch},
                )
                actual.update((int(row["source_id"]), int(row["target_id"])) for row in rows)
            actual_by_type[relationship_type] = actual
        if actual_by_type != expected_by_type:
            expected_count = sum(len(edges) for edges in expected_by_type.values())
            actual_count = sum(len(edges) for edges in actual_by_type.values())
            raise RuntimeError(
                "snapshot validation failed: expected "
                f"{expected_count} relationships, found {actual_count}"
            )

    def _activate_snapshot(
        self,
        repo_id: int,
        snapshot_key: str,
        updated_at: str,
        activation_started_at: str,
    ) -> bool:
        rows = self.db.query(
            "MATCH (repo:Repository) WHERE repo.id = $repo_id "
            "RETURN repo.current_activation_started_at AS current_activation_started_at",
            {"repo_id": repo_id},
        )
        current = str(rows[0].get("current_activation_started_at", "") or "") if rows else ""
        if current and current > activation_started_at:
            return False
        self.db.execute_write(
            "MATCH (repo:Repository) WHERE repo.id = $repo_id "
            "SET repo.current_snapshot_key = $snapshot_key, repo.updated_at = $updated_at, "
            "repo.current_activation_started_at = $activation_started_at",
            {
                "repo_id": repo_id,
                "snapshot_key": snapshot_key,
                "updated_at": updated_at,
                "activation_started_at": activation_started_at,
            },
        )
        return True

    def _merge_simple_relationship(
        self,
        kind: str,
        source_id: int,
        target_id: int,
        edge_id: int,
        source_label: str,
        target_label: str,
    ) -> None:
        query = (
            f"UNWIND $rows AS row MATCH (source:{source_label} {{id: row.source_id}}), "
            f"(target:{target_label} {{id: row.target_id}}) "
            f"MERGE (source)-[edge:{kind} {{id: row.id}}]->(target)"
        )
        self.db.execute_write(
            query,
            {"rows": [{"source_id": source_id, "target_id": target_id, "id": edge_id}]},
        )

    def _merge_relationship_batches(
        self,
        kind: str,
        source_label: str,
        target_label: str,
        rows: list[dict[str, int]],
    ) -> None:
        query = (
            f"UNWIND $rows AS row MATCH (source:{source_label} {{id: row.source_id}}), "
            f"(target:{target_label} {{id: row.target_id}}) "
            f"MERGE (source)-[edge:{kind} {{id: row.id}}]->(target)"
        )
        for batch in _batches(rows, self.batch_size):
            self.db.execute_write(query, {"rows": batch})


def _artifact_row(artifact: ArtifactRecord) -> dict[str, object]:
    return {
        "id": artifact.id,
        "id_text": str(artifact.id),
        "key": artifact.key,
        "repo_key": artifact.repo_key,
        "snapshot_key": artifact.snapshot_key,
        "logical_key": artifact.logical_key,
        "identity_key": artifact.identity_key,
        "kind": artifact.kind,
        "path": artifact.path,
        "qualified_name": artifact.qualified_name,
        "language": artifact.language,
        "line_start": artifact.line_start,
        "line_end": artifact.line_end,
        "content_hash": artifact.content_hash,
        "last_author": artifact.last_author,
        "last_modified": artifact.last_modified,
        "owner": artifact.owner,
        "owner_source": artifact.owner_source,
        "resolution_confidence": artifact.resolution_confidence,
        "text": artifact.text,
    }


def _relationship_row(edge: RelationshipRecord) -> dict[str, object]:
    return {
        "id": edge.id,
        "source_id": edge.source_id,
        "target_id": edge.target_id,
        "confidence": edge.confidence,
        "evidence_count": edge.evidence_count,
        "first_evidence_line": edge.first_evidence_line,
        "source": edge.source,
        "requirement": edge.requirement,
    }


T = TypeVar("T")


@contextmanager
def repository_index_lock(repo_key: str) -> Iterator[None]:
    """Serialize local writers for one repository across Seismic processes."""

    lock_root = Path(tempfile.gettempdir()) / "seismic-index-locks"
    lock_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = lock_root / f"{stable_id('repository-index-lock', repo_key)}.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _batches(values: list[T], size: int) -> list[list[T]]:
    return [values[index : index + size] for index in range(0, len(values), size)]
