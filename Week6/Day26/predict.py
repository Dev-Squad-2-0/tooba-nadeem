from pathlib import Path

import joblib
import pandas as pd


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "top_player_random_forest.joblib"
)

FEATURES_PATH = (
    BASE_DIR
    / "data"
    / "player_prediction_features.csv"
)


# -------------------------------------------------------------------
# Model features
# -------------------------------------------------------------------

PLAYER_FEATURES = [
    "fantasy_points_last3_avg",
    "fantasy_points_last5_avg",
    "goals_last3_avg",
    "goals_last5_avg",
    "disposals_last3_avg",
    "disposals_last5_avg",
    "career_experience",
    "days_since_last_match",
    "round_number",
    "team",
    "opponent",
    "home_away",
]


# -------------------------------------------------------------------
# Load model and feature data
# -------------------------------------------------------------------

def load_model():
    """Load the saved top-player prediction pipeline."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


def load_feature_table():
    """Load the player-level pre-match feature table."""
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Feature table not found: {FEATURES_PATH}"
        )

    data = pd.read_csv(
        FEATURES_PATH,
        parse_dates=["match_date"]
    )

    return data


# -------------------------------------------------------------------
# Prediction function
# -------------------------------------------------------------------

def predict_top_player(
    match_date,
    team_a,
    team_b,
    top_k=5
):
    """
    Predict the top fantasy-point players for an AFL matchup.

    Parameters
    ----------
    match_date : str or datetime-like
        Date of the match.

    team_a : str
        First team.

    team_b : str
        Second team.

    top_k : int, default=5
        Number of players to return.

    Returns
    -------
    dict
        Ranked player predictions.
    """

    # Validate top_k
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError(
            "top_k must be a positive integer."
        )

    # Validate team names
    data = load_feature_table()

    available_teams = set(
        data["team"].dropna().unique()
    )

    if team_a not in available_teams:
        raise ValueError(
            f"Unknown team: '{team_a}'. "
            "Please use a valid AFL team name."
        )

    if team_b not in available_teams:
        raise ValueError(
            f"Unknown team: '{team_b}'. "
            "Please use a valid AFL team name."
        )

    if team_a == team_b:
        raise ValueError(
            "team_a and team_b must be different teams."
        )

    # Validate date
    try:
        prediction_date = pd.to_datetime(match_date)
    except Exception:
        raise ValueError(
            f"Invalid match date: '{match_date}'."
        )

    # Find player records for the requested matchup
    match_players = data[
        (data["match_date"] == prediction_date)
        &
        (
            (
                (data["team"] == team_a)
                &
                (data["opponent"] == team_b)
            )
            |
            (
                (data["team"] == team_b)
                &
                (data["opponent"] == team_a)
            )
        )
    ].copy()

    if match_players.empty:
        raise ValueError(
            f"No player records found for "
            f"{team_a} vs {team_b} on "
            f"{prediction_date.date()}."
        )

    # Load model
    model = load_model()

    # Generate predictions
    X_match = match_players[PLAYER_FEATURES]

    match_players["predicted_fantasy_points"] = (
        model.predict(X_match)
    )

    # Rank players
    ranked = (
        match_players
        .sort_values(
            "predicted_fantasy_points",
            ascending=False
        )
        .head(top_k)
        .reset_index(drop=True)
    )

    ranked["rank"] = ranked.index + 1

    # Return clean output
    predictions = []

    for _, row in ranked.iterrows():
        predictions.append({
            "rank": int(row["rank"]),
            "player": row["player_name"],
            "team": row["team"],
            "predicted_fantasy_points": round(
                float(row["predicted_fantasy_points"]),
                2
            ),
        })

    return {
        "match_date": prediction_date.strftime("%Y-%m-%d"),
        "match": f"{team_a} vs {team_b}",
        "top_k": top_k,
        "predictions": predictions,
    }


# -------------------------------------------------------------------
# Match-winner model
# -------------------------------------------------------------------

MATCH_MODEL_PATH = (
    BASE_DIR
    / "models"
    / "match_winner_gradient_boosting.joblib"
)

MATCH_FEATURES_PATH = (
    BASE_DIR
    / "data"
    / "match_prediction_features.csv"
)


MATCH_WINNER_FEATURES = [
    "home_career_experience",
    "away_career_experience",
    "home_days_since_last_match",
    "away_days_since_last_match",
    "home_goals_last3_avg",
    "away_goals_last3_avg",
    "home_goals_last5_avg",
    "away_goals_last5_avg",
    "home_disposals_last3_avg",
    "away_disposals_last3_avg",
    "home_disposals_last5_avg",
    "away_disposals_last5_avg",
    "home_fantasy_points_last3_avg",
    "away_fantasy_points_last3_avg",
    "home_fantasy_points_last5_avg",
    "away_fantasy_points_last5_avg",
    "home_h2h_win_rate_entering_match",
    "away_h2h_win_rate_entering_match",
    "home_team",
    "away_team",
]


def load_match_winner_model():
    """Load the saved Gradient Boosting match-winner pipeline."""

    if not MATCH_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Match-winner model not found: {MATCH_MODEL_PATH}"
        )

    return joblib.load(MATCH_MODEL_PATH)


def load_match_feature_table():
    """Load the match-level pre-match feature table."""

    if not MATCH_FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Match feature table not found: {MATCH_FEATURES_PATH}"
        )

    return pd.read_csv(
        MATCH_FEATURES_PATH,
        parse_dates=["match_date"]
    )


def predict_match_winner(
    match_date,
    home_team,
    away_team
):
    """
    Predict the winner of an AFL match.

    Parameters
    ----------
    match_date : str or datetime-like
        Date of the match.

    home_team : str
        Home team.

    away_team : str
        Away team.

    Returns
    -------
    dict
        Predicted winner and win probabilities.
    """

    data = load_match_feature_table()

    # ---------------------------------------------------------------
    # Validate teams
    # ---------------------------------------------------------------

    available_teams = set(
        data["home_team"].dropna().unique()
    ) | set(
        data["away_team"].dropna().unique()
    )

    if home_team not in available_teams:
        raise ValueError(
            f"Unknown home team: '{home_team}'. "
            "Please use a valid AFL team name."
        )

    if away_team not in available_teams:
        raise ValueError(
            f"Unknown away team: '{away_team}'. "
            "Please use a valid AFL team name."
        )

    if home_team == away_team:
        raise ValueError(
            "home_team and away_team must be different teams."
        )

    # ---------------------------------------------------------------
    # Validate date
    # ---------------------------------------------------------------

    try:
        prediction_date = pd.to_datetime(match_date)
    except Exception:
        raise ValueError(
            f"Invalid match date: '{match_date}'."
        )

    # ---------------------------------------------------------------
    # Find the requested match
    # ---------------------------------------------------------------

    match = data[
        (data["match_date"] == prediction_date)
        &
        (data["home_team"] == home_team)
        &
        (data["away_team"] == away_team)
    ].copy()

    if match.empty:
        raise ValueError(
            f"No match records found for "
            f"{home_team} vs {away_team} on "
            f"{prediction_date.date()}."
        )

    # ---------------------------------------------------------------
    # Generate prediction
    # ---------------------------------------------------------------

    model = load_match_winner_model()

    X_match = match[MATCH_WINNER_FEATURES]

    predicted_class = int(
        model.predict(X_match)[0]
    )

    probabilities = model.predict_proba(X_match)[0]

    # Find probability associated with class 1 = home win
    classes = model.named_steps["model"].classes_

    home_win_probability = float(
        probabilities[
            list(classes).index(1)
        ]
    )

    away_win_probability = 1.0 - home_win_probability

    # ---------------------------------------------------------------
    # Determine winner
    # ---------------------------------------------------------------

    if predicted_class == 1:
        predicted_winner = home_team
    else:
        predicted_winner = away_team

    return {
        "match_date": prediction_date.strftime("%Y-%m-%d"),
        "home_team": home_team,
        "away_team": away_team,
        "predicted_winner": predicted_winner,
        "home_win_probability": round(
            home_win_probability,
            4
        ),
        "away_win_probability": round(
            away_win_probability,
            4
        ),
    }


# -------------------------------------------------------------------
# Example
# -------------------------------------------------------------------

if __name__ == "__main__":
    result = predict_top_player(
        match_date="2025-03-13",
        team_a="Carlton Blues",
        team_b="Richmond Tigers",
        top_k=5,
    )

    print(result)