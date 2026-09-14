"""The batch feature job.

In production this runs every 15 minutes and refreshes the online feature
store the ETA service reads at prediction time. Here it runs on demand, or
on a timer for slot 6:

    uv run python -m eta.feature_job                 # once
    uv run python -m eta.feature_job --loop 20       # every 20 s, until Ctrl-C

It writes data/feature_store.parquet: one row per restaurant, plus a
`computed_at` stamp. The service never recomputes these - it looks them up.
That split is the whole point: the service is only as fresh as this job.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

STORE = Path("data/feature_store.parquet")


def build_store(labelled: pl.DataFrame) -> pl.DataFrame:
    agg = (
        labelled.group_by("restaurant_id")
        .agg(
            pl.col("city").mode().first().alias("city"),
            pl.col("distance_km").median().round(2).alias("distance_km"),
            pl.col("restaurant_prep_min_estimate").median().round(1).alias("prep_min_estimate"),
            pl.col("courier_rating").mean().round(2).alias("courier_rating"),
            pl.col("promised_eta_min").median().alias("promised_eta_min"),
            pl.len().alias("orders_seen"),
        )
        .sort("restaurant_id")
    )
    return agg.with_columns(
        pl.lit(datetime.now(timezone.utc).isoformat(timespec="seconds")).alias("computed_at"),
        pl.lit("km").alias("distance_unit"),
    )


def run_once(src: str = "data/labelled.parquet") -> pl.DataFrame:
    store = build_store(pl.read_parquet(src))
    STORE.parent.mkdir(parents=True, exist_ok=True)
    store.write_parquet(STORE)
    return store


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loop", type=int, default=0, metavar="SECONDS",
                    help="rerun forever every SECONDS (slot 6)")
    args = ap.parse_args()

    while True:
        s = run_once()
        print(f"[feature_job] wrote {STORE}  rows={s.height}  computed_at={s['computed_at'][0]}",
              flush=True)
        if not args.loop:
            return
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
