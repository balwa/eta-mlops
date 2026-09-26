"""Slot 7 — three samples, three models, one test set

Same row budget, three sampling strategies, identical model, identical
full-distribution test set. Report overall AND a night slice.

Your job: write the three samplers. Training and scoring are ready in __main__.

    uv run python sampling_compare.py    # ~6 s, prints the three-row table

Done when:  uv run pytest tests/test_slot07.py
"""
import polars as pl

N = 40_000


def convenience(pool: pl.DataFrame, n: int = N) -> pl.DataFrame:
    """The first n rows, exactly as the file gives them."""
    # TODO
    raise NotImplementedError


def simple_random(pool: pl.DataFrame, n: int = N) -> pl.DataFrame:
    """n rows chosen at random (use a fixed seed)."""
    # TODO
    raise NotImplementedError


def stratified(pool: pl.DataFrame, n: int = N) -> pl.DataFrame:
    """Proportional within city x hour-of-day."""
    # TODO: every (city, hour) group keeps the same share it has in the pool.
    #       Hint: frac = n / pool.height, then group_by(...).map_groups(...)
    raise NotImplementedError


def is_night() -> pl.Expr:
    return (pl.col("hour") >= 21) | (pl.col("hour") < 9)


if __name__ == "__main__":
    import lightgbm as lgb
    import numpy as np

    from eta.label import time_split
    from eta.train import CATEGORICAL, to_frame

    pool, te = time_split(pl.read_parquet("data/labelled.parquet"))
    night_te = te.filter(is_night())

    rows = []
    for name, sampler in [("convenience head(n)", convenience),
                          ("simple random", simple_random),
                          ("stratified city x hour", stratified)]:
        tr = sampler(pool, N)
        m = lgb.LGBMRegressor(n_estimators=250, learning_rate=0.07, num_leaves=40,
                              random_state=2026, verbose=-1)
        m.fit(to_frame(tr), tr["actual_minutes"].to_numpy(), categorical_feature=CATEGORICAL)

        def mae(d: pl.DataFrame) -> float:
            return float(np.abs(m.predict(to_frame(d)) - d["actual_minutes"].to_numpy()).mean())

        rows.append({"sample": name, "train_rows": tr.height,
                     "night_rows_in_train": tr.filter(is_night()).height,
                     "MAE_overall": round(mae(te), 3), "MAE_night": round(mae(night_te), 3)})

    print(pl.DataFrame(rows))
    conv, rand = rows[0], rows[1]
    print(f"\nconvenience vs random, overall : {conv['MAE_overall'] - rand['MAE_overall']:+.2f} min")
    print(f"convenience vs random, at night: {conv['MAE_night'] - rand['MAE_night']:+.2f} min")
