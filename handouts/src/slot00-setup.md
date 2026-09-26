# Setup and everyday commands

**File:** keep this page open all weekend · **Time:** 45 min at home, before class

## 1. One-time setup (do this at home)

Open the **Terminal** app and run these, one by one.

```bash
xcode-select --install
brew install libomp        # needs Homebrew: see SETUP.md if brew is not found
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Now **close the Terminal and open a new one** (so it can find `uv`). Then:

```bash
git clone https://github.com/balwa/eta-mlops.git
cd eta-mlops
uv python install 3.12
uv sync --extra apple
make all
uv run python verify_stack.py
```

`make all` builds the data and the model. It takes about one minute.
The last line of `verify_stack.py` must say:

```text
FAILED: nothing — environment ready.
```

> **Note** A `warn` for docker or ollama is okay for Weekend One.

## 2. Getting the latest version (start of each day)

```bash
cd eta-mlops
git pull
```

## 3. Five rules for the weekend

1. **Always work inside the `eta-mlops` folder.** Every command assumes it. Check with `pwd`.
2. **Always put `uv run` in front of `python` and `pytest`.** It uses the course environment.
3. **Never `pip install`.** If something is missing, tell the instructor.
4. **Only one copy of the service.** If you have two copies of the repo, start the service from one only.
5. **Your work goes in the file for that slot.** The test tells you when you are done.

## 4. Commands you will use again and again

| what you want | command |
|---|---|
| start the ETA service | `make serve` |
| is it running? | `scripts/serve.sh status` |
| stop it | `scripts/serve.sh stop` |
| restart it | `scripts/serve.sh restart` |
| see its log | `scripts/serve.sh logs` |
| one prediction | `scripts/predict.sh R0001` |
| check one slot | `uv run pytest tests/test_slot04.py` |
| check all slots | `make test` |
| undo a corruption | `uv run python -m eta.corrupt restore` |
| make the service re-read the store | `curl -s -X POST localhost:8000/reload-store` |

After `make serve`, this should print `"store_rows":900`:

```bash
curl -s localhost:8000/health
```

## 5. If something goes wrong

| what you see | what to do |
|---|---|
| `port 8000 is already in use ... NOT starting` | Another service is running (maybe from another folder). Run the `kill <number>` it shows, then `make serve` again. |
| `command not found: uv` or `brew` | Open a new Terminal window and try again. |
| `No such file ... data/...` | Run `make all`. |
| `503 no model` | Run `make model`. |
| predictions look strange or all the same | `uv run python -m eta.corrupt restore`, then the `reload-store` command above. |
| `NotImplementedError` | You have not written that function yet. That is expected. |
| anything else | Copy the **whole** error and show it to the instructor. |
