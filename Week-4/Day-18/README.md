# README

This notebook implements a complete machine learning workflow for the **UCI Adult Income** dataset, focusing on **model tuning, regularization, probability calibration, and reproducible pipelines**.

## How to Reproduce the Results

1. Install the required libraries: **scikit-learn**, **LightGBM**, **XGBoost**, **NumPy**, **Pandas**, **Matplotlib**, and **Joblib**.
2. Run all notebook cells sequentially from top to bottom.
3. The dataset will be loaded, preprocessed, and engineered features will be generated automatically.
4. Hyperparameter tuning is performed using **RandomizedSearchCV** with **5-fold Stratified Cross-Validation**.
5. The best-performing model is calibrated, evaluated on the untouched hold-out test set, and saved as a `.joblib` file for future inference.

## Reproducibility

- `random_state = 42` is used throughout the project to ensure reproducibility.
- Cross-validation is performed using `StratifiedKFold(shuffle=True, random_state=42)`.
- All preprocessing, feature engineering, and modeling steps are combined into a single **scikit-learn Pipeline** to ensure consistent transformations during both training and inference.

## Library Versions

- **scikit-learn:** 1.8.0
- **LightGBM:** 4.6.0
- **XGBoost:** 3.3.0
- **NumPy:** 2.4.3
- **Pandas:** 3.0.1
