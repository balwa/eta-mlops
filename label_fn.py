"""Slot 3 — write the label function

make_label() turns one raw order into one training label, or tells you
it cannot. The hard part is not the arithmetic. It is deciding what counts.

Done when:  uv run pytest tests/test_slot03.py
"""
import polars as pl


def make_label(orders: pl.DataFrame) -> pl.DataFrame:
    """Raw orders in; rows with a trustworthy `actual_minutes` out.

    Every row you drop is a decision. Count them.
    """
    # TODO: which timestamp is "delivered"? what about cancelled orders?
    #       orders still in flight? timezones? deliveries before pickup?
    raise NotImplementedError


if __name__ == "__main__":
    raw = pl.read_parquet("data/orders.parquet")
    out = make_label(raw)
    print(f"kept {out.height:,} of {raw.height:,}  ({1 - out.height/raw.height:.1%} dropped)")
