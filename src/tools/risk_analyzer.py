"""Tool 3 - Goal Risk Analyzer (explainable, rule-based, empirically validated)."""
from __future__ import annotations

from src import config
from src.utils import fmt_inr, fmt_pct

RISK_LEVEL = {"ON_TRACK": "LOW", "AT_RISK": "MEDIUM", "NEEDS_ADJUSTMENT": "HIGH"}


def classify_status(committed_coverage: float, capacity_coverage: float) -> str:
    if committed_coverage >= config.COVERAGE_BREAK_EVEN:
        return "ON_TRACK"
    if capacity_coverage >= config.COVERAGE_BREAK_EVEN:
        return "AT_RISK"
    return "NEEDS_ADJUSTMENT"


def analyze_risk(p: dict, fin: dict, goal: dict, ml: dict | None = None) -> dict:
    b = goal["basic"]
    status = classify_status(b["committed_coverage"], b["capacity_coverage"])
    req = b["required_monthly_contribution"]

    if status == "ON_TRACK":
        reason = (f"The {fmt_inr(b['current_monthly_contribution'])} already invested each month "
                  f"covers the {fmt_inr(req)} required.")
        gap = 0.0
    elif status == "AT_RISK":
        reason = (f"Current invested contribution ({fmt_inr(b['current_monthly_contribution'])}) "
                  f"is {fmt_inr(b['monthly_gap_committed'])} short of the {fmt_inr(req)} required, "
                  f"but the full monthly surplus ({fmt_inr(b['maximum_monthly_capacity'])}) could cover it.")
        gap = b["monthly_gap_committed"]
    else:
        reason = (f"Even the entire monthly surplus ({fmt_inr(b['maximum_monthly_capacity'])}) is "
                  f"{fmt_inr(b['monthly_gap_capacity'])} short of the {fmt_inr(req)} required, "
                  f"so the goal amount, timeline or spending must change.")
        gap = b["monthly_gap_capacity"]

    factors = [
        {"factor": "Invested contribution vs requirement",
         "value": fmt_pct(b["committed_coverage"], 0), "impact": "positive" if b["committed_coverage"] >= 1 else "negative"},
        {"factor": "Total surplus vs requirement",
         "value": fmt_pct(b["capacity_coverage"], 0), "impact": "positive" if b["capacity_coverage"] >= 1 else "negative"},
    ]
    er = fin["expense_ratio"]
    if er > config.EXPENSE_RATIO_Q3:
        factors.append({"factor": "Expense ratio", "value": fmt_pct(er),
                        "impact": "negative", "note": f"top 25% of dataset (> {fmt_pct(config.EXPENSE_RATIO_Q3)})"})
    imp = p.get("Impulse_Spending_Score")
    if imp is not None and imp > config.IMPULSE_Q3:
        factors.append({"factor": "Impulse spending score", "value": str(int(imp)),
                        "impact": "negative", "note": f"top 25% of dataset (> {config.IMPULSE_Q3})"})
    if fin["investment_share_of_surplus"] < config.INVESTMENT_SHARE_MEDIAN and status != "ON_TRACK":
        factors.append({"factor": "Share of surplus invested", "value": fmt_pct(fin["investment_share_of_surplus"]),
                        "impact": "negative", "note": f"below dataset median ({fmt_pct(config.INVESTMENT_SHARE_MEDIAN)})"})

    ml_note = None
    if ml and ml.get("available"):
        prob = ml["probability"]
        if status == "ON_TRACK" and prob < 0.4:
            ml_note = (f"Caution: the ML model estimates only {fmt_pct(prob, 0)} likelihood of achievement "
                       "for similar profiles, despite the arithmetic being on track.")
        elif status == "AT_RISK" and prob < 0.3:
            ml_note = (f"Caution: although the gap is closable on paper, the ML model estimates only "
                       f"{fmt_pct(prob, 0)} likelihood of achievement for similar profiles in the dataset.")
        elif status == "NEEDS_ADJUSTMENT" and prob > 0.6:
            ml_note = (f"Note: similar profiles achieved this kind of goal {fmt_pct(prob, 0)} of the time "
                       "per the ML model, but the plan still needs adjustment on current numbers.")

    return {
        "status": status, "risk_level": RISK_LEVEL[status], "reason": reason,
        "financial_gap_monthly": round(gap, 2), "key_factors": factors,
        "historical_achievement_rate_for_status": config.STATUS_ACHIEVEMENT_RATES[status],
        "ml_consistency_note": ml_note,
    }
