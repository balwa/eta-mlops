"""Slot 9 — feature bake-off, model frozen

Build a real sklearn Pipeline. The model never changes. Only the feature
matrix does. Every historical aggregate is fitted on TRAIN ONLY.

Done when:  uv run pytest tests/test_slot09.py
"""
import polars as pl


def build_features(train: pl.DataFrame, other: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return (train, other) with your features added.

    Anything you learn from data must be learned from `train` and applied to
    both. If you fit on `other` too, slot 10 will find it.
    """
    raise NotImplementedError
