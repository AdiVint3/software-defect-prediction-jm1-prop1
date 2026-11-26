# Software Defect Prediction with Ensemble Learning

This study compares **three ensemble methods across 20 DefectData datasets** to predict whether a software module is defective. XGBoost, Random Forest, and AdaBoost are evaluated alongside seven non-ensemble classifiers using the same folds within each dataset. The study covers **115,688 module records**, including **16,659 defective records (14.4%)**.

## Models

| Ensemble method | How it works |
|---|---|
| XGBoost | Adds regularized decision trees in sequence to reduce classification loss. |
| Random Forest | Averages predictions from trees trained on sampled records and feature subsets. |
| AdaBoost | Fits shallow trees in sequence and increases the weight of misclassified examples. |

The comparison classifiers are Decision Tree, K-Nearest Neighbors, Linear SVM, Logistic Regression, PCA + Logistic Regression, a Multilayer Perceptron, and Gaussian Naive Bayes. An always-non-defective classifier provides a reference for interpreting accuracy under class imbalance.

## Data and evaluation

1. Select the 20 largest datasets in [DefectData](https://github.com/klainfo/DefectData/blob/master/README.md) with at least 50 records in each class. The [dataset inventory](results/MultiDataset_20x10/dataset_inventory.csv) lists the complete selection, sizes, defect rates, and feature counts.
2. Retain numeric software metrics as predictors and map each dataset’s defect label to a binary target. Fit imputation and scaling on the training fold where the model uses them.
3. Use three stratified grouped folds per dataset, keeping identical feature vectors together within each split. Train and evaluate each model separately within each dataset. This produces **600 model–fold evaluations**.
4. Average fold scores within each dataset, then give all 20 datasets equal weight in the macro averages. Report accuracy, precision, recall, F1, MCC, and ROC-AUC.

## Results

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

- **XGBoost** achieved the highest ROC-AUC (0.798), F1 (0.485), and MCC (0.371).
- **Random Forest** had the highest accuracy (0.837) and precision (0.511).
- **AdaBoost** had the highest defect recall (0.691).

The majority baseline achieved **0.812 accuracy with zero defect recall**. The model comparisons use fixed settings and held-out folds from the same datasets. No statistical significance test or external project validation was performed.

## Reproduce the benchmark

From the repository root, install the dependencies in a Python environment and run:

```bash
python -m pip install -r requirements.txt
python scripts/benchmark_multidataset.py
```

The script reads the included [benchmark data](data/DefectData_source/) directly, including the split compressed Eclipse files. It writes CSV and JSON results and PNG figures to `results/MultiDataset_20x10/`.

## Explore the outputs

| Output | Contents |
|---|---|
| [Results guide](results/MultiDataset_20x10/RESULTS_SUMMARY.md) | Scope, methods, and interpretation |
| [Macro summary](results/MultiDataset_20x10/overall_macro_summary.csv) | All six metrics across the 20 datasets |
| [Dataset results](results/MultiDataset_20x10/dataset_model_summary.csv) | Scores for every dataset and classifier pair |
| [Fold results](results/MultiDataset_20x10/fold_metrics.csv) | Scores and confusion counts for all 600 evaluations |
| [Figures](results/MultiDataset_20x10/figures/) | Metric boxplots, ROC-AUC and F1 heatmaps, and Random Forest feature importance |
| [Run log](results/MultiDataset_20x10/final_exact20_run.log) | Execution record for the full benchmark |
