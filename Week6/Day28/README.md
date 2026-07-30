# My Project Structure

```text
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
    │   ├── predict.py          # Day 2 prediction code
    │   ├── resolver.py
    │   ├── tools.py
    │   ├── nodes.py
    │   └── agent.py
    │
    ├── tests/
    │   └── test_guardrails.py
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

# Day 4: LangGraph Integration

## Overview

Today's task focused on integrating the AFL chat, retrieval, and prediction functionality into a single LangGraph workflow.

The system uses an explicit intent router to decide whether a user request should be handled as:

* `factual`
* `retrieval`
* `prediction`
* `off_topic`

Each intent follows a controlled graph path with validation and appropriate fallback handling.

The main goal was to make the system more predictable and controlled than a single generic agent that independently decides what to do for every request.

---

# Task 1: Graph Design

The system uses LangGraph to explicitly route each user query to the correct processing path.

The shared `AgentState` stores the user's query, conversation history, detected intent, tool results, validation information, errors, and final response.

The graph follows this structure:

```text
START
  |
  v
Router
  |
  +---- factual ------> Factual Node ----+
  |                                      |
  +---- retrieval ----> Retrieval Node --+
  |                                      |
  +---- prediction ---> Prediction Node -+--> Validation
  |                                      |        |
  +---- off_topic ----> Off-topic Node --+        |
                                               +--+--+
                                               |  |  |
                                               v  v  v
                                          Response
                                          Clarification
                                          Unsupported
                                               |
                                               v
                                              END
```

The main nodes are:

| Node          | Responsibility                                                 |
| ------------- | -------------------------------------------------------------- |
| Router        | Classifies the user's intent                                   |
| Factual       | Handles general AFL questions                                  |
| Retrieval     | Retrieves AFL statistics and historical information            |
| Prediction    | Runs match and top-player prediction tools                     |
| Off-topic     | Handles requests outside the AFL assistant's scope             |
| Validation    | Checks whether the previous operation produced a usable result |
| Response      | Formats successful results for the user                        |
| Clarification | Requests missing or ambiguous information                      |
| Unsupported   | Handles capabilities that are outside the supported system     |

---

# State Schema

The shared state is defined in `src/state.py`.

It contains the following major categories.

## User and Conversation

```text
user_query
conversation_history
```

These fields contain the current user request and previous conversation context.

## Intent

```text
intent
```

The intent can be:

```text
factual
retrieval
prediction
off_topic
```

## Prediction Information

```text
prediction_type
prediction_input
resolved_entities
```

These fields provide the information needed by the prediction branch.

## Retrieval Information

```text
retrieval_input
```

This stores the information needed to perform the requested retrieval operation.

## Tool Execution

```text
tool_result
error
```

These fields store the result of the tool operation and any error encountered during execution.

## Validation

```text
validation_result
validation_error
```

These fields allow the graph to determine whether it should continue normally, ask for clarification, or report an unsupported request.

## Final Response

```text
final_response
```

This contains the final user-facing response.

---

# Why Explicit LangGraph Routing Is Safer

The system uses explicit LangGraph routing instead of allowing one general-purpose agent to freely decide which tool or action to use.

The router first classifies each request as `factual`, `retrieval`, `prediction`, or `off_topic`, and LangGraph then sends the request to the corresponding controlled branch.

This is safer because each type of request has a defined processing path. In particular, prediction requests pass through dedicated prediction and response-formatting logic, ensuring that model probabilities are presented as probabilistic predictions rather than certain outcomes.

Explicit routing also reduces the risk of calling the wrong tool, using unsupported capabilities, or allowing the system to guess when required information is unavailable.

LangGraph makes the control flow explicit, which also makes validation, fallback handling, clarification, and error handling easier to implement.

---

# Task 2: Router Node

The router node is implemented in `src/nodes.py` and uses the intent-classification logic from `src/router.py`.

The router stores the detected intent in the shared state.

The graph then uses conditional routing to select the correct branch:

```text
User Query
    |
    v
Router
    |
    +--> factual
    |
    +--> retrieval
    |
    +--> prediction
    |
    +--> off_topic
```

Examples of intended routing include:

| Example Query                                                 | Expected Intent |
| ------------------------------------------------------------- | --------------- |
| `Who is Nick Daicos?`                                         | factual         |
| `What is a behind in AFL?`                                    | factual         |
| `What were Nick Daicos' stats last round?`                    | retrieval       |
| `Will Collingwood beat Geelong this week?`                    | prediction      |
| `Who will be the top fantasy player in the Collingwood game?` | prediction      |
| `What is the weather in Islamabad?`                           | off_topic       |

