"""Slot 2 — beat the model with five lines of rules

Write rules_eta(). No model, no fitting. Five lines of if-statements
and arithmetic. Then score it against the shipped model on the same split.

Done when:  uv run pytest tests/test_slot02.py
"""
import numpy as np
import polars as pl

from eta.label import time_split


def rules_eta(d: pl.DataFrame) -> np.ndarray:
    """Return a predicted ETA in minutes for every row. Rules only."""
    # TODO: start here. 12 + 3 * distance is already a real baseline.
    raise NotImplementedError


if __name__ == "__main__":
    te = time_split(pl.read_parquet("data/labelled.parquet"))[1]
    y = te["actual_minutes"].to_numpy()
    print("rules MAE:", float(np.abs(rules_eta(te) - y).mean()))
