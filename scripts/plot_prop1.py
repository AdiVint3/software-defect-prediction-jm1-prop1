import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "results" / "PROP1" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
M = json.loads((ROOT / "results" / "PROP1" / "prop1_analysis.json").read_text())["metrics"]
colors = {"Decision Tree": "#177E89", "KNN (k=5)": "#D47A32", "XGBoost": "#7356A8"}
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=190)
for name, color in colors.items():
    r = M[name]["roc"]
    ax.plot(r["fpr"], r["tpr"], lw=2.4, color=color,
            label=f"{name} (AUC {M[name]['auc']:.3f})")
ax.plot([0, 1], [0, 1], ls="--", lw=1.2, color="#8C98A3", label="No-skill reference")
ax.set(xlim=(0, 1), ylim=(0, 1.02), xlabel="False positive rate", ylabel="True positive rate",
       title="ROC curves on the grouped PROP-1 test set")
ax.grid(color="#D9E0E5", lw=.65)
ax.legend(frameon=False, loc="lower right", fontsize=8.5)
fig.tight_layout()
fig.savefig(FIG_DIR / "roc_curve.png", bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=190)
for name, color in colors.items():
    g = M[name]["cumulative_gains"]
    x = [0] + [v["population_fraction"] for v in g]
    y = [0] + [v["defects_captured_fraction"] for v in g]
    ax.plot(x, y, marker="o", ms=3.2, lw=2.1, color=color, label=name)
ax.plot([0, 1], [0, 1], ls="--", lw=1.2, color="#8C98A3", label="Random selection")
ax.set(xlim=(0, 1), ylim=(0, 1.02), xlabel="Fraction of modules reviewed (highest risk first)",
       ylabel="Fraction of test defects captured", title="Cumulative gains by risk-ranked inspection")
ax.grid(color="#D9E0E5", lw=.65)
ax.legend(frameon=False, loc="lower right", fontsize=8.5)
fig.tight_layout()
fig.savefig(FIG_DIR / "cumulative_gains.png", bbox_inches="tight")
plt.close(fig)
print("Created PROP-1 ROC and cumulative-gains charts")
