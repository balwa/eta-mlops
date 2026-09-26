"""Slot 4 — sweep the asymmetry

Train the same model at several quantile alphas and plot two business
counters that move in opposite directions. Then pick one and defend it.

Your job: write the two counters below. The sweep, the table and the plot
are already written for you in __main__.

    uv run python loss_sweep.py          # ~10 s, writes logs/loss_sweep.png

Done when:  uv run pytest tests/test_slot04.py
"""
import numpy as np
import polars as pl

ALPHAS = [0.5, 0.6, 0.7, 0.8, 0.9]


def promises_broken(pred, actual) -> float:
    """Share of orders where the promise was shorter than reality."""
    # TODO: a number between 0 and 1. Hint: np.asarray(pred) < np.asarray(actual)
    raise NotImplementedError


def courier_idle_minutes(pred, actual) -> float:
    """Total minutes couriers wait because the promise was too long."""
    # TODO: only over-promises count. An under-promise adds 0, not a negative.
    raise NotImplementedError


if __name__ == "__main__":
    import time
    from pathlib import Path

    import lightgbm as lgb
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from eta.label import time_split
    from eta.train import CATEGORICAL, to_frame

    tr, te = time_split(pl.read_parquet("data/labelled.parquet"))
    tr = tr.sample(60_000, seed=2026)
    Xtr, ytr = to_frame(tr), tr["actual_minutes"].to_numpy()
    Xte, yte = to_frame(te), te["actual_minutes"].to_numpy()

    rows = []
    t0 = time.perf_counter()
    for a in ALPHAS:
        m = lgb.LGBMRegressor(
            objective="quantile", alpha=a, n_estimators=250,
            learning_rate=0.08, num_leaves=40, random_state=2026, verbose=-1,
        ).fit(Xtr, ytr, categorical_feature=CATEGORICAL)
        p = m.predict(Xte)
        rows.append({
            "alpha": a,
            "promises_broken_pct": round(100 * promises_broken(p, yte), 1),
            "idle_min_per_1k": round(courier_idle_minutes(p, yte) / len(yte) * 1000),
            "mae": round(float(np.abs(p - yte).mean()), 2),
            "median_promise": round(float(np.median(p)), 1),
        })
    out = pl.DataFrame(rows)
    print(out)
    print(f"\n{len(ALPHAS)} models in {time.perf_counter() - t0:.1f} s")

    fig, ax1 = plt.subplots(figsize=(7, 4.2))
    ax1.plot(out["alpha"], out["promises_broken_pct"], "o-", color="#c0392b")
    ax1.set_xlabel("quantile alpha")
    ax1.set_ylabel("promises broken (%)", color="#c0392b")
    ax2 = ax1.twinx()
    ax2.plot(out["alpha"], out["idle_min_per_1k"], "s--", color="#2471a3")
    ax2.set_ylabel("courier idle min per 1,000 orders", color="#2471a3")
    ax1.set_title("The loss function is a business decision")
    fig.tight_layout()
    Path("logs").mkdir(exist_ok=True)
    fig.savefig("logs/loss_sweep.png", dpi=130)
    print("wrote logs/loss_sweep.png   (open it with: open logs/loss_sweep.png)")
