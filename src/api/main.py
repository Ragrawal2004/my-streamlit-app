"""FastAPI backend. Run: uvicorn src.api.main:app --reload"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.agent.graph import run_assessment
from src.agent.nodes import _customers

app = FastAPI(title="AI Financial Goal Assistance Agent", version="1.0.0")


class ManualProfile(BaseModel):
    Monthly_Income: float = Field(gt=0)
    Monthly_Expenses: float = Field(ge=0)
    Investment_Amount: float = Field(ge=0)
    Goal_Amount: float = Field(gt=0)
    Goal_Time_Period_Months: int = Field(gt=0)
    Financial_Goal: str = "Unspecified"
    Age: Optional[int] = None
    Digital_Payment_Frequency: Optional[int] = None
    Average_Transaction_Amount: Optional[float] = None
    Impulse_Spending_Score: Optional[int] = None


class AssessRequest(BaseModel):
    customer_id: Optional[str] = None
    manual_profile: Optional[ManualProfile] = None
    what_if: Optional[dict] = None
    question: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok", "customers": len(_customers())}


@app.get("/customers")
def customers(limit: int = 50):
    return _customers()["Customer_ID"].head(limit).tolist()


@app.post("/assess-goal")
def assess_goal(req: AssessRequest):
    out = run_assessment(customer_id=req.customer_id,
                         manual_profile=req.manual_profile.model_dump(exclude_none=True) if req.manual_profile else None,
                         what_if=req.what_if, question=req.question)
    if out.get("error"):
        raise HTTPException(status_code=404 if "not found" in out["error"] else 422, detail=out["error"])
    keys = ["profile", "financial_health", "goal_calculation", "ml_prediction", "risk",
            "recommendation", "explanation", "explanation_source", "report", "tool_calls"]
    return {k: out.get(k) for k in keys}
