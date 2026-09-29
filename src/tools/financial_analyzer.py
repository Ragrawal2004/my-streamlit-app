"""Tool 1 - Financial Health Analyzer (pure, deterministic)."""
from __future__ import annotations

from src import config
from src.utils import fmt_inr, fmt_pct


def _band(value, low, high, labels=("below the typical range", "in the typical range",
                                     "above the typical range")):
    return labels[0] if value < low else labels[2] if value > high else labels[1]


def analyze_financial_health(p: dict) -> dict:
    income, expenses = p["Monthly_Income"], p["Monthly_Expenses"]
    savings, invest = p["Monthly_Savings"], p["Investment_Amount"]
    expense_ratio = expenses / income
    savings_rate = savings / income
    committed = max(0.0, min(invest, savings))
    uncommitted = max(0.0, savings - committed)
    invest_share = committed / savings if savings > 0 else 0.0

    flags = []
    if savings <= 0:
        flags.append("Expenses equal or exceed income: no monthly surplus.")
    if invest > savings:
        flags.append("Investment exceeds monthly surplus (likely funded from past savings); "
                     "committed contribution is capped at the surplus.")

    sr_band = _band(savings_rate, config.SAVINGS_RATE_Q1, config.SAVINGS_RATE_Q3)
    summary = (f"Saves {fmt_pct(savings_rate)} of income ({sr_band} for this dataset, "
               f"interquartile range {fmt_pct(config.SAVINGS_RATE_Q1)}–{fmt_pct(config.SAVINGS_RATE_Q3)}). "
               f"{fmt_inr(committed)} of the {fmt_inr(savings)} monthly surplus is already invested; "
               f"{fmt_inr(uncommitted)} is uncommitted.")
    return {
        "monthly_income": income, "monthly_expenses": expenses, "monthly_savings": savings,
        "monthly_surplus": savings, "expense_ratio": round(expense_ratio, 4),
        "savings_rate": round(savings_rate, 4), "investment_amount": invest,
        "committed_contribution": committed, "uncommitted_surplus": uncommitted,
        "investment_share_of_surplus": round(invest_share, 4),
        "savings_rate_band": sr_band,
        "high_expense_ratio": expense_ratio > config.EXPENSE_RATIO_Q3,
        "data_flags": flags, "financial_health_summary": summary,
    }
