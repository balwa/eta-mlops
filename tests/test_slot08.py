"""Slot 8 is done when this passes.

the contest metric is computed correctly
"""
import numpy as np
import pytest

imbalance = pytest.importorskip("imbalance")


def test_returns_recall_and_threshold():
    y = np.array([0] * 90 + [1] * 10)
    proba = np.concatenate([np.linspace(0.0, 0.5, 90), np.linspace(0.5, 1.0, 10)])
    recall, thr = imbalance.contest_score(y, proba, min_precision=0.10)
    assert 0.0 <= recall <= 1.0 and 0.0 <= thr <= 1.0


def test_a_perfect_scorer_gets_recall_one():
    y = np.array([0] * 90 + [1] * 10)
    proba = np.array([0.01] * 90 + [0.99] * 10)
    recall, _ = imbalance.contest_score(y, proba, min_precision=0.10)
    assert recall == pytest.approx(1.0)


def test_a_useless_scorer_does_not_score_well():
    rng = np.random.default_rng(0)
    y = (rng.random(2000) < 0.01).astype(int)
    recall, _ = imbalance.contest_score(y, rng.random(2000), min_precision=0.10)
    assert recall < 0.5, "random scores should not clear a 10% precision floor at high recall"
