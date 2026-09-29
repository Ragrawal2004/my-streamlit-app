"""LangGraph nodes. Each node calls exactly one deterministic tool (or the LLM for
wording only) and records itself in state['tool_calls'] for traceability."""
from __future__ import annotations

import re
from functools import lru_cache

from src import config
from src.agent.llm import get_llm
from src.agent.prompts import SYSTEM_PROMPT, USER_TEMPLATE
from src.data.loader import get_customer, load_customers
from src.data.preprocessing import ProfileError, normalise_profile
from src.models.predict import predict_goal_probability
from src.tools.financial_analyzer import analyze_financial_health
from src.tools.goal_calculator import calculate_goal
from src.tools.recommendation_engine import recommend
from src.tools.risk_analyzer import analyze_risk
from src.utils import fmt_inr, fmt_months, fmt_pct

WHAT_IF_FIELDS = {"Goal_Amount", "Goal_Time_Period_Months", "Monthly_Expenses",
                  "Investment_Amount", "Monthly_Income"}


@lru_cache(maxsize=1)
def _customers():
    return load_customers()


def _trace(state, name):
    return state.get("tool_calls", []) + [name]


# ---------------------------------------------------------------- request/profile
def parse_request(state):
    if not state.get("customer_id") and not state.get("manual_profile"):
        return {"error": "Provide either a customer_id or a manual_profile.",
                "tool_calls": _trace(state, "parse_request")}
    bad = set((state.get("what_if") or {})) - WHAT_IF_FIELDS
    if bad:
        return {"error": f"Unsupported what-if fields: {sorted(bad)}",
                "tool_calls": _trace(state, "parse_request")}
    return {"tool_calls": _trace(state, "parse_request"), "error": None}


def load_profile(state):
    calls = _trace(state, "load_profile")
    try:
        if state.get("customer_id"):
            raw = get_customer(_customers(), state["customer_id"])
        else:
            raw = dict(state["manual_profile"])
        what_if = state.get("what_if") or {}
        raw.update(what_if)
        if what_if and ("Monthly_Income" in what_if or "Monthly_Expenses" in what_if):
            raw["Monthly_Savings"] = None  # re-derive surplus consistently
        profile = normalise_profile(raw)
    except KeyError as e:
        return {"error": str(e).strip("'\""), "tool_calls": calls}
    except ProfileError as e:
        return {"error": f"Invalid profile: {e}", "tool_calls": calls}
    return {"profile": profile, "tool_calls": calls}


def route_after(state):
    return "error" if state.get("error") else "ok"


# ---------------------------------------------------------------- tool nodes
def financial_health_node(state):
    return {"financial_health": analyze_financial_health(state["profile"]),
            "tool_calls": _trace(state, "financial_analyzer")}


def goal_calculation_node(state):
    return {"goal_calculation": calculate_goal(state["profile"], state["financial_health"]),
            "tool_calls": _trace(state, "goal_calculator")}


def ml_prediction_node(state):
    return {"ml_prediction": predict_goal_probability(state["profile"]),
            "tool_calls": _trace(state, "ml_predictor")}


def risk_node(state):
    return {"risk": analyze_risk(state["profile"], state["financial_health"],
                                 state["goal_calculation"], state["ml_prediction"]),
            "tool_calls": _trace(state, "risk_analyzer")}


def recommendation_node(state):
    return {"recommendation": recommend(state["profile"], state["financial_health"],
                                        state["goal_calculation"], state["risk"]),
            "tool_calls": _trace(state, "recommendation_engine")}


# ---------------------------------------------------------------- explanation
def build_facts(state) -> dict:
    p, f, g, r, rec, ml = (state["profile"], state["financial_health"], state["goal_calculation"],
                           state["risk"], state["recommendation"], state["ml_prediction"])
    b = g["basic"]
    facts = {
        "customer_id": p.get("Customer_ID"), "goal": p.get("Financial_Goal"),
        "goal_amount": fmt_inr(g["goal_amount"]), "timeline": fmt_months(g["goal_period_months"]),
        "monthly_income": fmt_inr(f["monthly_income"]), "monthly_expenses": fmt_inr(f["monthly_expenses"]),
        "monthly_surplus": fmt_inr(f["monthly_savings"]), "savings_rate": fmt_pct(f["savings_rate"]),
        "expense_ratio": fmt_pct(f["expense_ratio"]),
        "current_monthly_investment": fmt_inr(b["current_monthly_contribution"]),
        "required_monthly_contribution": fmt_inr(b["required_monthly_contribution"]),
        "status": r["status"], "risk_level": r["risk_level"], "status_reason": r["reason"],
        "monthly_gap": fmt_inr(r["financial_gap_monthly"]),
        "months_to_goal_at_current_investment": fmt_months(b["months_to_goal_at_committed"]),
        "key_factors": [f"{k['factor']}: {k['value']} ({k['impact']})" for k in r["key_factors"]],
        "primary_recommendation": rec["primary"]["headline"] + " " + rec["primary"]["reason"],
        "alternatives": [a["headline"] for a in rec["alternatives"]],
        "caveats": rec["caveats"],
        "assumption": g["current_amount_assumption"],
    }
    if ml.get("available"):
        facts["ml_probability_of_achievement"] = fmt_pct(ml["probability"], 0)
        facts["ml_top_drivers"] = [f"{d['feature']} {d['direction']} the likelihood" for d in ml["top_drivers"]]
    if r.get("ml_consistency_note"):
        facts["ml_caution"] = r["ml_consistency_note"]
    return facts


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set[str]:
    return {m.replace(",", "").rstrip(".") for m in _NUM.findall(text)}


