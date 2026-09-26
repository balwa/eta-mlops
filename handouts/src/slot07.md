# Slot 7 · Three samples, three models

**File:** `sampling_compare.py` · **Done when:** `uv run pytest tests/test_slot07.py` shows 4 passed · **Time:** 15 min

## Today's idea

You can only afford to train on **40,000 rows**. Which 40,000?
We try three ways of choosing, train the **same** model on each, and test all three
on the **same** test set. Then we look at the overall error **and** the error at night.

## Step 1 · Write three samplers

Open `sampling_compare.py`. Each function gets the full training pool and returns `n` rows.

| function | how to choose |
|---|---|
| `convenience(pool, n)` | just the first `n` rows of the file |
| `simple_random(pool, n)` | `n` rows at random (use a fixed `seed=` so it repeats) |
| `stratified(pool, n)` | every **city × hour** group keeps the same share it has in the pool |

For `stratified`, one way:

1. `frac = n / pool.height`
2. make a group key: city + hour, e.g. `pl.col("city") + "|" + pl.col("hour").cast(pl.Utf8)`
3. `group_by` that key and, inside `map_groups`, sample `round(g.height * frac)` rows from each group

> **Tip** Test your samplers quickly: `uv run pytest tests/test_slot07.py`

## Step 2 · Train and compare

Training and scoring are already written:

```bash
uv run python sampling_compare.py
```

About 6–10 seconds. You should see:

```text
sample                  night_rows_in_train  MAE_overall  MAE_night
convenience head(n)     0                    6.506        8.52
simple random           4735                 5.771        5.667
stratified city x hour  4785                 5.716        5.604

convenience vs random, overall : +0.74 min
convenience vs random, at night: +2.85 min
```

## Step 3 · Talk about it

> **Think** 1. **Zero** night orders in 40,000 rows. Why? (Hint: the file is sorted by time. What happened in the first four months of the business?) 2. Overall, convenience is only 0.74 min worse. Would you notice that? At night it is **2.85 min** worse — almost 4 times the gap. 3. In Slot 2, a "night" rule did almost nothing. Now night matters a lot. How can both be true?

> **Think** Stratified beats random by only 0.05 min here. When would stratifying really pay off?

## If something goes wrong

| what you see | what to do |
|---|---|
| convenience has night rows | Do not shuffle. Take `head(n)` of the pool as it is. |
| stratified city share test fails | Each group must be sampled in **proportion**, not the same size. |
| stratified returns far from `n` rows | Round per group: `max(1, round(g.height * frac))`. |
| all three MAEs are the same | You are returning the same rows three times. |
