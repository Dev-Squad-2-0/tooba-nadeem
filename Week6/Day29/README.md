# AFL Assistant — Week 6 Day 5

Hardening, evaluation, API wrapper, logging, monitoring, and documentation
added on top of the Days 1–4 AFL agent. See `executive_report.md` for the
full summary and `evaluation/day5_evaluation_report.md` for detailed
results.

## What's new in Day 5

- `src/tools.py` — prediction tools (`predict_match`, `predict_top_players`)
  are now registered with the chat agent (previously unreachable).
- `src/agent.py` — tool calls are isolated (errors/timeouts can't crash the
  agent), predictions get an enforced disclaimer, input size + rate limits
  are checked, and every turn is logged.
- `src/guardrails.py` — rate limiting, input validation, and a
  scope-override heuristic (secondary defense layer).
- `src/logging_utils.py` — structured JSON-line logging to
  `logs/agent_events.jsonl`.
- `main.py` — FastAPI app: `POST /chat`, `GET /health`, and a minimal
  built-in chat page at `/`.
- `evaluation/day5_test_cases.py` — 30 cases across 6 categories,
  including 5 prompt-injection attempts.
- `evaluation/run_day5_evaluation_stub.py` — runs the parts of the suite
  that don't need a live LLM (already executed; see the report).
- `evaluation/run_day5_evaluation_live.py` — run this yourself with a real
  API key to grade the LLM-dependent categories.
- `monitoring_checklist.md`, `executive_report.md`, `demo_script.md`.

## Setup (Windows-friendly)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `OPENROUTER_API_KEY` (this is what `src/config.py`
currently reads — the NetixSol block is present but commented out).

## Running the API

```
uvicorn main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000/docs` for Swagger, or
`http://127.0.0.1:8000/` for the minimal built-in chat page.

## Running the evaluation suite

```
python -m evaluation.run_day5_evaluation_stub
python -m evaluation.run_day5_evaluation_live
```

The first needs no API key and reproduces the results already documented
in `evaluation/day5_evaluation_report.md`. The second needs a working
`OPENROUTER_API_KEY` and writes `evaluation/day5_live_results.csv`.

## Running the tests

```
python -m tests.test_guardrails
```

(Requires a working API key — this exercises the live agent against
`evaluation/guardrail_tests.csv`.)
