"""Slot 7 — three samples, three models, one test set

Same row budget, three sampling strategies, identical model, identical
full-distribution test set. Report overall AND a night slice.

Done when:  uv run pytest tests/test_slot07.py
"""
import polars as pl

N = 40_000


def convenience(pool: pl.DataFrame, n: int = N) -> pl.DataFrame:
    raise NotImplementedError


def simple_random(pool: pl.DataFrame, n: int = N) -> pl.DataFrame:
    raise NotImplementedError


def stratified(pool: pl.DataFrame, n: int = N) -> pl.DataFrame:
    """Proportional within city x hour-of-day."""
    raise NotImplementedError
