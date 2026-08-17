"""Fixture entrypoint."""

from sample_app.service import handler


def main() -> None:
    """Invoke the service."""

    handler("10")
