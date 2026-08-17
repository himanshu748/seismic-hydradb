"""Live HydraDB integration tests for immutable indexing and native path evidence."""

from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from seismic.config import SeismicConfig
from seismic.db import HydraDB
from seismic.tools import SeismicService

FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "integration-repo"
    shutil.copytree(FIXTURE, repo)
    _git("init", "-b", "main", cwd=repo)
    _git("config", "user.email", "seismic@example.test", cwd=repo)
    _git("config", "user.name", "Seismic Test", cwd=repo)
    _git("add", ".", cwd=repo)
    _git("commit", "-m", "fixture", cwd=repo)
    return repo


@pytest.mark.integration
def test_index_analyze_explain_incident_and_reindex(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    repo_id = f"seismic-integration-{uuid.uuid4().hex[:12]}"
    environment = SeismicConfig.from_env()
    config = SeismicConfig(
        uri=environment.uri,
        username=environment.username,
        token=environment.token,
        database=environment.database,
        allowed_roots=(tmp_path.resolve(),),
    )
    with HydraDB(config) as db:
        db.verify_connection()
        db.setup_schema()
        service = SeismicService(db, config)

        first = service.index_repository(str(repo), repo_id=repo_id)
        repeated = service.index_repository(str(repo), repo_id=repo_id)
        report = service.analyze_change(
            repo_id,
            ["src/sample_app/pricing.py::calculate"],
            max_hops=4,
            limit=20,
        )

        assert first["activated"] is True
        assert repeated["snapshot_id"] == first["snapshot_id"]
        assert repeated["artifacts"] == first["artifacts"]
        result_keys = {result["logical_key"] for result in report["results"]}
        assert "src/sample_app/checkout.py::total" in result_keys
        assert "src/sample_app/service.py::handler" in result_keys
        assert "tests/test_checkout.py::test_total" in result_keys
        assert "pyproject.toml::script::sample" in result_keys
        assert report["engine"] == "HydraDB algo.SSpaths"

        diff_report = service.analyze_diff(
            repo_id,
            """diff --git a/src/sample_app/pricing.py b/src/sample_app/pricing.py
--- a/src/sample_app/pricing.py
+++ b/src/sample_app/pricing.py
@@ -7 +7 @@
-    return subtotal * 1.1
+    return subtotal * 1.2
""",
        )
        assert diff_report["targets"] == ["src/sample_app/pricing.py::calculate"]
        assert "tests/test_checkout.py::test_total" in {
            result["logical_key"] for result in diff_report["results"]
        }

        multi_target = service.analyze_change(
            repo_id,
            [
                "src/sample_app/pricing.py::calculate",
                "src/sample_app/checkout.py::total",
            ],
            max_hops=4,
            limit=20,
        )
        assert multi_target["engine"] == "HydraDB algo.MSpaths"
        assert "src/sample_app/service.py::handler" in {
            result["logical_key"] for result in multi_target["results"]
        }

        missing = service.analyze_change(
            repo_id,
            ["src/sample_app/pricing.py::not_real"],
        )
        assert missing["results"] == []
        assert missing["unresolved_targets"] == ["src/sample_app/pricing.py::not_real"]

        explanation = service.explain_impact(
            repo_id,
            "src/sample_app/pricing.py::calculate",
            "src/sample_app/service.py::handler",
        )
        assert explanation["supported"] is True
        assert [hop["type"] for hop in explanation["hops"]] == ["CALLS", "CALLS"]

        incident_id = service.record_incident(
            repo_id,
            "src/sample_app/pricing.py::calculate",
            "A pricing change broke the service response.",
            impacted=["src/sample_app/service.py::handler"],
            severity="high",
        )
        after_incident = service.analyze_change(
            repo_id,
            ["src/sample_app/pricing.py::calculate"],
            max_hops=4,
            limit=20,
        )
        service_result = next(
            result
            for result in after_incident["results"]
            if result["logical_key"] == "src/sample_app/service.py::handler"
        )
        assert incident_id
        assert service_result["incident_pair_count"] == 1
        assert service_result["score_components"]["incident_pair"] == 0.5

        pricing = repo / "src" / "sample_app" / "pricing.py"
        pricing.write_text(pricing.read_text() + "\n# New snapshot.\n", encoding="utf-8")
        _git("add", ".", cwd=repo)
        _git("commit", "-m", "new pricing snapshot", cwd=repo)
        new_snapshot = service.index_repository(str(repo), repo_id=repo_id)
        after_reindex = service.analyze_change(
            repo_id,
            ["src/sample_app/pricing.py::calculate"],
            max_hops=4,
            limit=20,
        )
        reindexed_service_result = next(
            result
            for result in after_reindex["results"]
            if result["logical_key"] == "src/sample_app/service.py::handler"
        )
        assert new_snapshot["snapshot_id"] != first["snapshot_id"]
        assert reindexed_service_result["incident_pair_count"] == 1

        unsupported = service.explain_impact(
            repo_id,
            "tests/test_checkout.py::test_total",
            "src/sample_app/pricing.py::calculate",
        )
        assert unsupported["supported"] is False
        assert unsupported["nodes"] == []
