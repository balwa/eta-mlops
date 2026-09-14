"""The ETA service. Slot 1 starts it; slot 22 is still the same file.

    uv run uvicorn eta.service:app --port 8000

The request carries what the app knows. Everything else is looked up in the
feature store the batch job writes. That division is deliberate - it is what
makes the service only as correct as its last feature refresh, which is the
whole of slot 1 and slot 6.

Nothing in here is a joke or a trap. Every questionable line is a line that
exists, verbatim, in real serving code.
"""

from __future__ import annotations

import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import pandas as pd
import polars as pl
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_PATH = Path("models/eta_model.pkl")
STORE_PATH = Path("data/feature_store.parquet")

# The service has to answer even when the store has never heard of a
# restaurant. Someone picked these numbers once and nobody has looked since.
DEFAULT_PROFILE = {
    "city": "Mumbai",
    "distance_km": 3.5,
    "prep_min_estimate": 15.0,
    "courier_rating": 4.4,
}

app = FastAPI(title="ETA service", version="1.0.0")

_bundle = pickle.loads(MODEL_PATH.read_bytes()) if MODEL_PATH.exists() else None
_store: dict[str, dict] = {}
_store_meta: dict = {}


def load_store() -> None:
    """Re-read the feature store from disk. Called at startup and on demand."""
    global _store, _store_meta
    if not STORE_PATH.exists():
        _store, _store_meta = {}, {"computed_at": None, "rows": 0}
        return
    df = pl.read_parquet(STORE_PATH)
    _store = {r["restaurant_id"]: r for r in df.to_dicts()}
    _store_meta = {
        "computed_at": df["computed_at"][0] if df.height else None,
        "rows": df.height,
        "distance_unit": df["distance_unit"][0] if df.height else None,
    }


load_store()


class PredictRequest(BaseModel):
    order_id: str
    restaurant_id: str
    n_items: int = Field(ge=1, le=30)
    weather: Literal["clear", "rain", "heavy_rain"] = "clear"
    placed_at: str | None = Field(
        default=None, description="ISO timestamp; defaults to now. Set it to make demos repeatable."
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_loaded": _bundle is not None,
        "store_rows": _store_meta.get("rows", 0),
    }


@app.get("/store-info")
def store_info() -> dict:
    computed_at = _store_meta.get("computed_at")
    age = None
    if computed_at:
        age = round(
            (datetime.now(timezone.utc) - datetime.fromisoformat(computed_at)).total_seconds()
        )
    return {**_store_meta, "age_seconds": age}


@app.post("/reload-store")
def reload_store() -> dict:
    load_store()
    return store_info()


@app.post("/predict")
def predict(req: PredictRequest) -> dict:
    if _bundle is None:
        raise HTTPException(503, "no model - run: uv run python -m eta.train")

    profile = _store.get(req.restaurant_id)
    used_default = profile is None
    if used_default:
        profile = DEFAULT_PROFILE

    when = datetime.fromisoformat(req.placed_at) if req.placed_at else datetime.now(timezone.utc)

    features = {
        "distance_km": profile["distance_km"],
        "prep_min_estimate": profile["prep_min_estimate"],
        "courier_rating": profile["courier_rating"],
        "n_items": req.n_items,
        "hour": when.hour,
        "dow": when.isoweekday(),
        "city": profile["city"],
        "weather": req.weather,
    }

    X = pd.DataFrame([features])[_bundle["features"]]
    for c in X.columns:
        if c in _bundle["categorical"]:
            X[c] = X[c].astype("category")
        else:
            # "Make it robust so it stops 500-ing in prod." It worked.
            X[c] = pd.to_numeric(X[c], errors="coerce")
    # Whatever arrives, the service answers. These two lines are the ones they
    # should be angry about by the end of the weekend.
    X = X.fillna(0)

    eta = float(_bundle["model"].predict(X)[0])

    return {
        "order_id": req.order_id,
        "eta_minutes": round(eta, 1),
        "model_version": _bundle["metrics"]["model_mae"],
        "features_used": features,
        "store_computed_at": _store_meta.get("computed_at"),
        "used_default_profile": used_default,
    }


# --- optional browser UI on /ui -------------------------------------------
# Post-L15 extra, installed with `uv sync --extra ui`. When gradio is absent
# this block does nothing at all: no import cost, no route, no behaviour
# change. Nothing in the 22 lectures depends on it.
def _mount_optional_ui() -> None:
    global app
    try:
        import gradio as gr
    except ImportError:
        return
    # Uninstalling gradio leaves behind its runtime `gradio/hash_seed.txt`,
    # and Python imports that empty directory as a namespace package — so the
    # import above succeeds with nothing in it. Check for the real thing.
    if not hasattr(gr, "mount_gradio_app"):
        return
    try:
        from eta.ui import build_demo

        app = gr.mount_gradio_app(app, build_demo(), path="/ui")
    except Exception as e:  # noqa: BLE001 — a broken UI must never break /predict
        print(f"[service] /ui not mounted: {type(e).__name__}: {e}")


_mount_optional_ui()
