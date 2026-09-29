"""Validation of a single customer profile (dataset row or manual entry)."""
from __future__ import annotations

import math

NUMERIC_FIELDS = ["Monthly_Income", "Monthly_Expenses", "Investment_Amount",
                  "Goal_Amount", "Goal_Time_Period_Months"]


class ProfileError(ValueError):
    pass


def _is_missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or v == ""


def normalise_profile(p: dict) -> dict:
    """Validate inputs and derive Monthly_Savings when absent.

    Monthly_Savings in the dataset is *exactly* Income - Expenses for all 1,000
    rows, so deriving it for manual entries is consistent with the data.
    """
    p = dict(p)
    missing = [f for f in NUMERIC_FIELDS if _is_missing(p.get(f))]
    if missing:
        raise ProfileError(f"Missing required values: {missing}")
    for f in NUMERIC_FIELDS + ["Monthly_Savings"]:
        if not _is_missing(p.get(f)):
            try:
                p[f] = float(p[f])
            except (TypeError, ValueError):
                raise ProfileError(f"{f} must be numeric")
    if p["Monthly_Income"] <= 0:
        raise ProfileError("Monthly_Income must be positive")
    if p["Monthly_Expenses"] < 0 or p["Investment_Amount"] < 0:
        raise ProfileError("Expenses and investment cannot be negative")
    if p["Goal_Amount"] <= 0:
        raise ProfileError("Goal_Amount must be positive")
    if p["Goal_Time_Period_Months"] <= 0:
        raise ProfileError("Goal_Time_Period_Months must be positive")
    if _is_missing(p.get("Monthly_Savings")):
        p["Monthly_Savings"] = p["Monthly_Income"] - p["Monthly_Expenses"]
    p.setdefault("Customer_ID", "MANUAL")
    if _is_missing(p.get("Financial_Goal")):
        p["Financial_Goal"] = "Unspecified"
    return p
