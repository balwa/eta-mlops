"""One command that breaks the ETA service without breaking the ETA service.

    uv run python -m eta.corrupt units     # geo switched km -> metres  (slot 1)
    uv run python -m eta.corrupt nulls     # prep estimate goes null    (slot 1 variant)
    uv run python -m eta.corrupt freeze    # backdate the store 6 hours (slot 6)
    uv run python -m eta.corrupt restore   # rebuild it honestly

Nothing here touches the model, the service, or the request. It edits the
feature store - the one place where an upstream team's change lands in your
predictions without passing through your code review.

After any of these, POST /reload-store (or restart the service) and curl again.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

import polars as pl

from eta.feature_job import STORE, run_once

MODES = ("units", "nulls", "freeze", "restore")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=MODES)
    ap.add_argument("--hours", type=float, default=6.0, help="for freeze")
    ap.add_argument("--stack", action="store_true",
                    help="corrupt on top of the current store instead of a fresh one")
    args = ap.parse_args()

    if args.mode == "restore":
        s = run_once()
        print(f"restored  rows={s.height}  computed_at={s['computed_at'][0]}")
        return

    if not STORE.exists():
        raise SystemExit("no feature store - run: uv run python -m eta.feature_job")

    # Each mode starts from an honest store unless asked to stack, so running
    # one twice, or two in a row, does what you expect.
    df = pl.read_parquet(STORE) if args.stack else run_once()
    before = df.select("restaurant_id", "distance_km", "prep_min_estimate").head(3)

    if args.mode == "units":
        # The geo team shipped metres. The column name still says km.
        df = df.with_columns((pl.col("distance_km") * 1000).alias("distance_km"))
        note = "distance_km is now metres. The column name did not change."
    elif args.mode == "nulls":
        # An upstream join started missing. The nulls arrive silently.
        df = df.with_columns(pl.lit(None, dtype=pl.Float64).alias("prep_min_estimate"))
        note = "prep_min_estimate is null. The service fillna(0)s it."
    else:  # freeze
        old = (datetime.now(timezone.utc) - timedelta(hours=args.hours)).isoformat(
            timespec="seconds"
        )
        df = df.with_columns(pl.lit(old).alias("computed_at"))
        note = f"computed_at backdated {args.hours} h. The values are unchanged."

    df.write_parquet(STORE)
    print(f"corrupted: {args.mode}")
    print(note)
    print("\nbefore:")
    print(before)
    print("after:")
    print(df.select("restaurant_id", "distance_km", "prep_min_estimate").head(3))
    print("\nNow: curl -X POST localhost:8000/reload-store   then predict again.")


if __name__ == "__main__":
    main()
