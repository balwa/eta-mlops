# Slot 6 · Freeze your own features

**File:** `freshness_check.py` · **Done when:** `uv run pytest tests/test_slot06.py` shows 2 passed (service must be running) · **Time:** 15 min

## Today's idea

Two programs share one file, and nothing else:

```text
 feature job  ──writes──▶  data/feature_store.parquet  ◀──reads──  ETA service
 (every 20 s)                 computed_at: 10:42:00                 (every request)
```

If the feature job dies, the service does not know. It keeps answering with **old**
data. Old data is not "wrong" — so every normal check still passes.
Today you write the check that catches it.

## Step 1 · Write the check

Open `freshness_check.py`. Write `check_freshness(max_age)`:

1. Ask the service: `info = httpx.get(f"{URL}/store-info", timeout=5).json()`
2. Work out the age: now (in UTC) minus `datetime.fromisoformat(info["computed_at"])`, in seconds
3. If the age is more than `max_age`, `raise FeatureStaleness(...)` with a clear message
4. Otherwise return `{"age_seconds": ..., "rows": info["rows"]}`

Try it (the service must be running — `make serve`):

```bash
uv run python freshness_check.py
```

```text
{'age_seconds': 44, 'rows': 900}
```

> **Tip** Use `datetime.now(timezone.utc)`. Plain `datetime.now()` has no timezone and Python will refuse to subtract.

## Step 2 · Three terminals

Open three Terminal windows, all inside `eta-mlops`. Put them side by side.

| terminal | command | what it does |
|---|---|---|
| **T1** | `uv run python -m eta.feature_job --loop 20` | refreshes the store every 20 s |
| **T2** | `make serve` | the ETA service (skip if already running) |
| **T3** | `uv run python freshness_check.py --watch --max-age 45` | predicts + checks every 10 s |

In T3 you should see `HTTP 200`, the same ETA, and `ok` with a small age.

## Step 3 · Kill the feature job

Click on T1 and press **Ctrl + C**. Now just watch T3 for about one minute.

```text
    t  http     eta  freshness check
   40   200    45.1  ok     {'age_seconds': 42, 'rows': 900}
   50   200    45.1  FIRED  feature store is 52 s old (limit 45 s)
   60   200    45.1  FIRED  feature store is 62 s old (limit 45 s)
```

> **Think** The ETA did not change. The status is still 200. Without your check, who would have noticed? When?

Press **Ctrl + C** in T3 to stop watching.

## Step 4 · A faster way to make it stale

```bash
uv run python -m eta.corrupt freeze --hours 3
curl -s -X POST localhost:8000/reload-store
uv run python freshness_check.py
```

You should see `FeatureStaleness: feature store is 10800 s old (limit 120 s)`.

Now put it back and check again:

```bash
uv run python -m eta.corrupt restore
curl -s -X POST localhost:8000/reload-store
uv run python freshness_check.py
```

## Step 5 · Check you are done

```bash
uv run pytest tests/test_slot06.py
```

> **Think** Who in a company should decide the number 120 seconds — the engineer or the product manager?

## If something goes wrong

| what you see | what to do |
|---|---|
| tests show `skipped` | The service is not running. `make serve` |
| check never fires | The service is caching the old store. Run the `reload-store` curl. |
| check fires immediately | `max_age` is too small for a 20 s loop. |
| `can't subtract offset-naive and offset-aware` | Use `datetime.now(timezone.utc)`. |
| T1 is not updating | T1 must be inside the `eta-mlops` folder. |
