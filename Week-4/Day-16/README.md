# Week 4 Day 2 — Supervised Learning

## Objective
Build the first supervised machine learning models for the Adult Census Income dataset using a reproducible preprocessing pipeline and compare their performance against the Day 1 baselines.

## Tasks Completed
- Implemented a preprocessing pipeline using `ColumnTransformer`
  - Numeric: Median Imputation → StandardScaler
  - Categorical: Most-Frequent Imputation → One-Hot Encoding
- Trained two supervised models:
  - Logistic Regression
  - Decision Tree Classifier
- Evaluated all models using:
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - ROC AUC
  - PR AUC
- Compared supervised models with the Day 1 baselines.
- Plotted ROC curves, Precision–Recall curves, and Confusion Matrices.
- Interpreted Logistic Regression coefficients and Decision Tree splits.
- Selected the model to continue for further development.

## Key Results

| Model | Precision | F1 Score |
|--------|----------:|---------:|
| Majority Baseline | 0.000 | 0.000 |
| Rule-Based Baseline | 0.608 | 0.318 |
| Logistic Regression | **0.728** | **0.654** |
| Decision Tree | 0.615 | 0.607 |

**Selected Model:** Logistic Regression

It achieved the highest overall performance and aligned best with the project's business objective of maximizing precision while maintaining good generalization.

## Files
- `Week4_Day2.ipynb` — Jupyter notebook
- `Week4_Day2_Supervised_Learning_Report.pdf` — Summary report
- `README.md`
