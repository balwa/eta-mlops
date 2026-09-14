"""Reference label function and the clean training table.

    uv run python -m eta.label          # writes data/labelled.parquet

SPOILER WARNING. Slot 3 asks you to write this yourself, in `label_fn.py`,
and the whole point is discovering what makes it hard. Try yours first. This
file exists so that nobody is blocked for the rest of the weekend by one
slot - slots 4 onward import from here, not from your file.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

TZ_SKEW_CITY = "Pune"
TZ_SKEW_MINUTES = 330

# Columns that only exist because the order already finished.
POST_OUTCOME = [
    "delivered_at",
    "cancelled_at",
    "picked_up_at",
    "courier_arrived_restaurant_at",
    "actual_prep_min",
    "courier_wait_min",
    "rider_trip_distance_km",
    "tip_inr",
    "customer_rating_of_delivery",
    "courier_payout_inr",
    "eta_error_min",
    "sla_breach",
    "accepted_at",
]

# Columns a request genuinely carries, or the platform genuinely knows, at the
# moment the ETA has to be produced.
HONEST_FEATURES = [
    "distance_km",
    "n_items",
    "subtotal_inr",
    "courier_rating",
    "restaurant_prep_min_estimate",
    "promised_eta_min",
    "city",
    "weather",
    "is_weekend",
    "hour",
    "dow",
]


def label(df: pl.DataFrame, *, drop_duplicates: bool = True) -> pl.DataFrame:
    """Raw orders in, labelled training rows out. Unlabelable rows are dropped."""
    d = df.with_columns(
        pl.col("placed_at").str.to_datetime(time_unit="us").alias("_placed_raw"),
        pl.col("delivered_at").str.to_datetime(time_unit="us").alias("_delivered"),
        pl.col("picked_up_at").str.to_datetime(time_unit="us").alias("_picked"),
    )

    # normalise placed_at to UTC
    d = d.with_columns(
        pl.when(pl.col("city") == TZ_SKEW_CITY)
        .then(pl.col("_placed_raw").dt.offset_by(f"-{TZ_SKEW_MINUTES}m"))
        .otherwise(pl.col("_placed_raw"))
        .alias("placed_utc")
    )

    d = d.with_columns(
        ((pl.col("_delivered") - pl.col("placed_utc")).dt.total_seconds() / 60.0).alias(
            "actual_minutes"
        )
    )

    # only delivered orders that recorded a delivery time
    d = d.filter(
        (pl.col("status") == "delivered") & pl.col("_delivered").is_not_null()
    )
    # delivery cannot precede pickup, and cannot take 12 hours
    d = d.filter(
        (pl.col("_delivered") > pl.col("_picked"))
        & (pl.col("actual_minutes") > 0)
        & (pl.col("actual_minutes") < 12 * 60)
    )

    # the upstream queue double-wrote some orders
    if drop_duplicates:
        d = d.unique(
            subset=["placed_at", "city", "restaurant_id", "courier_id",
                    "distance_km", "subtotal_inr"],
            keep="first",
            maintain_order=True,
        )

    return d.with_columns(
        pl.col("placed_utc").dt.hour().alias("hour"),
        pl.col("placed_utc").dt.weekday().alias("dow"),
        pl.col("placed_utc").dt.ordinal_day().alias("doy"),
        (pl.col("actual_minutes") > 90).alias("severely_late"),
    ).drop("_placed_raw", "_delivered", "_picked")


def time_split(d: pl.DataFrame, *, holdout_days: int = 45) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Train on the past, test on the future. The only honest split here."""
    cut = d["placed_utc"].max() - pl.duration(days=holdout_days)  # type: ignore[operator]
    return d.filter(pl.col("placed_utc") < cut), d.filter(pl.col("placed_utc") >= cut)


def main() -> None:
    raw = pl.read_parquet("data/orders.parquet")
    d = label(raw)
    Path("data").mkdir(exist_ok=True)
    d.write_parquet("data/labelled.parquet", compression="zstd")

    dropped = raw.height - d.height
    print(f"raw rows        {raw.height:,}")
    print(f"labelled rows   {d.height:,}")
    print(f"dropped         {dropped:,}  ({dropped / raw.height:.1%})")
    print()
    print(d.select("actual_minutes").describe())
    tr, te = time_split(d)
    print(f"time split      train {tr.height:,}   test {te.height:,}")
    print(f"severely_late   {d['severely_late'].mean():.4f}")


if __name__ == "__main__":
    main()
