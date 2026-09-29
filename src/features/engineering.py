"""Feature engineering for the ML model.

Excluded on purpose:
  - Customer_ID (identifier)
  - Monthly_Expenses, Monthly_Savings, Savings Rate: exact functions of Income
    and Expense Ratio in this dataset (Savings = Income - Expenses), so keeping
    them adds only perfect collinearity.
  - Goal_Achievement (target).
No feature is computed from the target, so there is no target leakage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "Age", "Monthly_Income", "Expense_Ratio", "Digital_Payment_Frequency",
    "Average_Transaction_Amount", "Impulse_Spending_Score", "Investment_Amount",
    "Goal_Amount", "Goal_Time_Period_Months", "Required_Monthly",
    "Log_Capacity_Coverage", "Log_Committed_Coverage",
]
CATEGORICAL_FEATURES = ["Financial_Goal"]
# Primary_Digital_Payment_Method is deliberately excluded from the final model:
# alone it scores CV ROC-AUC ~0.55 and removing it does not lower model AUC,
# consistent with the Part 1 chi-square result (p = 0.101). See models/model_meta.json.
PAYMENT_FEATURE = "Primary_Digital_Payment_Method"
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Expense_Ratio"] = out["Monthly_Expenses"] / out["Monthly_Income"]
    out["Required_Monthly"] = out["Goal_Amount"] / out["Goal_Time_Period_Months"]
    savings = out["Monthly_Savings"].clip(lower=1)
    committed = np.minimum(out["Investment_Amount"], out["Monthly_Savings"]).clip(lower=1)
    out["Log_Capacity_Coverage"] = np.log(savings / out["Required_Monthly"])
    out["Log_Committed_Coverage"] = np.log(committed / out["Required_Monthly"])
    return out


def target(df: pd.DataFrame) -> pd.Series:
    return (df["Goal_Achievement"] == "Yes").astype(int)
