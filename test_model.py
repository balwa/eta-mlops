"""Slot 12 — write tests that fail

Behavioural tests, not accuracy tests. Score points for tests the model
FAILS. Commit the failures.

    invariance    change something irrelevant -> the answer must not move
    directional   change something relevant   -> the answer must move the right way
    slice         no group of orders may be much worse than the overall MAE

The fixtures and predict() helper are ready. Write at least four tests.

    uv run pytest test_model.py -v       # red is good here

Done when:  uv run pytest tests/test_slot12.py
"""
import pickle

import numpy as np
import polars as pl
import pytest

from eta.label import time_split
from eta.train import to_frame


@pytest.fixture(scope="module")
def bundle():
    """The model the service ships."""
    return pickle.loads(open("models/eta_model.pkl", "rb").read())


@pytest.fixture(scope="module")
def test_rows():
    """4,000 held-out orders the model has never seen."""
    _, te = time_split(pl.read_parquet("data/labelled.parquet"))
    return te.sample(4_000, seed=7)


def predict(bundle, d: pl.DataFrame) -> np.ndarray:
    return bundle["model"].predict(to_frame(d))


# Example of the pattern - an invariance test that already works:
def test_order_id_does_not_matter(bundle, test_rows):
    a = predict(bundle, test_rows)
    b = predict(bundle, test_rows.with_columns(pl.lit("ORD-XXXX").alias("order_id")))
    assert np.allclose(a, b)


def test_more_distance_never_faster(bundle, test_rows):
    """Doubling the distance must not make the delivery arrive sooner."""
    # TODO: predict on test_rows, then on a copy with distance_km * 2.
    #       Count rows where the new ETA is smaller (use a 0.01 tolerance).
    raise NotImplementedError


def test_heavy_rain_never_faster_than_clear(bundle, test_rows):
    # TODO: set weather to "clear" for every row, then to "heavy_rain".
    raise NotImplementedError


# TODO: more ideas - 4 more items never faster; predictions between 3 and 240
#       minutes; MAE on long trips (> 10 km) or at night not more than 1.25x
#       the overall MAE.
