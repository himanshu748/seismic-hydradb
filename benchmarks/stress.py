"""Generate and verify a 5,000-node, 20,000-edge HydraDB code graph."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any

from seismic.config import SeismicConfig
from seismic.db import HydraDB
from seismic.identity import relationship_id, stable_id
from seismic.ingest import SnapshotWriter
from seismic.models import ArtifactRecord, RelationshipRecord, RepositoryGraph
from seismic.tools import SeismicService

PROJECT_ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = Path(__file__).parent / "results" / "stress.json"
REPO_ID = "seismic-stress-v1"
SNAPSHOT_KEY = f"{REPO_ID}@synthetic-v1"


def main() -> None:
    """Write the deterministic graph, assert target recovery and save raw evidence."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--queries", type=int, default=25)
    arguments = parser.parse_args()
    if not 5 <= arguments.queries <= 200:
        raise SystemExit("--queries must be between 5 and 200")
    result = run_stress(arguments.queries)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


def run_stress(query_count: int) -> dict[str, Any]:
    """Exercise exact ingestion and retrieval on the required synthetic graph size."""

    graph_started = time.perf_counter()
    graph = _graph()
    generation_ms = (time.perf_counter() - graph_started) * 1_000
    config = SeismicConfig.from_env()
    with HydraDB(config) as db:
        db.verify_connection()
        db.setup_schema()
        writer = SnapshotWriter(db)
        ingest_started = time.perf_counter()
        summary = writer.write(graph, generation_ms)
        ingest_seconds = time.perf_counter() - ingest_started
        service = SeismicService(db, config)
        changed = "stress/node_04998.py::run"
        expected = "stress/node_04999.py::run"
        latencies: list[float] = []
        verified = 0
        for _ in range(query_count):
            started = time.perf_counter()
            report = service.analyze_change(REPO_ID, [changed], max_hops=2, limit=10)
            latencies.append((time.perf_counter() - started) * 1_000)
            keys = {result["logical_key"] for result in report["results"]}
            if expected not in keys:
                raise RuntimeError(f"stress query did not recover exact target {expected}")
            verified += 1

    return {
        "kind": "local deterministic stress proof",
        "generated_at": datetime.now(UTC).isoformat(),
        "commit": _git_commit(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "hydradb_uri": config.uri,
        },
        "configuration": {
            "artifacts": len(graph.artifacts),
            "relationships": len(graph.relationships),
            "query_count": query_count,
            "changed_target": changed,
            "required_result": expected,
        },
        "summary": {
            "artifacts_written": summary["artifacts"],
            "relationships_written": summary["relationships"],
            "ingest_seconds": round(ingest_seconds, 3),
            "artifact_throughput_per_second": round(len(graph.artifacts) / ingest_seconds, 3),
            "relationship_throughput_per_second": round(
                len(graph.relationships) / ingest_seconds, 3
            ),
            "exact_queries_verified": verified,
            "query_latency_p50_ms": round(median(latencies), 3),
            "query_latency_p95_ms": round(_percentile(latencies, 0.95), 3),
        },
    }


def _graph() -> RepositoryGraph:
    artifacts: list[ArtifactRecord] = []
    for index in range(5_000):
        logical_key = f"stress/node_{index:05d}.py::run"
        identity_key = f"{REPO_ID}::function::{logical_key}"
        key = f"{SNAPSHOT_KEY}::function::{logical_key}"
        artifacts.append(
            ArtifactRecord(
                id=stable_id("artifact", key),
                key=key,
                identity_id=stable_id("artifact-identity", identity_key),
                identity_key=identity_key,
                repo_key=REPO_ID,
                snapshot_key=SNAPSHOT_KEY,
                logical_key=logical_key,
                kind="function",
                path=f"stress/node_{index:05d}.py",
                qualified_name="run",
                language="python",
                line_start=1,
                line_end=2,
                content_hash=f"synthetic-{index:05d}",
                resolution_confidence=1.0,
                text=f"def run(): return node_{max(0, index - 1):05d}",
            )
        )
    relationships: list[RelationshipRecord] = []
    for index in range(1, 5_000):
        for offset in (1, 2, 4, 8):
            if index < offset:
                continue
            _append_edge(relationships, artifacts[index], artifacts[index - offset])
    for index in range(16, 31):
        _append_edge(relationships, artifacts[index], artifacts[index - 16])
    if len(relationships) != 20_000:
        raise AssertionError(f"synthetic graph has {len(relationships)} relationships")
    return RepositoryGraph(
        repo_key=REPO_ID,
        snapshot_key=SNAPSHOT_KEY,
        commit_sha="synthetic-v1",
        root_name="seismic-stress",
        artifacts=artifacts,
        relationships=relationships,
    )


def _append_edge(
    relationships: list[RelationshipRecord],
    source: ArtifactRecord,
    target: ArtifactRecord,
) -> None:
    relationships.append(
        RelationshipRecord(
            id=relationship_id(SNAPSHOT_KEY, "CALLS", source.id, target.id),
            kind="CALLS",
            source_id=source.id,
            target_id=target.id,
            confidence=1.0,
            evidence_count=1,
            first_evidence_line=1,
            source="synthetic",
        )
    )


def _percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(len(ordered) - 1, lower + 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


if __name__ == "__main__":
    main()
