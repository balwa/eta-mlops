"""Slot 12 is done when this passes.

you wrote behavioural tests, and some of them fail
"""
import ast
from pathlib import Path

P = Path("test_model.py")


def test_file_exists():
    assert P.exists()


def test_has_at_least_four_tests():
    tree = ast.parse(P.read_text())
    tests = [n for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert len(tests) >= 4, f"only {len(tests)} tests — write more"


def test_nothing_is_still_a_stub():
    src = P.read_text()
    assert "NotImplementedError" not in src, "finish the stubs"


def test_some_of_them_fail():
    """This is the scoreboard. A suite that passes has not been tried hard enough."""
    import subprocess
    r = subprocess.run(["uv", "run", "pytest", str(P), "-q", "--no-header", "-p", "no:cacheprovider"],
                       capture_output=True, text=True)
    assert r.returncode != 0, (
        "every behavioural test passed. Either the model is perfect, or the "
        "tests are too easy. It is the tests."
    )
