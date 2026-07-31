from langchain_core.tools import tool

from .predict import (
    predict_match_winner,
    predict_top_player,
)


# -------------------------------------------------------------------
# Team aliases
# -------------------------------------------------------------------

TEAM_ALIASES = {
    "pies": "Collingwood Magpies",
    "collingwood": "Collingwood Magpies",

    "cats": "Geelong Cats",
    "geelong": "Geelong Cats",

    "blues": "Carlton Blues",
    "carlton": "Carlton Blues",

    "tigers": "Richmond Tigers",
    "richmond": "Richmond Tigers",

    "swans": "Sydney Swans",
    "sydney": "Sydney Swans",

    "bombers": "Essendon Bombers",
    "essendon": "Essendon Bombers",

    "lions": "Brisbane Lions",
    "brisbane": "Brisbane Lions",

    "dockers": "Fremantle Dockers",
    "fremantle": "Fremantle Dockers",

    "hawks": "Hawthorn Hawks",
    "hawthorn": "Hawthorn Hawks",

    "demons": "Melbourne Demons",
    "melbourne": "Melbourne Demons",

    "bulldogs": "Western Bulldogs",
    "western bulldogs": "Western Bulldogs",

    "eagles": "West Coast Eagles",
    "west coast": "West Coast Eagles",

    "power": "Port Adelaide Power",
    "port adelaide": "Port Adelaide Power",

    "suns": "Gold Coast Suns",
    "gold coast": "Gold Coast Suns",

    "giants": "Greater Western Sydney Giants",
    "gws": "Greater Western Sydney Giants",

    "saints": "St Kilda Saints",
    "st kilda": "St Kilda Saints",

    "kangaroos": "North Melbourne Kangaroos",
    "north melbourne": "North Melbourne Kangaroos",

    "crows": "Adelaide Crows",
    "adelaide": "Adelaide Crows",
}


def resolve_team_name(team: str) -> str:
    """
    Convert a team nickname or shorthand into the
    exact team name used by the prediction dataset.
    """

    normalized = team.strip().lower()

    if normalized in TEAM_ALIASES:
        return TEAM_ALIASES[normalized]

    return team.strip()


# -------------------------------------------------------------------
# Match winner tool
# -------------------------------------------------------------------

@tool
def predict_match(
    match_date: str,
    home_team: str,
    away_team: str,
) -> dict:
    """
    Predict the winner of an AFL match.

    Use the exact match date and team names when possible.
    Team nicknames such as 'Pies' and 'Cats' are accepted.
    """

    resolved_home = resolve_team_name(home_team)
    resolved_away = resolve_team_name(away_team)

    return predict_match_winner(
        match_date=match_date,
        home_team=resolved_home,
        away_team=resolved_away,
    )


# -------------------------------------------------------------------
# Top player tool
# -------------------------------------------------------------------

@tool
def predict_top_players(
    match_date: str,
    team_a: str,
    team_b: str,
    top_k: int = 5,
) -> dict:
    """
    Predict the players most likely to produce the highest
    fantasy-point totals in an AFL match.

    Team nicknames such as 'Pies' and 'Cats' are accepted.
    """

    resolved_team_a = resolve_team_name(team_a)
    resolved_team_b = resolve_team_name(team_b)

    return predict_top_player(
        match_date=match_date,
        team_a=resolved_team_a,
        team_b=resolved_team_b,
        top_k=top_k,
    )