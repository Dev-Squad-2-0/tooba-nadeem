## Structure:
```python
Week6/
└── Day3/
    │
    ├── data/
    │   ├──cleaned_round_by_round_stats_v2.csv  
    │   ├──cleaned_team_matches.csv
    │   ├──cleaned_seasonal_stats.csv
    │   ├── match_prediction_features.csv
    │   └── player_prediction_features.csv
    │
    ├── models/
    │   ├── match_winner_gradient_boosting.joblib
    │   └── top_player_random_forest.joblib
    │
    ├── src/
    │   ├── config.py
    │   ├── prompts.py
    │   ├── retrieval.py
    │   ├── tools.py
    │   └── agent.py
    │
    ├── tests/
    │   └── test_guardrails.py
    │
    ├── evaluation/
    │   ├── guardrail_tests.csv
    │   └── evaluation_report.md
    ├── requirements.txt
    ├── .env.example
    ├── .gitignore
    └── day3_demo.ipynb
```
