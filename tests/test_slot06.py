"""Slot 6 is done when this passes.

the freshness assertion fires on a stale store and not on a fresh one
"""
import pytest

freshness_check = pytest.importorskip("freshness_check")
httpx = pytest.importorskip("httpx")


def _service_up() -> bool:
    try:
        return httpx.get("http://localhost:8000/health", timeout=2).status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _service_up(), reason="start the service first")


def test_passes_on_a_fresh_store():
    import subprocess
    subprocess.run(["uv", "run", "python", "-m", "eta.feature_job"], check=True, capture_output=True)
    httpx.post("http://localhost:8000/reload-store", timeout=5)
    freshness_check.check_freshness(120)


def test_fires_on_a_stale_store():
    import subprocess
    subprocess.run(["uv", "run", "python", "-m", "eta.corrupt", "freeze", "--hours", "3"],
                   check=True, capture_output=True)
    httpx.post("http://localhost:8000/reload-store", timeout=5)
    with pytest.raises(AssertionError):
        freshness_check.check_freshness(120)
    subprocess.run(["uv", "run", "python", "-m", "eta.corrupt", "restore"],
                   check=True, capture_output=True)
    httpx.post("http://localhost:8000/reload-store", timeout=5)
