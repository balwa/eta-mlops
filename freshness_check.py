"""Slot 6 — freeze your own features

Assert that the feature store the service reads is fresh. Then kill the
batch job and watch the assertion fire while the service stays 200 OK.

Your job: write check_freshness(). Everything else is ready.

    uv run python freshness_check.py           # one check
    uv run python freshness_check.py --watch   # a check every 10 s, with a prediction
    uv run python freshness_check.py --watch --max-age 45   # fires sooner in class

Done when:  uv run pytest tests/test_slot06.py   (the service must be running)
"""
import argparse
import time
from datetime import datetime, timezone

import httpx

URL = "http://localhost:8000"
MAX_AGE_SECONDS = 120


class FeatureStaleness(AssertionError):
    pass


def check_freshness(max_age: int = MAX_AGE_SECONDS) -> dict:
    """Raise FeatureStaleness if the store is older than max_age."""
    # TODO:
    #   1. info = httpx.get(f"{URL}/store-info", timeout=5).json()
    #   2. age in seconds = now (UTC) - datetime.fromisoformat(info["computed_at"])
    #   3. if age > max_age: raise FeatureStaleness(...)
    #   4. otherwise return {"age_seconds": ..., "rows": info["rows"]}
    raise NotImplementedError


def watch(max_age: int = MAX_AGE_SECONDS, seconds: int = 600) -> None:
    """Every 10 s: reload the store, predict once, run your check."""
    body = {"order_id": "watch", "restaurant_id": "R0001", "n_items": 3,
            "weather": "clear", "placed_at": "2025-11-14T19:30:00+00:00"}
    print(f"{'t':>5}  {'http':>4}  {'eta':>6}  freshness check")
    t0 = time.time()
    while time.time() - t0 < seconds:
        httpx.post(f"{URL}/reload-store", timeout=5)
        r = httpx.post(f"{URL}/predict", json=body, timeout=5)
        try:
            verdict = f"ok     {check_freshness(max_age)}"
        except FeatureStaleness as e:
            verdict = f"FIRED  {e}"
        print(f"{time.time() - t0:5.0f}  {r.status_code:>4}  {r.json()['eta_minutes']:6.1f}  {verdict}",
              flush=True)
        time.sleep(10)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--max-age", type=int, default=MAX_AGE_SECONDS)
    args = ap.parse_args()
    if args.watch:
        watch(args.max_age)
    else:
        print(check_freshness(args.max_age))
