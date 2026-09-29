import pandas as pd

from src import config
from src.data.loader import clean, load_raw
from src.data.preprocessing import normalise_profile
from src.tools.financial_analyzer import analyze_financial_health
from src.tools.goal_calculator import calculate_goal
from src.tools.recommendation_engine import recommend
from src.tools.risk_analyzer import analyze_risk, classify_status


def run(**kw):
    base = dict(Monthly_Income=100000, Monthly_Expenses=60000, Investment_Amount=10000,
                Goal_Amount=360000, Goal_Time_Period_Months=36, Financial_Goal="Vehicle",
                Impulse_Spending_Score=30)
    base.update(kw)
    p = normalise_profile(base); f = analyze_financial_health(p); g = calculate_goal(p, f)
    r = analyze_risk(p, f, g, None)
    return p, f, g, r, recommend(p, f, g, r)


def test_status_boundaries():
    assert classify_status(1.0, 5.0) == "ON_TRACK"
    assert classify_status(0.99, 1.0) == "AT_RISK"
    assert classify_status(0.2, 0.99) == "NEEDS_ADJUSTMENT"


def test_on_track_maintain():
    *_, r, rec = run()
    assert r["status"] == "ON_TRACK" and r["risk_level"] == "LOW"
    assert rec["primary"]["action"] == "MAINTAIN"


def test_at_risk_increase_contribution():
    *_, r, rec = run(Investment_Amount=4000)
    assert r["status"] == "AT_RISK" and r["financial_gap_monthly"] == 6000
    assert rec["primary"]["action"] == "INCREASE_CONTRIBUTION"
    assert "₹6,000" in rec["primary"]["headline"]


def test_needs_adjustment_expense_cut_closes_gap():
    # income 100k, expenses 70k (ratio 0.70 > median 0.5724): cut frees 12,760
    # requirement 40,000 vs surplus 30,000 -> gap 10,000 < 12,760
    *_, r, rec = run(Monthly_Expenses=70000, Goal_Amount=480000, Goal_Time_Period_Months=12)
    assert r["status"] == "NEEDS_ADJUSTMENT"
    assert rec["primary"]["action"] == "REDUCE_EXPENSES"
    assert "₹10,000" in rec["primary"]["headline"]  # cut only what closes the gap, not the full 12,760


def test_needs_adjustment_combined_when_cut_insufficient():
    *_, r, rec = run(Monthly_Expenses=70000, Goal_Amount=1200000, Goal_Time_Period_Months=12)
    assert rec["primary"]["action"] == "COMBINED"


def test_needs_adjustment_extend_when_expenses_already_low():
    *_, r, rec = run(Monthly_Expenses=40000, Goal_Amount=2400000, Goal_Time_Period_Months=24)
    assert r["status"] == "NEEDS_ADJUSTMENT"
    assert rec["primary"]["action"] == "EXTEND_TIMELINE"
    assert rec["levers"]["extend_timeline"]["months_at_capacity"] == 40


def test_high_impulse_flagged():
    *_, r, _ = run(Impulse_Spending_Score=80)
    assert any(k["factor"] == "Impulse spending score" for k in r["key_factors"])


def test_ml_disagreement_note():
    p, f, g, _, _ = run(Investment_Amount=4000)
    r = analyze_risk(p, f, g, {"available": True, "probability": 0.1})
    assert r["ml_consistency_note"]


def test_config_thresholds_match_dataset():
    df = clean(load_raw())
    sr = df.Monthly_Savings / df.Monthly_Income
    er = df.Monthly_Expenses / df.Monthly_Income
    assert round(sr.quantile(.25), 4) == config.SAVINGS_RATE_Q1
    assert round(sr.quantile(.75), 4) == config.SAVINGS_RATE_Q3
    assert round(er.median(), 4) == config.EXPENSE_RATIO_MEDIAN
    assert round(er.quantile(.75), 4) == config.EXPENSE_RATIO_Q3
    assert int(df.Impulse_Spending_Score.quantile(.75)) == config.IMPULSE_Q3


def test_status_rule_is_monotonic_with_real_outcomes():
    """ON_TRACK customers should achieve goals more often than AT_RISK, and AT_RISK more than NEEDS_ADJUSTMENT."""
    r = config.STATUS_ACHIEVEMENT_RATES
    assert r["ON_TRACK"] > r["AT_RISK"] > r["NEEDS_ADJUSTMENT"]
