from langchain_core.tools import tool

from .retrieval import (
    get_player_season_stats,
    get_player_match_stats,
    get_team_vs_team_record,
)

from .prediction_tools import (
    predict_match,
    predict_top_players,
)


@tool
def player_season_stats(
    player_name: str,
    season: int,
    is_finals: bool = False,
) -> dict:
    """
    Retrieve exact AFL statistics for a player's regular season or finals season.

    Use this when the user asks about a player's season totals or averages,
    such as disposals, goals, tackles, marks, or games played.
    """
    return get_player_season_stats(
        player_name=player_name,
        season=season,
        is_finals=is_finals,
    )


@tool
def player_match_stats(
    player_name: str,
    season: int,
    round_number: int,
) -> dict:
    """
    Retrieve exact AFL statistics for a player in a specific round.

    Use this for questions about a player's performance in a particular
    AFL round, including disposals, goals, marks, tackles, and fantasy points.
    """
    return get_player_match_stats(
        player_name=player_name,
        season=season,
        round_number=round_number,
    )


@tool
def team_vs_team_record(
    team_name: str,
    opponent_name: str,
) -> dict:
    """
    Retrieve the historical AFL head-to-head record between two teams.

    Returns matches played, wins, losses, and draws for the first team
    against the second team.
    """
    return get_team_vs_team_record(
        team_name=team_name,
        opponent_name=opponent_name,
    )


AFL_TOOLS = [
    player_season_stats,
    player_match_stats,
    team_vs_team_record,
    predict_match,
    predict_top_players,
]