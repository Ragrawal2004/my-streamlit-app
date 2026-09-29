"""Streamlit demo. Run: streamlit run app/streamlit_app.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from src import config
from src.agent.graph import run_assessment
from src.agent.llm import get_llm
from src.agent.nodes import _customers
from src.utils import fmt_inr, fmt_months, fmt_pct

st.set_page_config(page_title="Financial Goal Assistant", page_icon="🎯", layout="wide")

STATUS_STYLE = {"ON_TRACK": ("#2E6B4F", "On track"), "AT_RISK": ("#B7791F", "At risk"),
                "NEEDS_ADJUSTMENT": ("#9B2C2C", "Needs adjustment")}
st.markdown("""<style>
.status{padding:1.1rem 1.4rem;border-radius:6px;color:#fff;margin:.4rem 0 1rem}
.status h2{margin:0;color:#fff;font-size:1.6rem;letter-spacing:.02em}
.status p{margin:.3rem 0 0;opacity:.95}
.card{background:#fff;border:1px solid #E2DDD2;border-radius:6px;padding:1rem 1.2rem;margin-bottom:.8rem}
.card .lbl{font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:#6B6558}
</style>""", unsafe_allow_html=True)

st.title("AI Financial Goal Assistance Agent")
st.caption("TEST → **ASSIST** → VISUALIZE  ·  Python computes every number; the ML model adds a likelihood; "
           "the agent orchestrates and explains.")

customers = _customers()
with st.sidebar:
    st.header("Customer")
    mode = st.radio("Input", ["Dataset customer", "Manual entry"], horizontal=True)
    manual, cid = None, None
    if mode == "Dataset customer":
        cid = st.selectbox("Customer ID", customers.index.tolist(), index=3)
        base = customers.loc[cid]
    else:
        manual = dict(
            Monthly_Income=st.number_input("Monthly income (₹)", 1000, 10_000_000, 80000, 1000),
            Monthly_Expenses=st.number_input("Monthly expenses (₹)", 0, 10_000_000, 50000, 1000),
            Investment_Amount=st.number_input("Monthly investment (₹)", 0, 10_000_000, 5000, 500),
            Financial_Goal=st.selectbox("Goal", config.FINANCIAL_GOALS),
            Goal_Amount=st.number_input("Goal amount (₹)", 1000, 100_000_000, 500000, 10000),
            Goal_Time_Period_Months=st.number_input("Timeline (months)", 1, 600, 36),
        )
        if st.checkbox("Add behaviour data (enables ML estimate)"):
            manual.update(Age=st.number_input("Age", 18, 80, 30),
                          Digital_Payment_Frequency=st.number_input("Digital payments / month", 0, 500, 50),
                          Average_Transaction_Amount=st.number_input("Avg transaction (₹)", 0, 100000, 3000),
                          Impulse_Spending_Score=st.slider("Impulse spending score", 0, 100, 40))
        base = pd.Series(manual)

    what_if = {}
    if mode == "Dataset customer":
        st.header("What-if")
        new_months = st.slider("Timeline (months)", 1, 360, int(base["Goal_Time_Period_Months"]),
                               key=f"wi_m_{cid}")
        new_invest = st.number_input("Monthly investment (₹)", 0, 10_000_000, int(base["Investment_Amount"]),
                                     500, key=f"wi_i_{cid}")
        if new_months != int(base["Goal_Time_Period_Months"]):
            what_if["Goal_Time_Period_Months"] = new_months
        if new_invest != int(base["Investment_Amount"]):
            what_if["Investment_Amount"] = new_invest
    question = st.text_input("Question for the agent (optional)")
    llm_on = get_llm() is not None
    st.caption(f"LLM explanation: **{'enabled' if llm_on else 'off — using deterministic template'}**")

out = run_assessment(customer_id=cid, manual_profile=manual, what_if=what_if or None, question=question or None)
if out.get("error"):
    st.error(out["error"]); st.stop()

p, f, g, r, rec, ml = (out["profile"], out["financial_health"], out["goal_calculation"],
                       out["risk"], out["recommendation"], out["ml_prediction"])
b = g["basic"]
color, label = STATUS_STYLE[r["status"]]
if what_if:
    st.info(f"What-if scenario applied: {what_if}")
st.markdown(f"<div class='status' style='background:{color}'><h2>{label.upper()} · risk {r['risk_level']}</h2>"
            f"<p>{r['reason']}</p></div>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Required / month", fmt_inr(b["required_monthly_contribution"]))
c2.metric("Currently invested / month", fmt_inr(b["current_monthly_contribution"]))
c3.metric("Monthly gap", fmt_inr(r["financial_gap_monthly"]))
c4.metric("Completion at current pace", fmt_months(b["months_to_goal_at_committed"]))

left, right = st.columns([1.1, 1])
with left:
    st.subheader("AI recommendation")
    st.markdown(f"<div class='card'><div class='lbl'>Primary · {rec['primary']['action'].replace('_', ' ')}</div>"
                f"<b>{rec['primary']['headline']}</b><br>{rec['primary']['reason']}</div>", unsafe_allow_html=True)
    for a in rec["alternatives"]:
        st.markdown(f"<div class='card'><div class='lbl'>Alternative · {a['action'].replace('_', ' ')}</div>"
                    f"{a['headline']}<br><small>{a['reason']}</small></div>", unsafe_allow_html=True)
    for c in rec["caveats"]:
        st.caption(f"⚠️ {c}")
    st.subheader("Explanation")
    st.write(out["explanation"])
    st.caption(f"Source: {out['explanation_source']}")
with right:
    st.subheader("Customer profile")
    st.table(pd.DataFrame({"Value": [
        p.get("Financial_Goal"), fmt_inr(p["Goal_Amount"]), fmt_months(p["Goal_Time_Period_Months"]),
        fmt_inr(f["monthly_income"]), fmt_inr(f["monthly_expenses"]), fmt_inr(f["monthly_savings"]),
        fmt_inr(f["investment_amount"]), fmt_pct(f["savings_rate"]), fmt_pct(f["expense_ratio"])]},
        index=["Goal", "Goal amount", "Timeline", "Income", "Expenses", "Monthly surplus",
               "Investment", "Savings rate", "Expense ratio"]))
    st.subheader("Key factors")
    for k in r["key_factors"]:
        icon = "🟢" if k["impact"] == "positive" else "🔴"
        st.write(f"{icon} **{k['factor']}:** {k['value']}" + (f" — {k['note']}" if k.get("note") else ""))
    st.subheader("ML insight")
    if ml.get("available"):
        st.metric("Likelihood of achievement", fmt_pct(ml["probability"], 0),
                  help=f"{ml['model']}, hold-out ROC-AUC {ml['holdout_auc']}")
        for d in ml["top_drivers"]:
            st.write(f"• {d['feature'].capitalize()} {d['direction']} the likelihood")
        if r.get("ml_consistency_note"):
            st.warning(r["ml_consistency_note"])
    else:
        st.caption(ml.get("reason"))
    st.caption(f"Historically, {fmt_pct(r['historical_achievement_rate_for_status'], 0)} of dataset customers "
               f"with this status achieved their goal.")

with st.expander("Assumption-based projection (not used for status)"):
    pr = g["assumption_based_projection"]
    st.write(pr["label"])
    st.write(f"Required monthly with returns: **{fmt_inr(pr['required_monthly_contribution'])}** · "
             f"months at current investment: **{fmt_months(pr['months_to_goal_at_committed'])}**")
with st.expander("Agent trace & full report"):
    st.code(" → ".join(out["tool_calls"]))
    st.text(out["report"])
st.caption(config.DISCLAIMER)
