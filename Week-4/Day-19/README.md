# Week 4 - Day 19: Ensemble Learning, Deployment & Final Deliverables

## Overview

Today's work focused on completing the final stages of the Adult Income Prediction capstone project. This included building ensemble models, handling class imbalance, performing model interpretability and fairness analysis, developing an end-to-end inference pipeline, and preparing the final project deliverables.

## Tasks Completed

- Trained and compared Random Forest, LightGBM, and a Stacking Ensemble.
- Evaluated ensemble models using hold-out metrics and inference time.
- Investigated class imbalance using:
  - Class Weighting
  - Random Oversampling
  - SMOTE
- Compared cross-validation and hold-out performance for each imbalance handling technique.
- Selected the original tuned LightGBM model based on the project's primary business metric (Precision).
- Performed model interpretability using:
  - Feature Importance
  - Permutation Importance
  - SHAP Summary Plot
  - SHAP Waterfall Plots
- Conducted fairness analysis across sex and race groups.
- Developed an end-to-end inference pipeline with:
  - Saved model loading
  - Input validation
  - Prediction probabilities
  - Custom decision threshold (0.45)
  - Top-3 feature contributions
- Implemented unit tests for inference.
- Created a monitoring checklist for deployment.
- Prepared the executive report and presentation materials.

## Files Included

- `Capstone_Model_Development.ipynb`
- `feature_engineering.py`
- `inference.py`
- `test_inference.py`
- `final_pipeline_day4.pkl`
- `lgbm_pipeline_day5.pkl`
- `random_forest_pipeline_day5.pkl`
- Monitoring Checklist
- Executive Report

## Final Model Performance

| Metric | Value |
|---------|-------|
| Accuracy | 86.72% |
| Precision | 79.49% |
| Recall | 60.01% |
| F1-score | 68.39% |
| ROC AUC | 0.9198 |
| PR AUC | 0.7988 |

The final deployed model is a **Calibrated LightGBM** classifier using a custom decision threshold of **0.45**, selected to satisfy the business requirement of achieving at least **75% precision** while maximizing recall.
