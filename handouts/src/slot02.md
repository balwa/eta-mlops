# Slot 2 · Beat the model with five lines of rules

**File:** `baseline_rules.py` · **Done when:** `uv run pytest tests/test_slot02.py` shows 4 passed · **Time:** 15 min

## Today's idea

Before you build an ML model, ask: **how far can simple rules take me?**
Google's first rule of ML is "don't be afraid to launch without ML".
Today you write a few `if` statements and see how close they get to a trained model.

## Step 1 · Warm-up (instructor-led)

For each scenario the instructor reads out, vote: **ML / not ML / not yet**.

## Step 2 · Write your rules

Open `baseline_rules.py`. Fill in `rules_eta(d)`. It gets a table of orders and must
return one number (minutes) per order.

Rules only: **no fitting, no sklearn**. Just arithmetic and `np.where`.

A starting point (it is a bit wrong on purpose, so you can improve it):

```python
def rules_eta(d):
    return 12 + 3 * d["distance_km"].to_numpy()
```

Useful columns: `distance_km`, `restaurant_prep_min_estimate`, `hour`, `weather`
(`"clear"`, `"rain"`, `"heavy_rain"`), `n_items`.

A pattern for "add 5 minutes when it rains":

```python
w = d["weather"].to_numpy()
eta = eta + np.where(w == "rain", 5.0, 0.0)
```

## Step 3 · Run it and see your score

```bash
uv run python baseline_rules.py
```

You will see your MAE (average error in minutes) next to the other baselines:

```text
baseline                         MAE (min)  predict ms
predict the mean                     9.958         0.0
promised_eta_min (production)        7.393         0.0
YOUR rules                           ?.???         ?.?
LightGBM, 400 trees                  5.600       128.9
```

**Lower is better.** Change a rule, run again. Try to get close to the model.

> **Tip** Ask yourself: what else do I already believe matters? Busy lunch and dinner hours? Rain? How long the kitchen takes? Number of items?

## Step 4 · The leaderboard

Tell the instructor your best MAE. A good set of rules gets around **6.3**.
The model gets **5.6**.

> **Think** 1. Your rules beat the system in production today (7.39). Could you ship them on Monday? 2. Look at the last column. How many times faster are your rules than the model? 3. Is 0.7 minutes of accuracy worth a training pipeline, a model registry and monitoring?

## Step 5 · Check you are done

```bash
uv run pytest tests/test_slot02.py
```

## If something goes wrong

| what you see | what to do |
|---|---|
| `NotImplementedError` | You have not replaced the `raise` line in `rules_eta` yet. |
| MAE around 25–40 | Check for a `*` where you meant `+`. Print a few predictions next to `te["actual_minutes"]`. |
| `test_within_two_minutes_of_the_model` fails | Your rules are more than 2 minutes worse than the model. Remove rules that do not help. |
| `test_beats_predicting_the_mean` fails | You are probably returning one number for every row. Use `distance_km`. |