def numbers_grounded(text: str, facts: dict) -> tuple[bool, list[str]]:
    """Every number in the LLM text must appear in the facts (small counts 0-12 allowed)."""
    allowed = _numbers(str(facts))
    unknown = [n for n in _numbers(text)
               if n not in allowed and not (n.isdigit() and int(n) <= 12)]
    return (not unknown, unknown)


def template_explanation(state) -> str:
    fx = build_facts(state)
    r, rec = state["risk"], state["recommendation"]
    parts = [f"For the {fx['goal']} goal of {fx['goal_amount']} over {fx['timeline']}, the plan needs "
             f"{fx['required_monthly_contribution']} a month. {r['reason']}"]
    parts.append(f"Recommended next step: {rec['primary']['headline']} {rec['primary']['reason']}")
    if rec["alternatives"]:
        parts.append("Alternative: " + rec["alternatives"][0]["headline"])
    if fx.get("ml_probability_of_achievement"):
        parts.append(f"The ML model, trained on 1,000 customers, estimates a "
                     f"{fx['ml_probability_of_achievement']} likelihood of achievement for this profile.")
    if fx.get("ml_caution"):
        parts.append(fx["ml_caution"])
    return " ".join(parts)


def explanation_node(state, llm=None):
    calls = _trace(state, "explanation")
    # llm=None -> read env config; llm=False -> force deterministic template
    llm = get_llm() if llm is None else (llm or None)
    if llm is None:
        return {"explanation": template_explanation(state), "explanation_source": "template",
                "tool_calls": calls}
    facts = build_facts(state)
    fact_text = "\n".join(f"- {k}: {v}" for k, v in facts.items())
    try:
        text = llm(SYSTEM_PROMPT, USER_TEMPLATE.format(facts=fact_text,
                                                       question=state.get("question") or ""))
    except Exception as e:  # network/auth failure -> degrade gracefully
        return {"explanation": template_explanation(state),
                "explanation_source": f"template (LLM unavailable: {type(e).__name__})",
                "tool_calls": calls}
    ok, unknown = numbers_grounded(text, facts)
    if not ok:
        return {"explanation": template_explanation(state),
                "explanation_source": f"template (LLM output rejected: ungrounded numbers {unknown[:5]})",
                "tool_calls": calls}
    return {"explanation": text.strip(), "explanation_source": "llm", "tool_calls": calls + ["llm"]}


# ---------------------------------------------------------------- report
def report_node(state):
    p, g, r, rec, f, ml = (state["profile"], state["goal_calculation"], state["risk"],
                           state["recommendation"], state["financial_health"], state["ml_prediction"])
    b = g["basic"]
    lines = [
        "CUSTOMER FINANCIAL GOAL ASSESSMENT", "=" * 34,
        f"Customer: {p.get('Customer_ID')}", f"Goal: {p.get('Financial_Goal')}",
        f"Goal Amount: {fmt_inr(g['goal_amount'])}", f"Timeline: {fmt_months(g['goal_period_months'])}", "",
        f"Monthly Income: {fmt_inr(f['monthly_income'])}   Expenses: {fmt_inr(f['monthly_expenses'])}",
        f"Monthly Surplus: {fmt_inr(f['monthly_savings'])}   Savings Rate: {fmt_pct(f['savings_rate'])}   "
        f"Expense Ratio: {fmt_pct(f['expense_ratio'])}", "",
        f"Current Monthly Investment: {fmt_inr(b['current_monthly_contribution'])}",
        f"Required Monthly Contribution: {fmt_inr(b['required_monthly_contribution'])}",
        f"Monthly Gap: {fmt_inr(r['financial_gap_monthly'])}",
        f"Estimated Completion at Current Investment: {fmt_months(b['months_to_goal_at_committed'])}", "",
        f"STATUS: {r['status'].replace('_', ' ')}  (risk: {r['risk_level']})",
        f"WHY: {r['reason']}", "",
        f"RECOMMENDED ACTION: {rec['primary']['headline']}", f"  Reason: {rec['primary']['reason']}",
    ]
    for a in rec["alternatives"]:
        lines.append(f"ALTERNATIVE: {a['headline']}")
    lines += ["", "KEY FACTORS:"] + [f"  • {k['factor']}: {k['value']} ({k['impact']})" for k in r["key_factors"]]
    if ml.get("available"):
        lines.append(f"\nML likelihood of achievement: {fmt_pct(ml['probability'], 0)} "
                     f"({ml['model']}, hold-out ROC-AUC {ml['holdout_auc']})")
    if r.get("ml_consistency_note"):
        lines.append(r["ml_consistency_note"])
    lines += ["", "EXPLANATION:", state["explanation"], "",
              f"Assumption: {g['current_amount_assumption']}", f"IMPORTANT: {config.DISCLAIMER}"]
    return {"report": "\n".join(lines), "tool_calls": _trace(state, "report")}


def error_node(state):
    return {"report": f"ERROR: {state['error']}"}
