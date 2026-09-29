import re

import pytest

from src.agent.graph import run_assessment
from src.agent.nodes import numbers_grounded
from src.utils import fmt_inr

EXPECTED_TRACE = ["parse_request", "load_profile", "financial_analyzer", "goal_calculator",
                  "ml_predictor", "risk_analyzer", "recommendation_engine", "explanation", "report"]


def test_full_trace_and_sections():
    out = run_assessment("CUST0004", llm=False)
    assert out["tool_calls"] == EXPECTED_TRACE
    for section in ["STATUS:", "WHY:", "RECOMMENDED ACTION:", "KEY FACTORS:", "EXPLANATION:", "IMPORTANT:"]:
        assert section in out["report"]


def test_report_numbers_match_tools():
    out = run_assessment("CUST0004", llm=False)
    b = out["goal_calculation"]["basic"]
    assert fmt_inr(b["required_monthly_contribution"]) in out["report"]
    assert fmt_inr(out["risk"]["financial_gap_monthly"]) in out["report"]
    assert out["goal_calculation"]["goal_amount"] == 210730  # raw dataset value, not invented


def test_invalid_customer_id():
    out = run_assessment("CUST9999", llm=False)
    assert "not found" in out["error"] and "financial_analyzer" not in out["tool_calls"]


def test_empty_request():
    assert run_assessment(llm=False)["error"]


def test_manual_profile_missing_values():
    out = run_assessment(manual_profile={"Monthly_Income": 50000}, llm=False)
    assert "Missing required values" in out["error"]


def test_manual_profile_without_behaviour_skips_ml():
    out = run_assessment(manual_profile=dict(Monthly_Income=80000, Monthly_Expenses=50000,
                                             Investment_Amount=5000, Goal_Amount=300000,
                                             Goal_Time_Period_Months=24), llm=False)
    assert out["ml_prediction"]["available"] is False
    assert out["risk"]["status"] == "AT_RISK"


def test_what_if_changes_timeline():
    base = run_assessment("CUST0004", llm=False)
    wi = run_assessment("CUST0004", what_if={"Goal_Time_Period_Months": 200}, llm=False)
    assert base["risk"]["status"] == "AT_RISK" and wi["risk"]["status"] == "ON_TRACK"


def test_bad_what_if_field():
    assert "Unsupported" in run_assessment("CUST0004", what_if={"Age": 99}, llm=False)["error"]


def test_llm_faithful_output_is_used():
    def good_llm(system, user):
        req = re.search(r"required_monthly_contribution: (\S+)", user).group(1)
        return f"You need {req} each month to stay on course."
    out = run_assessment("CUST0004", llm=good_llm)
    assert out["explanation_source"] == "llm" and "₹5,546" in out["explanation"]


def test_llm_hallucinated_number_is_rejected():
    out = run_assessment("CUST0004", llm=lambda s, u: "You need ₹7,777 per month.")
    assert out["explanation_source"].startswith("template (LLM output rejected")
    assert "7,777" not in out["report"]


def test_llm_failure_degrades_gracefully():
    def broken(system, user):
        raise ConnectionError("offline")
    out = run_assessment("CUST0004", llm=broken)
    assert "LLM unavailable" in out["explanation_source"] and out["report"]


def test_llm_cannot_change_status():
    out = run_assessment("CUST0004", llm=lambda s, u: "Status is ON_TRACK, relax.")
    assert out["risk"]["status"] == "AT_RISK" and "STATUS: AT RISK" in out["report"]


def test_numbers_grounded_helper():
    assert numbers_grounded("Gap is ₹4,146 over 3 steps", {"gap": "₹4,146"})[0]
    assert not numbers_grounded("Gap is ₹4,200", {"gap": "₹4,146"})[0]


def test_determinism():
    a = run_assessment("CUST0100", llm=False); b = run_assessment("CUST0100", llm=False)
    assert a["report"] == b["report"]


def test_api():
    from fastapi.testclient import TestClient
    from src.api.main import app
    c = TestClient(app)
    r = c.post("/assess-goal", json={"customer_id": "CUST0004"})
    assert r.status_code == 200 and r.json()["risk"]["status"] == "AT_RISK"
    assert c.post("/assess-goal", json={"customer_id": "NOPE"}).status_code == 404
