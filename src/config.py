"""Central configuration: paths, column names, and every documented threshold.

Every threshold below is either a financial break-even point (1.0 coverage)
or a quantile computed from the dataset (see scripts/profile_data.py, which
recomputes them; tests/test_config.py asserts they still match the data).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "BA_project_data.xlsx"
DATA_SHEET = "Sheet2"  # Sheet1 is identical plus Excel side-notes in 2 unnamed columns
MODEL_DIR = ROOT / "models"
MODEL_PATH = MODEL_DIR / "goal_model.joblib"
MODEL_META_PATH = MODEL_DIR / "model_meta.json"
OUTPUT_DIR = ROOT / "outputs"

REQUIRED_COLUMNS = [
    "Customer_ID", "Age", "Monthly_Income", "Monthly_Expenses", "Monthly_Savings",
    "Digital_Payment_Frequency", "Average_Transaction_Amount",
    "Primary_Digital_Payment_Method", "Impulse_Spending_Score", "Investment_Amount",
    "Financial_Goal", "Goal_Amount", "Goal_Time_Period_Months", "Goal_Achievement",
]
TARGET = "Goal_Achievement"
PAYMENT_METHODS = ["UPI", "Mixed", "Card", "Wallet"]
FINANCIAL_GOALS = ["Emergency Fund", "Vehicle", "Home Purchase", "Retirement",
                   "Higher Education", "Travel"]

# ---- Goal status (financial break-even logic) --------------------------------
# committed coverage = committed monthly contribution / required monthly contribution
# capacity coverage  = full monthly surplus            / required monthly contribution
# ON_TRACK          : committed coverage >= 1.0  (money already invested covers the goal)
# AT_RISK           : committed < 1.0 <= capacity (feasible only if more surplus is redirected)
# NEEDS_ADJUSTMENT  : capacity coverage < 1.0    (even 100% of surplus is not enough)
COVERAGE_BREAK_EVEN = 1.0

# ---- Dataset-derived reference points (1,000 customers, Sheet2) ---------------
SAVINGS_RATE_Q1 = 0.3337      # 25th percentile
SAVINGS_RATE_MEDIAN = 0.4276
SAVINGS_RATE_Q3 = 0.5226      # 75th percentile
EXPENSE_RATIO_MEDIAN = 0.5724  # target used for the "realistic expense cut" lever
EXPENSE_RATIO_Q3 = 0.6663      # above this = high expense ratio
IMPULSE_Q3 = 50                # above this = high impulse spending
INVESTMENT_SHARE_MEDIAN = 0.2348  # Investment_Amount / Monthly_Savings, median

# ---- Assumption-based projection (clearly labelled, NOT used for status) ------
ASSUMED_ANNUAL_RETURN = 0.07  # illustrative long-run balanced-portfolio assumption

DISCLAIMER = ("This is an analytical academic-project assessment, not regulated "
              "financial advice.")

# Observed Goal_Achievement = "Yes" rate for customers the status rule places in
# each group (empirical validation of the rule; recomputed by profile_data.py).
STATUS_ACHIEVEMENT_RATES = {"ON_TRACK": 0.832, "AT_RISK": 0.525, "NEEDS_ADJUSTMENT": 0.202}
STATUS_COUNTS = {"ON_TRACK": 226, "AT_RISK": 482, "NEEDS_ADJUSTMENT": 292}
