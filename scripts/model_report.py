"""Write reports/MODEL_REPORT.md from models/model_meta.json."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT / "models" / "model_meta.json").read_text())
lines = ["# Model Report — Goal_Achievement classifier", "",
         f"Train {m['n_train']} / test {m['n_test']} (stratified). Selection: {m['selection_rule']}.", "",
         "## 5-fold CV on training set", "", "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC (±sd) |",
         "|---|---|---|---|---|---|"]
for k, v in m["cv_train"].items():
    lines.append(f"| {k} | {v['accuracy']:.3f} | {v['precision']:.3f} | {v['recall']:.3f} | {v['f1']:.3f} | "
                 f"{v['roc_auc']:.3f} (±{v['roc_auc_std']:.3f}) |")
h = m["holdout_test"]; cm = h["confusion_matrix"]
lines += ["", f"## Selected: {m['selected_model']} — hold-out test", "",
          f"Accuracy {h['accuracy']:.3f} · Precision {h['precision']:.3f} · Recall {h['recall']:.3f} · "
          f"F1 {h['f1']:.3f} · ROC-AUC {h['roc_auc']:.3f}", "",
          "| | Pred No | Pred Yes |", "|---|---|---|", f"| Actual No | {cm[0][0]} | {cm[0][1]} |",
          f"| Actual Yes | {cm[1][0]} | {cm[1][1]} |", "", "## Ablations", "",
          *[f"- {k}: {v}" for k, v in m["ablation"].items()], "",
          "## Features", "", ", ".join(m["features"]), ""]
if "coefficients" in m:
    lines += ["## Standardised coefficients (sign = direction of effect)", "", "| Feature | Coef |", "|---|---|"]
    lines += [f"| {c['feature']} | {c['coef']:+.3f} |" for c in m["coefficients"]]
    lines += ["", "Note: Goal_Amount and Required_Monthly are correlated, so individual coefficients "
              "should be read together, not in isolation."]
(ROOT / "reports" / "MODEL_REPORT.md").write_text("\n".join(lines))
