## Task 4: End-to-End Inference & Basic Monitoring

"""
Inference script for the Adult Income Prediction model.

This script:
- Loads the saved calibrated LightGBM pipeline.
- Accepts raw input as a dictionary or CSV.
- Performs input validation.
- Returns:
    - Predicted probability
    - Predicted class
    - Top-3 contributing features (SHAP)
"""
import warnings
import joblib
import shap
import pandas as pd
import numpy as np

from feature_engineering import add_engineered_features

warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names.*"
)

# ==========================================================
# Part 0 - Configuration
# ==========================================================

MODEL_PATH = "final_pipeline_day4.pkl"

DECISION_THRESHOLD = 0.45

EXPECTED_COLUMNS = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education-num",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country"
]

# ==========================================================
# Part 1 — Load the saved model
# ==========================================================

# Load calibrated model
calibrated_model = joblib.load(MODEL_PATH)

# Extract the fitted pipeline
pipeline = calibrated_model.estimator.estimator

# Extract the fitted LightGBM model
lgbm_model = pipeline.named_steps["classifier"]

# SHAP explainer
explainer = shap.TreeExplainer(lgbm_model)


# ==========================================================
# Part 4 — Input Validation
# ==========================================================

def validate_input(df):

    missing = set(EXPECTED_COLUMNS) - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    return True


# ==========================================================
# Part 2 — Build Inference Function
# Prediction 
# ==========================================================

def predict(sample):

    """
    Predict from either

    - dictionary

    OR

    - pandas DataFrame

    Returns dictionary.
    """

    if isinstance(sample, dict):
        sample = pd.DataFrame([sample])

    validate_input(sample)

    probability = calibrated_model.predict_proba(sample)[0, 1]

    prediction = int(probability >= DECISION_THRESHOLD)

    # -------------------------------
    # SHAP
    # -------------------------------

    engineered = (
        pipeline.named_steps["feature_engineering"]
        .transform(sample)
    )

    processed = (
        pipeline.named_steps["preprocessor"]
        .transform(engineered)
    )

    shap_values = explainer(processed)

    values = np.abs(shap_values.values[0])

    feature_names = (
        pipeline
        .named_steps["preprocessor"]
        .get_feature_names_out()
    )

    top3 = (
        pd.DataFrame({

            "Feature": feature_names,

            "Contribution": values

        })
        .sort_values(
            by="Contribution",
            ascending=False
        )
        .head(3)
        ["Feature"]
        .tolist()
    )

    return {

        "Probability": round(float(probability), 4),

        "Prediction":

            ">50K"

            if prediction == 1

            else "<=50K",

        "Threshold": DECISION_THRESHOLD,

        "Top 3 Features": top3

    }


# ==========================================================
# Part 3 — Test on Sample Record
# ==========================================================

if __name__ == "__main__":

    sample = {

        "age": 39,
        "workclass": "Private",
        "fnlwgt": 77516,
        "education": "Bachelors",
        "education-num": 13,
        "marital-status": "Never-married",
        "occupation": "Prof-specialty",
        "relationship": "Not-in-family",
        "race": "White",
        "sex": "Male",
        "capital-gain": 2174,
        "capital-loss": 0,
        "hours-per-week": 40,
        "native-country": "United-States"

    }

    print(predict(sample))