"""Stable identity tests."""

from seismic.identity import relationship_id, stable_id


def test_stable_ids_are_positive_repeatable_and_domain_separated() -> None:
    value = stable_id("artifact", "repo@snapshot::file::src/app.py")

    assert value == stable_id("artifact", "repo@snapshot::file::src/app.py")
    assert value > 0
    assert value != stable_id("snapshot", "repo@snapshot::file::src/app.py")


def test_relationship_identity_includes_direction_and_type() -> None:
    forward = relationship_id("snapshot", "CALLS", 10, 20)

    assert forward != relationship_id("snapshot", "CALLS", 20, 10)
    assert forward != relationship_id("snapshot", "IMPORTS", 10, 20)
