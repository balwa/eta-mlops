# Setup — do this before the weekend

Apple Silicon MacBook Pro (M1/M2/M3, 16 GB is fine).

Budget **45 minutes**, most of it downloads. Do it on good wifi at home.
Do not do it in the classroom on the morning — thirty people pulling 2 GB of
Docker images through one router does not end well.

The goal: `uv run python verify_stack.py` prints `ok` on every line and
`FAILED: nothing — environment ready.` at the bottom. Bring the laptop like
that and slot 1 just works.

---

## 1 · Command-line tools and Homebrew

```bash
xcode-select --install
```

A dialog appears; click Install and wait. If it says the tools are already
installed, you're fine.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Homebrew prints two or three `export` commands at the end. **Run them** — it
is easy to skip that and then wonder why `brew` is not found.

## 2 · Docker Desktop and Ollama

```bash
brew install --cask docker
brew install ollama
```

Open Docker Desktop once from Applications so the daemon actually starts, and
accept its prompts. Then, in a terminal:

```bash
ollama serve &
```

## 3 · uv, and the course environment

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Open a new terminal window** — the installer edits your shell config and the
old window won't see it.

```bash
git clone https://github.com/balwa/eta-mlops.git
cd eta-mlops
uv python install 3.12
uv sync --extra apple
```

`uv sync` reads `uv.lock`, so you get byte-for-byte the same versions as
everyone else in the room. That matters more than it sounds: half the
activities are leaderboards, and a leaderboard across different library
versions is meaningless.

**Never `pip install` into this environment.** If you need a package, say so
and it goes in the lockfile for everyone.

## 4 · Pre-pull the heavy things

A small language model (keep it under 4 B parameters on a 16 GB machine):

```bash
ollama pull llama3.2:3b
```

Docker images:

```bash
docker pull pgvector/pgvector:pg17
docker pull prom/prometheus
docker pull grafana/grafana
```

## 5 · Build the data

```bash
make all
```

About 30 seconds. It generates a year of delivery orders, labels them, builds
a feature store and trains a model. Everything is seeded, so your files are
identical to everyone else's.

This writes roughly **350 MB** into `data/`. Make sure you have a couple of GB
free.

## 6 · Verify

```bash
uv run python verify_stack.py
```

Every line should say `ok`. The last line should say:

```
FAILED: nothing — environment ready.
```

`warn` on docker or ollama just means the service isn't running — start Docker
Desktop, run `ollama serve &`, and try again. `warn` on `mlx-lm` is fine if
you skipped `--extra apple`, but do install it; L14 uses it.

Then check the service starts:

```bash
make serve
curl -s localhost:8000/health
```

You should see:

```json
{"status":"ok","model_loaded":true,"store_rows":900}
```

Stop it again with `scripts/serve.sh stop`.

---

## If something breaks

Paste the **whole** output of `verify_stack.py` into the help thread — that's
what it's designed for, and it tells us more than "it didn't work" ever will.

Common ones:

| what you see | what it means |
|---|---|
| `command not found: brew` | you skipped Homebrew's `export` lines — reopen the terminal |
| `command not found: uv` | same thing, for uv — open a new terminal |
| `docker daemon not reachable` | Docker Desktop isn't running; open it from Applications |
| `ollama not reachable on :11434` | run `ollama serve &` |
| `No space left on device` | `data/` needs ~350 MB and Docker images another ~1.5 GB |
| `did not come up in 60 s` | something else is on port 8000 — `PORT=8001 scripts/serve.sh start` |

There is a setup amnesty during the first break on Saturday. It is a safety
net, not a plan — it costs you the best activity of the morning.

---

## A note on reading ahead

`eta/` is the shipped library. You're meant to read it — that's part of the
point.

Two exceptions. `eta/label.py` is the answer to Saturday's third activity and
`eta/generate.py` is how the data was made. Both are right there and nobody is
going to stop you. But those activities are built around finding things out,
and knowing the answer in advance turns forty minutes of genuinely good
detective work into typing. Your call.
