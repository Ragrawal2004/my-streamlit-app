# Architecture — AI Financial Goal Assistance Agent

```
BA_project_data.xlsx (Sheet2, 1,000 customers)
        │
        ▼
src/data        load → validate (14 checks) → clean
        │
        ├──────────────► src/features + src/models   (offline: train & compare 4 classifiers,
        │                                              save Logistic Regression pipeline)
        ▼
LangGraph agent (src/agent/graph.py) — structured AgentState
  parse_request ─► load_profile ─► financial_analyzer ─► goal_calculator ─► ml_predictor
        │               │                                                        │
        └── error ◄─────┘                                                        ▼
                                  report ◄─ explanation ◄─ recommendation_engine ◄─ risk_analyzer
                                               │
                                     LLM (optional, any provider) + number-grounding guard
                                               │  fallback: deterministic template
        ▼
FastAPI  POST /assess-goal         Streamlit demo UI         scripts/export_powerbi.py
                                                                   │
                                                  outputs/customer_goal_assessment.csv → Power BI
```

## Decisions and why

| Decision | Choice | Reason |
|---|---|---|
| Numbers | Pure Python tools | Reproducible, testable, auditable. The LLM never computes. |
| Status rule | Coverage break-even (1.0) on two contributions | Financially meaningful, needs no arbitrary cut-off, and validated against real outcomes (83% / 52% / 20% achieved). |
| ML | Logistic Regression | Best CV ROC-AUC (0.905) **and** most interpretable. Trees/boosting did not beat it. |
| ML role | Secondary signal + caution flags | The label's generating process is unknown; ML captures patterns arithmetic misses (e.g. retirement goals rarely achieved), but does not override the arithmetic. |
| Orchestration | LangGraph | Explicit, inspectable state machine with conditional error routing; the graph itself is a presentation artefact. |
| LLM | Optional, provider-agnostic HTTP client | Works with Anthropic, OpenAI or any OpenAI-compatible endpoint. Output is accepted only if every number in it appears in the computed facts; otherwise the template is used. |
| API | FastAPI | Lets other clients (and a future Power BI refresh job) call the agent. |
| Not used | RAG, vector DB, multi-agent, XGBoost | No document corpus to retrieve from; one linear workflow suffices; sklearn's gradient boosting covers the boosting comparison without an extra dependency. |

## Honest scope of "AI"

- **Genuinely learned:** the ML model (trained on 1,000 labelled customers, evaluated on a hold-out set).
- **Genuinely generative (optional):** the LLM's personalised explanation and answers to a free-text question.
- **Deterministic by design:** status, gaps, and recommendation choice. The workflow order is fixed rather than LLM-chosen, because letting a model decide whether to run the calculator would add risk without adding value. This is the "Python = numerical truth" principle.

## Assumptions

1. No column records money already saved toward the goal → starting balance ₹0.
2. `Monthly_Savings` equals Income − Expenses in every row → it is the monthly **surplus** (capacity).
3. `Investment_Amount` is the money already being put away each month → **committed** contribution (capped at the surplus for the 12 rows where it exceeds it).
4. Basic calculations use 0% return and no inflation. A separately labelled projection uses an assumed 7% annual return and is never used for status.
5. Realistic expense-cut ceiling = bringing the expense ratio to the dataset median (57.2%).
