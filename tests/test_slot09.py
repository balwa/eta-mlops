"""Slot 9 is done when this passes.

features are fitted on train only and actually help
"""
import polars as pl
import pytest

features = pytest.importorskip("features")


@pytest.fixture(scope="module")
def split():
    from eta.label import time_split
    tr, te = time_split(pl.read_parquet("data/labelled.parquet"))
    return tr.head(60_000), te.head(20_000)


def test_returns_both_frames_with_the_same_columns(split):
    tr, te = features.build_features(*split)
    assert set(tr.columns) == set(te.columns)
    assert tr.height == split[0].height and te.height == split[1].height


def test_added_something(split):
    tr, _ = features.build_features(*split)
    assert set(tr.columns) - set(split[0].columns), "no new features"


def test_declares_which_columns_it_feeds_the_model():
    assert hasattr(features, "FEATURES"), (
        "declare FEATURES = [...]: the columns you actually feed the model. "
        "Slot 10 audits this list."
    )


def test_no_post_outcome_columns_in_FEATURES():
    from eta.label import POST_OUTCOME
    leaked = [c for c in POST_OUTCOME if c in features.FEATURES]
    assert not leaked, f"post-outcome columns in FEATURES: {leaked}"


def test_fitted_on_train_only(split):
    """Swapping the second frame must not change the first frame's features."""
    tr_a, _ = features.build_features(split[0], split[1])
    tr_b, _ = features.build_features(split[0], split[1].head(100))
    for c in set(tr_a.columns) - set(split[0].columns):
        assert tr_a[c].equals(tr_b[c]), f"{c} depends on the frame you are predicting on"
