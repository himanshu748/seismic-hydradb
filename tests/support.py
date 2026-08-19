"""Shared helpers for live Seismic integration tests."""

from seismic.db import HydraDB
from seismic.identity import stable_id


def cleanup_repository(db: HydraDB, repo_id: str) -> None:
    """Delete one test repository through exact snapshot relationships and IDs."""

    repository_id = stable_id("repository", repo_id)
    receipt_rows = db.query(
        "MATCH (repo:Repository {id: $repository_id})-[:HAS_SNAPSHOT]->"
        "(snapshot:Snapshot)<-[:EVALUATED_SNAPSHOT]-(receipt:DecisionReceipt) "
        "RETURN receipt.id AS receipt_id",
        {"repository_id": repository_id},
    )
    receipt_ids = {int(row["receipt_id"]) for row in receipt_rows}
    rows = db.query(
        "MATCH (repo:Repository {id: $repository_id})-[:HAS_SNAPSHOT]->"
        "(snapshot:Snapshot)-[:CONTAINS]->(artifact:Artifact)-[:INSTANCE_OF]->"
        "(identity:ArtifactIdentity) "
        "RETURN snapshot.id AS snapshot_id, artifact.id AS artifact_id, "
        "identity.id AS identity_id",
        {"repository_id": repository_id},
    )
    snapshot_ids: set[int] = set()
    artifact_ids: set[int] = set()
    identity_ids: set[int] = set()
    for row in rows:
        snapshot_ids.add(int(row["snapshot_id"]))
        artifact_ids.add(int(row["artifact_id"]))
        identity_ids.add(int(row["identity_id"]))
    for label, node_ids in (
        ("DecisionReceipt", receipt_ids),
        ("Artifact", artifact_ids),
        ("ArtifactIdentity", identity_ids),
        ("Snapshot", snapshot_ids),
        ("Repository", {repository_id}),
    ):
        for node_id in sorted(node_ids):
            db.execute_write(
                f"MATCH (node:{label} {{id: $node_id}}) DETACH DELETE node",
                {"node_id": node_id},
            )
