"""Slot 10 — the audit, as code

Project Milestone 2. A check that asserts every feature you use was
available at prediction time. Run it against your own features.py.

Done when:  uv run pytest tests/test_slot10.py
"""
import polars as pl

from eta.label import POST_OUTCOME


def audit(feature_names: list[str]) -> list[str]:
    """Return the feature names that could not have been known at order time."""
    raise NotImplementedError


def assert_no_leakage(feature_names: list[str]) -> None:
    bad = audit(feature_names)
    assert not bad, f"features unavailable at prediction time: {bad}"
