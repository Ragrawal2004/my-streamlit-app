"""Train and compare candidate classifiers for Goal_Achievement.

Protocol: stratified 80/20 hold-out split (random_state=42); 5-fold stratified
CV on the training part for model comparison; selected model refit on the
training set and reported once on the untouched test set.
Selection rule: highest CV ROC-AUC; if within 0.01 of a more interpretable
model, the more interpretable model wins (explainability matters for this project).
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from src import config
from src.data.loader import load_customers
from src.features.engineering import (CATEGORICAL_FEATURES, FEATURES,
                                      NUMERIC_FEATURES, PAYMENT_FEATURE,
                                      add_features, target)

SEED = 42
# Ordered from most to least interpretable.
INTERPRETABILITY_ORDER = ["Logistic Regression", "Decision Tree", "Random Forest",
                          "Gradient Boosting"]


def make_preprocessor(numeric, categorical, scale: bool):
    num = StandardScaler() if scale else "passthrough"
    return ColumnTransformer([
        ("num", num, numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ])


def candidates(numeric=NUMERIC_FEATURES, categorical=CATEGORICAL_FEATURES):
    return {
        "Logistic Regression": Pipeline([
            ("prep", make_preprocessor(numeric, categorical, scale=True)),
            ("clf", LogisticRegression(max_iter=2000, C=1.0))]),
        "Decision Tree": Pipeline([
            ("prep", make_preprocessor(numeric, categorical, scale=False)),
            ("clf", DecisionTreeClassifier(max_depth=4, min_samples_leaf=20, random_state=SEED))]),
        "Random Forest": Pipeline([
            ("prep", make_preprocessor(numeric, categorical, scale=False)),
            ("clf", RandomForestClassifier(n_estimators=300, min_samples_leaf=5,
                                           random_state=SEED, n_jobs=-1))]),
        "Gradient Boosting": Pipeline([
            ("prep", make_preprocessor(numeric, categorical, scale=False)),
            ("clf", HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05,
                                                   max_iter=200, random_state=SEED))]),
    }


def test_metrics(model, X, y) -> dict:
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {
        "accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred),
        "recall": recall_score(y, pred), "f1": f1_score(y, pred),
        "roc_auc": roc_auc_score(y, proba),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }


def lr_coefficients(model) -> list[dict]:
    names = model.named_steps["prep"].get_feature_names_out()
    coefs = model.named_steps["clf"].coef_[0]
    rows = sorted(zip(names, coefs), key=lambda t: -abs(t[1]))
    return [{"feature": n.split("__", 1)[1], "coef": round(float(c), 4)} for n, c in rows]


def main() -> dict:
    df = add_features(load_customers())
    X, y = df[FEATURES + [PAYMENT_FEATURE]], target(df)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    scoring = ["accuracy", "precision", "recall", "f1", "roc_auc"]

    cv_results = {}
    for name, model in candidates().items():
        r = cross_validate(model, X_tr[FEATURES], y_tr, cv=cv, scoring=scoring)
        cv_results[name] = {m: round(float(np.mean(r[f"test_{m}"])), 4) for m in scoring}
        cv_results[name]["roc_auc_std"] = round(float(np.std(r["test_roc_auc"])), 4)

    best_auc = max(v["roc_auc"] for v in cv_results.values())
    selected = next(n for n in INTERPRETABILITY_ORDER if cv_results[n]["roc_auc"] >= best_auc - 0.01)

    model = candidates()[selected].fit(X_tr[FEATURES], y_tr)
    holdout = {k: (round(v, 4) if isinstance(v, float) else v)
               for k, v in test_metrics(model, X_te[FEATURES], y_te).items()}

    # Ablation 1: does adding payment method help? (links back to Part 1 chi-square)
    ab = candidates(NUMERIC_FEATURES, CATEGORICAL_FEATURES + [PAYMENT_FEATURE])[selected]
    ab_auc = float(np.mean(cross_validate(ab, X_tr, y_tr, cv=cv, scoring="roc_auc")["test_score"]))
    # Ablation 2: payment method alone
    pay_only = Pipeline([("prep", make_preprocessor([], [PAYMENT_FEATURE], False)),
                         ("clf", LogisticRegression())])
    pay_auc = float(np.mean(cross_validate(pay_only, X_tr, y_tr, cv=cv,
                                           scoring="roc_auc")["test_score"]))
    # Baseline: single deterministic metric (capacity coverage) as a score
    base_auc = float(roc_auc_score(y_te, X_te["Log_Capacity_Coverage"]))

    final = candidates()[selected].fit(X[FEATURES], y)  # refit on all data for serving
    config.MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(final, config.MODEL_PATH)
    meta = {
        "selected_model": selected,
        "selection_rule": "highest CV ROC-AUC; ties within 0.01 go to the more interpretable model",
        "features": FEATURES, "cv_train": cv_results, "holdout_test": holdout,
        "n_train": len(X_tr), "n_test": len(X_te),
        "ablation": {"cv_auc_with_payment_method_added": round(ab_auc, 4),
                     "cv_auc_payment_method_only": round(pay_auc, 4),
                     "holdout_auc_capacity_coverage_only": round(base_auc, 4)},
    }
    if selected == "Logistic Regression":
        meta["coefficients"] = lr_coefficients(model)
    config.MODEL_META_PATH.write_text(json.dumps(meta, indent=2))
    return meta


if __name__ == "__main__":
    m = main()
    print(pd.DataFrame(m["cv_train"]).T.to_string())
    print("Selected:", m["selected_model"])
    print("Hold-out:", m["holdout_test"])
    print("Ablation:", m["ablation"])
    for c in m.get("coefficients", [])[:10]:
        print(c)
