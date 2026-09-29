"""LangGraph workflow:

START -> parse_request -> load_profile -> financial_health -> goal_calculation
      -> ml_prediction -> risk_analysis -> recommendation -> explanation -> report -> END
(parse_request / load_profile route to `error` -> END on invalid input)
"""
from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph

from src.agent import nodes
from src.agent.state import AgentState


def build_graph(llm=None):
    g = StateGraph(AgentState)
    g.add_node("parse_request", nodes.parse_request)
    g.add_node("load_profile", nodes.load_profile)
    g.add_node("financial_health", nodes.financial_health_node)
    g.add_node("goal_calculation", nodes.goal_calculation_node)
    g.add_node("ml_prediction", nodes.ml_prediction_node)
    g.add_node("risk_analysis", nodes.risk_node)
    g.add_node("recommendation", nodes.recommendation_node)
    g.add_node("explanation", partial(nodes.explanation_node, llm=llm))
    g.add_node("report", nodes.report_node)
    g.add_node("error", nodes.error_node)

    g.add_edge(START, "parse_request")
    g.add_conditional_edges("parse_request", nodes.route_after, {"ok": "load_profile", "error": "error"})
    g.add_conditional_edges("load_profile", nodes.route_after, {"ok": "financial_health", "error": "error"})
    for a, b in [("financial_health", "goal_calculation"), ("goal_calculation", "ml_prediction"),
                 ("ml_prediction", "risk_analysis"), ("risk_analysis", "recommendation"),
                 ("recommendation", "explanation"), ("explanation", "report")]:
        g.add_edge(a, b)
    g.add_edge("report", END)
    g.add_edge("error", END)
    return g.compile()


def run_assessment(customer_id=None, manual_profile=None, what_if=None, question=None, llm=None) -> dict:
    graph = build_graph(llm=llm)
    return graph.invoke({"customer_id": customer_id, "manual_profile": manual_profile,
                         "what_if": what_if, "question": question, "tool_calls": []})


if __name__ == "__main__":
    import sys
    out = run_assessment(sys.argv[1] if len(sys.argv) > 1 else "CUST0004")
    print(out["report"])
    print("\nTool trace:", " -> ".join(out["tool_calls"]))
