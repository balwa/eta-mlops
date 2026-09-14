"""Slot 1 is done when this passes.

logs/silent_failure.md exists and records a before, an after, and a 200
"""
from pathlib import Path

P = Path("logs/silent_failure.md")


def test_artifact_exists():
    assert P.exists(), "run the slot 1 sequence and save your output to logs/silent_failure.md"


def test_records_before_and_after():
    t = P.read_text().lower()
    assert "before" in t and "after" in t


def test_records_that_nothing_failed():
    t = P.read_text()
    assert "200" in t, "the point of the slot is that it stayed 200 OK — show it"


def test_the_numbers_actually_moved():
    import re
    etas = [float(x) for x in re.findall(r'"eta_minutes":\s*([0-9.]+)', P.read_text())]
    assert len(etas) >= 2, "capture at least one before and one after prediction"
    assert max(etas) / min(etas) > 1.5, "the corrupted ETAs should differ sharply"
