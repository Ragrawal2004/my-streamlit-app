# Model Report — Goal_Achievement classifier

Train 800 / test 200 (stratified). Selection: highest CV ROC-AUC; ties within 0.01 go to the more interpretable model.

## 5-fold CV on training set

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC (±sd) |
|---|---|---|---|---|---|
| Logistic Regression | 0.814 | 0.809 | 0.823 | 0.814 | 0.905 (±0.014) |
| Decision Tree | 0.797 | 0.797 | 0.800 | 0.797 | 0.859 (±0.020) |
| Random Forest | 0.812 | 0.803 | 0.830 | 0.814 | 0.896 (±0.020) |
| Gradient Boosting | 0.819 | 0.812 | 0.833 | 0.820 | 0.893 (±0.017) |

## Selected: Logistic Regression — hold-out test

Accuracy 0.830 · Precision 0.830 · Recall 0.830 · F1 0.830 · ROC-AUC 0.900

| | Pred No | Pred Yes |
|---|---|---|
| Actual No | 83 | 17 |
| Actual Yes | 17 | 83 |

## Ablations

- cv_auc_with_payment_method_added: 0.9038
- cv_auc_payment_method_only: 0.5521
- holdout_auc_capacity_coverage_only: 0.844

## Features

Age, Monthly_Income, Expense_Ratio, Digital_Payment_Frequency, Average_Transaction_Amount, Impulse_Spending_Score, Investment_Amount, Goal_Amount, Goal_Time_Period_Months, Required_Monthly, Log_Capacity_Coverage, Log_Committed_Coverage, Financial_Goal

## Standardised coefficients (sign = direction of effect)

| Feature | Coef |
|---|---|
| Goal_Amount | -2.555 |
| Monthly_Income | +1.270 |
| Impulse_Spending_Score | -0.688 |
| Financial_Goal_Travel | +0.499 |
| Expense_Ratio | -0.481 |
| Financial_Goal_Retirement | -0.462 |
| Digital_Payment_Frequency | -0.250 |
| Financial_Goal_Home Purchase | -0.231 |
| Required_Monthly | +0.177 |
| Average_Transaction_Amount | -0.170 |
| Financial_Goal_Emergency Fund | -0.164 |
| Financial_Goal_Vehicle | +0.164 |
| Log_Committed_Coverage | +0.112 |
| Goal_Time_Period_Months | +0.092 |
| Age | -0.091 |
| Log_Capacity_Coverage | +0.071 |
| Investment_Amount | +0.065 |
| Financial_Goal_Higher Education | -0.026 |

Note: Goal_Amount and Required_Monthly are correlated, so individual coefficients should be read together, not in isolation.