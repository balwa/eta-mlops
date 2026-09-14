"""Slot 12 — write tests that fail

Behavioural tests, not accuracy tests. Score points for tests the model
FAILS. Commit the failures.

Done when:  uv run pytest tests/test_slot12.py
"""
import numpy as np
import pytest


def test_more_distance_never_faster():
    """Doubling the distance must not make the delivery arrive sooner."""
    raise NotImplementedError


def test_heavy_rain_never_faster_than_clear():
    raise NotImplementedError
