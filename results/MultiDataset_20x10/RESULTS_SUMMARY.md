# Expanded 20-dataset benchmark results

This is the empirical analysis output only; no research paper or report has been drafted.

## Scope and preparation

The benchmark uses 20 larger datasets selected from the [DefectData repository](https://github.com/klainfo/DefectData/blob/master/README.md), requiring at least 50 defective and 50 non-defective observations, then taking the 20 largest eligible datasets by row count. Selected datasets: prop-2, prop-1, eclipse-3.0, prop-3, prop-4, prop-5, eclipse-2.1, JM1, eclipse-2.0, mylyn, PC5, pde, eclipse34_swt, PC4, PC3, eclipse34_debug, jdt, camel-1.6, xalan-2.6, camel-1.4.

Preparation removes identifiers and target fields, retains numeric predictors, checks missingness and duplicate feature vectors, and uses three stratified grouped folds where identical feature vectors stay together. Model pipelines impute missing values, scale where needed, and handle class imbalance. All datasets had zero missing feature cells before preprocessing. Metrics use a fixed 0.5 probability threshold (zero decision boundary for linear SVM); ROC-AUC uses continuous scores. Fold results are averaged within each dataset, then each dataset receives equal weight in macro averages.

## Algorithms

Decision Tree, KNN, XGBoost, Random Forest, Linear SVM, Logistic Regression, PCA + Logistic Regression, AdaBoost, Neural Network (MLP), and Gaussian Naive Bayes. PCA is dimensionality reduction in a supervised pipeline. CNN is not included because the inputs are flat metric tables; Gaussian Mixture is unsupervised, while this benchmark evaluates classification.

## Macro-average results

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

## Reading the results

XGBoost has the highest macro ROC-AUC (0.798), F1 (0.485), and MCC (0.371). Random Forest has the highest accuracy (0.837) and precision (0.511), while AdaBoost has the highest recall (0.691). The majority-class baseline has macro accuracy 0.812 and zero defect recall, showing why accuracy alone is misleading. These are descriptive averages; no significance test was run.

## Output files

- `dataset_inventory.csv`: exact 20 datasets and preprocessing/split details.
- `fold_metrics.csv`: 600 dataset-model-fold records.
- `dataset_model_summary.csv`: per-dataset averages.
- `overall_macro_summary.csv`: table above.
- `majority_baseline_*.csv`: majority-class reference.
- `model_failures.csv`: no model fit failures.
- `figures/`: metric boxplots, ROC-AUC and F1 heatmaps, and Random Forest feature importance.
- `final_exact20_run.log`: final run log.

MLP hit its 55-iteration training cap in some folds (convergence warnings); its scores are a fixed-budget baseline and may improve with tuning. Results are exploratory, not production-readiness evidence.
