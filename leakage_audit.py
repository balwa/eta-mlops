"""Slot 10 — the audit, as code

Project Milestone 2. A check that asserts every feature you use was
available at prediction time. Run it against your own features.py.

First, the hunt:   uv run jupyter lab notebooks/leak_hunt.ipynb
Then, the audit:   uv run python leakage_audit.py     # audits features.FEATURES

Done when:  uv run pytest tests/test_slot10.py
"""
import polars as pl

from eta.label import POST_OUTCOME


def audit(feature_names: list[str]) -> list[str]:
    """Return the feature names that could not have been known at order time."""
    # TODO: POST_OUTCOME lists the columns that only exist after delivery.
    #       Start there. Then ask: what about a column *derived* from one of
    #       them, like "rest_mean_payout"? An exact-match list will miss it.
    raise NotImplementedError


def assert_no_leakage(feature_names: list[str]) -> None:
    bad = audit(feature_names)
    assert not bad, f"features unavailable at prediction time: {bad}"


if __name__ == "__main__":
    from features import FEATURES

    print(f"auditing {len(FEATURES)} features from features.py")
    bad = audit(FEATURES)
    print("clean - every feature is known when the order is placed." if not bad
          else f"LEAKS: {bad}")
