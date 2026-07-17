import pandas as pd
import numpy as np

# ==========================================================
# Part -1 - Featiure Engineering Function
# ==========================================================

# from sklearn.feature_selection import mutual_info_classif (added already in above cells)

def add_engineered_features(X):
    """
    FunctionTransformer-compatible feature engineering.
    Uses ONLY current-row data — no target, no cross-row aggregation, no leakage.
    """
    X = X.copy()

    # 1. Age buckets
    X["age_bucket"] = pd.cut(
        X["age"], bins=[0, 25, 35, 45, 55, 65, 100],
        labels=["<25", "25-34", "35-44", "45-54", "55-64", "65+"]
    ).astype(str)

    # 2. Hours-per-week bins
    X["hours_bucket"] = pd.cut(
        X["hours-per-week"], bins=[0, 39, 40, 50, 100],
        labels=["part-time(<40)", "standard(40)", "overtime(41-50)", "heavy(50+)"]
    ).astype(str)

    # 3. Flag: capital_gain > 0
    X["has_capital_gain"] = (X["capital-gain"] > 0).astype(int)

    # 4. Flag: capital_loss > 0 (symmetric addition to #3)
    X["has_capital_loss"] = (X["capital-loss"] > 0).astype(int)

    # 5. log(capital_gain + 1) — handles zero-inflation (Day 2 discussion: plain log() breaks on the ~92% zero rows)
    X["log_capital_gain"] = np.log1p(X["capital-gain"]) # same as "np.log(X["capital-gain"] + 1)"

    # 6. log(capital_loss + 1)
    X["log_capital_loss"] = np.log1p(X["capital-loss"])

    # 7. Higher-education boolean (Bachelors+ i.e. education-num >= 13)
    X["higher_education"] = (X["education-num"] >= 13).astype(int)

    # 8. Interaction: education_num x hours_per_week
    X["education_hours_interaction"] = X["education-num"] * X["hours-per-week"]

    return X