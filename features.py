"""Slot 9 — feature bake-off, model frozen

The model never changes. Only the feature matrix does. Every historical
aggregate is fitted on TRAIN ONLY.

Your job: write build_features() and list the columns you use in FEATURES.

    uv run python features.py            # ~10 s: base columns vs YOUR features

Done when:  uv run pytest tests/test_slot09.py
"""
import polars as pl


def build_features(train: pl.DataFrame, other: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return (train, other) with your features added.

    Anything you learn from data must be learned from `train` and applied to
    both. If you fit on `other` too, slot 10 will find it.
    """
    # TODO: ideas, roughly in the order people try them:
    #   - flags: is_night, is_peak, is_weekend        (with_columns)
    #   - ratios: distance per prep minute, price per item
    #   - history: each restaurant's / courier's average actual_minutes,
    #     computed with group_by on `train`, then joined onto BOTH frames
    #     (fill_null for restaurants that never appear in train)
    raise NotImplementedError


# The columns you actually feed the model. Slot 10 audits this list.
FEATURES: list[str] = [
    "distance_km", "n_items", "courier_rating", "restaurant_prep_min_estimate",
    "hour", "dow", "city", "weather",
    # TODO: add your new columns here
]

BASE = ["distance_km", "n_items", "courier_rating", "restaurant_prep_min_estimate",
        "hour", "dow", "city", "weather"]


def frozen_model_mae(tr: pl.DataFrame, te: pl.DataFrame, cols: list[str]) -> float:
    """The frozen model. Nobody changes this - only the columns change."""
    import lightgbm as lgb
    import numpy as np

    def frame(d):
        X = d.select(cols).to_pandas()
        for c in X.columns:
            if X[c].dtype == object or str(X[c].dtype) in ("string", "str"):
                X[c] = X[c].astype("category")
        return X

    m = lgb.LGBMRegressor(n_estimators=250, learning_rate=0.07, num_leaves=40,
                          random_state=2026, verbose=-1)
    m.fit(frame(tr), tr["actual_minutes"].to_numpy())
    return float(np.abs(m.predict(frame(te)) - te["actual_minutes"].to_numpy()).mean())


if __name__ == "__main__":
    from eta.label import time_split

    tr, te = time_split(pl.read_parquet("data/labelled.parquet"))
    base = frozen_model_mae(tr, te, BASE)
    print(f"{'base columns, as shipped':<30} MAE {base:.3f}")
    try:
        tr2, te2 = build_features(tr, te)
    except NotImplementedError:
        raise SystemExit("\nnow write build_features() and add your columns to FEATURES.")
    mine = frozen_model_mae(tr2, te2, FEATURES)
    print(f"{'YOUR features':<30} MAE {mine:.3f}   gain {base - mine:+.3f}")
    print(f"\nFEATURES ({len(FEATURES)}): {FEATURES}")
