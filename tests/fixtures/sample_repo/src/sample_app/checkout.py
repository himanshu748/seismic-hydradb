"""Checkout depends on pricing without sharing its terminology."""

from sample_app.pricing import calculate


def total(subtotal: float) -> float:
    """Produce the amount charged at checkout."""

    return calculate(subtotal)
