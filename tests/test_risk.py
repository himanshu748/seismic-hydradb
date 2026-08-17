"""Transparent change-risk scoring tests."""

from seismic.risk import risk_reason, score_risk


def test_closer_and_historically_risky_artifacts_rank_higher() -> None:
    direct, direct_components = score_risk(
        hop_distance=1,
        incident_pair_count=1,
        incident_count=2,
        fan_in=3,
        max_fan_in=5,
        kind="file",
    )
    distant, _ = score_risk(
        hop_distance=3,
        incident_pair_count=0,
        incident_count=0,
        fan_in=1,
        max_fan_in=5,
        kind="file",
    )

    assert direct > distant
    assert direct_components["incident_pair"] == 0.5


def test_risk_reason_discloses_absence_of_incident_evidence() -> None:
    reason = risk_reason(
        logical_key="src/app.py",
        hop_distance=2,
        incident_pair_count=0,
        incident_count=0,
    )

    assert "2 dependency hops" in reason
    assert "No prior incident evidence" in reason
