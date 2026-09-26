# MLOps — Designing & Operating ML Systems

The course repository. One project, twenty-two lectures, and by the end the
ETA service you start in slot 1 has tracking, tests, a container, a dashboard,
a shadow router and an MCP interface — and it is your code.

**Weekend One covers L1–L12.** Everything here is built for that.

**Class handouts** — one PDF per activity, step by step — are in
[`handouts/`](handouts/). Open the one for the slot we are doing.

---

## Setup

Do this at home, before the weekend. See `SETUP.md` for the full
Apple Silicon instructions, or the prep PDF you were sent.

First install libomp, that is required for LightGBM.

```bash
brew install libomp
```

```bash
uv python install 3.12
uv sync --extra apple          # drop --extra apple on Linux
uv run python verify_stack.py  # every line must say ok
```

Then build the data and the model — about twenty seconds:

```bash
make all
```

---

## What you just built

| | |
|---|---|
| `data/orders.parquet` | 412,000 food-delivery orders across six Indian cities, one year |
| `data/orders.csv`, `.db` | the same rows as CSV and SQLite, for the L5 format race |
| `data/labelled.parquet` | 366,000 rows with a delivery time you can trust |
| `data/feature_store.parquet` | what the service looks up at prediction time |
| `models/eta_model.pkl` | LightGBM, MAE 5.60 min on a held-out future |

The data is **seeded**. Every laptop generates byte-identical files, so a
leaderboard means something. It is also **deliberately flawed** — finding out
how is most of the weekend.

---

## Running the service

```bash
make serve                       # scripts/serve.sh start
curl -s localhost:8000/health

curl -s -X POST localhost:8000/predict \
  -H 'content-type: application/json' \
  -d '{"order_id":"a1","restaurant_id":"R0001","n_items":3,
       "weather":"rain","placed_at":"2025-11-14T19:30:00+00:00"}'
```

`scripts/serve.sh start | stop | restart | status | logs`

Shortcut for one prediction, without typing the long curl:

```bash
scripts/predict.sh R0042             # restaurant R0042, 3 items, rain
scripts/predict.sh R0042 5 clear     # restaurant, items, weather
```

**One service at a time.** If you have two copies of this repo, only start the
service from one of them. `serve.sh start` now refuses to start when port 8000
is already taken, and tells you which folder the other one is running from.

### Optional: a browser UI

```bash
uv sync --extra ui       # adds gradio
scripts/serve.sh restart
open http://localhost:8000/ui
```

A page that calls the same `predict()` the API does, and shows the feature
vector and the feature-store age next to each answer. Optional in the real
sense: without the extra the service has no `/ui` route and behaves
identically. 

---

## The twelve slots

Each slot leaves one file in this repo that wasn't there when it began. The
test tells you when you're done.

Each file has a `TODO` for you to write, and a ready-made `__main__` that
runs the experiment with your code. Run it with `uv run python <file>`.

| # | file | test | handout |
|---|---|---|---|
| 1 | `logs/silent_failure.md` | `pytest tests/test_slot01.py` | `handouts/slot01.pdf` |
| 2 | `baseline_rules.py` | `pytest tests/test_slot02.py` | `handouts/slot02.pdf` |
| 3 | `label_fn.py` | `pytest tests/test_slot03.py` | `handouts/slot03.pdf` |
| 4 | `loss_sweep.py` | `pytest tests/test_slot04.py` | `handouts/slot04.pdf` |
| 5 | `format_bench.py` | `pytest tests/test_slot05.py` | `handouts/slot05.pdf` |
| 6 | `freshness_check.py` | `pytest tests/test_slot06.py` | `handouts/slot06.pdf` |
| 7 | `sampling_compare.py` | `pytest tests/test_slot07.py` | `handouts/slot07.pdf` |
| 8 | `imbalance.py` | `pytest tests/test_slot08.py` | `handouts/slot08.pdf` |
| 9 | `features.py` | `pytest tests/test_slot09.py` | `handouts/slot09.pdf` |
| 10 | `leakage_audit.py` | `pytest tests/test_slot10.py` | `handouts/slot10.pdf` |
| 11 | `track.py` | `pytest tests/test_slot11.py` | `handouts/slot11.pdf` |
| 12 | `test_model.py` | `pytest tests/test_slot12.py` | `handouts/slot12.pdf` |

```bash
make test        # all of them
```

Slot 12's test is the odd one: it asserts that *your* `test_model.py` fails.
That's not a mistake.

---

## Layout

```
eta/          the shipped library — you read it, you don't edit it
  generate.py     seeded data generator
  label.py        reference label function + the honest time split
  feature_job.py  the batch job that writes the feature store
  train.py        trains the model the service ships
  service.py      the FastAPI ETA service
  ui.py           optional gradio UI mounted at /ui (needs --extra ui)
  corrupt.py      one command to break it in four different ways

notebooks/    leak_hunt.ipynb (slot 10)
scripts/      serve.sh, predict.sh, hint_slot03.py, slice_table.py
tests/        one test file per slot
handouts/     one PDF per slot, plus setup
```

---

## Make targets

```
make all      generate + label + feature store + train
make serve    start the ETA service
make verify   verify_stack.py
make test     run the twelve slot tests
make clean    delete everything generated
```

---

## If something breaks

1. `make verify` — is the environment intact?
2. `make all` — rebuild the data and model from the seed
3. `uv run python -m eta.corrupt restore` — undo a corruption from slot 1 or 6
4. `scripts/serve.sh restart` — the service caches the feature store at startup
5. `port 8000 is already in use` — another service is running, maybe from a
   different folder. Run the `kill <pid>` it prints, then `make serve` again.

Never `pip install` into this environment. `uv sync` reads `uv.lock`, which is
why everyone has the same versions.
