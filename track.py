"""Slot 11 — put your run on the class leaderboard

Log params, metrics AND the data fingerprint. The fingerprint is the
point: it is what settles an argument about two identical-looking scores.

Done when:  uv run pytest tests/test_slot11.py
"""
import argparse

import mlflow


def data_fingerprint(train, test, cols) -> str:
    """A short hash of exactly what you trained on."""
    raise NotImplementedError
