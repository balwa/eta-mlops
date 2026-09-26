# Slot 12 · Write tests that fail

**File:** `test_model.py` · **Done when:** `uv run pytest tests/test_slot12.py` shows 4 passed · **Time:** 18 min

## Today's idea

For two days, green meant good. **Today you score a point for every test the model FAILS.**
These are not accuracy tests. They are **behaviour** tests — things any sensible ETA model
must do, whatever its MAE.

| kind | rule | example |
|---|---|---|
| **invariance** | change something that should not matter → answer must not move | a different `order_id` |
| **directional** | change something that matters → answer must move the right way | double the distance → not faster |
| **slice** | no group of orders may be much worse than overall | long trips, night, Pune |

## Step 1 · Look at the ready-made parts

Open `test_model.py`. Already there for you:

- `bundle` — the model the service uses
- `test_rows` — 4,000 orders the model has never seen
- `predict(bundle, rows)` — returns an array of ETAs
- one finished example: `test_order_id_does_not_matter`

## Step 2 · Write at least four tests

Start with the two unfinished ones, then add your own. The pattern for a directional test:

```python
def test_more_distance_never_faster(bundle, test_rows):
    a = predict(bundle, test_rows)
    b = predict(bundle, test_rows.with_columns(
        (pl.col("distance_km") * 2).alias("distance_km")))
    bad = int((b < a - 0.01).sum())          # 0.01 = small tolerance
    assert bad == 0, f"{bad}/{len(a)} rows got FASTER when distance doubled"
```

More ideas:

- heavy rain never faster than clear (set `weather` to `"clear"`, then to `"heavy_rain"`)
- 4 more items never faster
- every prediction between 3 and 240 minutes
- MAE on long trips (`distance_km > 10`) at most 1.25 × the overall MAE

```bash
uv run pytest test_model.py -v
```

**Red is good today.** Count your failures.

## Step 3 · Reference results

On the shipped model, a good set of tests gives **4 failed, 5 passed**:

| test | result |
|---|---|
| doubling distance never faster | **FAIL** — 15 of 4,000 rows got faster |
| heavy rain never faster than clear | **FAIL** — 55 of 4,000 rows got faster |
| 4 more items never faster | **FAIL** — 6 of 4,000 rows got faster |
| long trips > 10 km | **FAIL** — MAE 7.58 vs 5.60 overall (1.35×) |

> **Think** For 55 orders, making the weather **worse** gives a **faster** ETA. Is that noise? No metric caught it. Would a customer?

## Step 4 · The reveal (together, after everyone has written tests)

```bash
uv run python scripts/slice_table.py
```

Look at the **bias** column, not the MAE column. Every slice is about **−3.5 minutes**:
the model is too optimistic by the same amount everywhere. Then read the last three lines —
what happened around **day 274**? (Remember the 76.5% from Slot 4?)

## Step 5 · Check you are done

```bash
uv run pytest tests/test_slot12.py
```

This checks that you wrote at least 4 tests, no `NotImplementedError` is left, and that
**some of your tests fail**. If all of them pass, your tests are too easy!

## If something goes wrong

| what you see | what to do |
|---|---|
| every test passes | Your tests are too gentle. Try bigger changes, or slices. |
| every test fails | You compared floats exactly. Use a tolerance: `b < a - 0.01`. |
| error about changing a DataFrame | polars tables do not change in place. Use `with_columns`. |
| `test_nothing_is_still_a_stub` fails | Remove every `raise NotImplementedError`. |
