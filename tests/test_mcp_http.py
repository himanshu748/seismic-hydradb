"""Live checks for Seismic's sessionless Streamable HTTP transport."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import anyio
import pytest
from mcp import Client

from seismic.config import SeismicConfig
from seismic.db import HydraDB

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "http-fixture"
    shutil.copytree(FIXTURE, repo)
    _git("init", "-b", "main", cwd=repo)
    _git("config", "user.email", "seismic@example.test", cwd=repo)
    _git("config", "user.name", "Seismic Test", cwd=repo)
    _git("add", ".", cwd=repo)
    _git("commit", "-m", "fixture", cwd=repo)
    return repo


def test_fresh_http_clients_share_only_durable_hydradb_graph(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    repo_id = f"seismic-http-{uuid.uuid4().hex[:12]}"

    async def exercise(url: str) -> None:
        async with Client(url) as first:
            assert first.protocol_version == "2026-07-28"
            indexed = await first.call_tool(
                "index_repository", {"repo_path": str(repo), "repo_id": repo_id}
            )
            assert not indexed.is_error
            assert indexed.structured_content is not None
            snapshot_id = str(indexed.structured_content["snapshot_id"])

        async with Client(url) as fresh:
            assert fresh.protocol_version == "2026-07-28"
            report = await fresh.call_tool(
                "analyze_change",
                {
                    "repo_id": repo_id,
                    "targets": ["src/sample_app/pricing.py::calculate"],
                    "max_hops": 4,
                },
            )
            assert not report.is_error
            assert report.structured_content is not None
            assert report.structured_content["snapshot_id"] == snapshot_id
            assert "tests/test_checkout.py::test_total" in {
                result["logical_key"] for result in report.structured_content["results"]
            }

    try:
        with _running_server(tmp_path) as url:
            anyio.run(exercise, url)
    finally:
        config = SeismicConfig.from_env()
        with HydraDB(config) as db:
            for label in ("Artifact", "ArtifactIdentity", "Snapshot", "Incident"):
                db.execute_write(
                    f"MATCH (node:{label}) WHERE node.repo_key = $repo_key DETACH DELETE node",
                    {"repo_key": repo_id},
                )
            db.execute_write(
                "MATCH (node:Repository) WHERE node.key = $repo_key DETACH DELETE node",
                {"repo_key": repo_id},
            )


@contextmanager
def _running_server(allowed_root: Path) -> Iterator[str]:
    port = _unused_port()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    env["SEISMIC_ALLOWED_ROOTS"] = str(allowed_root)
    env["SEISMIC_MCP_HOST"] = "127.0.0.1"
    env["SEISMIC_MCP_PORT"] = str(port)
    process = subprocess.Popen(
        [sys.executable, "-c", "from seismic.server import http_main; http_main()"],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_until_listening(process, port)
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _wait_until_listening(process: subprocess.Popen[str], port: int) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stderr = process.stderr.read() if process.stderr is not None else ""
            raise AssertionError(f"stateless MCP server exited early: {stderr}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("stateless MCP server did not start within 10 seconds")
