"""Load and validate the project dataset. Never invents values."""
from __future__ import annotations

import pandas as pd

from src import config


class DataValidationError(ValueError):
    pass


def load_raw(path=config.DATA_PATH, sheet=config.DATA_SHEET) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet)


def validate(df: pd.DataFrame) -> dict:
    """Return a report of data-quality checks; raise on hard failures."""
    missing_cols = [c for c in config.REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")
    report = {
        "rows": len(df),
        "missing_values": int(df[config.REQUIRED_COLUMNS].isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_ids": int(df["Customer_ID"].duplicated().sum()),
        "savings_identity_violations": int(
            (df["Monthly_Savings"] != df["Monthly_Income"] - df["Monthly_Expenses"]).sum()),
        "investment_exceeds_savings": int((df["Investment_Amount"] > df["Monthly_Savings"]).sum()),
        "non_positive_goal_period": int((df["Goal_Time_Period_Months"] <= 0).sum()),
        "non_positive_income": int((df["Monthly_Income"] <= 0).sum()),
    }
    if report["duplicate_ids"]:
        raise DataValidationError("Duplicate Customer_IDs found")
    return report


def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df[config.REQUIRED_COLUMNS].copy()
    out["Customer_ID"] = out["Customer_ID"].astype(str).str.strip()
    for c in ["Primary_Digital_Payment_Method", "Financial_Goal", "Goal_Achievement"]:
        out[c] = out[c].astype(str).str.strip()
    return out


def load_customers(path=config.DATA_PATH) -> pd.DataFrame:
    df = clean(load_raw(path))
    validate(df)
    return df.set_index("Customer_ID", drop=False)


def get_customer(df: pd.DataFrame, customer_id: str) -> dict:
    cid = str(customer_id).strip().upper()
    if cid not in df.index:
        raise KeyError(f"Customer ID '{customer_id}' not found")
    return df.loc[cid].to_dict()
