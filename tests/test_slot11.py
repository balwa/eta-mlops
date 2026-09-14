"""Slot 11 is done when this passes.

the fingerprint distinguishes different data, not different luck
"""
import polars as pl
import pytest

track = pytest.importorskip("track")

COLS = ["distance_km", "hour"]


@pytest.fixture(scope="module")
def split():
    from eta.label import time_split
    return time_split(pl.read_parquet("data/labelled.parquet"))


def test_is_stable(split):
    tr, te = split
    assert track.data_fingerprint(tr, te, COLS) == track.data_fingerprint(tr, te, COLS)


def test_changes_when_the_data_changes(split):
    tr, te = split
    assert track.data_fingerprint(tr, te, COLS) != track.data_fingerprint(tr.head(1000), te, COLS)


def test_changes_when_the_features_change(split):
    tr, te = split
    assert track.data_fingerprint(tr, te, COLS) != track.data_fingerprint(tr, te, COLS + ["city"])


def test_is_short_enough_to_read_off_a_projector(split):
    tr, te = split
    assert len(track.data_fingerprint(tr, te, COLS)) <= 16
