"""Checkout regression test."""

from sample_app.checkout import total


def test_total() -> None:
    """Keep the checkout contract stable."""

    assert total(10) == 11
