import csv, json, sys
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (confusion_matrix, accuracy_score, precision_score,
    recall_score, f1_score, roc_auc_score, roc_curve)
from xgboost import XGBClassifier
import sklearn, xgboost

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "PROP1"
RESULTS.mkdir(parents=True, exist_ok=True)
csv_path = ROOT / "data" / "PROP1.csv"
with csv_path.open(newline="", encoding="utf-8-sig") as f:
    raw = list(csv.DictReader(f))
all_cols = list(raw[0].keys())
feature_names = [c for c in all_cols if c not in ("Name", "version", "bug")]
X = np.array([[float(row[c]) if row[c] not in ("", "?") else np.nan for c in feature_names] for row in raw], dtype=float)
bug_counts = np.array([float(row["bug"]) for row in raw], dtype=float)
y = (bug_counts > 0).astype(int)
missing = int(np.isnan(X).sum())
duplicates = len(raw) - len({tuple(row[c] for c in all_cols) for row in raw})
unique_features, groups = np.unique(X, axis=0, return_inverse=True)
group_label_counts = np.zeros((len(unique_features), 2), dtype=int)
np.add.at(group_label_counts, (groups, y), 1)
mixed_label_groups = int(np.sum(np.all(group_label_counts > 0, axis=1)))
splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
tr, te = next(splitter.split(X, y, groups))
Xtr, Xte, ytr, yte = X[tr], X[te], y[tr], y[te]
pos_weight = float((ytr == 0).sum() / (ytr == 1).sum())
models = {
    "Decision Tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=10, class_weight="balanced", random_state=42),
    "KNN (k=5)": Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()),
        ("knn", KNeighborsClassifier(n_neighbors=5, weights="uniform", metric="minkowski", p=2))]),
    "XGBoost": XGBClassifier(n_estimators=300, max_depth=4, learning_rate=.05, subsample=.8,
        colsample_bytree=.8, reg_lambda=1.0, scale_pos_weight=pos_weight, eval_metric="logloss",
        tree_method="hist", n_jobs=4, random_state=42),
}
metrics = {}
fitted = {}
for name, model in models.items():
    model.fit(Xtr, ytr)
    fitted[name] = model
    pred = model.predict(Xte)
    prob = model.predict_proba(Xte)[:, 1]
    cm = confusion_matrix(yte, pred, labels=[1, 0])
    fpr, tpr, _ = roc_curve(yte, prob)
    n_top = int(np.ceil(.10 * len(yte)))
    top = np.argsort(prob)[::-1][:n_top]
    ordered = np.argsort(prob)[::-1]
    n_def = int(yte.sum())
    gains = []
    for decile in range(1, 11):
        end = min(len(yte), int(np.ceil(decile * len(yte) / 10)))
        gains.append({"population_fraction": end / len(yte),
                      "defects_captured_fraction": float(yte[ordered[:end]].sum() / n_def)})
    captured = int(yte[top].sum())
    metrics[name] = {
        "confusion_matrix": cm.tolist(), "accuracy": float(accuracy_score(yte, pred)),
        "precision": float(precision_score(yte, pred, zero_division=0)),
        "recall": float(recall_score(yte, pred, zero_division=0)),
        "f1": float(f1_score(yte, pred, zero_division=0)),
        "auc": float(roc_auc_score(yte, prob)), "predicted_positive": int(pred.sum()),
        "top_decile_n": n_top, "top_decile_defects_captured": captured,
        "test_defects": n_def, "top_decile_recall": captured / n_def,
        "top_decile_lift": (captured / n_top) / (n_def / len(yte)),
        "cumulative_gains": gains, "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
    }

descriptives = {}
for j, name in enumerate(feature_names):
    vals = X[:, j]
    vals = vals[np.isfinite(vals)]
    sd = float(np.std(vals, ddof=1))
    z = (vals - vals.mean()) / np.std(vals)
    descriptives[name] = {"mean": float(np.mean(vals)), "median": float(np.median(vals)),
        "sd": sd, "variance": float(np.var(vals, ddof=1)),
        "skewness": float(np.mean(z ** 3)), "kurtosis_excess": float(np.mean(z ** 4) - 3)}

selected = ["loc", "wmc", "max_cc", "avg_cc"]
mat = np.column_stack([X[:, feature_names.index(c)] for c in selected])
from scipy.stats import rankdata
spearman_mat = np.column_stack([rankdata(mat[:, i], nan_policy="omit") for i in range(mat.shape[1])])
result = {
    "dataset": {"name": "PROP1", "source": "klainfo/DefectData inst/extdata/terapromise/ck/prop-1.csv",
        "n_rows": len(y), "n_features": len(feature_names), "feature_names": feature_names,
        "class_counts": {"defective": int(y.sum()), "non_defective": int((1-y).sum())},
        "defect_rate": float(y.mean()), "missing_feature_cells": missing,
        "duplicate_rows": duplicates, "train_n": len(tr), "test_n": len(te),
        "train_defects": int(ytr.sum()), "test_defects": int(yte.sum()),
        "unique_feature_vectors": int(len(unique_features)),
        "repeated_feature_rows": int(len(y) - len(unique_features)),
        "mixed_label_feature_groups": mixed_label_groups,
        "split_design": "first fold of 5-fold shuffled stratified group split; identical feature vectors stay in one partition",
        "seed": 42, "test_size": .20, "bug_count_max": float(np.max(bug_counts)),
        "bug_count_mean": float(np.mean(bug_counts)), "identifier_columns_excluded": ["Name", "version"],
        "label_definition": "defective when bug > 0"},
    "metrics": metrics, "descriptives": descriptives,
    "correlation_features": selected,
    "correlations": {"pearson": np.corrcoef(mat, rowvar=False).tolist(),
                     "spearman": np.corrcoef(spearman_mat, rowvar=False).tolist()},
    "software_versions": {"scikit_learn": sklearn.__version__, "xgboost": xgboost.__version__},
    "xgboost_parameters": {"n_estimators": 300, "max_depth": 4, "learning_rate": .05,
        "subsample": .8, "colsample_bytree": .8, "reg_lambda": 1.0,
        "scale_pos_weight": pos_weight, "eval_metric": "logloss", "tree_method": "hist", "random_state": 42},
    "xgboost_top_features": sorted(zip(feature_names, fitted["XGBoost"].feature_importances_.tolist()),
        key=lambda x: x[1], reverse=True)[:10],
    "tree_top_features": sorted(zip(feature_names, fitted["Decision Tree"].feature_importances_.tolist()),
        key=lambda x: x[1], reverse=True)[:10],
    "tree_structure": {"depth": fitted["Decision Tree"].get_depth(), "leaves": fitted["Decision Tree"].get_n_leaves()},
}
(RESULTS / "prop1_analysis.json").write_text(json.dumps(result, indent=2, default=lambda x: x.item() if hasattr(x, "item") else str(x)))
print(json.dumps({"dataset": result["dataset"], "metrics": {
    k: {m: v[m] for m in ("accuracy", "precision", "recall", "f1", "auc", "top_decile_defects_captured", "top_decile_lift")}
    | {"confusion_matrix": v["confusion_matrix"]} for k, v in metrics.items()},
    "top_features_xgboost": result["xgboost_top_features"][:5]}, indent=2))
