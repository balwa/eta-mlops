# One command per thing. `make` alone builds everything from scratch.
.PHONY: all data model serve stop verify handouts test clean

all: data model
	@echo "ready. now: make serve"

data:
	uv run python -m eta.generate
	uv run python -m eta.label
	uv run python -m eta.feature_job

model:
	uv run python -m eta.train

serve:
	scripts/serve.sh start

stop:
	scripts/serve.sh stop

verify:
	uv run python verify_stack.py

test:
	uv run pytest tests/ -q

clean:
	rm -rf data models mlflow.db mlruns .run logs/*.png

handouts:
	uv run --with markdown python handouts/build.py
