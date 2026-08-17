"""End-to-end checks through the official MCP stdio client transport."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import anyio
import pytest
from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

from seismic.config import SeismicConfig
from seismic.db import HydraDB
from tests.support import cleanup_repository

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "mcp-fixture"
    shutil.copytree(FIXTURE, repo)
    _git("init", "-b", "main", cwd=repo)
    _git("config", "user.email", "seismic@example.test", cwd=repo)
    _git("config", "user.name", "Seismic Test", cwd=repo)
    _git("add", ".", cwd=repo)
    _git("commit", "-m", "fixture", cwd=repo)
    return repo


def _parameters(tmp_path: Path) -> StdioServerParameters:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    env["SEISMIC_ALLOWED_ROOTS"] = str(tmp_path)
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "seismic"],
        env=env,
        cwd=str(PROJECT_ROOT),
    )


def test_fresh_mcp_process_analyzes_graph_indexed_by_prior_process(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    repo_id = f"seismic-mcp-{uuid.uuid4().hex[:12]}"
    parameters = _parameters(tmp_path)

    async def index_in_first_process() -> str:
        async with Client(stdio_client(parameters)) as client:
            assert client.protocol_version == "2026-07-28"
            tools = {tool.name for tool in (await client.list_tools()).tools}
            assert tools == {
                "index_repository",
                "analyze_change",
                "analyze_diff",
                "retrieve_context",
                "explain_impact",
                "record_incident",
                "repository_status",
            }
            indexed = await client.call_tool(
                "index_repository",
                {"repo_path": str(repo), "repo_id": repo_id},
            )
            assert not indexed.is_error
            assert indexed.structured_content is not None
            assert indexed.structured_content["activated"] is True
            return str(indexed.structured_content["snapshot_id"])

    async def analyze_in_fresh_process(snapshot_id: str) -> None:
        async with Client(stdio_client(parameters)) as client:
            assert client.protocol_version == "2026-07-28"
            report = await client.call_tool(
                "analyze_change",
                {
                    "repo_id": repo_id,
                    "targets": ["src/sample_app/pricing.py::calculate"],
                    "max_hops": 4,
                    "limit": 20,
                },
            )
            assert not report.is_error
            assert report.structured_content is not None
            assert report.structured_content["snapshot_id"] == snapshot_id
            results = report.structured_content["results"]
            assert isinstance(results, list)
            result_keys = {str(result["logical_key"]) for result in results}
            assert "src/sample_app/service.py::handler" in result_keys
            assert "tests/test_checkout.py::test_total" in result_keys
            assert all(result["hops"] for result in results)

            diffed = await client.call_tool(
                "analyze_diff",
                {
                    "repo_id": repo_id,
                    "diff": (
                        "--- a/src/sample_app/pricing.py\n"
                        "+++ b/src/sample_app/pricing.py\n"
                        "@@ -7 +7 @@\n"
                    ),
                },
            )
            assert not diffed.is_error
            assert diffed.structured_content is not None
            assert diffed.structured_content["targets"] == ["src/sample_app/pricing.py::calculate"]

    try:
        snapshot_id = anyio.run(index_in_first_process)
        anyio.run(analyze_in_fresh_process, snapshot_id)
    finally:
        config = SeismicConfig.from_env()
        with HydraDB(config) as db:
            cleanup_repository(db, repo_id)
