"""Slot 7 is done when this passes.

the three samplers differ in exactly the way the lesson needs
"""
import polars as pl
import pytest

sampling_compare = pytest.importorskip("sampling_compare")

N = 5_000


@pytest.fixture(scope="module")
def pool():
    from eta.label import time_split
    return time_split(pl.read_parquet("data/labelled.parquet"))[0]


def night(d):
    return d.filter((pl.col("hour") >= 21) | (pl.col("hour") < 9)).height


def test_all_three_return_the_row_budget(pool):
    for f in (sampling_compare.convenience, sampling_compare.simple_random,
              sampling_compare.stratified):
        assert abs(f(pool, N).height - N) <= N * 0.05, f"{f.__name__} returned the wrong size"


def test_convenience_has_no_night_rows(pool):
    assert night(sampling_compare.convenience(pool, N)) == 0, (
        "head(n) on a time-sorted file should contain zero night orders"
    )


def test_random_and_stratified_do(pool):
    assert night(sampling_compare.simple_random(pool, N)) > 0
    assert night(sampling_compare.stratified(pool, N)) > 0


def test_stratified_matches_the_population_by_city(pool):
    s = sampling_compare.stratified(pool, N)
    for city in pool["city"].unique():
        want = (pool["city"] == city).mean()
        got = (s["city"] == city).mean()
        assert abs(got - want) < 0.02, f"{city}: {got:.3f} vs population {want:.3f}"
