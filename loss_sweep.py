"""Slot 4 — sweep the asymmetry

Train the same model at several quantile alphas and plot two business
counters that move in opposite directions. Then pick one and defend it.

Done when:  uv run pytest tests/test_slot04.py
"""
import polars as pl

ALPHAS = [0.5, 0.6, 0.7, 0.8, 0.9]


def promises_broken(pred, actual) -> float:
    """Share of orders where the promise was shorter than reality."""
    raise NotImplementedError


def courier_idle_minutes(pred, actual) -> float:
    """Total minutes couriers wait because the promise was too long."""
    raise NotImplementedError


if __name__ == "__main__":
    ...  # TODO: sweep, tabulate, plot to logs/loss_sweep.png
