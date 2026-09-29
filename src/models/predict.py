"""Serve the trained model: probability + local, explainable drivers."""
from __future__ import annotations

import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from src import config
from src.features.engineering import FEATURES, NUMERIC_FEATURES, add_features

READABLE = {
    "Goal_Amount": "goal amount", "Monthly_Income": "monthly income",
    "Impulse_Spending_Score": "impulse spending score", "Expense_Ratio": "expense ratio",
    "Digital_Payment_Frequency": "digital payment frequency",
    "Average_Transaction_Amount": "average transaction amount",
    "Investment_Amount": "monthly investment", "Goal_Time_Period_Months": "goal timeline",
    "Required_Monthly": "required monthly contribution", "Age": "age",
    "Log_Capacity_Coverage": "surplus coverage of the requirement",
    "Log_Committed_Coverage": "investment coverage of the requirement",
}


@lru_cache(maxsize=1)
def load_model():
    if not config.MODEL_PATH.exists():
        return None, None
    return joblib.load(config.MODEL_PATH), json.loads(config.MODEL_META_PATH.read_text())


def predict_goal_probability(profile: dict) -> dict:
    """Return ML probability of achievement, or a reason why it was skipped.

    Manual profiles that lack behavioural fields are NOT imputed with invented
    values; the ML step is skipped instead.
    """
    model, meta = load_model()
    if model is None:
        return {"available": False, "reason": "Model not trained (run python -m src.models.train)"}
    needed = ["Age", "Digital_Payment_Frequency", "Average_Transaction_Amount",
              "Impulse_Spending_Score", "Financial_Goal"]
    missing = [f for f in needed if profile.get(f) in (None, "", "Unspecified")]
    if missing:
        return {"available": False, "reason": f"ML skipped: profile lacks {missing}"}
    row = add_features(pd.DataFrame([profile]))[FEATURES]
    proba = float(model.predict_proba(row)[0, 1])

    drivers = []
    if meta["selected_model"] == "Logistic Regression":
        prep, clf = model.named_steps["prep"], model.named_steps["clf"]
        z = prep.transform(row)[0]
        contrib = z * clf.coef_[0]
        names = [n.split("__", 1)[1] for n in prep.get_feature_names_out()]
        for n, c in sorted(zip(names, contrib), key=lambda t: -abs(t[1]))[:4]:
            if abs(c) < 0.05:
                continue
            label = READABLE.get(n, n.replace("Financial_Goal_", "goal type: "))
            drivers.append({"feature": label,
                            "direction": "raises" if c > 0 else "lowers",
                            "strength": round(float(abs(c)), 2)})
    return {"available": True, "probability": round(proba, 4),
            "model": meta["selected_model"],
            "holdout_auc": meta["holdout_test"]["roc_auc"], "top_drivers": drivers}
