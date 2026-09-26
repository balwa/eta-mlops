"""Slot 11 — put your run on the class leaderboard

Log params, metrics AND the data fingerprint. The fingerprint is the
point: it is what settles an argument about two identical-looking scores.

Your job: write data_fingerprint(). The training and logging are ready.

    # a local MLflow server, in a second terminal (port 5001, NOT 5000 on a Mac)
    uv run mlflow server --backend-store-uri sqlite:///mlflow.db --port 5001

    # your run
    MLFLOW_TRACKING_URI=http://localhost:5001 uv run python track.py --name yourname
    # try also:  --features slim      --rows 40000

Done when:  uv run pytest tests/test_slot11.py
"""
import argparse
import hashlib
import os
import time

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")  # keep the output readable

import mlflow  # noqa: E402

FEATURE_SETS = {
    "base": ["distance_km", "n_items", "courier_rating", "restaurant_prep_min_estimate",
             "hour", "dow", "city", "weather"],
    "slim": ["distance_km", "restaurant_prep_min_estimate", "hour", "city"],
}


def data_fingerprint(train, test, cols) -> str:
    """A short hash of exactly what you trained on."""
    # TODO: build a string from the things that define "what data" - row
    #       counts, the column list, first/last order_id ... - then
    #       hashlib.sha256(text.encode()).hexdigest()[:12]
    raise NotImplementedError


def main() -> None:
    import lightgbm as lgb
    import numpy as np
    import polars as pl

    from eta.label import time_split
    from eta.train import CATEGORICAL

    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="your name - this is your leaderboard row")
    ap.add_argument("--features", choices=list(FEATURE_SETS), default="base")
    ap.add_argument("--rows", type=int, default=0, help="train on only the first N rows (0 = all)")
    ap.add_argument("--n-estimators", type=int, default=250)
    ap.add_argument("--learning-rate", type=float, default=0.07)
    ap.add_argument("--num-leaves", type=int, default=40)
    args = ap.parse_args()

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment("eta-leaderboard")

    tr, te = time_split(pl.read_parquet("data/labelled.parquet"))
    if args.rows:
        tr = tr.head(args.rows)
    cols = FEATURE_SETS[args.features]
    sha = data_fingerprint(tr, te, cols)

    with mlflow.start_run(run_name=args.name):
        mlflow.log_params({"features": args.features, "n_estimators": args.n_estimators,
                           "learning_rate": args.learning_rate, "num_leaves": args.num_leaves,
                           "data_rows": tr.height, "data_sha": sha, "split": "time"})
        t = time.perf_counter()
        cats = [c for c in CATEGORICAL if c in cols]
        Xtr, Xte = tr.select(cols).to_pandas(), te.select(cols).to_pandas()
        for c in cats:
            Xtr[c], Xte[c] = Xtr[c].astype("category"), Xte[c].astype("category")
        m = lgb.LGBMRegressor(n_estimators=args.n_estimators, learning_rate=args.learning_rate,
                              num_leaves=args.num_leaves, random_state=2026, verbose=-1)
        m.fit(Xtr, tr["actual_minutes"].to_numpy(), categorical_feature=cats)
        fit_s = time.perf_counter() - t
        y, p = te["actual_minutes"].to_numpy(), m.predict(Xte)
        mae = float(np.abs(p - y).mean())
        mlflow.log_metrics({"mae": mae, "bias": float((p - y).mean()), "fit_seconds": fit_s})

    print(f"{args.name:>12}  MAE {mae:.3f}  features={args.features}  "
          f"rows={tr.height:,}  data_sha={sha}  ({fit_s:.1f} s)")


if __name__ == "__main__":
    main()
