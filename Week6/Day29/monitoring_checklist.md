# AFL Agent — Monitoring Checklist (Week 6 Day 5)

One-page reference for what to watch in production and when to act.
Source of truth for the metrics below is `logs/agent_events.jsonl`
(one JSON record per turn — see `src/logging_utils.py`).

## 1. Response Latency

| Metric | How to compute | Alert threshold |
|---|---|---|
| p50 / p95 / p99 turn latency | `total_latency_ms` per record, windowed hourly | p95 > 8s → investigate; p95 > 15s → page |
| Tool latency | `tools_called[].latency_ms` | any single tool call > `TOOL_TIMEOUT_SECONDS` (10s) is already cut off and logged as `status="timeout"` |
| LLM fallback frequency | count of `model_used != PRIMARY_MODEL` per hour | >20% of turns falling back → provider/proxy likely degraded |

## 2. Tool Error Rate

| Metric | How to compute | Alert threshold |
|---|---|---|
| Tool error rate | `status in {"tool_error"}` / total turns | >5% sustained over 1hr → investigate (usually bad team/player name parsing, or a data file issue) |
| Per-tool error rate | group `tools_called[].status == "error"` by `name` | one tool consistently failing → check that tool's underlying CSV/model file is present and loadable |
| Agent crash rate | `status == "agent_error"` | any nonzero rate is worth a same-day look — this path exists as a safety net, not an expected outcome |

## 3. Off-Topic Leak Rate

Definition: the fraction of clearly off-topic / injection-style messages that receive a substantive (non-refusal) answer instead of the AFL redirect.

| Metric | How to compute | Alert threshold |
|---|---|---|
| Leak rate | run the prompt_injection + scope subset of `evaluation/day5_test_cases.py` weekly against the live model; % that fail to refuse | >0% on prompt_injection cases → treat as a priority fix, not a minor bug (this is the core scope guarantee) |
| Heuristic-only catch rate | `guardrails.looks_like_override_attempt()` catch rate on the same set (fast, no LLM call needed) | tracked as a secondary/faster signal; a drop here means new injection phrasing patterns are emerging and the keyword list needs updating |

## 4. Prediction Accuracy Drift

| Metric | How to compute | Alert threshold |
|---|---|---|
| Match-winner accuracy vs. baseline | re-run the holdout comparison in `evaluation/day5_evaluation_report.md` §Model Comparison on newly completed rounds each week | if model accuracy drops within ~5 points of the h2h/form baseline → retrain candidate |
| Distribution shift | compare current-season feature averages (form, h2h win rate) to the training data's distribution | large shift (e.g. new team relocations, rule changes affecting scoring) → flag for retraining review |

## 5. Alert Thresholds Summary

| Signal | Warning | Page/urgent |
|---|---|---|
| p95 latency | > 8s | > 15s |
| Tool error rate | > 5%/hr | > 15%/hr |
| Agent crash rate | > 0.5%/hr | > 2%/hr |
| Injection leak rate (weekly eval) | > 0% | any repeated failure on the same case across 2 weekly runs |
| Rate-limit hits | informational only (expected under abuse) | sudden spike (10x baseline) → possible bot/abuse traffic |

## 6. Evaluation / Retraining Cadence

- **Weekly**: re-run `evaluation/day5_test_cases.py` (all 30 cases) against the live model. Track category pass rates over time in a simple running log.
- **Weekly**: re-run the model-vs-baseline accuracy comparison as new AFL rounds complete and get appended to `match_prediction_features.csv`.
- **Per-round (during season)**: refresh `data/*.csv` with newly completed round results so `_last3_avg`/`_last5_avg`/`h2h_win_rate` features stay current — stale rolling averages are the most likely silent failure mode for prediction quality.
- **Retraining trigger**: retrain match-winner / top-player models if (a) accuracy drops within 5 points of baseline for 2 consecutive weekly evals, OR (b) a full season of new data has accumulated since the last training run, whichever comes first.

## 7. Weekly Data / Model Refresh Loop

```
New round results published
        |
        v
Append to cleaned_round_by_round_stats_v2.csv / cleaned_team_matches.csv
        |
        v
Regenerate match_prediction_features.csv / player_prediction_features.csv
  (recompute rolling averages with .shift(1) leakage guard)
        |
        v
Run weekly evaluation (30-case suite + model-vs-baseline accuracy)
        |
        v
If retraining trigger met -> retrain, re-validate on holdout, redeploy joblib files
        |
        v
Log results in evaluation/ for trend tracking
```
