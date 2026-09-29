# AI-Powered Personalized Financial Goal Assistance Agent

**BBA project, Part 2 of TEST → ASSIST → VISUALIZE**
*Predicting Financial Goal Achievement Through Digital Payment and Financial Behaviour Analysis*

## Problem

Part 1 (Jamovi chi-square) tested whether primary digital payment method is associated with goal
achievement: **p = 0.101**, not significant at 5%. This repository reproduces that result (p = 0.1007).
The ML ablation agrees: payment method alone predicts achievement with ROC-AUC 0.55 (close to a coin
flip), and adding it to the model does not improve it.

So *how* someone pays does not explain whether they reach their goal. What does is the arithmetic of
their situation: income, spending, how much they actually put away, and how big and how soon the goal is.
Part 2 turns that into a personal assessment and action plan.

## Solution

Given a customer, the agent answers: *where does this goal stand, and what specifically would keep it on track?*

- **Python tools** compute every number (surplus, ratios, required contribution, gap, months to goal).
- **An ML model** estimates the likelihood of achievement from 1,000 real outcomes and flags when that disagrees with the arithmetic.
- **A LangGraph agent** runs the tools in a validated workflow and produces a structured report plus a plain-English explanation (LLM optional; guarded against invented numbers).
- **Streamlit** demo, **FastAPI** endpoint, and a **Power BI-ready CSV**.

See `ARCHITECTURE.md` for the design rationale.

## Dataset (verified from the file)

1,000 customers × 14 variables (Sheet2; Sheet1 is identical plus Excel notes). No missing values, no
duplicates, perfectly balanced target (500 Yes / 500 No). Full data dictionary: `DATA_PROFILE.md`.

Key facts that shaped the design:
- `Monthly_Savings = Monthly_Income − Monthly_Expenses` for every row → it's the monthly surplus.
- `Expense Ratio` and `Savings Rate` are derived columns that sum to 1.
- There is **no** "amount already saved toward goal" column → a ₹0 starting balance is assumed.
- Surplus ÷ required monthly amount is the strongest single signal: achievement rises from 14% in the
  lowest quintile to 87% in the highest.

## Goal status (explainable, validated)

`required = Goal_Amount ÷ Goal_Time_Period_Months` · `committed = Investment_Amount` · `capacity = Monthly_Savings`

| Status | Rule | Customers | Actually achieved |
|---|---|---|---|
| ON TRACK | committed ≥ required | 226 | 83.2% |
| AT RISK | committed < required ≤ capacity | 482 | 52.5% |
| NEEDS ADJUSTMENT | capacity < required | 292 | 20.2% |

The only threshold is the financial break-even point (1.0). The table shows the rule tracks real outcomes.

## ML model

- **Target:** Goal_Achievement (Yes = 1).
- **Features (13):** age, income, expense ratio, payment frequency, average transaction, impulse score,
  investment, goal amount, goal months, required monthly, log surplus coverage, log investment coverage,
  goal type. Excluded: Customer_ID; Monthly_Expenses / Monthly_Savings / Savings Rate (exact duplicates of
  other columns); payment method (see ablation). No feature uses the target → no leakage.
- **Preprocessing:** one-hot goal type; standard scaling for LR. No imputation needed; no rebalancing needed.
- **Protocol:** stratified 80/20 split, 5-fold CV for comparison, single hold-out evaluation.

| Model | CV ROC-AUC | CV F1 |
|---|---|---|
| **Logistic Regression** | **0.905** | 0.814 |
| Random Forest | 0.897 | 0.814 |
| Gradient Boosting | 0.893 | 0.821 |
| Decision Tree | 0.859 | 0.797 |

**Selected: Logistic Regression.** Hold-out: accuracy 0.83, precision 0.83, recall 0.83, F1 0.83,
ROC-AUC 0.90. Strongest effects: larger goal amount (−), higher income (+), higher impulse spending (−),
higher expense ratio (−), retirement goal (−), travel goal (+). Details: `reports/MODEL_REPORT.md`.

## Agent

```
parse_request → load_profile → financial_analyzer → goal_calculator → ml_predictor
             → risk_analyzer → recommendation_engine → explanation → report
(invalid input at either of the first two steps routes to an error node)
```

| Tool | Output |
|---|---|
| `financial_analyzer` | surplus, savings rate, expense ratio, committed vs uncommitted surplus, health summary |
| `goal_calculator` | required monthly, gaps, coverage, months to goal; separate 7%-return projection (labelled assumption) |
| `ml_predictor` | probability of achievement + top personal drivers |
| `risk_analyzer` | status, risk level, reason, gap, key factors, ML-disagreement caution |
| `recommendation_engine` | primary action + alternatives, each with a number-based reason |

**Recommendation logic:**
ON TRACK → maintain (optionally accelerate with spare surplus).
AT RISK → raise the contribution by exactly the gap, drawn from uninvested surplus; alternative: longer timeline.
NEEDS ADJUSTMENT → cut expenses by exactly the shortfall if a realistic cut (to the median expense ratio) covers it;
otherwise combine a realistic cut with a longer timeline; if spending is already below median, extend the
timeline. Alternatives always include a smaller target for the original timeline.

**LLM guard:** the LLM receives only pre-formatted facts. Any number in its reply that is not in those facts
causes the reply to be discarded and the template used instead. It cannot change status or actions.

## Running

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # optional: set LLM_PROVIDER / LLM_MODEL / LLM_API_KEY

python -m src.models.train                # retrain model (a trained model is already included)
python scripts/profile_data.py            # regenerate DATA_PROFILE.md
python scripts/export_powerbi.py          # regenerate outputs/customer_goal_assessment.csv
python scripts/validate_customers.py      # hand-check real customers → reports/VALIDATION.md
python -m pytest -q                       # 38 tests

streamlit run app/streamlit_app.py        # demo UI
uvicorn src.api.main:app --reload         # API at http://127.0.0.1:8000/docs
python -m src.agent.graph CUST0012        # one report in the terminal
```

## Example (CUST0012, from the real dataset)

```
Goal: Vehicle · ₹7,09,336 · 40 months
Income ₹51,186 · Expenses ₹33,700 · Surplus ₹17,486 · Investing ₹6,500/month
Required ₹17,733/month · Gap ₹247

STATUS: NEEDS ADJUSTMENT (risk HIGH)
WHY: Even the entire monthly surplus (₹17,486) is ₹247 short of the ₹17,733 required.
RECOMMENDED: Cut monthly expenses by ₹247 (0.7% of spending) and invest the full surplus.
  A realistic cut to the median expense ratio would free up to ₹4,401, and impulse
  spending is high, so discretionary spending is the place to start.
ALTERNATIVES: Keep 40 months with a ₹6,99,440 target, or extend to 41 months.
ML likelihood: 14%
```

## Power BI

`outputs/customer_goal_assessment.csv` (1,000 rows, 32 columns, UTF-8 with BOM) includes status, risk,
required saving, gap, coverage, recommendation type/text/reason, expense cut needed, **out-of-fold** ML
probability (each customer scored by a model that never saw them) and the actual outcome for comparison.

## Limitations

- The dataset appears constructed (exactly 500/500 target, clean ranges); how `Goal_Achievement` was
  defined is unknown, so the ML model learns that definition, whatever it is.
- No record of money already saved toward goals; ₹0 start assumed.
- One goal per customer; real people split surplus across goals and need an emergency buffer.
- No inflation, taxes, income growth or market risk in the basic calculation.
- Static snapshot, not live financial data.
- Recommendations are analytical outputs for an academic project, **not regulated financial advice**.
