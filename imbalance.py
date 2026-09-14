"""Slot 8 — 99% accurate and useless

Predict severely_late (about 0.8% of orders). Show the confusion matrix
before and after class weights. Contest: recall at precision >= 0.10.

Done when:  uv run pytest tests/test_slot08.py
"""
import polars as pl


def contest_score(y_true, proba, min_precision: float = 0.10) -> tuple[float, float]:
    """Return (best recall at >= min_precision, the threshold that got it)."""
    raise NotImplementedError
