"""Structured state passed between LangGraph nodes."""
from __future__ import annotations

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # request
    customer_id: Optional[str]
    manual_profile: Optional[dict]
    what_if: Optional[dict]          # structured overrides: Goal_Amount, Goal_Time_Period_Months, ...
    question: Optional[str]          # optional free-text question for the explanation step
    # data + tool outputs
    profile: dict
    financial_health: dict
    goal_calculation: dict
    ml_prediction: dict
    risk: dict
    recommendation: dict
    # output
    explanation: str
    explanation_source: str          # "llm" | "template" | "template (llm output rejected: ...)"
    report: str
    tool_calls: list[str]
    error: Optional[str]
