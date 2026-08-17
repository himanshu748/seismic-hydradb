"""Service layer."""

from sample_app.checkout import total


def handler(raw_amount: str) -> float:
    """Handle a request without using pricing vocabulary."""

    return total(float(raw_amount))
