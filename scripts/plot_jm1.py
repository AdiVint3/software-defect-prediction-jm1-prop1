"""Generate ROC and cumulative gains figures from the JM1 holdout results."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    results = Path(__file__).resolve().parents[1] / "results" / "JM1"
    metrics = json.loads((results / "analysis_results.json").read_text())["metrics"]
    figures = results / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    colors = {"Decision Tree": "#177E89", "KNN (k=5)": "#D47A32", "XGBoost": "#7356A8"}

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=190)
    for name, color in colors.items():
        roc = metrics[name]["roc"]
        ax.plot(roc["fpr"], roc["tpr"], lw=2.5, color=color,
                label=f"{name} (AUC {metrics[name]['auc']:.3f})")
    ax.plot([0, 1], [0, 1], "--", lw=1.2, color="#8C98A3", label="No-skill reference")
    ax.set(xlim=(0, 1), ylim=(0, 1.02), xlabel="False positive rate",
           ylabel="True positive rate", title="ROC curves on the held-out JM1 test set")
    ax.grid(color="#D9E0E5", lw=.65)
    ax.legend(frameon=False, loc="lower right", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(figures / "roc_curve.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=190)
    for name, color in colors.items():
        gains = metrics[name]["cumulative_gains"]
        review_fraction = [0] + [point["population_fraction"] for point in gains]
        defect_fraction = [0] + [point["defects_captured_fraction"] for point in gains]
        ax.plot(review_fraction, defect_fraction, marker="o", ms=3.2, lw=2.1,
                color=color, label=name)
    ax.plot([0, 1], [0, 1], "--", lw=1.2, color="#8C98A3", label="Random selection")
    ax.set(xlim=(0, 1), ylim=(0, 1.02),
           xlabel="Fraction of modules reviewed (highest risk first)",
           ylabel="Fraction of test defects captured",
           title="Cumulative gains by risk-ranked inspection")
    ax.grid(color="#D9E0E5", lw=.65)
    ax.legend(frameon=False, loc="lower right", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(figures / "cumulative_gains.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
