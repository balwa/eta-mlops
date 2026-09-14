"""Slot 5 — the format race, three ways

One question, several storage formats. Time each honestly (best of three,
warm). Then answer the question that matters: what did we give up?

Done when:  uv run pytest tests/test_slot05.py
"""
import time

RESULTS: list[dict] = []


def timed(fn, repeats: int = 3):
    raise NotImplementedError


if __name__ == "__main__":
    ...  # TODO: CSV vs Parquet vs DuckDB-over-Parquet vs SQLite
