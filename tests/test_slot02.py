"""Slot 2 is done when this passes.

rules_eta beats predict-the-mean and is within 2 minutes of the model
"""
import numpy as np
import polars as pl
import pytest

from eta.label import time_split

baseline_rules = pytest.importorskip("baseline_rules")


@pytest.fixture(scope="module")
def te():
    return time_split(pl.read_parquet("data/labelled.parquet"))[1].sample(20_000, seed=1)


def test_returns_one_number_per_row(te):
    p = np.asarray(baseline_rules.rules_eta(te))
    assert p.shape == (te.height,)
    assert np.isfinite(p).all()


def test_predictions_are_plausible(te):
    p = np.asarray(baseline_rules.rules_eta(te))
    assert 5 < p.mean() < 120


def test_beats_predicting_the_mean(te):
    y = te["actual_minutes"].to_numpy()
    rules = float(np.abs(baseline_rules.rules_eta(te) - y).mean())
    mean_mae = float(np.abs(y.mean() - y).mean())
    assert rules < mean_mae, f"rules MAE {rules:.2f} vs mean-baseline {mean_mae:.2f}"


def test_within_two_minutes_of_the_model(te):
    import pickle
    from eta.train import to_frame
    y = te["actual_minutes"].to_numpy()
    b = pickle.loads(open("models/eta_model.pkl", "rb").read())
    model = float(np.abs(b["model"].predict(to_frame(te)) - y).mean())
    rules = float(np.abs(baseline_rules.rules_eta(te) - y).mean())
    assert rules - model < 2.0, f"rules {rules:.2f} vs model {model:.2f} — keep going"
