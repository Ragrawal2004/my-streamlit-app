import math

import pytest

from src.data.preprocessing import ProfileError, normalise_profile
from src.tools.financial_analyzer import analyze_financial_health
from src.tools.goal_calculator import (calculate_goal, months_to_goal_basic,
                                       months_to_goal_with_return,
                                       required_monthly_with_return)
from src.utils import fmt_inr


def prof(**kw):
    base = dict(Monthly_Income=100000, Monthly_Expenses=60000, Investment_Amount=10000,
                Goal_Amount=360000, Goal_Time_Period_Months=36, Financial_Goal="Vehicle")
    base.update(kw)
    return normalise_profile(base)


def test_surplus_derived_from_income_minus_expenses():
    assert prof()["Monthly_Savings"] == 40000


def test_ratios():
    f = analyze_financial_health(prof())
    assert f["savings_rate"] == pytest.approx(0.4)
    assert f["expense_ratio"] == pytest.approx(0.6)
    assert f["savings_rate"] + f["expense_ratio"] == pytest.approx(1.0)
    assert f["committed_contribution"] == 10000 and f["uncommitted_surplus"] == 30000


def test_required_contribution_and_gap():
    p = prof(); f = analyze_financial_health(p); g = calculate_goal(p, f)["basic"]
    assert g["required_monthly_contribution"] == 10000
    assert g["monthly_gap_committed"] == 0
    p = prof(Investment_Amount=7000); f = analyze_financial_health(p); g = calculate_goal(p, f)["basic"]
    assert g["monthly_gap_committed"] == 3000
    assert g["months_to_goal_at_committed"] == math.ceil(360000 / 7000)


def test_investment_capped_at_surplus():
    p = prof(Monthly_Expenses=95000, Investment_Amount=9000)  # surplus 5000
    f = analyze_financial_health(p)
    assert f["committed_contribution"] == 5000 and f["data_flags"]


def test_zero_contribution_months_is_none():
    assert months_to_goal_basic(1000, 0) is None


def test_annuity_math_roundtrip():
    pmt = required_monthly_with_return(1_000_000, 60, 0.07)
    assert pmt < 1_000_000 / 60            # returns reduce the requirement
    fv = pmt * (((1 + 0.07 / 12) ** 60 - 1) / (0.07 / 12))
    assert fv == pytest.approx(1_000_000, rel=1e-9)
    assert months_to_goal_with_return(1_000_000, pmt, 0.07) == 60


def test_zero_rate_projection_equals_basic():
    assert required_monthly_with_return(1200, 12, 0) == 100


@pytest.mark.parametrize("bad", [dict(Monthly_Income=0), dict(Goal_Time_Period_Months=0),
                                 dict(Goal_Amount=-5), dict(Monthly_Income=None),
                                 dict(Monthly_Expenses="abc")])
def test_invalid_profiles_rejected(bad):
    with pytest.raises(ProfileError):
        prof(**bad)


def test_indian_formatting():
    assert fmt_inr(2000000) == "₹20,00,000"
    assert fmt_inr(55556) == "₹55,556"
    assert fmt_inr(999) == "₹999"
    assert fmt_inr(-1500) == "-₹1,500"
