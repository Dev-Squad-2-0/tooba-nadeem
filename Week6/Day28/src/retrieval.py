import pandas as pd

from .config import (
    ROUND_STATS_PATH,
    TEAM_MATCHES_PATH,
    SEASONAL_STATS_PATH,
)


round_stats = pd.read_csv(ROUND_STATS_PATH)
team_matches = pd.read_csv(TEAM_MATCHES_PATH)
seasonal_stats = pd.read_csv(SEASONAL_STATS_PATH)


#  Tool 1: Player season statistics
 
def get_player_season_stats(
    player_name: str,
    season: int,
    is_finals: bool = False,
) -> dict:
    """
    Retrieve a player's AFL season statistics.

    By default, returns regular-season statistics.
    Set is_finals=True to retrieve finals statistics.
    """

    matches = seasonal_stats[
        seasonal_stats["player_name"].str.lower() == player_name.lower()
    ]

    matches = matches[
        (matches["year"] == season) &
        (matches["is_finals"] == is_finals)
    ]

    if matches.empty:
        season_type = "finals" if is_finals else "regular season"

        return {
            "found": False,
            "message": (
                f"No {season_type} statistics found for "
                f"{player_name} in {season}."
            ),
        }

    if len(matches) > 1:
        return {
            "found": False,
            "message": (
                f"Multiple matching records found for {player_name} "
                f"in {season}. More specific identification is required."
            ),
        }

    row = matches.iloc[0]

    return {
        "found": True,
        "player_name": row["player_name"],
        "team": row["team"],
        "season": int(row["year"]),
        "is_finals": bool(row["is_finals"]),
        "games_played": row["games_played"],
        "disposals": row["disposals"],
        "goals": row["goals"],
        "marks": row["marks"],
        "tackles": row["tackles"],
        "avg_disposals": row["avg_disposals"],
        "avg_goals": row["avg_goals"],
        "avg_tackles": row["avg_tackles"],
    }


# Tool 2: Player match statistics

def get_player_match_stats(
    player_name: str,
    season: int,
    round_number: str,
) -> dict:
    """
    Retrieve a player's statistics for a specific AFL round.
    """

    player_records = seasonal_stats[
        seasonal_stats["player_name"].str.lower() == player_name.lower()
    ]

    if player_records.empty:
        return {
            "found": False,
            "message": f"Player {player_name} was not found.",
        }

    player_ids = player_records["player_id"].unique()

    matches = round_stats[
        (round_stats["player_id"].isin(player_ids)) &
        (round_stats["year"] == season) &
        (round_stats["round"].astype(str) == str(round_number))
    ]

    if matches.empty:
        return {
            "found": False,
            "message": (
                f"No match statistics found for {player_name} "
                f"in {season}, round {round_number}."
            ),
        }

    if len(matches) > 1:
        return {
            "found": False,
            "message": (
                f"Multiple match records found for {player_name} "
                f"in {season}, round {round_number}."
            ),
        }

    row = matches.iloc[0]

    return {
        "found": True,
        "player_name": player_name,
        "season": int(row["year"]),
        "round": row["round"],
        "team": row["team"],
        "opponent": row["opponent"],
        "result": row["result"],
        "disposals": row["disposals"],
        "goals": row["goals"],
        "marks": row["marks"],
        "tackles": row["tackles"],
        "fantasy_points": row["fantasy_points"],
    }


# Tool 3: Team vs Team record

def get_team_vs_team_record(
    team_name: str,
    opponent_name: str
) -> dict:
    """
    Retrieve a team's historical win-loss record against another AFL team.
    """
    matches = team_matches[
        (
            team_matches["team"].str.lower() == team_name.lower()
        ) &
        (
            team_matches["opponent"].str.lower() == opponent_name.lower()
        )
    ]

    if matches.empty:
        return {
            "found": False,
            "message": (
                f"No match history found between "
                f"{team_name} and {opponent_name}."
            )
        }

    wins = (matches["result"] == "W").sum()
    losses = (matches["result"] == "L").sum()
    draws = (matches["result"] == "D").sum()

    return {
    "found": True,
    "team": team_name,
    "opponent": opponent_name,
    "matches_played": len(matches),
    "wins": int(wins),
    "losses": int(losses),
    "draws": int(draws),
  }


