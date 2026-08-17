"""Pricing leaf module."""


def calculate(subtotal: float) -> float:
    """Apply the fixture's markup."""

    return subtotal * 1.1


def unused(value: float) -> float:
    """Remain outside the expected change path."""

    return value
