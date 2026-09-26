"""Slot 12, part two — the reveal.

    uv run python scripts/slice_table.py

The aggregate MAE is one number. This is the same model, sliced eleven ways.
Run it after you have written your tests, not before: the month-10
row is the one nobody writes a test for, and it is the largest gap on the
board.
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `eta` imports

import numpy as np
import polars as pl

from eta.label import time_split
from eta.train import to_frame

SLICES: list[tuple[str, pl.Expr]] = [
    ("night 21:00-09:00", (pl.col("hour") >= 21) | (pl.col("hour") < 9)),
    ("peak 12/13/19/20", pl.col("hour").is_in([12, 13, 19, 20])),
    ("clear", pl.col("weather") == "clear"),
    ("rain", pl.col("weather") == "rain"),
    ("heavy rain", pl.col("weather") == "heavy_rain"),
    ("short trips < 2 km", pl.col("distance_km") < 2),
    ("long trips > 10 km", pl.col("distance_km") > 10),
    ("weekend", pl.col("dow") >= 6),
    ("Pune", pl.col("city") == "Pune"),
    ("Mumbai", pl.col("city") == "Mumbai"),
]
REGIME_SHIFT_DOY = 274


def main() -> None:
    bundle = pickle.loads(open("models/eta_model.pkl", "rb").read())
    _, te = time_split(pl.read_parquet("data/labelled.parquet"))
    y = te["actual_minutes"].to_numpy()
    p = bundle["model"].predict(to_frame(te))
    overall = float(np.abs(p - y).mean())

    rows = []
    for name, expr in SLICES:
        m = te.select(expr).to_series().to_numpy()
        if m.sum() < 100:
            continue
        mae = float(np.abs(p[m] - y[m]).mean())
        bias = float((p[m] - y[m]).mean())
        rows.append({
            "slice": name, "rows": int(m.sum()),
            "MAE": round(mae, 2), "vs overall": round(mae / overall, 2),
            "bias": round(bias, 2),
        })

    out = pl.DataFrame(rows).sort("vs overall", descending=True)
    print(f"overall MAE on the held-out set: {overall:.2f} min over {te.height:,} rows\n")
    with pl.Config(tbl_rows=20):
        print(out)
    worst = out.row(0, named=True)
    print(f"\nworst slice: {worst['slice']}  -  {worst['vs overall']}x the aggregate.")

    # --- the reveal -------------------------------------------------------
    # MAE is roughly flat across every slice. Bias is not: it is the same
    # large negative number everywhere. That is not a modelling error spread
    # thin, it is one event. Show this only after the tests are written.
    print(
        "\n--- now look at the bias column, not the MAE column ---\n"
        f"every slice sits near {out['bias'].median():.1f} min. The model is not wrong at "
        "random;\nit is optimistic by the same amount everywhere."
    )

    d = pl.read_parquet("data/labelled.parquet")
    pre = d.filter(pl.col("doy") < REGIME_SHIFT_DOY).sample(20_000, seed=3)
    post_train = d.filter(pl.col("doy") >= REGIME_SHIFT_DOY).head(20_000)
    for name, sub, note in [
        ("before month 10", pre, "(in-sample: the model trained on this)"),
        ("after  month 10", post_train, "(in-sample)"),
        ("the held-out future", te, "(out-of-sample)"),
    ]:
        pp = bundle["model"].predict(to_frame(sub))
        yy = sub["actual_minutes"].to_numpy()
        print(f"  {name:<22} mean actual {yy.mean():6.2f} min   "
              f"mean predicted {pp.mean():6.2f} min   bias {(pp-yy).mean():+6.2f}  {note}")
    print(
        "\nOn day 274 the platform started batching two orders per courier.\n"
        "Nobody told the model. Nobody wrote a test that would have caught it."
    )


if __name__ == "__main__":
    main()
