"""Slot 6 — freeze your own features

Assert that the feature store the service reads is fresh. Then kill the
batch job and watch the assertion fire while the service stays 200 OK.

Done when:  uv run pytest tests/test_slot06.py
"""
from datetime import datetime, timezone

import httpx

URL = "http://localhost:8000"
MAX_AGE_SECONDS = 120


class FeatureStaleness(AssertionError):
    pass


def check_freshness(max_age: int = MAX_AGE_SECONDS) -> dict:
    """Raise FeatureStaleness if the store is older than max_age."""
    raise NotImplementedError


if __name__ == "__main__":
    print(check_freshness())
