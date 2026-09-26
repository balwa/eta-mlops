"""Slot 5 — the format race, three ways

One question, several storage formats. Time each honestly (best of three,
warm). Then answer the question that matters: what did we give up?

The question, the same every time:
    average eta_error_min by city, for orders over 5 km

Your job: write timed(), then add the two missing racers in race().

    uv run python format_bench.py        # prints the race table

Done when:  uv run pytest tests/test_slot05.py
"""
import sqlite3
import time
from pathlib import Path

RESULTS: list[dict] = []


def timed(fn, repeats: int = 3):
    """Run fn() `repeats` times. Return (best time in milliseconds, fn's result)."""
    # TODO: time.perf_counter() before and after each call; keep the fastest.
    raise NotImplementedError


def race() -> list[dict]:
    import duckdb
    import pandas as pd
    import polars as pl

    COLS = ["city", "distance_km", "eta_error_min"]
    RESULTS.clear()

    def add(name: str, path: str, fn) -> None:
        ms, out = timed(fn)
        RESULTS.append({"approach": name, "file_MB": round(Path(path).stat().st_size / 1e6, 1),
                        "ms": round(ms, 1), "rows_out": len(out)})

    add("pandas read CSV", "data/orders.csv", lambda: (
        pd.read_csv("data/orders.csv", usecols=COLS)
        .query("distance_km > 5").groupby("city")["eta_error_min"].mean()
    ))
    add("polars read CSV", "data/orders.csv", lambda: (
        pl.read_csv("data/orders.csv", columns=COLS)
        .filter(pl.col("distance_km") > 5).group_by("city").agg(pl.col("eta_error_min").mean())
    ))
    add("polars read Parquet", "data/orders.parquet", lambda: (
        pl.read_parquet("data/orders.parquet", columns=COLS)
        .filter(pl.col("distance_km") > 5).group_by("city").agg(pl.col("eta_error_min").mean())
    ))
    add("DuckDB over Parquet", "data/orders.parquet", lambda: duckdb.sql(
        "select city, avg(eta_error_min) from 'data/orders.parquet' "
        "where distance_km > 5 group by city").fetchall())

    # TODO 1: the same question on 'data/orders_uncompressed.parquet' with DuckDB.
    # TODO 2: the same question in SQLite. The table is called `orders`:
    #         con = sqlite3.connect("data/orders.db")
    #         add("SQLite", "data/orders.db", lambda: con.execute("select ...").fetchall())

    return RESULTS


try:
    race()          # runs on import, so the slot-5 test can see RESULTS
except NotImplementedError:
    pass            # timed() not written yet


if __name__ == "__main__":
    import polars as pl

    df = pl.DataFrame(RESULTS).sort("ms")
    df = df.with_columns((pl.col("ms") / df["ms"][0]).round(1).alias("x_fastest"))
    with pl.Config(fmt_str_lengths=40, tbl_width_chars=120):
        print(df)
    print(f"\nspread: {df['ms'].max() / df['ms'].min():.0f}x. Same answer every time.")
    print("Now the real question: what did each format make you give up?")
