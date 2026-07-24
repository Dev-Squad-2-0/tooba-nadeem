# Web3Geeks Intelligent Support Triage Agent

A production-shaped LangGraph agent that reads incoming support tickets, identifies which
Web3Geeks product they belong to, classifies the issue, sets priority, routes to the right
department, retrieves relevant FAQ content, drafts a reply, and — for anything consequential
(refunds, billing disputes, account recovery, security incidents) — pauses for a human
approval before resolving. Wrapped behind a FastAPI service with structured logging.

## Folder structure

```
app/
  config.py              # env-driven config, model fallback chain, sensitive categories
  state.py               # shared LangGraph state schema (TicketState)
  graph.py               # graph topology: nodes, conditional edges, interrupt, checkpointer
  logging_config.py       # structured JSON logging setup
  nodes/                 # one file per graph node
  tools/
    llm_client.py         # OpenAI-compatible client w/ model fallback + refusal detection
    classifier_rules.py   # deterministic keyword classifier (fallback path)
    faq_tool.py           # FAQ retrieval tool (external data source)
  data/
    projects.json         # product -> department/escalation mapping (external data source)
    faq.json              # FAQ knowledge base (external data source)
  api/
    main.py               # FastAPI app: /tickets, /tickets/{id}, /tickets/{id}/approve, /health
    schemas.py            # Pydantic request/response models
evaluation/
  test_cases.json         # 10 test cases (8 regular + 2 adversarial)
  run_eval.py             # runs the suite, scores 6 criteria, writes results.md/json
  results.md / results.json
reports/
  build_report.py          # generates the 2-page executive report PDF
  build_diagram.py          # generates the architecture diagram PNG
  architecture_diagram.png
  monitoring_checklist.md
  presentation_outline.md
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in API_KEY with your real company key
```

## Running the API

```bash
export $(cat .env | xargs)   # or use python-dotenv / your process manager
uvicorn app.api.main:app --reload
```

- `POST /tickets` — submit a ticket. Returns `resolved`, `pending_human_review`, or
  `rejected_invalid_input` immediately (synchronous graph run).
- `GET /tickets/{ticket_id}` — check current status of a ticket (useful while it's pending).
- `POST /tickets/{ticket_id}/approve` — resume a ticket paused at the human-approval gate.
  Body: `{"approved": true, "reviewer_notes": "..."}`.
- `GET /health` — liveness check.

## Running in mock mode (no live API key needed)

Every LLM-calling node automatically falls back to a deterministic rule-based classifier on
any model error. Set `LLM_MODE=mock` to force every call through that fallback path — useful
for local development, CI, or environments without network access to the company endpoint:

```bash
LLM_MODE=mock uvicorn app.api.main:app --reload
```

## Running the evaluation suite

```bash
LLM_MODE=mock python evaluation/run_eval.py    # offline
LLM_MODE=live python evaluation/run_eval.py    # against the real company endpoint
```

Results are written to `evaluation/results.md` (human-readable table + failure analysis) and
`evaluation/results.json` (raw scored output per case).

**Important:** the results currently committed in this repo were generated with
`LLM_MODE=mock`, because the dev sandbox this was built in has no network egress to
`https://llm.netixsol.com`. In mock mode, every node's LLM call intentionally fails validation
and falls back to the rule-based path — a genuine test of the graceful-degradation logic, but
not of the LLM's own classification/drafting quality. **Before submitting for grading or
deploying, rerun with `LLM_MODE=live` and a real `API_KEY`** to get the numbers that reflect
actual LLM performance; nothing else about the harness needs to change.

## Regenerating the report / diagram

```bash
python reports/build_diagram.py   # -> reports/architecture_diagram.png
python reports/build_report.py    # -> /mnt/user-data/outputs/...Executive_Report.pdf
```

## Known limitations & next steps

See Section 5 and 6 of the executive report (`reports/` output PDF) and
`reports/monitoring_checklist.md` for the full list — in short: this needs a live-endpoint
evaluation run, a persistent (non-in-memory) LangGraph checkpointer, and basic API
authentication before production deployment.

