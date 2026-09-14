"""Slot 4 is done when this passes.

the two business counters move in opposite directions
"""
import numpy as np
import pytest

loss_sweep = pytest.importorskip("loss_sweep")

PRED = np.array([30.0, 40.0, 50.0])
ACTUAL = np.array([35.0, 35.0, 35.0])


def test_promises_broken_is_a_share():
    v = loss_sweep.promises_broken(PRED, ACTUAL)
    assert 0.0 <= v <= 1.0
    assert abs(v - 1 / 3) < 1e-9, "one of three promises was shorter than reality"


def test_idle_minutes_counts_only_over_promises():
    v = loss_sweep.courier_idle_minutes(PRED, ACTUAL)
    assert abs(v - 20.0) < 1e-9, "5 + 15 minutes of waiting; the under-promise contributes 0"


def test_counters_disagree():
    """A longer promise must break fewer promises and cost more idle time."""
    short, long_ = np.full(3, 30.0), np.full(3, 60.0)
    assert loss_sweep.promises_broken(long_, ACTUAL) < loss_sweep.promises_broken(short, ACTUAL)
    assert loss_sweep.courier_idle_minutes(long_, ACTUAL) > loss_sweep.courier_idle_minutes(short, ACTUAL)
