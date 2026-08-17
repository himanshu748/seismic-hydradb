"""Stateless MCP transports for Seismic's durable HydraDB code graph."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from seismic.config import SeismicConfig, SeismicConfigError
from seismic.db import HydraDB, HydraDBError
from seismic.models import ChangeImpactReport, ContextPack, ImpactExplanation, IngestSummary
from seismic.tools import SeismicService

LOGGER = logging.getLogger("seismic")
SEISMIC_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class RuntimeState:
    """Reusable infrastructure that never stores durable MCP session state."""

    service: SeismicService


@asynccontextmanager
async def seismic_lifespan(_: MCPServer[RuntimeState]) -> AsyncIterator[RuntimeState]:
    """Verify Bolt and schema readiness before accepting any agent request."""

    db: HydraDB | None = None
    try:
        config = SeismicConfig.from_env()
        db = HydraDB(config)
        db.verify_connection()
        db.setup_schema()
        yield RuntimeState(service=SeismicService(db, config))
    except (HydraDBError, SeismicConfigError, ValueError) as exc:
        LOGGER.error("Seismic startup failed: %s", exc)
        raise RuntimeError(f"Seismic startup failed: {exc}") from exc
    finally:
        if db is not None:
            db.close()


mcp = MCPServer[RuntimeState](
    "Seismic",
    title="Seismic",
    description="Graph-native code change impact analysis backed by HydraDB.",
    instructions=(
        "Index an allowed Git repository, then call analyze_change before editing code. "
        "Every reported impact includes a bounded HydraDB dependency path. Empty or "
        "unsupported results mean the available graph does not justify a claim."
    ),
    version=SEISMIC_VERSION,
    lifespan=seismic_lifespan,
)


@mcp.tool()
def index_repository(
    repo_path: str,
    ctx: Context[RuntimeState],
    repo_id: str | None = None,
) -> IngestSummary:
    """Create and activate an immutable repository graph before agents rely on it."""

    return ctx.request_context.lifespan_context.service.index_repository(repo_path, repo_id)


@mcp.tool()
def analyze_change(
    repo_id: str,
    targets: list[str],
    ctx: Context[RuntimeState],
    max_hops: int = 4,
    limit: int = 30,
) -> ChangeImpactReport:
    """Rank what a planned change can affect using exact reverse dependency paths."""

    return ctx.request_context.lifespan_context.service.analyze_change(
        repo_id, targets, max_hops, limit
    )


@mcp.tool()
def retrieve_context(
    repo_id: str,
    query: str,
    ctx: Context[RuntimeState],
    candidate_targets: list[str] | None = None,
    limit: int = 20,
) -> ContextPack:
    """Expand lexical or agent-supplied seeds through the graph for grounded context."""

    return ctx.request_context.lifespan_context.service.retrieve_context(
        repo_id, query, candidate_targets, limit
    )


@mcp.tool()
def explain_impact(
    repo_id: str,
    changed_target: str,
    affected_target: str,
    ctx: Context[RuntimeState],
    max_hops: int = 6,
) -> ImpactExplanation:
    """Show one exact HydraDB path or explicitly abstain when no path supports impact."""

    return ctx.request_context.lifespan_context.service.explain_impact(
        repo_id, changed_target, affected_target, max_hops
    )


@mcp.tool()
def record_incident(
    repo_id: str,
    trigger: str,
    description: str,
    ctx: Context[RuntimeState],
    impacted: list[str] | None = None,
    severity: str = "medium",
    source: str = "manual",
) -> str:
    """Persist real breakage evidence so later blast-radius ranking learns from history."""

    return ctx.request_context.lifespan_context.service.record_incident(
        repo_id, trigger, description, impacted, severity, source
    )


@mcp.tool()
def repository_status(repo_id: str, ctx: Context[RuntimeState]) -> dict[str, object]:
    """Report the current immutable snapshot so agents can verify evidence freshness."""

    return ctx.request_context.lifespan_context.service.repository_status(repo_id)


def main() -> None:
    """Serve Seismic over local stdio for coding-agent MCP clients."""

    _configure_logging()
    mcp.run(transport="stdio")


def http_main() -> None:
    """Serve sessionless Streamable HTTP while retaining only a reusable driver pool."""

    _configure_logging()
    host = os.getenv("SEISMIC_MCP_HOST", "127.0.0.1")
    port = _bounded_int("SEISMIC_MCP_PORT", default=8790, minimum=1, maximum=65535)
    max_body = _bounded_int(
        "SEISMIC_MCP_MAX_BODY_BYTES",
        default=1_048_576,
        minimum=1_024,
        maximum=4_194_304,
    )
    LOGGER.info("Seismic stateless MCP: http://%s:%s/mcp", host, port)
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        max_request_body_size=max_body,
    )


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)


def _bounded_int(name: str, *, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise SystemExit(f"{name} must be between {minimum} and {maximum}")
    return value


if __name__ == "__main__":
    main()
