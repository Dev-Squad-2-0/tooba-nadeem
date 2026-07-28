
# Week 6 Day 2: AFL Prediction Models

This project builds and evaluates two machine learning models for AFL prediction:

1. **Match Winner Model**  
   Predicts whether the home team will win using pre-match team features.

2. **Top Player Model**  
   Predicts player fantasy points for an upcoming match and ranks players by their predicted performance.

## Models

### Match Winner
Two classification models were evaluated:

- Logistic Regression
- Gradient Boosting (`HistGradientBoostingClassifier`)

The models were evaluated using accuracy, F1, ROC AUC, and Brier score. Gradient Boosting was selected as the final match-winner model based on the evaluation results and overall predictive performance.

### Top Player
The top-player task was framed as a regression problem.

- Baseline: recent-form fantasy-point average
- Model: Random Forest Regressor

The model was evaluated using MAE, RMSE, Top-1 hit rate, and Top-5 hit rate.

The Random Forest improved MAE, RMSE, and Top-5 hit rate over the baseline.

## Data and Leakage

The match-winner target is `home_win`, where:

- `1` = home team won
- `0` = home team did not win

Draws were excluded from the binary match-winner modelling dataset.

Only information available before the match was used as predictive input. Rolling statistics and other player/team features were constructed from previous matches to avoid target leakage.

## Project Files

```text
Day26/
├── notebook.ipynb
├── predict.py
├── models/
│   ├── match_winner_gradient_boosting.joblib
│   └── top_player_random_forest.joblib
└── data/
    ├── match_prediction_features.csv
    └── player_prediction_features.csv
