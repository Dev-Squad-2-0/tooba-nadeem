# Part 5 — Unit Tests

import warnings

import __main__

from feature_engineering import add_engineered_features

__main__.add_engineered_features = add_engineered_features

import pandas as pd

from inference import predict

warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names.*"
)

# ==========================================================
# Test 1
# Valid Input
# ==========================================================

def test_valid_prediction():

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

    result = predict(sample)

    assert "Probability" in result

    assert "Prediction" in result

    assert "Top 3 Features" in result


# ==========================================================
# Test 2
# Missing Column
# ==========================================================

def test_missing_column():

    sample = {

        "age": 39

    }

    try:

        predict(sample)

        assert False

    except ValueError:

        assert True


# ==========================================================
# Test 3
# Unseen Category
# ==========================================================

def test_unseen_category():

    sample = {

        "age": 39,
        "workclass": "Google",
        "fnlwgt": 77516,
        "education": "Bachelors",
        "education-num": 13,
        "marital-status": "Never-married",
        "occupation": "Scientist",
        "relationship": "Not-in-family",
        "race": "White",
        "sex": "Male",
        "capital-gain": 2174,
        "capital-loss": 0,
        "hours-per-week": 40,
        "native-country": "Mars"

    }

    try:

        predict(sample)

        print("Handled successfully.")

    except Exception:

        print("Unexpected category detected.")

if __name__ == "__main__":

    print("Running unit tests...\n")

    test_valid_prediction()
    print("✓ Test 1 Passed: Valid prediction")

    test_missing_column()
    print("✓ Test 2 Passed: Missing column validation")

    test_unseen_category()
    print("✓ Test 3 Completed: Unseen category test")

    print("\nAll tests completed successfully.")