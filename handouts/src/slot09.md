# Slot 9 · Feature bake-off, model frozen

**File:** `features.py` · **Done when:** `uv run pytest tests/test_slot09.py` shows 5 passed · **Time:** 12 min

## Today's idea

The model is **frozen**. Nobody changes it. You can only change the **columns** you give it.
Which new columns actually help? The answer surprises most people.

The frozen model (do not touch):

```python
lgb.LGBMRegressor(n_estimators=250, learning_rate=0.07, num_leaves=40, random_state=2026)
```

## Step 1 · See the starting score

```bash
uv run python features.py
```

```text
base columns, as shipped       MAE 5.606

now write build_features() and add your columns to FEATURES.
```

## Step 2 · Add features, round by round

Write `build_features(train, other)`. It returns both tables with your new columns added.
Then add the new column names to the `FEATURES` list at the bottom. Try in this order,
and run after each round:

```bash
uv run python features.py
```

| round | idea | example |
|---|---|---|
| 1 | flags | `is_night`, `is_peak` (12, 13, 19, 20), `is_weekend` |
| 2 | ratios | distance per prep minute, price per item |
| 3 | history | each restaurant's average `actual_minutes` in the past |
| 4 | more history | each courier's average; restaurant × peak-hour average |

A flag looks like this:

```python
tr = train.with_columns(pl.col("hour").is_in([12, 13, 19, 20]).alias("is_peak"))
```

A history column looks like this — **learn it from `train` only**, then join it on **both**:

```python
rest = train.group_by("restaurant_id").agg(
    pl.col("actual_minutes").mean().alias("rest_hist_mean"))
tr = train.join(rest, on="restaurant_id", how="left")
ot = other.join(rest, on="restaurant_id", how="left")
# a restaurant never seen in train gets null -> fill it with the train average
```

> **Careful** Never compute an average over `other` (or over train + other together). That is cheating: the model gets to peek at the answers. The test `test_fitted_on_train_only` checks this.

## Step 3 · The leaderboard

Tell the instructor your best MAE and your best feature. Reference results:

```text
base columns                    5.606
+ flags                         5.589   (gain 0.017)
+ ratios                        5.589   (gain 0.000)
+ history (train only)          5.126   (gain 0.463)
+ restaurant x peak history     5.094   (gain 0.032)
```

> **Think** Flags and ratios gave almost **nothing**. History gave **everything**. Why? (Hint: does a flag give the model any information it did not already have?)

## Step 4 · Check you are done

```bash
uv run pytest tests/test_slot09.py
```

## If something goes wrong

| what you see | what to do |
|---|---|
| MAE below about 4.5 | Suspicious! You probably used a column that is only known after delivery. Slot 10 is about this. |
| `test_fitted_on_train_only` fails | You aggregated over `other`. Aggregate over `train` only, join onto both. |
| nulls after the join | Restaurant or courier not in train. `fill_null(train["actual_minutes"].mean())` |
| `KeyError` / column not found | A name in `FEATURES` is not a column your `build_features` made. |
