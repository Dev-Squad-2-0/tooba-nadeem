# Week 4 - Day 3: Feature Engineering, Cross-Validation & Model Comparison

## Overview

Today's objective was to improve the Adult Income prediction model by creating meaningful engineered features, integrating them into the machine learning pipeline, comparing multiple classification models using cross-validation, performing statistical significance testing, and evaluating whether feature selection should be used before hyperparameter tuning.

## Tasks Completed

### Task 1: Feature Engineering

* Created 8 engineered features using only current-row information (no data leakage).
* Justified each engineered feature based on domain knowledge.
* Evaluated their predictive strength using Mutual Information.
* Documented the engineered features in a feature dictionary.

### Task 2: Pipeline Integration

* Integrated feature engineering into the preprocessing pipeline using `FunctionTransformer`.
* Applied preprocessing consistently using `ColumnTransformer`.
* Ensured the entire workflow remained leakage-free.

### Task 3: Cross-Validated Model Comparison

Compared the following models using **5-fold Stratified Cross-Validation**:

* Logistic Regression
* Random Forest
* HistGradientBoosting
* XGBoost
* LightGBM

Models were evaluated using:

* Precision (Primary Metric)
* F1 Score
* ROC AUC

Cross-validation results were summarized using tables and boxplots.

### Task 4: Statistical Comparison & Feature Analysis

* Compared the top two models using:

  * Paired t-test
  * Wilcoxon Signed-Rank Test
* Interpreted the statistical significance of the observed performance difference.
* Examined Logistic Regression coefficients and Random Forest feature importances to identify the most influential engineered features.

### Task 5: Feature Selection

* Applied `SelectKBest` with Mutual Information.
* Compared performance and training time against the complete feature set.
* Determined whether feature selection should be used before hyperparameter tuning.

## Key Outcomes

* HistGradientBoosting achieved the highest Precision, while LightGBM achieved the best F1 Score and ROC AUC.
* Statistical testing showed no significant difference between the two best-performing models.
* Capital gain-related features and the interaction between education level and working hours were among the most informative engineered features.
* Feature selection provided only a negligible improvement in Precision while increasing training time substantially and reducing F1 Score and ROC AUC.
* The complete engineered feature set was selected for the next stage of hyperparameter tuning.

## Technologies & Libraries

* Python
* Pandas
* NumPy
* Scikit-learn
* XGBoost
* LightGBM
* Matplotlib
* SciPy

## Learning Outcomes

By completing this task, I gained practical experience in:

* Feature engineering using domain knowledge
* Building reusable preprocessing pipelines
* Cross-validation for reliable model evaluation
* Comparing multiple machine learning models
* Statistical significance testing for model comparison
* Interpreting feature importance and model coefficients
* Evaluating the trade-offs of feature selection
