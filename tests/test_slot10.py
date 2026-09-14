"""Slot 10 is done when this passes.

the audit catches every post-outcome column
"""
import pytest

leakage_audit = pytest.importorskip("leakage_audit")

HONEST = ["distance_km", "n_items", "city", "weather", "hour", "dow", "courier_rating"]


def test_passes_honest_features():
    assert leakage_audit.audit(HONEST) == []
    leakage_audit.assert_no_leakage(HONEST)


@pytest.mark.parametrize(
    "col",
    ["eta_error_min", "courier_payout_inr", "actual_prep_min", "courier_wait_min",
     "rider_trip_distance_km", "tip_inr", "customer_rating_of_delivery",
     "sla_breach", "delivered_at"],
)
def test_catches_each_post_outcome_column(col):
    assert col in leakage_audit.audit(HONEST + [col]), f"{col} slipped through"


def test_assert_raises():
    with pytest.raises(AssertionError):
        leakage_audit.assert_no_leakage(HONEST + ["eta_error_min"])
