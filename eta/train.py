"""Train the ETA model the service ships with.

    uv run python -m eta.train

Honest features only, trained on the past, tested on the future. The numbers
it prints are the reference every leaderboard this weekend is measured against.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.metrics import mean_absolute_error, r2_score

from eta.label import time_split

MODEL = Path("models/eta_model.pkl")

# What the service can actually assemble at prediction time: three fields from
# the request, four looked up in the feature store, two from the clock.
SERVING_FEATURES = [
    "distance_km",
    "prep_min_estimate",
    "courier_rating",
    "n_items",
    "hour",
    "dow",
    "city",
    "weather",
]
CATEGORICAL = ["city", "weather"]


def to_frame(d: pl.DataFrame):
    import pandas as pd

    X = d.select(
        [pl.col("restaurant_prep_min_estimate").alias("prep_min_estimate")
         if c == "prep_min_estimate" else pl.col(c) for c in SERVING_FEATURES]
    ).to_pandas()
    for c in CATEGORICAL:
        X[c] = X[c].astype("category")
    return X


def main() -> None:
    import lightgbm as lgb

    d = pl.read_parquet("data/labelled.parquet")
    tr, te = time_split(d)

    Xtr, ytr = to_frame(tr), tr["actual_minutes"].to_numpy()
    Xte, yte = to_frame(te), te["actual_minutes"].to_numpy()

    model = lgb.LGBMRegressor(
        n_estimators=400, learning_rate=0.06, num_leaves=48,
        min_child_samples=40, random_state=2026, verbose=-1,
    ).fit(Xtr, ytr, categorical_feature=CATEGORICAL)

    pred = model.predict(Xte)
    metrics = {
        "model_mae": round(float(mean_absolute_error(yte, pred)), 3),
        "model_r2": round(float(r2_score(yte, pred)), 4),
        "promised_eta_mae": round(float(mean_absolute_error(yte, te["promised_eta_min"])), 3),
        "predict_the_mean_mae": round(float(np.abs(yte - ytr.mean()).mean()), 3),
        "n_train": tr.height,
        "n_test": te.height,
        "features": SERVING_FEATURES,
    }

    MODEL.parent.mkdir(parents=True, exist_ok=True)
    with MODEL.open("wb") as f:
        pickle.dump({"model": model, "features": SERVING_FEATURES,
                     "categorical": CATEGORICAL, "metrics": metrics}, f)
    Path("models/metrics.json").write_text(json.dumps(metrics, indent=2))

    w = max(len(k) for k in metrics if k != "features")
    for k, v in metrics.items():
        if k != "features":
            print(f"{k:<{w}}  {v}")
    print(f"\nwrote {MODEL}")


if __name__ == "__main__":
    main()
