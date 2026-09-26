# Slot 11 · The class MLflow leaderboard

**File:** `track.py` · **Done when:** `uv run pytest tests/test_slot11.py` shows 4 passed · **Time:** 15 min

## Today's idea

Two people both say "my model gets 5.6". Did they train on the same data?
Without tracking, nobody knows. **MLflow** records every run: the settings, the score, and a
**fingerprint of the data**. The fingerprint is what settles the argument.

## Step 1 · Write the data fingerprint

Open `track.py`. Write `data_fingerprint(train, test, cols)`. It must return a **short text**
(12 characters is good) that:

- is the **same** every time for the same data
- **changes** if the rows change (e.g. only the first 1,000 rows)
- **changes** if the column list changes

Idea: join the things that define "what data" into one string — number of train rows, number
of test rows, the sorted column names, the first and last `order_id` — then hash it:

```python
text = "|".join([str(train.height), ...])
return hashlib.sha256(text.encode()).hexdigest()[:12]
```

```bash
uv run pytest tests/test_slot11.py
```

## Step 2 · Log your run to the class server

The instructor will write the server address on the board, like `http://10.6.1.150:5001`.

```bash
MLFLOW_TRACKING_URI=http://<address-on-board>:5001 uv run python track.py --name yourname
```

```text
     yourname  MAE 5.606  features=base  rows=320,414  data_sha=975bf5819849  (2.7 s)
```

Now try a different run, and log it too:

```bash
MLFLOW_TRACKING_URI=http://<address-on-board>:5001 uv run python track.py --name yourname-slim --features slim
MLFLOW_TRACKING_URI=http://<address-on-board>:5001 uv run python track.py --name yourname-40k --rows 40000
```

> **Fallback** Class server not reachable? Run your own. In a **second terminal**:
> `uv run mlflow server --backend-store-uri sqlite:///mlflow.db --port 5001`
> then use `MLFLOW_TRACKING_URI=http://localhost:5001` in the commands above.

## Step 3 · The compare view

Open the address in your browser (or `open http://localhost:5001` for your own server).
Click the experiment **eta-leaderboard**, tick two runs with a similar MAE, and click **Compare**.
Look at `data_rows` and `data_sha`.

> **Think** Two runs, similar scores, different fingerprints. Were they the same experiment? "A metric without a data fingerprint is a rumour."

## Step 4 · Write this down: first five checks when your model will not learn

1. Can it **overfit 100 rows**? If not, the bug is in the data or the loss, not the model.
2. Is the **label** what you think? Print 5 rows next to 5 predictions.
3. Is the target almost **constant** after your filtering?
4. Are **train and test** from the same distribution? Compare the means.
5. Did your **features** actually get in? Check `model.feature_importances_`.

## If something goes wrong

| what you see | what to do |
|---|---|
| `403 Forbidden` on port 5000 | On a Mac, port 5000 is AirPlay. Always use **5001**. |
| `Connection refused` | The server is not running, or it was started without `--host 0.0.0.0`. |
| hangs for 30 seconds | The Wi-Fi blocks laptop-to-laptop traffic. Use the fallback. |
| all fingerprints are the same | Your fingerprint does not include the column list or row count. |
| `the following arguments are required: --name` | Add `--name yourname`. |
