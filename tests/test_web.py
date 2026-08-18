"""Fast API contract tests for the dashboard backend."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from seismic.web import create_app


class FakeDB:
    """Minimal healthy database double used only by the health endpoint."""

    def verify_connection(self) -> None:
        return None


class FakeService:
    """Deterministic service double that records web endpoint inputs."""

    def __init__(self) -> None:
        self.db = FakeDB()
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def index_repository(self, repo_path: str, repo_id: str | None = None) -> dict[str, Any]:
        self.calls.append(("index", (repo_path, repo_id)))
        return {
            "repo_id": repo_id or "demo",
            "snapshot_id": "demo@abc123",
            "commit_sha": "abc123",
            "files": 3,
            "artifacts": 8,
            "packages": 1,
            "relationships": 9,
            "unresolved_imports": 0,
            "unresolved_calls": 1,
            "skipped_files": 0,
            "duration_ms": 12.5,
            "activated": True,
            "warnings": [],
        }

    def analyze_change(
        self, repo_id: str, targets: list[str], max_hops: int, limit: int
    ) -> dict[str, Any]:
        self.calls.append(("analyze", (repo_id, targets, max_hops, limit)))
        return {
            "repo_id": repo_id,
            "snapshot_id": f"{repo_id}@abc123",
            "targets": targets,
            "engine": "HydraDB algo.SSpaths",
            "gate": _gate(),
            "results": [],
            "unresolved_targets": [],
            "warnings": [],
        }

    def analyze_diff(self, repo_id: str, diff: str, max_hops: int, limit: int) -> dict[str, Any]:
        self.calls.append(("diff", (repo_id, diff, max_hops, limit)))
        return {
            "repo_id": repo_id,
            "snapshot_id": f"{repo_id}@abc123",
            "targets": ["src/a.py::run"],
            "diff_files": ["src/a.py"],
            "engine": "HydraDB algo.SSpaths",
            "gate": _gate(),
            "results": [],
            "unresolved_targets": [],
            "warnings": [],
        }

    def repository_status(self, repo_id: str) -> dict[str, Any]:
        if repo_id == "missing":
            raise ValueError("repository missing has no active Seismic snapshot")
        return {
            "repo_id": repo_id,
            "snapshot_id": f"{repo_id}@abc123",
            "commit_sha": "abc123",
            "status": "ready",
            "artifact_count": 8,
            "relationship_count": 9,
            "created_at": "2026-08-17T00:00:00+00:00",
        }


def _gate() -> dict[str, Any]:
    return {
        "policy": "seismic-change-gate-v1",
        "decision": "review",
        "headline": "Review graph evidence before editing",
        "summary": "Inspect exact paths before changing code.",
        "max_risk_score": 0.0,
        "impacted_artifacts": 0,
        "required_tests": [],
        "verification_commands": [],
        "affected_entrypoints": [],
        "affected_owners": [],
        "reasons": [],
    }


def test_health_index_analyze_and_status_contracts() -> None:
    service = FakeService()
    with TestClient(create_app(service)) as client:  # type: ignore[arg-type]
        health = client.get("/api/health")
        indexed = client.post("/api/index", json={"repo_path": "/safe/repo", "repo_id": "demo"})
        analyzed = client.post(
            "/api/analyze",
            json={"repo_id": "demo", "targets": ["src/a.py::run"], "max_hops": 3},
        )
        diffed = client.post(
            "/api/analyze-diff",
            json={"repo_id": "demo", "diff": "--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@"},
        )
        status = client.get("/api/repositories/demo")

    assert health.status_code == 200
    assert health.json()["backend"] == "HydraDB"
    assert indexed.json()["activated"] is True
    assert analyzed.json()["engine"] == "HydraDB algo.SSpaths"
    assert diffed.json()["diff_files"] == ["src/a.py"]
    assert diffed.json()["gate"]["decision"] == "review"
    assert status.json()["artifact_count"] == 8
    assert service.calls == [
        ("index", ("/safe/repo", "demo")),
        ("analyze", ("demo", ["src/a.py::run"], 3, 30)),
        ("diff", ("demo", "--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@", 4, 30)),
    ]


def test_dashboard_returns_clear_validation_and_service_errors() -> None:
    service = FakeService()
    with TestClient(create_app(service)) as client:  # type: ignore[arg-type]
        invalid = client.post("/api/analyze", json={"repo_id": "demo", "targets": []})
        missing = client.get("/api/repositories/missing")

    assert invalid.status_code == 422
    assert missing.status_code == 400
    assert "no active Seismic snapshot" in missing.json()["detail"]
