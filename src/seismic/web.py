"""FastAPI surface shared by Seismic's landing page and live dashboard."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, cast

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi import Path as ApiPath
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from seismic.config import SeismicConfig, SeismicConfigError
from seismic.db import HydraDB, HydraDBError
from seismic.server import SEISMIC_VERSION
from seismic.tools import SeismicService

LOGGER = logging.getLogger("seismic.web")


class IndexBody(BaseModel):
    """Validated repository indexing request from the dashboard."""

    repo_path: str = Field(min_length=1, max_length=4_096)
    repo_id: str | None = Field(default=None, min_length=1, max_length=120)


class AnalyzeBody(BaseModel):
    """Validated change-analysis request from the dashboard."""

    repo_id: str = Field(min_length=1, max_length=120)
    targets: list[str] = Field(min_length=1, max_length=10)
    max_hops: int = Field(default=4, ge=1, le=8)
    limit: int = Field(default=30, ge=1, le=200)


class DiffBody(BaseModel):
    """Validated unified-diff analysis request from an agent or dashboard."""

    repo_id: str = Field(min_length=1, max_length=120)
    diff: str = Field(min_length=1, max_length=250_000)
    max_hops: int = Field(default=4, ge=1, le=8)
    limit: int = Field(default=30, ge=1, le=200)


class ContextBody(BaseModel):
    """Validated graph-context retrieval request from the dashboard."""

    repo_id: str = Field(min_length=1, max_length=120)
    query: str = Field(min_length=1, max_length=2_000)
    candidate_targets: list[str] | None = Field(default=None, max_length=8)
    limit: int = Field(default=20, ge=1, le=100)


class ExplainBody(BaseModel):
    """Validated exact-impact explanation request from the dashboard."""

    repo_id: str = Field(min_length=1, max_length=120)
    changed_target: str = Field(min_length=1, max_length=500)
    affected_target: str = Field(min_length=1, max_length=500)
    max_hops: int = Field(default=6, ge=1, le=8)


class IncidentBody(BaseModel):
    """Validated historical incident submitted through the dashboard."""

    repo_id: str = Field(min_length=1, max_length=120)
    trigger: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=4_000)
    impacted: list[str] | None = Field(default=None, max_length=20)
    severity: str = Field(default="medium", min_length=1, max_length=20)
    source: str = Field(default="dashboard", min_length=1, max_length=120)


def create_app(service_override: SeismicService | None = None) -> FastAPI:
    """Create the web app, optionally injecting a service for isolated API tests."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if service_override is not None:
            app.state.service = service_override
            yield
            return
        db: HydraDB | None = None
        try:
            config = SeismicConfig.from_env()
            db = HydraDB(config)
            db.verify_connection()
            db.setup_schema()
            app.state.service = SeismicService(db, config)
            yield
        except (HydraDBError, SeismicConfigError, ValueError) as exc:
            LOGGER.error("Seismic web startup failed: %s", exc)
            raise RuntimeError(f"Seismic web startup failed: {exc}") from exc
        finally:
            if db is not None:
                db.close()

    web = FastAPI(
        title="Seismic",
        version=SEISMIC_VERSION,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    @web.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @web.exception_handler(HydraDBError)
    async def hydradb_error_handler(_: Request, exc: HydraDBError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @web.get("/api/health")
    async def health(request: Request) -> dict[str, object]:
        service = _service(request)
        service.db.verify_connection()
        return {
            "ok": True,
            "product": "Seismic",
            "version": SEISMIC_VERSION,
            "backend": "HydraDB",
            "transport": "Bolt",
        }

    @web.post("/api/index")
    async def index_repository(request: Request, body: IndexBody) -> dict[str, object]:
        return dict(_service(request).index_repository(body.repo_path, repo_id=body.repo_id))

    @web.post("/api/analyze")
    async def analyze_change(request: Request, body: AnalyzeBody) -> dict[str, object]:
        return dict(
            _service(request).analyze_change(body.repo_id, body.targets, body.max_hops, body.limit)
        )

    @web.post("/api/analyze-diff")
    async def analyze_diff(request: Request, body: DiffBody) -> dict[str, object]:
        return dict(
            _service(request).analyze_diff(body.repo_id, body.diff, body.max_hops, body.limit)
        )

    @web.post("/api/context")
    async def retrieve_context(request: Request, body: ContextBody) -> dict[str, object]:
        return dict(
            _service(request).retrieve_context(
                body.repo_id, body.query, body.candidate_targets, body.limit
            )
        )

    @web.post("/api/explain")
    async def explain_impact(request: Request, body: ExplainBody) -> dict[str, object]:
        return dict(
            _service(request).explain_impact(
                body.repo_id,
                body.changed_target,
                body.affected_target,
                body.max_hops,
            )
        )

    @web.post("/api/incidents")
    async def record_incident(request: Request, body: IncidentBody) -> dict[str, str]:
        incident_id = _service(request).record_incident(
            body.repo_id,
            body.trigger,
            body.description,
            body.impacted,
            body.severity,
            body.source,
        )
        return {"incident_id": incident_id}

    @web.get("/api/repositories/{repo_id}")
    async def repository_status(
        request: Request,
        repo_id: Annotated[
            str,
            ApiPath(min_length=1, max_length=120, pattern=r"[A-Za-z0-9][A-Za-z0-9._-]*"),
        ],
    ) -> dict[str, object]:
        return _service(request).repository_status(repo_id)

    @web.get("/api/repositories/{repo_id}/decisions")
    async def decision_history(
        request: Request,
        repo_id: Annotated[
            str,
            ApiPath(min_length=1, max_length=120, pattern=r"[A-Za-z0-9][A-Za-z0-9._-]*"),
        ],
        limit: int = 20,
    ) -> list[dict[str, object]]:
        return [dict(receipt) for receipt in _service(request).decision_history(repo_id, limit)]

    dist = _ui_dist()
    assets = dist / "assets"
    if assets.is_dir():
        web.mount("/assets", StaticFiles(directory=assets), name="assets")

    @web.get("/")
    @web.get("/app")
    async def ui_shell() -> FileResponse:
        index = dist / "index.html"
        if not index.is_file():
            raise HTTPException(
                status_code=503,
                detail="Seismic UI is not built. Run npm install and npm run build in ui/.",
            )
        return FileResponse(index)

    return web


def _service(request: Request) -> SeismicService:
    return cast(SeismicService, request.app.state.service)


def _ui_dist() -> Path:
    packaged = Path(__file__).parent / "ui"
    if packaged.is_dir():
        return packaged
    return Path(__file__).parents[2] / "ui" / "dist"


app = create_app()


def main() -> None:
    """Run the local landing page and dashboard server."""

    logging.basicConfig(level=logging.INFO)
    host = os.getenv("SEISMIC_WEB_HOST", "127.0.0.1")
    try:
        port = int(os.getenv("SEISMIC_WEB_PORT", "8791"))
    except ValueError as exc:
        raise SystemExit("SEISMIC_WEB_PORT must be an integer") from exc
    if not 1 <= port <= 65_535:
        raise SystemExit("SEISMIC_WEB_PORT must be between 1 and 65535")
    uvicorn.run("seismic.web:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
