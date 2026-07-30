from src.prediction_tools import (
    resolve_team_name,
)


tests = [
    "Pies",
    "Cats",
    "Blues",
    "Tigers",
    "Swans",
    "Collingwood Magpies",
    "Geelong Cats",
]


for team in tests:
    print(f"{team:25} → {resolve_team_name(team)}")