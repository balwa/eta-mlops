# Slot 5 · The format race

**File:** `format_bench.py` · **Done when:** `uv run pytest tests/test_slot05.py` shows 3 passed · **Time:** 12 min

## Today's idea

The same data is saved in four ways: **CSV**, **Parquet**, **Parquet without compression**
and **SQLite**. We ask all of them the same question and time each one.

The question is not only "which is fastest?". The real question is:
**what did we give up to get that speed?**

The question we ask every time:

> **Note** Average `eta_error_min` by city, for orders over 5 km. (Answer: 6 rows.)

## Step 1 · Write a fair timer

Open `format_bench.py`. Write `timed(fn, repeats=3)`:

- run `fn()` three times
- measure each run with `time.perf_counter()`
- return **(the fastest time in milliseconds, the result of fn)**

Why the fastest of three? The first run is often slow because the file is not yet in memory.
Then you are timing your disk, not the format.

## Step 2 · Add the two missing racers

Four racers are already written in `race()`. Add two more, following the same pattern:

1. **DuckDB** on `data/orders_uncompressed.parquet` (copy the DuckDB line, change the file name)
2. **SQLite** on `data/orders.db` — the table is called `orders`:

```python
con = sqlite3.connect("data/orders.db")
add("SQLite", "data/orders.db", lambda: con.execute(
    "select city, avg(eta_error_min) from orders "
    "where distance_km > 5 group by city").fetchall())
```

## Step 3 · Race

```bash
uv run python format_bench.py
```

Your numbers will be different, but the **order** should be similar:

```text
approach                          file_MB  ms     x_fastest
DuckDB over uncompressed Parquet  93.3     2.4    1.0
DuckDB over Parquet               20.1     4.4    1.8
polars read Parquet               20.1     5.2    2.2
polars read CSV                   90.7     24.1   10.0
SQLite                            108.0    151.4  63.1
pandas read CSV                   90.7     276.7  115.3
```

Tell the instructor your fastest and slowest numbers.

## Step 4 · What did we give up?

Discuss with your neighbour and fill this in:

| format | what is good | what we give up |
|---|---|---|
| CSV | anyone can open it, even Excel | |
| Parquet | small and fast | |
| Parquet, no compression | fastest here | |
| SQLite | | |

> **Think** Uncompressed Parquet was fastest but **4.6× bigger**. Would it still win if the file was on a slow network drive instead of your SSD?

## Step 5 · Check you are done

```bash
uv run pytest tests/test_slot05.py
```

## If something goes wrong

| what you see | what to do |
|---|---|
| `test_timed_takes_the_best_not_the_first` fails | You must call `fn()` exactly `repeats` times. |
| first run much slower than the rest | Normal. That is why we take the best of three. |
| `no such table: orders` | Run `make data`. |
| SQLite is the fastest | Check that you used the same question, not `count(*)`. |
