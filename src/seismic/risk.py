"""Transparent deterministic risk scoring for graph-derived change impact."""

from __future__ import annotations

import math


def score_risk(
    *,
    hop_distance: int,
    incident_pair_count: int,
    incident_count: int,
    fan_in: int,
    max_fan_in: int,
    kind: str,
) -> tuple[float, dict[str, float]]:
    """Score one affected artifact and expose every normalized component."""

    if hop_distance < 1:
        raise ValueError("hop_distance must be at least 1")
    proximity = 1.0 / hop_distance
    incident_pair = min(1.0, incident_pair_count / 2.0)
    incident_node = min(1.0, incident_count / 3.0)
    normalized_fan_in = math.log1p(max(0, fan_in)) / math.log1p(max(1, max_fan_in))
    criticality = {
        "entrypoint": 1.0,
        "file": 0.8,
        "function": 0.8,
        "class": 0.8,
        "test": 0.6,
        "package_version": 0.4,
    }.get(kind, 0.4)
    components = {
        "proximity": round(proximity, 4),
        "incident_pair": round(incident_pair, 4),
        "incident_node": round(incident_node, 4),
        "fan_in": round(normalized_fan_in, 4),
        "criticality": round(criticality, 4),
    }
    score = 100.0 * (
        0.45 * proximity
        + 0.20 * incident_pair
        + 0.10 * incident_node
        + 0.15 * normalized_fan_in
        + 0.10 * criticality
    )
    return round(score, 2), components


def risk_reason(
    *,
    logical_key: str,
    hop_distance: int,
    incident_pair_count: int,
    incident_count: int,
) -> str:
    """Explain why an artifact ranked where it did without implying prediction."""

    reason = f"{logical_key} is reachable in {hop_distance} dependency hop"
    reason += "." if hop_distance == 1 else "s."
    if incident_pair_count:
        reason += (
            f" This exact trigger-impact pair appears in {incident_pair_count} prior "
            f"incident{'s' if incident_pair_count != 1 else ''}."
        )
    elif incident_count:
        reason += (
            f" The affected artifact appears in {incident_count} prior "
            f"incident{'s' if incident_count != 1 else ''}."
        )
    else:
        reason += " No prior incident evidence was found for this artifact."
    return reason
