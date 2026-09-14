"""Seeded ETA dataset generator.

One command, deterministic everywhere:

    uv run python -m eta.generate

Writes into ./data/ :
    orders.parquet   the canonical table (everything reads this)
    orders.csv       the same rows, as CSV
    orders.db        SQLite, same rows

A year of food-delivery orders across six Indian cities, simulated from a
plausible generative process: courier speed by city and hour, restaurant prep
times, weather, and the operational history of a real-ish delivery platform.

Nothing here is random at runtime - SEED fixes every draw, so thirty laptops
produce byte-identical files and a leaderboard is meaningful.

Like any real dataset, it is not clean. Working out how is most of the course.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import polars as pl

SEED = 2026
N_ORDERS = 400_000
DAYS = 365
START = np.datetime64("2025-01-01T00:00:00")

CITIES = ["Pune", "Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Chennai"]
CITY_W = np.array([0.16, 0.24, 0.22, 0.18, 0.11, 0.09])
# average courier speed, km/h, on an empty road
CITY_SPEED = np.array([26.0, 19.0, 21.0, 24.0, 25.0, 23.0])

WEATHER = ["clear", "rain", "heavy_rain"]
WEATHER_W = np.array([0.78, 0.17, 0.05])
WEATHER_SPEED = np.array([1.00, 0.82, 0.62])

N_RESTAURANTS = 900
N_COURIERS = 2_400

# --- platform history and upstream quirks --------------------------------
TZ_SKEW_CITY = "Pune"
CANCEL_RATE = 0.060
INFLIGHT_TAIL_DAYS = 3
LOST_DELIVERED_AT = 0.008
CLOCK_SKEW_RATE = 0.005
NIGHT_LAUNCH_DAY = 120
REGIME_SHIFT_DAY = 274
SEVERE_LATE_MIN = 90
DUP_RATE = 0.030


def _hour_demand_curve(rng: np.random.Generator, n: int) -> np.ndarray:
    """Order volume by hour: lunch and dinner peaks, a thin overnight tail."""
    weights = np.array(
        [
            0.6, 0.4, 0.3, 0.2, 0.2, 0.3,   # 00-05
            0.6, 1.2, 2.0, 2.6, 3.2, 5.5,   # 06-11
            9.0, 8.0, 4.5, 3.0, 3.2, 4.5,   # 12-17
            7.5, 10.0, 9.0, 6.0, 3.5, 1.6,  # 18-23
        ]
    )
    return rng.choice(24, size=n, p=weights / weights.sum())


def build(seed: int = SEED, n_orders: int = N_ORDERS) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    n = n_orders

    # ---------- when ----------
    day = rng.integers(0, DAYS, size=n)
    hour = _hour_demand_curve(rng, n)

    # The platform launched 24-hour delivery partway through the year.
    early = day < NIGHT_LAUNCH_DAY
    night = (hour >= 21) | (hour < 9)
    move = early & night
    hour = np.where(move, rng.integers(11, 21, size=n), hour)

    minute = rng.integers(0, 60, size=n)
    second = rng.integers(0, 60, size=n)
    placed_true = (
        START
        + day.astype("timedelta64[D]")
        + hour.astype("timedelta64[h]")
        + minute.astype("timedelta64[m]")
        + second.astype("timedelta64[s]")
    )

    dow = ((day + 2) % 7).astype(np.int64)  # 2025-01-01 was a Wednesday
    is_weekend = np.isin(dow, [5, 6])

    # ---------- where / who ----------
    city_idx = rng.choice(len(CITIES), size=n, p=CITY_W)
    city = np.array(CITIES)[city_idx]
    restaurant_idx = rng.integers(0, N_RESTAURANTS, size=n)
    courier_idx = rng.integers(0, N_COURIERS, size=n)

    weather_idx = rng.choice(len(WEATHER), size=n, p=WEATHER_W)
    # rain is seasonal: heavier June-September
    monsoon = (day >= 152) & (day <= 273)
    bump = monsoon & (rng.random(n) < 0.35)
    weather_idx = np.where(bump, rng.choice([1, 2], size=n, p=[0.7, 0.3]), weather_idx)
    weather = np.array(WEATHER)[weather_idx]

    # ---------- order shape ----------
    distance_km = np.clip(rng.gamma(shape=2.6, scale=1.35, size=n), 0.4, 22.0)
    n_items = np.clip(rng.poisson(2.3, size=n) + 1, 1, 14)
    subtotal_inr = np.round(n_items * rng.normal(215, 70, size=n).clip(60, None), 0)

    # per-restaurant prep personality, stable across the year
    rest_prep_base = rng.normal(15.0, 4.5, size=N_RESTAURANTS).clip(5.0, 34.0)
    # per-courier speed personality
    courier_speed_mult = rng.normal(1.0, 0.11, size=N_COURIERS).clip(0.7, 1.35)
    courier_rating_base = rng.normal(4.4, 0.35, size=N_COURIERS).clip(2.6, 5.0)

    # Kitchens do not degrade equally under load: some hold their prep time
    # at dinner rush, some fall apart.
    rest_peak_mult = rng.normal(1.40, 0.32, size=N_RESTAURANTS).clip(0.95, 2.4)

    _peak_now = np.isin(hour, [12, 13, 19, 20])
    actual_prep_min = (
        rest_prep_base[restaurant_idx]
        * np.where(_peak_now, rest_peak_mult[restaurant_idx], 1.0)
        + rng.exponential(3.0, size=n)
        + 0.9 * (n_items - 2.3)
    ).clip(3.0, None)

    # peak-hour congestion, and empty roads after dark
    peak = np.isin(hour, [12, 13, 19, 20])
    is_night = (hour >= 21) | (hour < 9)
    hour_factor = np.where(peak, 0.74, np.where(np.isin(hour, [11, 14, 18]), 0.88, 1.0))
    hour_factor = np.where(is_night, 1.28, hour_factor)

    speed = (
        CITY_SPEED[city_idx]
        * hour_factor
        * WEATHER_SPEED[weather_idx]
        * courier_speed_mult[courier_idx]
        * rng.normal(1.0, 0.05, size=n).clip(0.6, 1.5)
    )
    rider_trip_distance_km = np.round(distance_km * rng.normal(1.18, 0.09, size=n).clip(1.0, 1.8), 2)
    travel_min = rider_trip_distance_km / speed * 60.0

    # Overnight: emptier roads, but thinner courier supply.
    courier_to_rest_min = rng.uniform(1.5, 9.0, size=n) + np.where(
        is_night, rng.gamma(shape=2.2, scale=5.0, size=n), 0.0
    )
    courier_wait_min = np.clip(actual_prep_min - courier_to_rest_min, 0, None)

    actual_minutes = (
        2.0
        + courier_to_rest_min
        + courier_wait_min
        + travel_min
        + rng.normal(0.0, 1.8, size=n)
    )

    # Partway through the year the platform began batching two orders per
    # courier.
    shifted = day >= REGIME_SHIFT_DAY
    batch_extra = rng.gamma(shape=2.0, scale=2.0, size=n)
    actual_minutes = np.where(
        shifted,
        actual_minutes * 0.94 + batch_extra + 2.5,
        actual_minutes,
    )
    actual_minutes = actual_minutes.clip(6.0, None)

    # Traffic incidents, wrong addresses, courier drop-offs.
    incident = rng.random(n) < 0.012
    actual_minutes = np.where(incident, actual_minutes + rng.gamma(3.0, 18.0, size=n), actual_minutes)
    actual_minutes = np.round(actual_minutes, 2)

    # what the current (dumb) planner promised at order time, rounded to 5 min
    restaurant_prep_min_estimate = np.round(rest_prep_base[restaurant_idx], 1)
    # The planner currently in production.
    promised_eta_min = np.round(
        (13.0 + 3.3 * distance_km + 0.95 * restaurant_prep_min_estimate) / 5.0
    ) * 5.0

    # ---------- event timestamps, from the durations above ----------
    def _plus(base: np.ndarray, mins: np.ndarray) -> np.ndarray:
        return base + (mins * 60).astype("timedelta64[s]")

    accepted_at = _plus(placed_true, np.full(n, 1.0) + rng.uniform(0, 2, n))
    courier_arrived_restaurant_at = _plus(placed_true, 2.0 + courier_to_rest_min)
    picked_up_at = _plus(placed_true, 2.0 + courier_to_rest_min + courier_wait_min)
    delivered_true = _plus(placed_true, actual_minutes)

    # ---------- outcomes ----------
    status = np.full(n, "delivered", dtype=object)
    cancelled = rng.random(n) < CANCEL_RATE
    status[cancelled] = "cancelled"
    in_flight = day >= (DAYS - INFLIGHT_TAIL_DAYS)
    status[in_flight & ~cancelled] = "in_flight"

    tip_inr = np.where(
        rng.random(n) < 0.31, np.round(rng.gamma(2.0, 16.0, size=n), 0), 0.0
    )
    # Finance computes courier payout after the fact.
    courier_payout_inr = np.round(
        22.0
        + 1.6 * rider_trip_distance_km
        + 0.85 * actual_minutes
        + rng.normal(0.0, 1.1, size=n),
        2,
    )
    sla_breach = actual_minutes > promised_eta_min
    # The ops dashboard stores promise-vs-reality.
    eta_error_min = np.round(actual_minutes - promised_eta_min, 2)
    late_vs_promise = actual_minutes - promised_eta_min
    rating_mu = 4.75 - 0.05 * np.clip(late_vs_promise, 0, 40)
    customer_rating_of_delivery = np.round(
        rng.normal(rating_mu, 0.45, size=n).clip(1.0, 5.0), 1
    )

    # ---------- string timestamps, as the warehouse stores them ----------
    def _iso(a: np.ndarray) -> np.ndarray:
        return a.astype("datetime64[s]").astype(str)

    # The mobile app build in one city stamps placed_at from the handset.
    tz_skew = city == TZ_SKEW_CITY
    placed_recorded = np.where(
        tz_skew, placed_true + np.timedelta64(330, "m"), placed_true
    )

    delivered_recorded = delivered_true.copy()
    # Some delivered orders lost delivered_at upstream.
    lost = (status == "delivered") & (rng.random(n) < LOST_DELIVERED_AT)
    # Some courier handsets have a skewed clock.
    skewed = (status == "delivered") & (rng.random(n) < CLOCK_SKEW_RATE)
    delivered_recorded = np.where(
        skewed, picked_up_at - np.timedelta64(rng.integers(60, 900), "s"), delivered_recorded
    )

    placed_s = _iso(placed_recorded)
    accepted_s = _iso(accepted_at)
    arrived_s = _iso(courier_arrived_restaurant_at)
    picked_s = _iso(picked_up_at)
    delivered_s = _iso(delivered_recorded)
    cancelled_s = _iso(_plus(placed_true, rng.uniform(1, 25, n)))

    is_delivered = status == "delivered"

    def _nullable(values: np.ndarray, keep: np.ndarray) -> pl.Series:
        """A Utf8 column that is null wherever `keep` is False."""
        s = pl.Series(values.astype("U19"), dtype=pl.Utf8)
        return pl.select(
            pl.when(pl.Series(keep)).then(s).otherwise(None)
        ).to_series()

    delivered_out = _nullable(delivered_s, is_delivered & ~lost)
    cancelled_out = _nullable(cancelled_s, status == "cancelled")
    accepted_out = _nullable(accepted_s, status != "cancelled")
    arrived_out = _nullable(arrived_s, is_delivered)
    picked_out = _nullable(picked_s, is_delivered)

    # post-outcome measurements are only recorded for delivered orders
    def _post(a: np.ndarray) -> np.ndarray:
        return np.where(is_delivered, np.round(a, 2), np.nan)

    df = pl.DataFrame(
        {
            "order_id": [f"ORD-{i:07d}" for i in range(n)],
            "placed_at": placed_s,
            "city": city,
            "restaurant_id": np.array([f"R{i:04d}" for i in range(N_RESTAURANTS)])[restaurant_idx],
            "courier_id": np.array([f"C{i:05d}" for i in range(N_COURIERS)])[courier_idx],
            "status": status.astype("U9"),
            # --- available at prediction time ---
            "distance_km": np.round(distance_km, 2),
            "n_items": n_items.astype(np.int32),
            "subtotal_inr": subtotal_inr,
            "weather": weather,
            "is_weekend": is_weekend,
            "courier_rating": np.round(courier_rating_base[courier_idx], 2),
            "restaurant_prep_min_estimate": restaurant_prep_min_estimate,
            "promised_eta_min": promised_eta_min,
            # --- event log ---
            "accepted_at": accepted_out,
            "courier_arrived_restaurant_at": arrived_out,
            "picked_up_at": picked_out,
            "delivered_at": delivered_out,
            "cancelled_at": cancelled_out,
            # --- measured after the delivery finished ---
            "actual_prep_min": _post(actual_prep_min),
            "courier_wait_min": _post(courier_wait_min),
            "rider_trip_distance_km": _post(rider_trip_distance_km),
            "tip_inr": _post(tip_inr),
            "customer_rating_of_delivery": _post(customer_rating_of_delivery),
            "courier_payout_inr": _post(courier_payout_inr),
            "eta_error_min": _post(eta_error_min),
            "sla_breach": pl.select(
                pl.when(pl.Series(is_delivered))
                .then(pl.Series(sla_breach))
                .otherwise(None)
            ).to_series(),
        }
    )

    # The upstream queue double-wrote a slice of orders.
    dup_n = int(n * DUP_RATE)
    dup_idx = rng.choice(n, size=dup_n, replace=False)
    dups = df[dup_idx].with_columns(
        pl.Series("order_id", [f"ORD-{n + i:07d}" for i in range(dup_n)])
    )
    df = pl.concat([df, dups])

    # The export is ordered by time, as the warehouse produces it.
    df = df.sort("placed_at")

    return df


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data", help="output directory (default: data)")
    ap.add_argument("--rows", type=int, default=N_ORDERS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--no-csv", action="store_true", help="skip the ~100 MB CSV")
    ap.add_argument("--no-sqlite", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    df = build(seed=args.seed, n_orders=args.rows)

    df.write_parquet(out / "orders.parquet", compression="zstd")
    df.write_parquet(out / "orders_uncompressed.parquet", compression="uncompressed")
    if not args.no_csv:
        df.write_csv(out / "orders.csv")
    if not args.no_sqlite:
        p = out / "orders.db"
        if p.exists():
            p.unlink()
        con = sqlite3.connect(p)
        df.to_pandas().to_sql("orders", con, index=False, chunksize=50_000)
        con.execute("CREATE INDEX idx_city ON orders(city)")
        con.commit()
        con.close()

    n_del = df.filter(pl.col("status") == "delivered").height
    print(f"rows           {df.height:,}  ({n_del:,} delivered)")
    print(f"columns        {df.width}")
    for f in sorted(out.iterdir()):
        print(f"{f.name:<28} {f.stat().st_size / 1e6:8.1f} MB")


if __name__ == "__main__":
    main()
