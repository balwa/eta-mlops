"""Slot 8 — 99% accurate and useless

Predict severely_late (about 1% of orders). Show the confusion matrix
before and after class weights. Contest: recall at precision >= 0.10.

Three parts:

  1. Label 20 borderline orders and measure agreement with a neighbour
         uv run python imbalance.py --make-labels yourname
         (open labels_yourname.csv, fill the `acceptable` column with 1 or 0)
         uv run python imbalance.py --kappa labels_yourname.csv labels_friend.csv

  2. 99% accurate and useless — plain vs class_weight="balanced"
         uv run python imbalance.py          # ~15 s

  3. Contest: write contest_score() below, then beat the reference score.

Done when:  uv run pytest tests/test_slot08.py
"""
import sys

import numpy as np
import polars as pl


def contest_score(y_true, proba, min_precision: float = 0.10) -> tuple[float, float]:
    """Return (best recall at >= min_precision, the threshold that got it)."""
    # TODO: try many thresholds t. For each one, pred = proba >= t.
    #       Keep only the thresholds where precision >= min_precision.
    #       Among those, return the highest recall and its threshold.
    #       sklearn.metrics has precision_score and recall_score.
    raise NotImplementedError


def make_labels(name: str) -> None:
    """Write the same 20 borderline orders for everyone, with a blank column."""
    from eta.label import time_split
    _, te = time_split(pl.read_parquet("data/labelled.parquet"))
    rows = (
        te.filter(((pl.col("actual_minutes") - pl.col("promised_eta_min")).abs() <= 6))
        .sample(20, seed=8)
        .select("order_id", "city", "hour", "weather", "distance_km", "n_items",
                "promised_eta_min", pl.col("actual_minutes").round(1))
        .with_columns(pl.lit("").alias("acceptable"))
    )
    out = f"labels_{name}.csv"
    rows.write_csv(out)
    print(f"wrote {out}. Open it, and in the `acceptable` column write 1 (acceptable)")
    print("or 0 (not acceptable) for each of the 20 orders. Decide on your own.")


def kappa(a: str, b: str) -> None:
    from sklearn.metrics import cohen_kappa_score
    x = pl.read_csv(a).sort("order_id")["acceptable"].to_numpy()
    y = pl.read_csv(b).sort("order_id")["acceptable"].to_numpy()
    print(f"agree on {int((x == y).sum())} of {len(x)} orders")
    print(f"Cohen's kappa = {cohen_kappa_score(x, y):.2f}   (1.0 = perfect, 0 = chance)")


def report(name, y, pred, proba) -> dict:
    from sklearn.metrics import average_precision_score, confusion_matrix
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {"model": name, "accuracy": round(float((pred == y).mean()), 4),
            "precision": round(float(tp / max(tp + fp, 1)), 3),
            "recall": round(float(tp / max(tp + fn, 1)), 3),
            "caught": int(tp), "missed": int(fn), "false_alarms": int(fp),
            "avg_precision": round(float(average_precision_score(y, proba)), 3)}


def main() -> None:
    import lightgbm as lgb

    from eta.label import time_split
    from eta.train import CATEGORICAL, to_frame

    tr, te = time_split(pl.read_parquet("data/labelled.parquet"))
    Xtr, ytr = to_frame(tr), tr["severely_late"].to_numpy().astype(int)
    Xte, yte = to_frame(te), te["severely_late"].to_numpy().astype(int)
    print(f"positive rate  train {ytr.mean():.4f}   test {yte.mean():.4f}")
    print(f"imbalance      1 : {int(1 / ytr.mean())}\n")

    params = dict(n_estimators=300, learning_rate=0.06, num_leaves=40, random_state=2026, verbose=-1)
    plain = lgb.LGBMClassifier(**params).fit(Xtr, ytr, categorical_feature=CATEGORICAL)
    p_plain = plain.predict_proba(Xte)[:, 1]
    bal = lgb.LGBMClassifier(class_weight="balanced", **params).fit(
        Xtr, ytr, categorical_feature=CATEGORICAL)
    p_bal = bal.predict_proba(Xte)[:, 1]

    rows = [report("plain", yte, (p_plain > 0.5).astype(int), p_plain),
            report("class_weight=balanced", yte, (p_bal > 0.5).astype(int), p_bal)]
    try:
        recall, thr = contest_score(yte, p_bal)
        rows.append(report(f"balanced @ thr={thr:.2f}", yte, (p_bal >= thr).astype(int), p_bal))
    except NotImplementedError:
        recall = None
    with pl.Config(tbl_width_chars=140):
        print(pl.DataFrame(rows))
    print(f"\nthe plain model is {rows[0]['accuracy']:.1%} accurate and catches "
          f"{rows[0]['caught']} of {int(yte.sum())} severe delays.")
    if recall is None:
        print("\nwrite contest_score() to see your contest score.")
    else:
        print(f"\nCONTEST SCORE — recall at precision >= 0.10 : {recall:.3f}   (reference: 0.410)")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--make-labels":
        make_labels(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "--kappa":
        kappa(sys.argv[2], sys.argv[3])
    else:
        main()
