"""Slot 3 is done when this passes.

make_label drops the unlabelable rows and keeps the rest
"""
import polars as pl
import pytest

label_fn = pytest.importorskip("label_fn")


@pytest.fixture(scope="module")
def out():
    return label_fn.make_label(pl.read_parquet("data/orders.parquet"))


def test_has_a_label_column(out):
    assert "actual_minutes" in out.columns


def test_no_null_labels(out):
    assert out["actual_minutes"].null_count() == 0


def test_no_negative_or_absurd_labels(out):
    assert out["actual_minutes"].min() > 0, "a delivery cannot take negative time"
    assert out["actual_minutes"].max() < 12 * 60


def test_dropped_the_right_order_of_magnitude(out):
    raw = pl.read_parquet("data/orders.parquet").height
    kept = out.height / raw
    assert 0.80 < kept < 0.95, (
        f"kept {kept:.1%}. Too high means you kept rows you cannot label; "
        "too low means you threw away good ones."
    )


def test_pune_is_not_silently_dropped(out):
    share = (out["city"] == "Pune").mean()
    assert share > 0.10, (
        f"Pune is {share:.1%} of your labelled rows. It is ~16% of the data. "
        "Dropping a whole city is not a fix."
    )