The routing evaluation was also tested using a larger set of representative queries.

---

# Task 3: Retrieval Integration

The retrieval branch handles AFL statistics and historical-data requests.

The retrieval node supports:

* Player season statistics
* Player match statistics
* Team-vs-team records

The retrieval node checks whether the required information is available before calling the appropriate retrieval function.

For example, player match statistics require information such as:

```text
player_name
season
round_number
```

If required information is missing, the system does not guess. Instead, it returns a clarification path.

The retrieval flow is:

```text
Router
   |
   v
Retrieval Node
   |
   v
Retrieval Tool
   |
   v
Validation
   |
   +---- success ------------> Response
   |
   +---- missing/error -------> Clarification
```

This separation helps prevent unsupported or fabricated statistics from being presented as retrieved data.

---

# Task 3: Prediction Integration

The prediction branch integrates the prediction functionality from the earlier prediction task.

The system supports two prediction types:

1. Match-winner prediction
2. Top-player prediction

The prediction node selects the appropriate prediction tool based on the prediction type.

## Match Prediction

The match prediction path uses the match-winner model and produces:

* Predicted winner
* Home-team win probability
* Away-team win probability

The final response presents these probabilities rather than claiming that the predicted result is guaranteed.

Example response structure:

```text
Prediction: [team] are the more likely winner.

[home team]: [probability]% win probability
[away team]: [probability]% win probability

This is a model-based prediction, not a certainty.
```

## Top-Player Prediction

The top-player prediction path produces a ranked list of predicted fantasy performers.

The response includes predicted fantasy points and explicitly states that the predictions are not guaranteed outcomes.

---

# Prediction Response Framing

Prediction responses are deliberately different from factual responses.

A factual response can provide an answer directly when the information is available.

A prediction is inherently uncertain, so the response formatter presents model probabilities and uses language that makes the uncertainty clear.

For example:

```text
This is a model-based prediction, not a certainty.
```

This prevents a model output from being presented as a guaranteed future event.

---

# Task 4: Validation and Fallbacks

A validation node runs after the factual, retrieval, prediction, and off-topic branches.

The validation node checks:

* Whether an error occurred
* Whether a tool returned a result
* Whether the result indicates that requested data was not found
* Whether the request is unsupported
* Whether clarification is required

The validation outcomes are:

```text
success
clarification_needed
unsupported
```

## Successful Result

A successful result is sent to the response node.

```text
Validation
    |
    v
Response
    |
    v
END
```

## Missing or Ambiguous Information

If required information is missing, the system routes to the clarification node.

```text
Validation
    |
    v
Clarification
    |
    v
END
```

The system asks the user for the required information instead of guessing.

## Unsupported Request

If the request is understood but the requested capability is outside the supported functionality, the graph routes to the unsupported node.

For example, the current prediction system supports match-winner and top-player predictions, rather than arbitrary predictions of every possible player statistic.

The unsupported path is:

```text
Validation
    |
    v
Unsupported
    |
    v
END
```

---

# Task 4: Error Handling

The system uses controlled fallback behavior when a tool fails or required information cannot be obtained.

For retrieval and prediction requests, a missing tool result does not automatically become a generated answer.

Instead, the validation node checks the state and can route the request to clarification.

This is important because the system should not invent:

* Player statistics
* Match statistics
* Team information
* Prediction inputs
* Match details

when the required information is unavailable.

---

# Conversation History and Follow-Up Questions

The state schema includes:

```text
conversation_history
```

This allows the graph to receive previous user and assistant messages.

A follow-up such as:

```text
Tell me about Nick Daicos.
```

followed by:

```text
What were his stats last round?
```

can carry the earlier conversation context into the graph.

This provides the foundation for resolving references such as `his`, `that player`, or similar follow-up expressions.

---

# Task 5: End-to-End Testing

The end-to-end evaluation contains 10 representative test cases covering the major graph paths.

