# Data Profile — BA_project_data.xlsx

## Structure
- Sheets: Sheet1 (1000×18), Sheet2 (1000×16).
- Sheet1 first 16 columns identical to Sheet2: **True**. Sheet1's two extra unnamed columns hold only Excel side-notes (ratio definitions). **Sheet2 is used.**

## Data quality
- rows: 1000
- missing_values: 0
- duplicate_rows: 0
- duplicate_ids: 0
- savings_identity_violations: 0
- investment_exceeds_savings: 12
- non_positive_goal_period: 0
- non_positive_income: 0
- `Monthly_Savings == Monthly_Income − Monthly_Expenses` holds for **every row** → savings is the monthly *surplus*, not a goal-specific contribution.
- `Expense Ratio` and `Savings Rate` are exact derivations (Expenses/Income, Savings/Income) and sum to 1.
- **No column records money already saved toward the goal** → assessments assume a ₹0 starting balance.
- 12 rows have Investment_Amount > Monthly_Savings (flagged; committed contribution capped at the surplus).

## Data dictionary

| Column | Type | Description | Range / values |
|---|---|---|---|
| Customer_ID | str | Unique identifier | 1000 unique |
| Age | int64 | Customer age (years) | 21 – 60 (median 41) |
| Monthly_Income | int64 | Monthly income (₹) | 18,055 – 199,772 (median 107,598) |
| Monthly_Expenses | int64 | Monthly expenses (₹) | 5,600 – 168,700 (median 58,200) |
| Monthly_Savings | int64 | Income − Expenses (₹) | 2,690 – 147,124 (median 41,049) |
| Digital_Payment_Frequency | int64 | Digital payments per month | 5 – 100 (median 53) |
| Average_Transaction_Amount | int64 | Average digital transaction (₹) | 100 – 6,000 (median 3,045) |
| Primary_Digital_Payment_Method | str | Main payment method | UPI (523), Mixed (208), Card (187), Wallet (82) |
| Impulse_Spending_Score | int64 | Impulse spending score | 5 – 94 (median 39) |
| Investment_Amount | int64 | Monthly investment (₹) | 300 – 38,700 (median 8,500) |
| Financial_Goal | str | Goal category | Emergency Fund (268), Vehicle (179), Home Purchase (173), Retirement (157), Higher Education (112), Travel (111) |
| Goal_Amount | int64 | Target amount (₹) | 35,052 – 7,950,894 (median 476,306) |
| Goal_Time_Period_Months | int64 | Goal horizon (months) | 3 – 180 (median 28) |
| Goal_Achievement | str | Target label (Yes/No) | No (500), Yes (500) |

## Numeric summary

|                            |   count |             mean |             std |   min |      25% |      50% |              75% |              max |
|:---------------------------|--------:|-----------------:|----------------:|------:|---------:|---------:|-----------------:|-----------------:|
| Age                        |    1000 |     40.93        |    11.49        |    21 |     31   |     41   |     51           |     60           |
| Monthly_Income             |    1000 | 107672           | 52585.7         | 18055 |  61432   | 107598   | 153450           | 199772           |
| Monthly_Expenses           |    1000 |  61414.2         | 34252.2         |  5600 |  32775   |  58200   |  83225           | 168700           |
| Monthly_Savings            |    1000 |  46257.6         | 28487.7         |  2690 |  23388.8 |  41049   |  63801.8         | 147124           |
| Digital_Payment_Frequency  |    1000 |     54.01        |    27.82        |     5 |     30   |     53   |     79           |    100           |
| Average_Transaction_Amount |    1000 |   3074.57        |  1739.17        |   100 |   1565   |   3045   |   4638           |   6000           |
| Impulse_Spending_Score     |    1000 |     39.14        |    16.46        |     5 |     28   |     39   |     50           |     94           |
| Investment_Amount          |    1000 |  10865.1         |  8424.72        |   300 |   4000   |   8500   |  16225           |  38700           |
| Goal_Amount                |    1000 |      1.42603e+06 |     1.81968e+06 | 35052 | 207241   | 476306   |      2.24374e+06 |      7.95089e+06 |
| Goal_Time_Period_Months    |    1000 |     43.75        |    39.79        |     3 |     15   |     28.5 |     57           |    180           |

## Target
- Goal_Achievement: 500 Yes / 500 No (perfectly balanced → likely a synthetic/constructed dataset; no resampling needed).

## Achievement by goal type

| Financial_Goal   |   n |   achieved |      median_goal |   median_months |
|:-----------------|----:|-----------:|-----------------:|----------------:|
| Emergency Fund   | 268 |      0.679 | 184116           |            15   |
| Higher Education | 112 |      0.607 | 461872           |            29.5 |
| Home Purchase    | 173 |      0.214 |      2.82186e+06 |            69   |
| Retirement       | 157 |      0.089 |      4.41347e+06 |           100   |
| Travel           | 111 |      0.757 | 188756           |            11   |
| Vehicle          | 179 |      0.642 | 593096           |            36   |

## Correlation of numeric variables with achievement

|                            |   Achieved |
|:---------------------------|-----------:|
| Goal_Amount                |     -0.501 |
| Goal_Time_Period_Months    |     -0.396 |
| Impulse_Spending_Score     |     -0.184 |
| Digital_Payment_Frequency  |     -0.129 |
| Age                        |     -0.013 |
| Average_Transaction_Amount |      0.003 |
| Monthly_Expenses           |      0.191 |
| Investment_Amount          |      0.218 |
| Monthly_Income             |      0.304 |
| Monthly_Savings            |      0.332 |

## Part 1 re-check: payment method × achievement

| Primary_Digital_Payment_Method   |   No |   Yes |
|:---------------------------------|-----:|------:|
| Card                             |  105 |    82 |
| Mixed                            |   95 |   113 |
| UPI                              |  265 |   258 |
| Wallet                           |   35 |    47 |

Chi-square = 6.236, dof = 3, **p = 0.101** (matches Jamovi p = 0.101).

## Key relationship: surplus coverage of the required monthly amount

Coverage = Monthly_Savings ÷ (Goal_Amount ÷ Goal_Time_Period_Months), split into quintiles:

|                 |   mean |   size |
|:----------------|-------:|-------:|
| (0.0604, 0.688] |  0.14  |    200 |
| (0.688, 1.41]   |  0.315 |    200 |
| (1.41, 2.542]   |  0.505 |    200 |
| (2.542, 4.698]  |  0.67  |    200 |
| (4.698, 46.018] |  0.87  |    200 |

## Validation of the goal-status rule

|                  |   mean |   size |
|:-----------------|-------:|-------:|
| AT_RISK          |  0.525 |    482 |
| NEEDS_ADJUSTMENT |  0.202 |    292 |
| ON_TRACK         |  0.832 |    226 |

## Dataset-derived thresholds (copied into src/config.py)

- SAVINGS_RATE_Q1 = 0.3337
- SAVINGS_RATE_MEDIAN = 0.4276
- SAVINGS_RATE_Q3 = 0.5226
- EXPENSE_RATIO_MEDIAN = 0.5724
- EXPENSE_RATIO_Q3 = 0.6663
- IMPULSE_Q3 = 50
- INVESTMENT_SHARE_MEDIAN = 0.2348