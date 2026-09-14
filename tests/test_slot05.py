"""Slot 5 is done when this passes.

the benchmark is honest: repeated, warm, and same answer every way
"""
import pytest

format_bench = pytest.importorskip("format_bench")


def test_timed_returns_ms_and_result():
    ms, out = format_bench.timed(lambda: sum(range(100_000)), repeats=3)
    assert ms > 0 and out == sum(range(100_000))


def test_timed_takes_the_best_not_the_first():
    calls = []

    def f():
        calls.append(1)
        return 1

    format_bench.timed(f, repeats=3)
    assert len(calls) == 3, "time it more than once or you are timing your disk cache"


def test_results_were_recorded():
    assert len(format_bench.RESULTS) >= 3, "race at least three formats"
    assert {"approach", "ms"} <= set(format_bench.RESULTS[0]), "record approach and ms"
