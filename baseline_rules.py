"""Slot 2 — beat the model with five lines of rules

Write rules_eta(). No model, no fitting. Five lines of if-statements
and arithmetic. Then score it against the shipped model on the same split.

    uv run python baseline_rules.py      # your MAE next to the other baselines

Done when:  uv run pytest tests/test_slot02.py
"""
import numpy as np
import polars as pl

from eta.label import time_split


def rules_eta(d: pl.DataFrame) -> np.ndarray:
    """Return a predicted ETA in minutes for every row. Rules only."""
    # TODO: start here. 12 + 3 * distance is already a real baseline.
    #       Columns you may use: distance_km, restaurant_prep_min_estimate,
    #       hour, weather, n_items, city, dow ...
    raise NotImplementedError


if __name__ == "__main__":
    import pickle
    import time

    from eta.train import to_frame

    tr, te = time_split(pl.read_parquet("data/labelled.parquet"))
    y = te["actual_minutes"].to_numpy()

    def mae(p) -> float:
        return float(np.abs(np.asarray(p) - y).mean())

    t = time.perf_counter()
    mine = rules_eta(te)
    rules_ms = (time.perf_counter() - t) * 1000

    bundle = pickle.loads(open("models/eta_model.pkl", "rb").read())
    X = to_frame(te)
    t = time.perf_counter()
    model_pred = bundle["model"].predict(X)
    model_ms = (time.perf_counter() - t) * 1000

    mean_pred = np.full_like(y, tr["actual_minutes"].mean())

    print(f"held-out rows: {te.height:,}\n")
    print(f"{'baseline':<32}{'MAE (min)':>10}{'predict ms':>12}")
    print(f"{'predict the mean':<32}{mae(mean_pred):>10.3f}{0.0:>12.1f}")
    print(f"{'promised_eta_min (production)':<32}{mae(te['promised_eta_min'].to_numpy()):>10.3f}{0.0:>12.1f}")
    print(f"{'YOUR rules':<32}{mae(mine):>10.3f}{rules_ms:>12.1f}")
    print(f"{'LightGBM, 400 trees':<32}{mae(model_pred):>10.3f}{model_ms:>12.1f}")
    print(f"\nthe model is {mae(mine) - mae(model_pred):.2f} min better than your rules.")
