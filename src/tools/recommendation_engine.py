"""Tool 4 - Recommendation Engine.

Every lever is computed from the customer's own numbers; the primary action is
chosen by status and by which lever actually closes the gap.
Realistic expense cut = bring expense ratio down to the dataset median
(config.EXPENSE_RATIO_MEDIAN); only offered when the customer is above it.
"""
from __future__ import annotations

from src import config
from src.tools.goal_calculator import months_to_goal_basic
from src.utils import fmt_inr, fmt_months, fmt_pct


def compute_levers(p: dict, fin: dict, goal: dict) -> dict:
    b = goal["basic"]
    months, amount = goal["goal_period_months"], goal["goal_amount"]
    income, expenses = fin["monthly_income"], fin["monthly_expenses"]
    median_expenses = config.EXPENSE_RATIO_MEDIAN * income
    freed = max(0.0, expenses - median_expenses)
    capacity_after_cut = b["maximum_monthly_capacity"] + freed
    return {
        "redirect_surplus": {
            "extra_needed": b["monthly_gap_committed"],
            "uncommitted_available": fin["uncommitted_surplus"],
            "closes_gap": b["monthly_gap_committed"] <= fin["uncommitted_surplus"] + 1e-6,
        },
        "expense_cut_to_median": {
            "applicable": freed > 0, "monthly_saving_freed": round(freed, 2),
            "cut_pct_of_expenses": round(freed / expenses, 4) if expenses else 0.0,
            "target_expense_ratio": config.EXPENSE_RATIO_MEDIAN,
            "closes_capacity_gap": freed > 0 and freed >= b["monthly_gap_capacity"],
            "months_to_goal_after_cut": months_to_goal_basic(amount, capacity_after_cut),
        },
        "extend_timeline": {
            "months_at_committed": b["months_to_goal_at_committed"],
            "months_at_capacity": b["months_to_goal_at_capacity"],
            "extra_months_at_capacity": (None if b["months_to_goal_at_capacity"] is None
                                         else max(0, b["months_to_goal_at_capacity"] - int(months))),
        },
        "reduce_goal": {
            "achievable_at_committed": round(b["current_monthly_contribution"] * months, 2),
            "achievable_at_capacity": round(b["maximum_monthly_capacity"] * months, 2),
        },
    }


def recommend(p: dict, fin: dict, goal: dict, risk: dict) -> dict:
    lv = compute_levers(p, fin, goal)
    b, status = goal["basic"], risk["status"]
    months = int(goal["goal_period_months"])
    ec, et, rg, rs = lv["expense_cut_to_median"], lv["extend_timeline"], lv["reduce_goal"], lv["redirect_surplus"]
    impulse_high = (p.get("Impulse_Spending_Score") or 0) > config.IMPULSE_Q3
    caveats = []

    if status == "ON_TRACK":
        primary = {"action": "MAINTAIN",
                   "headline": f"Maintain the current {fmt_inr(b['current_monthly_contribution'])} monthly investment.",
                   "reason": f"It already covers the {fmt_inr(b['required_monthly_contribution'])} required "
                             f"({fmt_pct(b['committed_coverage'], 0)} coverage)."}
        alternatives = []
        if fin["uncommitted_surplus"] > 0 and et["months_at_capacity"] and et["months_at_capacity"] < months:
            alternatives.append({"action": "ACCELERATE",
                                 "headline": f"Optionally reach the goal in {fmt_months(et['months_at_capacity'])} "
                                             f"by directing the full {fmt_inr(b['maximum_monthly_capacity'])} surplus to it.",
                                 "reason": "Only if other needs (emergency buffer, other goals) are already covered."})
    elif status == "AT_RISK":
        share = rs["extra_needed"] / rs["uncommitted_available"] if rs["uncommitted_available"] else 1.0
        primary = {"action": "INCREASE_CONTRIBUTION",
                   "headline": f"Increase the monthly goal contribution by {fmt_inr(rs['extra_needed'])} "
                               f"(to {fmt_inr(b['required_monthly_contribution'])}).",
                   "reason": f"This uses {fmt_pct(share, 0)} of the {fmt_inr(rs['uncommitted_available'])} "
                             f"surplus that is currently not invested, so no spending cut is strictly required."}
        alternatives = [{"action": "EXTEND_TIMELINE",
                         "headline": f"Keep the current contribution and extend the timeline to "
                                     f"{fmt_months(et['months_at_committed'])}.",
                         "reason": f"At {fmt_inr(b['current_monthly_contribution'])}/month the goal needs "
                                   f"{fmt_months(et['months_at_committed'])} instead of {months}."}]
        if share > 0.8:
            caveats.append("The increase uses most of the spare surplus, leaving little buffer.")
    else:  # NEEDS_ADJUSTMENT
        caveats.append("Closing this gap means directing essentially all monthly surplus to one goal.")
        if ec["closes_capacity_gap"]:
            needed = b["monthly_gap_capacity"]
            primary = {"action": "REDUCE_EXPENSES",
                       "headline": f"Cut monthly expenses by {fmt_inr(needed)} "
                                   f"({fmt_pct(needed / fin['monthly_expenses'], 1)} of spending) and invest the full surplus.",
                       "reason": f"That exactly closes the shortfall within the original {months} months. "
                                 f"It is well within a realistic cut: bringing the expense ratio down to the dataset "
                                 f"median of {fmt_pct(ec['target_expense_ratio'])} would free up to "
                                 f"{fmt_inr(ec['monthly_saving_freed'])} a month."
                                 + (" High impulse spending suggests discretionary spending is the place to start." if impulse_high else "")}
        elif ec["applicable"]:
            primary = {"action": "COMBINED",
                       "headline": f"Cut expenses by {fmt_inr(ec['monthly_saving_freed'])} "
                                   f"({fmt_pct(ec['cut_pct_of_expenses'], 0)}) and extend the timeline to "
                                   f"{fmt_months(ec['months_to_goal_after_cut'])}.",
                       "reason": f"A realistic expense cut alone does not close the {fmt_inr(b['monthly_gap_capacity'])} "
                                 f"gap, so it is combined with a longer timeline."
                                 + (" High impulse spending suggests discretionary spending is the place to start." if impulse_high else "")}
        else:
            primary = {"action": "EXTEND_TIMELINE",
                       "headline": f"Extend the timeline to {fmt_months(et['months_at_capacity'])} "
                                   f"while investing the full {fmt_inr(b['maximum_monthly_capacity'])} surplus.",
                       "reason": f"Expenses are already at or below the dataset median ratio, so a longer "
                                 f"timeline is the main lever."}
        alternatives = [{"action": "REDUCE_GOAL",
                         "headline": f"Keep the {months}-month timeline with a smaller target of about "
                                     f"{fmt_inr(rg['achievable_at_capacity'])}.",
                         "reason": f"That is what the full surplus accumulates over {months} months (0% return)."}]
        if primary["action"] != "EXTEND_TIMELINE" and et["months_at_capacity"]:
            alternatives.append({"action": "EXTEND_TIMELINE",
                                 "headline": f"Keep current spending and extend the timeline to {fmt_months(et['months_at_capacity'])}.",
                                 "reason": "Uses the full current surplus with no spending change."})
    return {"primary": primary, "alternatives": alternatives, "levers": lv, "caveats": caveats}
