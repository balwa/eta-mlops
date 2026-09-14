"""Verify the course environment in ~10 s. Run:  uv run python verify_stack.py
Reports, never crashes: every line is  ok / warn / FAIL  so a student can paste the whole thing into a help thread."""
from __future__ import annotations
import importlib, importlib.metadata, platform, shutil, subprocess, sys, tempfile, time, urllib.request

OK, WARN, FAIL = "  ok  ", " warn ", " FAIL "
fails: list[str] = []

def line(status: str, label: str, detail: str = "") -> None:
    print(f"[{status}] {label:<34} {detail}")
    if status == FAIL:
        fails.append(label)

# ---- interpreter ---------------------------------------------------------
py = platform.python_version()
line(OK if py.startswith("3.12") else FAIL, "python", f"{py}  {sys.executable}")
line(OK, "machine", f"{platform.system()} {platform.machine()}")

# ---- imports: one line per tool, version shown so the room can compare ---
TOOLS = [
    ("pandas", "pandas"), ("polars", "polars"), ("duckdb", "duckdb"), ("pyarrow", "pyarrow"),
    ("pandera", "pandera"), ("sklearn", "scikit-learn"), ("lightgbm", "lightgbm"),
    ("imblearn", "imbalanced-learn"), ("mlflow", "mlflow"), ("evidently", "evidently"),
    ("pytest", "pytest"), ("prometheus_client", "prometheus-client"), ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"), ("onnx", "onnx"), ("onnxruntime", "onnxruntime"),
    ("skl2onnx", "skl2onnx"), ("torch", "torch"), ("dagster", "dagster"),
    ("openai", "openai"), ("mcp", "mcp"), ("langfuse", "langfuse"), ("psycopg", "psycopg"),
]
for mod, name in TOOLS:
    try:
        importlib.import_module(mod)
        line(OK, name, importlib.metadata.version(name))
    except Exception as e:  # noqa: BLE001
        line(FAIL, name, f"{type(e).__name__}: {e}")

# mlx-lm is Apple-only; absence elsewhere is expected
try:
    import mlx_lm  # type: ignore
    line(OK, "mlx-lm (Apple extra)", getattr(mlx_lm, "__version__", ""))
except Exception:
    apple = platform.system() == "Darwin" and platform.machine() == "arm64"
    line(WARN if apple else OK, "mlx-lm (Apple extra)", "not installed — `uv sync --extra apple`" if apple else "n/a on this platform")

# ---- three real smoke tests: data, model, export -------------------------
try:
    import duckdb, polars as pl
    t = time.perf_counter()
    df = pl.DataFrame({"city": ["A", "B", "A"] * 1000, "mins": list(range(3000))})
    n = duckdb.sql("select city, avg(mins) from df group by city").fetchall()
    line(OK, "duckdb ⟷ polars (Arrow)", f"{len(n)} groups in {1000*(time.perf_counter()-t):.0f} ms")
except Exception as e:  # noqa: BLE001
    line(FAIL, "duckdb ⟷ polars (Arrow)", str(e))

try:
    import numpy as np, lightgbm as lgb, mlflow
    X = np.random.rand(500, 4); y = X @ [3, -2, 1, 0.5] + np.random.rand(500)
    with tempfile.TemporaryDirectory() as d:
        mlflow.set_tracking_uri(f"sqlite:///{d}/mlflow.db")  # MLflow 3 retired the plain file store
        with mlflow.start_run():
            m = lgb.LGBMRegressor(n_estimators=20, verbose=-1).fit(X, y)
            mlflow.log_metric("train_r2", float(m.score(X, y)))
    line(OK, "lightgbm → mlflow (local sqlite)", "trained + logged")
except Exception as e:  # noqa: BLE001
    line(FAIL, "lightgbm → mlflow (local sqlite)", str(e))

try:
    from sklearn.linear_model import Ridge
    from skl2onnx import to_onnx
    import onnxruntime as ort, numpy as np
    X = np.random.rand(50, 3).astype(np.float32); r = Ridge().fit(X, X.sum(1))
    onx = to_onnx(r, X[:1])
    sess = ort.InferenceSession(onx.SerializeToString())
    sess.run(None, {sess.get_inputs()[0].name: X[:2]})
    line(OK, "sklearn → ONNX → onnxruntime", "exported + ran")
except Exception as e:  # noqa: BLE001
    line(FAIL, "sklearn → ONNX → onnxruntime", str(e))

# ---- external services: warn only, they're installed separately ----------
if shutil.which("docker"):
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True, timeout=10)
        line(OK, "docker daemon", "reachable")
    except Exception:
        line(WARN, "docker daemon", "docker found but daemon not reachable — start Docker Desktop")
else:
    line(WARN, "docker", "not on PATH — needed from L6 onward")

try:
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
        import json; models = [m["name"] for m in json.load(r).get("models", [])]
        line(OK, "ollama", f"running · models: {', '.join(models) or 'none pulled yet'}")
except Exception:
    line(WARN, "ollama", "not reachable on :11434 — needed for L8 and L22")

print()
print("FAILED:", ", ".join(fails) if fails else "nothing — environment ready.")
raise SystemExit(1 if fails else 0)
