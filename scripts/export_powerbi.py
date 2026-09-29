"""Run the full agent over every customer and write outputs/customer_goal_assessment.csv
for Power BI. Uses the deterministic template explanation (no LLM cost for 1,000 rows)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import config
from src.agent.graph import build_graph
from src.agent.nodes import _customers
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from src.features.engineering import FEATURES, add_features, target
from src.models.train import candidates, SEED
from src.models.predict import load_model


def out_of_fold_probabilities():
    """Each customer's probability comes from a model that never saw that customer."""
    df = add_features(_customers())
    model = candidates()[load_model()[1]["selected_model"]]
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    proba = cross_val_predict(model, df[FEATURES], target(df), cv=cv, method="predict_proba")[:, 1]
    return dict(zip(df.index, proba.round(4)))


def main():
    graph = build_graph(llm=False)  # False -> force template explanation
    oof = out_of_fold_probabilities()
    rows = []
    for cid in _customers().index:
        s = graph.invoke({"customer_id": cid, "tool_calls": []})
        p, f, g, r, rec, ml = (s["profile"], s["financial_health"], s["goal_calculation"],
                               s["risk"], s["recommendation"], s["ml_prediction"])
        b, lv = g["basic"], rec["levers"]
        rows.append({
            "Customer_ID": cid, "Age": p["Age"], "Financial_Goal": p["Financial_Goal"],
            "Primary_Digital_Payment_Method": p["Primary_Digital_Payment_Method"],
            "Goal_Amount": p["Goal_Amount"], "Goal_Time_Period_Months": int(p["Goal_Time_Period_Months"]),
            "Monthly_Income": p["Monthly_Income"], "Monthly_Expenses": p["Monthly_Expenses"],
            "Monthly_Savings": p["Monthly_Savings"], "Investment_Amount": p["Investment_Amount"],
            "Impulse_Spending_Score": p["Impulse_Spending_Score"],
            "Savings_Rate": f["savings_rate"], "Expense_Ratio": f["expense_ratio"],
            "Uncommitted_Surplus": f["uncommitted_surplus"],
            "Required_Monthly_Saving": b["required_monthly_contribution"],
            "Current_Monthly_Contribution": b["current_monthly_contribution"],
            "Monthly_Savings_Gap": r["financial_gap_monthly"],
            "Committed_Coverage": b["committed_coverage"], "Capacity_Coverage": b["capacity_coverage"],
            "Months_To_Goal_At_Current": b["months_to_goal_at_committed"],
            "Months_To_Goal_At_Full_Surplus": b["months_to_goal_at_capacity"],
            "Feasible_Within_Timeline": b["feasible_within_timeline"],
            "Goal_Status": r["status"], "Risk_Level": r["risk_level"],
            "Recommendation_Type": rec["primary"]["action"],
            "Recommendation": rec["primary"]["headline"],
            "Recommendation_Reason": rec["primary"]["reason"],
            "Alternative_Recommendation": rec["alternatives"][0]["headline"] if rec["alternatives"] else "",
            "Expense_Cut_Needed": lv["expense_cut_to_median"]["monthly_saving_freed"],
            "ML_Probability": oof[cid],  # out-of-fold (5-fold CV)
            "ML_Caution": r["ml_consistency_note"] or "",
            "Actual_Goal_Achievement": p["Goal_Achievement"],
        })
    out = pd.DataFrame(rows)
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    path = config.OUTPUT_DIR / "customer_goal_assessment.csv"
    out.to_csv(path, index=False, encoding="utf-8-sig")  # BOM so Power BI/Excel read ₹ correctly
    print(f"Wrote {len(out)} rows to {path}")
    print(out.groupby("Goal_Status").agg(n=("Customer_ID", "size"),
                                          achieved=("Actual_Goal_Achievement", lambda s: (s == "Yes").mean())))
    print(out["Recommendation_Type"].value_counts())


if __name__ == "__main__":
    main()
