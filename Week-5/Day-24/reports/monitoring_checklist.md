# Production Monitoring Checklist — Web3Geeks Support Triage Agent

## What to track

| Metric | Why it matters | Source |
|---|---|---|
| **Error rate** (5xx / unhandled exceptions per 100 requests) | Catches bugs and upstream endpoint outages before customers notice | FastAPI logs (`errors` field), `/health` |
| **LLM fallback rate** (% of runs using `rule_based_fallback` / `template_fallback`) | A rising rate means the company LLM endpoint is degrading (rate limits, latency, outages) even if the pipeline itself looks "fine" | `classification_source` field in structured logs |
| **Latency** (p50 / p95 per ticket, and per node) | Slow triage delays every downstream team; per-node timing isolates whether it's the LLM call or a tool | `trace` array in state (per-node `latency_ms`) |
| **Cost per run** (tokens × model price, summed daily) | Model costs drift as ticket volume or fallback-chain usage changes | Token usage from LLM response (add to `LLMResult` before going live) |
| **Output quality drift** (spot-check sample of drafts weekly) | Classification/response quality can silently degrade after a model or prompt change | Manual review sample + periodic re-run of `evaluation/run_eval.py` |
| **Human-checkpoint integrity** (% of sensitive tickets that actually paused for approval) | This must always be 100% — any drop is a safety-critical regression, not a quality one | `requires_human_approval` vs. `status` in logs; alert on any sensitive-category ticket that reached `resolved` without an `approval_status` |

## Alert thresholds (starting points — tune after two weeks of real data)

- Error rate > 2% over any rolling 15-minute window → page on-call.
- LLM fallback rate > 25% over 1 hour → investigate company endpoint status; > 50% → page on-call.
- p95 latency > 5x the 7-day baseline → investigate.
- **Any** sensitive-category ticket resolved without a recorded approval decision → page on-call immediately (safety-critical, zero-tolerance).
- Daily cost > 150% of the trailing 7-day average → flag for review (not necessarily page).

## Re-evaluation cadence

- **Weekly:** rerun `evaluation/run_eval.py` against the live endpoint; track the 6 scoring criteria over time in a simple spreadsheet/dashboard.
- **On every prompt or model change:** rerun the full evaluation suite before deploying, and add the specific failure case to `test_cases.json` if the change was prompted by a real incident.
- **Monthly:** review a random sample of 20 resolved tickets manually for tone/quality drift and routing correctness that automated scoring might miss.
- **Quarterly:** revisit the `SENSITIVE_ISSUE_CATEGORIES` list and FAQ/project keyword data — new products or new consequential actions need to be added deliberately, not discovered via a routing miss.