| #  | Test Case                                                         | Expected Intent |
| -- | ----------------------------------------------------------------- | --------------- |
| 1  | Who is Nick Daicos?                                               | factual         |
| 2  | What is a behind in AFL?                                          | factual         |
| 3  | What were Nick Daicos' stats last round?                          | retrieval       |
| 4  | Stats for a nonexistent AFL player                                | retrieval       |
| 5  | Will Collingwood beat Geelong this week?                          | prediction      |
| 6  | Who will be the top fantasy player in the Collingwood game?       | prediction      |
| 7  | Predict the exact number of goals each player will score.         | prediction      |
| 8  | Who will win the next match?                                      | prediction      |
| 9  | What is the weather in Islamabad?                                 | off_topic       |
| 10 | What were his stats last round? with previous Nick Daicos context | retrieval       |

These cases exercise:

* Factual answering
* Retrieval
* Retrieval failure
* Match prediction
* Top-player prediction
* Unsupported prediction requests
* Missing information
* Off-topic refusal
* Follow-up conversation

---

# Routing Evaluation

The evaluation was executed using:

```text
python -m evaluation.test_end_to_end
```

The test suite successfully executed all 10 test cases.

However, during the evaluation the external LLM router reached its daily free-model request limit.

The router returned:

```text
RateLimitError: 429
Rate limit exceeded: free-models-per-day
```

The endpoint also reported:

```text
X-RateLimit-Remaining: 0
```

Because the router could not make the required LLM request, the application's fallback behavior classified most requests as:

```text
off_topic
```

The observed result was:

```text
TOTAL TESTS: 10
PASSED:      1
FAILED:      9
```

The one passing test was:

```text
"What is the weather in Islamabad?"

Expected:
off_topic

Actual:
off_topic
```

## Important Evaluation Limitation

The observed `1/10` result should **not** be interpreted as the actual routing accuracy of the LangGraph router.

The failures occurred because the external LLM router was unavailable after its free-model daily request limit was exhausted.

Therefore, the evaluation confirms that the test suite executes and that the fallback behavior works, but it does not provide a valid measurement of the router's classification accuracy under normal LLM availability.

The test suite can be rerun when the configured LLM endpoint becomes available again.

---

# Annotated State Traces

Three representative traces are documented in the `traces/` directory.

## 1. Retrieval Trace

File:

```text
traces/retrieval_trace.txt
```

The retrieval path is:

```text
START
  |
  v
Router
  |
  v
Retrieval
  |
  v
Validation
  |
  +---- success ----------> Response
  |
  +---- clarification ---> Clarification
  |
  v
END
```

This demonstrates how a statistics request is routed to the retrieval functionality and validated before producing a response.

---

## 2. Prediction Trace

File:

```text
traces/prediction_trace.txt
```

The prediction path is:

```text
START
  |
  v
Router
  |
  v
Prediction
  |
  v
Prediction Tool
  |
  v
Validation
  |
  v
Response
  |
  v
END
```

This demonstrates how prediction requests use a dedicated prediction path and are formatted as probabilistic model outputs.

---

## 3. Clarification Trace

File:

```text
traces/clarification_trace.txt
```

The clarification path demonstrates what happens when the user does not provide enough information to safely perform a prediction or retrieval operation.

For example:

```text
Who will win the next match?
```

does not specify which match is being discussed.

The system therefore follows:

```text
START
  |
  v
Router
  |
  v
Prediction
  |
  v
Validation
  |
  v
Clarification
  |
  v
END
```

The system asks the user to provide the specific teams, player, match, date, or other missing information rather than guessing.

---

# LangGraph vs Monolithic LangChain Agent

A monolithic LangChain agent would allow one general-purpose agent to decide which tools to use for every request. This can make routing and response behavior less predictable because the same agent is responsible for factual questions, retrieval, prediction, and refusal behavior.

The LangGraph design makes these decisions explicit. Factual questions, retrieval requests, prediction requests, and off-topic requests follow controlled paths, while prediction requests receive dedicated validation and probabilistic response formatting.

This separation also makes the system easier to debug because each stage has a clear responsibility.

---

# Day 4 Deliverable Summary

The completed Day 4 design integrates the AFL assistant's major capabilities through LangGraph.

The system includes:

* Explicit intent classification
* Factual question handling
* Retrieval/statistics handling
* Match prediction
* Top-player prediction
* Off-topic refusal
* Validation after processing
* Clarification handling
* Unsupported-request handling
* Conversation-history support
* Probabilistic prediction framing
* End-to-end testing
* Annotated state traces
* Routing evaluation
* Controlled graph-based orchestration

The overall workflow separates intent detection, task-specific processing, validation, and response formatting.

This makes the system more controlled than a single generic agent and is especially useful for prediction requests where the system must consistently communicate uncertainty rather than present predictions as guaranteed outcomes.
