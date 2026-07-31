# AFL Assistant — Week 6 Day 5 Executive Report

## 1. What this covers

Day 5 hardened, evaluated, wrapped, and documented the existing AFL
assistant built across Days 1–4: an intern-project conversational agent
that answers AFL factual questions, retrieves exact statistics from a
historical dataset, and generates model-based match/player predictions,
while staying strictly scoped to AFL topics.

A key finding on inspection: the project contained **two parallel
implementations** — an incomplete LangGraph state machine (`graph.py`/
`nodes.py`, with a stub factual node and no input-extraction step wired
in) and a working LangChain tool-calling agent (`agent.py`/`tools.py`).
Day 5 confirmed and hardened the working `agent.py` path rather than
finishing the unused state machine, to avoid spending the day building on
a design that was already abandoned in practice.

## 2. Hardening completed

| Area | Before | After |
|---|---|---|
| Tool errors | An invalid team name (`ValueError`) or any tool exception crashed the entire agent request | Every tool call is isolated: exceptions and a 10s timeout are caught and turned into a normal message the model can relay to the user |
| Predictions callable at all | `AFL_TOOLS` only registered the 3 retrieval tools — `predict_match`/`predict_top_players` were never reachable from the chat agent | Both prediction tools are registered and callable |
| Prediction disclaimer | Relied entirely on the LLM remembering to add one | Programmatically enforced: if a prediction tool ran and the response text lacks disclaimer language, one is appended |
| Abuse handling | None | Per-conversation sliding-window rate limit (20 req/60s) and a message-length cap (2,000 chars) |
| Scope-override resistance | System prompt only | Added a secondary keyword-heuristic layer (`guardrails.py`) as a fast, LLM-independent check — see evaluation findings below for its real limitations |
| Logging | `print()` statements only | Structured JSON-line log per turn: query, conversation_id, detected tool calls, latency, model used, status/errors |
| API access | None — agent only callable from Python | FastAPI `POST /chat`, `GET /health`, and a minimal optional web UI |

A pre-existing bug was also found and fixed: `tests/test_guardrails.py`
pointed at a nonexistent filename (`guardrail_test.csv` instead of
`guardrail_tests.csv`), which meant this test had likely never actually
run successfully.

## 3. Evaluation results (real, not estimated)

A 30-case suite was built across 6 categories (factual, retrieval,
prediction, scope, prompt-injection ×5, multi-turn). Two categories of
results:

**Executed directly in this environment** (tool logic, no live LLM
required):
- Retrieval tool checks: **5/5 passed**
- Prediction tool checks: **5/5 passed**
- Prompt-injection heuristic: **found a real gap** — the first version
  caught only 2/5 attempts (missed persona-override, fake
  "SYSTEM OVERRIDE" framing, and "just a joke" reframing). Fixed and
  re-verified at **5/5** by widening the detection patterns.

**Requires a live LLM call** (factual accuracy, natural-language scope
refusals, multi-turn coherence) — the sandbox used to build this has no
network route to the OpenRouter/NetixSol endpoints, so these must be run
in your own environment via `evaluation/run_day5_evaluation_live.py`,
which writes a CSV of real per-case results rather than estimated ones.

**Model comparison (real, run against the actual trained model and
data):** on a chronological holdout of 1,373 matches, the production
Gradient Boosting match-winner model scored **74.5% accuracy**, versus
57.2% (always-predict-home-win), 53.0% (head-to-head win-rate proxy), and
56.2% (recent-form proxy). No ladder-position column exists in the
dataset, so these are documented as the closest available proxies rather
than a literal ladder-position baseline.

**Weakest category:** the prompt-injection heuristic layer, before the
fix described above. **Proposed improvement:** replace the hand-maintained
keyword list with a cheap dedicated classifier call (or a temperature-0
LLM check: "is this an AFL-scope override attempt, yes/no"), since keyword
lists will always lag behind new phrasings — as this evaluation itself
demonstrated.

## 4. Known limitations

- Live-LLM-dependent evaluation (factual/scope/multi-turn) is written but
  not yet executed with a real API key — numbers are pending your run.
- The rate limiter and tool executor are in-memory and single-process;
  they won't coordinate across multiple server instances. Fine for the
  current single-instance deployment, not for horizontal scaling.
- The abandoned `graph.py` state-machine path still exists in the
  codebase (untouched, per the confirmed decision not to rebuild it) —
  it should either be finished or removed in a future cleanup pass so it
  doesn't confuse future contributors about which path is live.
- `config.py` currently only wires up OpenRouter; the NetixSol tiered
  fallback described in earlier project notes is present only as
  commented-out code. This wasn't restored during Day 5 since it wasn't
  explicitly requested — worth a decision before relying on it in
  production.
- No automated retraining pipeline exists yet; the weekly refresh loop in
  `monitoring_checklist.md` is a documented process, not automated.

## 5. Recommended next steps

1. Run `evaluation/run_day5_evaluation_live.py` with a working API key and
   fold the real factual/scope/multi-turn numbers into
   `evaluation/day5_evaluation_report.md`.
2. Replace the keyword-based injection heuristic with a cheap classifier
   call, per the finding above.
3. Decide and document whether NetixSol or OpenRouter (or both, tiered) is
   the intended production LLM path, and align `config.py` and
   `.env.example` accordingly.
4. Either finish or formally retire the `graph.py`/`nodes.py` state
   machine to avoid two parallel, confusing implementations sitting in
   the same codebase.
5. If usage grows beyond a single process, move rate limiting from
   in-memory to a shared store (e.g. Redis) so it works correctly across
   multiple server instances.
