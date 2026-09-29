"""Independent hand-check of the agent on real customers (one per recommendation path).
Recomputes every number from the raw Excel columns with plain arithmetic (not the tool code)
and asserts the agent agrees. Writes reports/VALIDATION.md."""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import config
from src.agent.graph import run_assessment
from src.utils import fmt_inr

ROOT = Path(__file__).resolve().parents[1]


def pick_cases():
    df = pd.read_csv(config.OUTPUT_DIR / "customer_goal_assessment.csv")
    cases = []
    for action in ["MAINTAIN", "INCREASE_CONTRIBUTION", "REDUCE_EXPENSES", "COMBINED", "EXTEND_TIMELINE"]:
        cases.append(df[df.Recommendation_Type == action].iloc[0].Customer_ID)
    caution = df[(df.ML_Caution != "") & df.ML_Caution.notna()]
    if len(caution):
        cases.append(caution.iloc[0].Customer_ID)
    return list(dict.fromkeys(cases))  # de-duplicate, keep order


def hand_check(row):
    inc, exp, inv = row.Monthly_Income, row.Monthly_Expenses, row.Investment_Amount
    goal, n = row.Goal_Amount, row.Goal_Time_Period_Months
    surplus = inc - exp
    committed = min(inv, surplus)
    req = goal / n
    if committed >= req:
        status, gap = "ON_TRACK", 0.0
    elif surplus >= req:
        status, gap = "AT_RISK", req - committed
    else:
        status, gap = "NEEDS_ADJUSTMENT", req - surplus
    return dict(surplus=surplus, savings_rate=surplus / inc, expense_ratio=exp / inc,
                committed=committed, req=req, gap=gap, status=status,
                months_current=math.ceil(round(goal / committed, 9)) if committed > 0 else None)


def main():
    raw = pd.read_excel(config.DATA_PATH, sheet_name=config.DATA_SHEET).set_index("Customer_ID")
    md = ["# Validation — agent vs. independent hand calculation", "",
          "Each customer below was recomputed from raw Excel columns with plain arithmetic and "
          "compared with the agent. All assertions passed.", ""]
    for cid in pick_cases():
        h = hand_check(raw.loc[cid])
        out = run_assessment(cid, llm=False)
        b, r = out["goal_calculation"]["basic"], out["risk"]
        assert abs(b["required_monthly_contribution"] - h["req"]) < 0.01
        assert abs(r["financial_gap_monthly"] - h["gap"]) < 0.01
        assert r["status"] == h["status"]
        assert b["months_to_goal_at_committed"] == h["months_current"]
        assert abs(out["financial_health"]["savings_rate"] - h["savings_rate"]) < 1e-4
        assert fmt_inr(h["req"]) in out["report"] and fmt_inr(h["gap"]) in out["report"]
        row = raw.loc[cid]
        md += [f"## {cid} — {row.Financial_Goal} → {r['status']} / {out['recommendation']['primary']['action']}", "",
               f"**Input:** income {fmt_inr(row.Monthly_Income)}, expenses {fmt_inr(row.Monthly_Expenses)}, "
               f"investment {fmt_inr(row.Investment_Amount)}, goal {fmt_inr(row.Goal_Amount)} in "
               f"{row.Goal_Time_Period_Months} months, impulse score {row.Impulse_Spending_Score}. "
               f"Actual outcome in dataset: **{row.Goal_Achievement}**.", "",
               f"**Hand calculation:** surplus = {fmt_inr(row.Monthly_Income)} − {fmt_inr(row.Monthly_Expenses)} = "
               f"{fmt_inr(h['surplus'])}; required = {fmt_inr(row.Goal_Amount)} ÷ {row.Goal_Time_Period_Months} = "
               f"{fmt_inr(h['req'])}; committed = min(investment, surplus) = {fmt_inr(h['committed'])}; "
               f"gap = {fmt_inr(h['gap'])}; status = {h['status']}.", "",
               f"**Agent recommendation:** {out['recommendation']['primary']['headline']}", "",
               f"**Agent explanation:** {out['explanation']}", "",
               "**Check:** ✅ required, gap, status, months-to-goal and savings rate all match; "
               "explanation numbers match the calculation layer.", ""]
        print(f"{cid}: OK  {h['status']:<17} {out['recommendation']['primary']['action']}")
    (ROOT / "reports" / "VALIDATION.md").write_text("\n".join(md))


if __name__ == "__main__":
    main()
