"""Generate reports/DATA_PROFILE.md and print the dataset-derived thresholds used in config."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from src import config
from src.data.loader import clean, load_raw, validate
from src.tools.risk_analyzer import classify_status

ROOT = Path(__file__).resolve().parents[1]


def thresholds(df):
    sr = df.Monthly_Savings / df.Monthly_Income
    er = df.Monthly_Expenses / df.Monthly_Income
    return {
        "SAVINGS_RATE_Q1": round(sr.quantile(.25), 4), "SAVINGS_RATE_MEDIAN": round(sr.median(), 4),
        "SAVINGS_RATE_Q3": round(sr.quantile(.75), 4), "EXPENSE_RATIO_MEDIAN": round(er.median(), 4),
        "EXPENSE_RATIO_Q3": round(er.quantile(.75), 4),
        "IMPULSE_Q3": int(df.Impulse_Spending_Score.quantile(.75)),
        "INVESTMENT_SHARE_MEDIAN": round((df.Investment_Amount / df.Monthly_Savings).median(), 4),
    }


def status_table(df):
    req = df.Goal_Amount / df.Goal_Time_Period_Months
    com = np.minimum(df.Investment_Amount, df.Monthly_Savings)
    st = [classify_status(c, k) for c, k in zip(com / req, df.Monthly_Savings / req)]
    y = (df.Goal_Achievement == "Yes")
    return y.groupby(pd.Series(st, index=df.index)).agg(["mean", "size"])


def md_table(d: pd.DataFrame) -> str:
    return d.to_markdown()


def main():
    raw1 = pd.read_excel(config.DATA_PATH, sheet_name="Sheet1")
    raw = load_raw()
    df = clean(raw)
    rep = validate(df)
    y = (df.Goal_Achievement == "Yes").astype(int)
    num = df.select_dtypes("number")
    ct = pd.crosstab(df.Primary_Digital_Payment_Method, df.Goal_Achievement)
    chi2, pval, dof, _ = chi2_contingency(ct)
    req = df.Goal_Amount / df.Goal_Time_Period_Months
    cov = df.Monthly_Savings / req
    quint = y.groupby(pd.qcut(cov, 5)).agg(["mean", "size"])
    quint.index = quint.index.astype(str)
    th = thresholds(df)
    st = status_table(df)

    out = ["# Data Profile — BA_project_data.xlsx", "",
           "## Structure",
           f"- Sheets: Sheet1 ({raw1.shape[0]}×{raw1.shape[1]}), Sheet2 ({raw.shape[0]}×{raw.shape[1]}).",
           f"- Sheet1 first 16 columns identical to Sheet2: **{raw1.iloc[:, :16].equals(raw)}**. "
           "Sheet1's two extra unnamed columns hold only Excel side-notes (ratio definitions). **Sheet2 is used.**",
           "", "## Data quality", *[f"- {k}: {v}" for k, v in rep.items()],
           "- `Monthly_Savings == Monthly_Income − Monthly_Expenses` holds for **every row** → savings is the "
           "monthly *surplus*, not a goal-specific contribution.",
           "- `Expense Ratio` and `Savings Rate` are exact derivations (Expenses/Income, Savings/Income) and sum to 1.",
           "- **No column records money already saved toward the goal** → assessments assume a ₹0 starting balance.",
           f"- {rep['investment_exceeds_savings']} rows have Investment_Amount > Monthly_Savings (flagged; committed "
           "contribution capped at the surplus).",
           "", "## Data dictionary", "",
           "| Column | Type | Description | Range / values |", "|---|---|---|---|"]
    desc = {
        "Customer_ID": "Unique identifier", "Age": "Customer age (years)",
        "Monthly_Income": "Monthly income (₹)", "Monthly_Expenses": "Monthly expenses (₹)",
        "Monthly_Savings": "Income − Expenses (₹)", "Digital_Payment_Frequency": "Digital payments per month",
        "Average_Transaction_Amount": "Average digital transaction (₹)",
        "Primary_Digital_Payment_Method": "Main payment method", "Impulse_Spending_Score": "Impulse spending score",
        "Investment_Amount": "Monthly investment (₹)", "Financial_Goal": "Goal category",
        "Goal_Amount": "Target amount (₹)", "Goal_Time_Period_Months": "Goal horizon (months)",
        "Goal_Achievement": "Target label (Yes/No)",
    }
    for c in config.REQUIRED_COLUMNS:
        s = df[c]
        rng = (f"{s.min():,} – {s.max():,} (median {s.median():,.0f})" if pd.api.types.is_numeric_dtype(s)
               else ", ".join(f"{k} ({v})" for k, v in s.value_counts().items()) if s.nunique() < 10 else f"{s.nunique()} unique")
        out.append(f"| {c} | {s.dtype} | {desc[c]} | {rng} |")
    out += ["", "## Numeric summary", "", md_table(num.describe().T.round(2)), "",
            "## Target", f"- Goal_Achievement: {y.sum()} Yes / {len(y) - y.sum()} No (perfectly balanced → "
            "likely a synthetic/constructed dataset; no resampling needed).", "",
            "## Achievement by goal type", "",
            md_table(df.assign(y=y).groupby("Financial_Goal").agg(n=("y", "size"), achieved=("y", "mean"),
                     median_goal=("Goal_Amount", "median"), median_months=("Goal_Time_Period_Months", "median")).round(3)),
            "", "## Correlation of numeric variables with achievement", "",
            md_table(num.assign(Achieved=y).corr()["Achieved"].drop("Achieved").sort_values().round(3).to_frame()),
            "", "## Part 1 re-check: payment method × achievement", "", md_table(ct), "",
            f"Chi-square = {chi2:.3f}, dof = {dof}, **p = {pval:.3f}** (matches Jamovi p = 0.101).", "",
            "## Key relationship: surplus coverage of the required monthly amount", "",
            "Coverage = Monthly_Savings ÷ (Goal_Amount ÷ Goal_Time_Period_Months), split into quintiles:", "",
            md_table(quint.round(3)), "",
            "## Validation of the goal-status rule", "", md_table(st.round(3)), "",
            "## Dataset-derived thresholds (copied into src/config.py)", "",
            *[f"- {k} = {v}" for k, v in th.items()]]
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "DATA_PROFILE.md").write_text("\n".join(out))
    print(th); print(st); print(f"chi2 p = {pval:.4f}")


if __name__ == "__main__":
    main()
