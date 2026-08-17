"""Fast checks for Seismic's public MCP contract and stateless HTTP settings."""

from __future__ import annotations

import anyio
import pytest

from seismic.server import http_main, mcp


def test_server_registers_documented_tools_with_descriptions() -> None:
    tools = anyio.run(mcp.list_tools)
    by_name = {tool.name: tool for tool in tools}

    assert set(by_name) == {
        "index_repository",
        "analyze_change",
        "retrieve_context",
        "explain_impact",
        "record_incident",
        "repository_status",
    }
    assert all(tool.description for tool in by_name.values())
    assert by_name["index_repository"].input_schema["required"] == ["repo_path"]
    assert by_name["analyze_change"].input_schema["required"] == ["repo_id", "targets"]
    assert by_name["explain_impact"].input_schema["required"] == [
        "repo_id",
        "changed_target",
        "affected_target",
    ]


def test_http_entrypoint_forces_stateless_json_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def capture_run(*, transport: str, **kwargs: object) -> None:
        captured["transport"] = transport
        captured.update(kwargs)

    monkeypatch.setattr(mcp, "run", capture_run)
    monkeypatch.setenv("SEISMIC_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("SEISMIC_MCP_PORT", "9877")

    http_main()

    assert captured == {
        "transport": "streamable-http",
        "host": "127.0.0.1",
        "port": 9877,
        "streamable_http_path": "/mcp",
        "json_response": True,
        "stateless_http": True,
        "max_request_body_size": 1_048_576,
    }
