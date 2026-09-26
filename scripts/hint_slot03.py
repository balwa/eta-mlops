"""Slot 3 hint — only run this if you are stuck on negative minutes.

    uv run python scripts/hint_slot03.py

Computes the naive delivery time (delivered_at - placed_at, no cleaning at
all) and groups it by city. Look at which row looks different, and by how
much.
"""
import polars as pl

raw = pl.read_parquet("data/orders.parquet")
ts = lambda c: pl.col(c).str.to_datetime(time_unit="us")  # noqa: E731
d = raw.with_columns(
    ((ts("delivered_at") - ts("placed_at")).dt.total_seconds() / 60).alias("naive_minutes")
)
print(
    d.group_by("city")
    .agg(
        pl.col("naive_minutes").median().round(1).alias("median_minutes"),
        (pl.col("naive_minutes") < 0).mean().round(2).alias("share_negative"),
    )
    .sort("median_minutes")
)
print("\nOne city is very different. How many hours off is it? Which timezone is that?")
