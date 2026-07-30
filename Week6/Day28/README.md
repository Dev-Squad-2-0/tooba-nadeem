
# My project sturcture
```python
Week6/
└── Day4/
    │
    ├── data/
    │   ├── cleaned_round_by_round_stats_v2.csv
    │   ├── cleaned_team_matches.csv
    │   ├── cleaned_seasonal_stats.csv
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
    │   ├── state.py
    │   ├── router.py
    │   ├── retrieval.py
    │   ├── predict.py          ← Day 2 prediction code
    │   ├── resolver.py
    │   ├── tools.py
    │   ├── nodes.py
    │   └── agent.py
    │
    ├── tests/
    │   ├── test_guardrails.py
    │   ├── test_router.py
    │   ├── test_resolver.py
    │   ├── test_prediction.py
    │   └── test_graph.py
    │
    ├── evaluation/
    │   ├── guardrail_tests.csv
    │   ├── evaluation_report.md
    │   ├── routing_tests.csv
    │   ├── routing_results.csv
    │   └── day4_report.md
    │
    ├── traces/
    │   ├── prediction_trace.txt
    │   ├── retrieval_trace.txt
    │   └── clarification_trace.txt
    │
    ├── requirements.txt
    ├── .env.example
    ├── .gitignore
    └── day4_demo.ipynb
```

# Task 1 requirement:
## Why Explicit LangGraph Routing Is Safer

The system uses explicit LangGraph routing instead of allowing one general-purpose agent to freely decide which tool or action to use. The router first classifies each request as `factual`, `retrieval`, `prediction`, or `off_topic`, and LangGraph then sends the request to the corresponding controlled branch.

This is safer because each type of request has a defined processing path. In particular, prediction requests always pass through the prediction and response-formatting logic, ensuring that model probabilities are presented as probabilistic predictions rather than certain outcomes. Explicit routing also reduces the risk of calling the wrong tool, using unsupported capabilities, or allowing the agent to guess when required information is unavailable.

