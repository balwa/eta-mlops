"""Optional browser UI for the ETA service. Post-L15 material, not a lecture.

Two ways to run it:

    scripts/serve.sh start          # mounted at http://localhost:8000/ui
    uv run python -m eta.ui         # standalone on :7860
    uv run python -m eta.ui --share # standalone + a public link, 72 h

Requires the optional extra:  uv sync --extra ui

The one rule this file follows: it does NOT predict. It calls
`eta.service.predict`, the same function the `/predict` endpoint runs, with
the same request object. There is one prediction path in this repo and this
is a client of it, not a second copy. If that ever stops being true, the UI
and the API will disagree in front of a room, which is the exact failure the
course spends L6 teaching them to fear.

It also shows two things the JSON response already contained but nobody read:
the feature vector the model was actually given, and how old the feature
store is. That turns slot 1's silent failure into something you can see.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

import gradio as gr

from eta.service import PredictRequest, load_store, predict, store_info

# A Monday, so the weekday dropdown maps onto real dates and demos repeat.
REF_MONDAY = datetime(2025, 11, 10, tzinfo=timezone.utc)
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

EXAMPLE_RESTAURANTS = [f"R{i:04d}" for i in (1, 42, 117, 288, 356, 500, 601, 742, 899)]


def _training_ranges() -> dict[str, tuple[float, float]]:
    """Honest reference ranges, read from the training data — never from the
    feature store, because the store is the thing that gets corrupted."""
    try:
        import polars as pl

        d = pl.read_parquet(
            "data/labelled.parquet",
            columns=["distance_km", "restaurant_prep_min_estimate", "courier_rating"],
        )
        return {
            "distance_km": (d["distance_km"].min(), d["distance_km"].max()),
            "prep_min_estimate": (
                d["restaurant_prep_min_estimate"].min(),
                d["restaurant_prep_min_estimate"].max(),
            ),
            "courier_rating": (d["courier_rating"].min(), d["courier_rating"].max()),
        }
    except Exception:
        return {}


RANGES = _training_ranges()


def _feature_rows(features: dict) -> list[list]:
    """Feature name, value, and the range the model was trained on."""
    rows = []
    for k, v in features.items():
        lo_hi = RANGES.get(k)
        if lo_hi is None:
            ref, flag = "—", ""
        else:
            lo, hi = lo_hi
            ref = f"{lo:g} – {hi:g}"
            flag = "  ⟵ OUTSIDE" if isinstance(v, (int, float)) and not (lo <= v <= hi) else ""
        rows.append([k, v, ref + flag])
    return rows


def run(restaurant_id: str, n_items: int, weather: str, day: str, hour: int):
    when = REF_MONDAY + timedelta(days=DAYS.index(day), hours=int(hour))
    req = PredictRequest(
        order_id=f"ui-{restaurant_id}-{when.isoformat()}",
        restaurant_id=restaurant_id.strip(),
        n_items=int(n_items),
        weather=weather,
        placed_at=when.isoformat(),
    )
    # The same call the HTTP endpoint makes. Nothing is recomputed here.
    out = predict(req)

    eta = out["eta_minutes"]
    info = store_info()
    age = info.get("age_seconds")
    age_txt = "unknown" if age is None else f"{age:,} s"
    warn = []
    if age is not None and age > 120:
        warn.append(f"feature store is **{age_txt} old** (SLA 120 s)")
    if out["used_default_profile"]:
        warn.append(f"`{restaurant_id}` is not in the store — served the **default profile**")
    outside = [r[0] for r in _feature_rows(out["features_used"]) if "OUTSIDE" in str(r[2])]
    if outside:
        warn.append(f"**{', '.join(outside)}** outside the training range")

    status = (
        f"store refreshed `{info.get('computed_at')}` · age {age_txt} · "
        f"{info.get('rows')} restaurants"
    )
    if warn:
        status += "\n\n" + "\n\n".join(f"⚠️  {w}" for w in warn)

    return f"## {eta:.1f} minutes", _feature_rows(out["features_used"]), status


def build_demo() -> gr.Blocks:
    # Gradio 6 moved `theme` from the Blocks constructor to launch(); when the
    # app is mounted rather than launched there is no launch() to pass it to,
    # so the mounted UI just uses the default theme.
    with gr.Blocks(title="ETA service") as demo:
        gr.Markdown(
            "# ETA service\n"
            "The same model, the same feature store and the same `predict()` "
            "the `/predict` endpoint calls. This page is a client, not a copy."
        )
        with gr.Row():
            with gr.Column(scale=2):
                restaurant = gr.Dropdown(
                    EXAMPLE_RESTAURANTS, value="R0001", label="restaurant_id",
                    allow_custom_value=True, info="R0000–R0899 exist in the store",
                )
                n_items = gr.Slider(1, 14, value=3, step=1, label="n_items")
                weather = gr.Radio(
                    ["clear", "rain", "heavy_rain"], value="rain", label="weather"
                )
                day = gr.Dropdown(DAYS, value="Friday", label="day")
                hour = gr.Slider(0, 23, value=19, step=1, label="hour of day")
                go = gr.Button("Predict", variant="primary")
            with gr.Column(scale=3):
                eta_out = gr.Markdown("## —")
                feats = gr.Dataframe(
                    headers=["feature", "value given to the model", "training range"],
                    label="what the model was actually given",
                    interactive=False,
                    wrap=True,
                )
                status = gr.Markdown()

        inputs = [restaurant, n_items, weather, day, hour]
        go.click(run, inputs=inputs, outputs=[eta_out, feats, status])
        for c in inputs:
            c.change(run, inputs=inputs, outputs=[eta_out, feats, status])
        demo.load(run, inputs=inputs, outputs=[eta_out, feats, status])

        gr.Markdown(
            "---\n"
            "Try it, then in a terminal run `uv run python -m eta.corrupt units` "
            "and `curl -X POST localhost:8000/reload-store`. Change any input to "
            "re-predict. The service will not complain and neither will this page — "
            "but the middle panel will show you exactly what happened."
        )
    return demo


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--share", action="store_true",
                    help="also publish a public gradio.live link, valid 72 h")
    ap.add_argument("--port", type=int, default=7860)
    args = ap.parse_args()

    load_store()
    build_demo().launch(server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()
