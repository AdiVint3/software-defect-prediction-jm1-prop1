# Software Defect Prediction

This repository contains the datasets, analysis scripts, and results for the original JM1 and PROP-1 holdout experiments and the expanded benchmark of ten classifiers across 20 DefectData datasets.

## Repository layout

- `data/DefectData_source/` contains the 20 benchmark inputs. The benchmark loader reads the compressed files, including the split Eclipse archives, directly.
- `data/JM1.arff` and `data/PROP1.csv` are inputs for the original holdout experiments.
- `scripts/` contains the analysis and plotting scripts.
- [Expanded benchmark results](results/MultiDataset_20x10/RESULTS_SUMMARY.md) include the dataset inventory, scores for all 600 model and fold combinations, aggregate metrics, confusion counts by fold, baseline scores, figures, and final run log.
- [JM1 results](results/JM1/) and [PROP-1 results](results/PROP1/) contain the original holdout metrics and figures.

## Expanded 20-dataset benchmark (latest analysis)

The project now includes a classification benchmark using 20 larger eligible datasets from the [DefectData repository](https://github.com/klainfo/DefectData/blob/master/README.md), ten algorithms, and three grouped stratified folds per dataset. The inventory and methodology are in [`dataset_inventory.csv`](results/MultiDataset_20x10/dataset_inventory.csv) and [`RESULTS_SUMMARY.md`](results/MultiDataset_20x10/RESULTS_SUMMARY.md). JM1 and PROP-1 are included.

| Algorithm | Accuracy | Precision | Recall | F1 | MCC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost | 0.773 | 0.412 | 0.637 | 0.485 | 0.371 | 0.798 |
| Random Forest | 0.837 | 0.511 | 0.366 | 0.413 | 0.332 | 0.791 |
| AdaBoost | 0.707 | 0.354 | 0.691 | 0.448 | 0.322 | 0.773 |
| Logistic Regression | 0.727 | 0.368 | 0.645 | 0.448 | 0.321 | 0.764 |
| Linear SVM | 0.728 | 0.369 | 0.642 | 0.448 | 0.321 | 0.763 |
| Neural Network (MLP) | 0.719 | 0.356 | 0.644 | 0.439 | 0.307 | 0.759 |
| PCA + Logistic Regression | 0.726 | 0.364 | 0.634 | 0.443 | 0.312 | 0.758 |
| Decision Tree | 0.708 | 0.347 | 0.677 | 0.444 | 0.311 | 0.740 |
| Gaussian Naive Bayes | 0.757 | 0.435 | 0.362 | 0.346 | 0.249 | 0.723 |
| KNN (k=5) | 0.833 | 0.475 | 0.275 | 0.338 | 0.264 | 0.723 |

XGBoost leads on macro ROC-AUC, F1, and MCC; Random Forest leads on accuracy and precision; AdaBoost leads on recall. The majority-class baseline reaches 0.812 accuracy with zero defect recall, so accuracy alone is misleading. Differences are descriptive; no significance test was performed. MLP reached its 55-iteration cap in some folds. Figures are in `results/MultiDataset_20x10/figures/`. The earlier JM1 and PROP-1 holdout results are listed below for comparison.

## Findings at a glance

Scores below are from the held-out test sets. Precision, recall, and accuracy are percentages. Lift is for the highest-risk 10% of test observations.

### JM1

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | Top-decile lift |
|---|---:|---:|---:|---:|---:|---:|
| Decision Tree | 62.6% | 30.3% | 56.7% | 0.395 | 0.643 | 1.85 |
| KNN (k=5) | 75.5% | 36.6% | 18.8% | 0.249 | 0.617 | 1.67 |
| XGBoost | 66.7% | 32.9% | 52.8% | 0.405 | 0.659 | 2.03 |
| Majority baseline | 78.5% | -- | 0.0% | 0.000 | -- | 1.00 |

JM1 used a stratified 80/20 split with random seed 42. The dataset has 7,782 modules, 21 numeric predictors, and a 21.5% defect rate. XGBoost had the strongest AUC and top-decile lift in this split; the Decision Tree had the highest recall among fitted models.

### PROP-1

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | Top-decile lift |
|---|---:|---:|---:|---:|---:|---:|
| Decision Tree | 62.7% | 26.5% | 78.1% | 0.396 | 0.778 | 2.93 |
| KNN (k=5) | 84.0% | 48.6% | 32.7% | 0.391 | 0.745 | 3.15 |
| XGBoost | 75.0% | 35.5% | 72.8% | 0.478 | 0.819 | 3.33 |
| Majority baseline | 84.3% | -- | 0.0% | 0.000 | -- | 1.00 |

PROP-1 used the first fold of a shuffled, stratified five-fold group split (seed 42). Identical 20-metric vectors were assigned to the same partition to reduce leakage from repeated patterns. Of 18,471 rows, 14,860 were used for training and 3,611 for testing. XGBoost achieved the strongest ranking (AUC 0.819) and top-decile lift (3.33); the Decision Tree achieved the highest fixed-threshold recall (78.1%).

These metrics describe one holdout split per dataset. They do not establish statistical superiority.

## Reproducing the analysis

Python 3.10 or newer is recommended. From the project root:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the full benchmark from the repository root:

```bash
python scripts/benchmark_multidataset.py
```

It writes CSV and JSON outputs, plus figures, under `results/MultiDataset_20x10/`. For each dataset, it prepares features, trains each model on the same three grouped folds, and scores the held-out fold. Rows with identical predictor values stay together. The script averages scores across folds within each dataset and then gives each dataset equal weight in the final comparison.

To reproduce the separate JM1 and PROP-1 experiments and plots:

```bash
python scripts/analyze_jm1.py
python scripts/plot_jm1.py
python scripts/analyze_prop1.py
python scripts/plot_prop1.py
```

## Data sources and target definitions

- JM1: [DefectData JM1 data file](https://github.com/klainfo/DefectData/blob/master/inst/extdata/terapromise/mccabe/JM1.arff). The final target indicates whether a module is defective.
- PROP-1: [DefectData PROP-1 data file](https://github.com/klainfo/DefectData/blob/master/inst/extdata/terapromise/ck/prop-1.csv). The target is defective when `bug > 0`, following the package loading code.
- Package and dataset profile: [klainfo/DefectData README](https://github.com/klainfo/DefectData/blob/master/README.md) and [data-loading function](https://github.com/klainfo/DefectData/blob/master/R/loadData.R).

The dataset files are included here to make the analysis runnable without a separate download. Please consult the upstream project for its licensing and attribution terms before redistributing the raw datasets.

## Software

The original analysis used scikit-learn 1.7.2 and XGBoost 3.4.1. See `requirements.txt` for the project dependencies.
