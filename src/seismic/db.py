"""HydraDB connection handling and Seismic schema initialization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from neo4j import Driver, GraphDatabase, Record
from neo4j.exceptions import ConfigurationError, Neo4jError, ServiceUnavailable

from seismic.config import SeismicConfig
from seismic.identity import stable_id


class HydraDBError(RuntimeError):
    """Raised when Seismic cannot configure, reach, or query HydraDB."""


SCHEMA_ID = stable_id("schema", "seismic-v1")


class HydraDB:
    """Small official-driver wrapper tailored to HydraDB's OpenCypher subset."""

    def __init__(
        self,
        config: SeismicConfig | None = None,
        *,
        driver: Driver | None = None,
    ) -> None:
        self.config = config or SeismicConfig.from_env()
        self._owns_driver = driver is None
        if driver is not None:
            self._driver = driver
            return
        auth = None if self.config.token is None else (self.config.username, self.config.token)
        try:
            self._driver = GraphDatabase.driver(self.config.uri, auth=auth)
        except (ConfigurationError, Neo4jError, ValueError) as exc:
            raise HydraDBError(
                f"Invalid HydraDB connection configuration for {self.config.uri}: {exc}"
            ) from exc

    def verify_connection(self) -> None:
        """Verify Bolt connectivity and return a clear actionable error on failure."""

        try:
            self._driver.verify_connectivity()
            self.query(
                "MATCH (schema:SeismicSchema {id: $schema_id}) RETURN count(*) AS connected",
                {"schema_id": SCHEMA_ID},
            )
        except (HydraDBError, Neo4jError, ServiceUnavailable, OSError) as exc:
            token_hint = (
                " Set SEISMIC_TOKEN to the graph-node auth token."
                if self.config.token is None
                else ""
            )
            raise HydraDBError(
                f"HydraDB is unreachable at {self.config.uri}: {exc}.{token_hint}"
            ) from exc

    def setup_schema(self) -> None:
        """Create Seismic's schema marker in HydraDB's schema-on-write model."""

        self.execute_write(
            "UNWIND $rows AS row MERGE (schema {id: row.id}) "
            "SET schema:SeismicSchema, schema.key = row.key, schema.version = row.version",
            {"rows": [{"id": SCHEMA_ID, "key": "seismic", "version": "1"}]},
        )

    def query(
        self,
        cypher: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> list[Record]:
        """Execute one OpenCypher statement and materialize all returned records."""

        try:
            with self._driver.session(database=self.config.database) as session:
                return list(session.run(cypher, dict(parameters or {})))
        except (Neo4jError, ServiceUnavailable, OSError) as exc:
            raise HydraDBError(f"HydraDB query failed at {self.config.uri}: {exc}") from exc

    def execute_write(
        self,
        cypher: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> list[Record]:
        """Execute one parameterized auto-commit mutation through Bolt."""

        return self.query(cypher, parameters)

    def close(self) -> None:
        """Close the underlying driver when this wrapper created it."""

        if self._owns_driver:
            self._driver.close()

    def __enter__(self) -> HydraDB:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
