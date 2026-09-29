"""Tool 2 - Goal Calculator.

ASSUMPTION (dataset has no 'amount already saved toward goal' column):
every goal is assessed as starting from ₹0 today.

Two contributions are distinguished, both taken from actual columns:
  committed = min(Investment_Amount, Monthly_Savings)  - money already being put away
  capacity  = Monthly_Savings (= Income - Expenses)    - the most that could be put away

BASIC calculation (used for status): 0% return, required = goal / months.
PROJECTION (illustrative only): monthly compounding at an ASSUMED annual return.
"""
from __future__ import annotations

import math

from src import config


def _ceil(x: float) -> int:
    """Ceiling that ignores floating-point noise (60.0000000001 -> 60)."""
    return math.ceil(round(x, 9))


def required_monthly_basic(goal: float, months: float) -> float:
    return goal / months


def months_to_goal_basic(goal: float, monthly: float):
    return None if monthly <= 0 else _ceil(goal / monthly)


def required_monthly_with_return(goal: float, months: float, annual_rate: float) -> float:
    r = annual_rate / 12
    if r == 0:
        return goal / months
    return goal * r / ((1 + r) ** months - 1)


def months_to_goal_with_return(goal: float, monthly: float, annual_rate: float):
    if monthly <= 0:
        return None
    r = annual_rate / 12
    if r == 0:
        return _ceil(goal / monthly)
    return _ceil(math.log(1 + goal * r / monthly) / math.log(1 + r))


def calculate_goal(p: dict, fin: dict, annual_return: float = config.ASSUMED_ANNUAL_RETURN) -> dict:
    goal, months = p["Goal_Amount"], p["Goal_Time_Period_Months"]
    committed, capacity = fin["committed_contribution"], max(0.0, fin["monthly_savings"])
    req = required_monthly_basic(goal, months)
    return {
        "financial_goal": p.get("Financial_Goal"),
        "goal_amount": goal, "goal_period_months": months,
        "current_amount_toward_goal": 0.0,
        "current_amount_assumption": "Not in dataset; assumed ₹0 saved toward this goal so far.",
        "remaining_goal_amount": goal,
        "basic": {
            "required_monthly_contribution": round(req, 2),
            "current_monthly_contribution": committed,
            "maximum_monthly_capacity": capacity,
            "monthly_gap_committed": round(max(0.0, req - committed), 2),
            "monthly_gap_capacity": round(max(0.0, req - capacity), 2),
            "committed_coverage": round(committed / req, 4),
            "capacity_coverage": round(capacity / req, 4),
            "months_to_goal_at_committed": months_to_goal_basic(goal, committed),
            "months_to_goal_at_capacity": months_to_goal_basic(goal, capacity),
            "feasible_within_timeline": capacity >= req,
        },
        "assumption_based_projection": {
            "label": f"ASSUMPTION: {annual_return:.0%} annual return, monthly compounding. "
                     "Illustrative only; not used for goal status.",
            "annual_return": annual_return,
            "required_monthly_contribution": round(required_monthly_with_return(goal, months, annual_return), 2),
            "months_to_goal_at_committed": months_to_goal_with_return(goal, committed, annual_return),
            "months_to_goal_at_capacity": months_to_goal_with_return(goal, capacity, annual_return),
        },
    }
