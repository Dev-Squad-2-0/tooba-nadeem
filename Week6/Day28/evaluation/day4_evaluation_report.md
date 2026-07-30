# Day 4 Evaluation Report

## LangGraph Integration: Routing Between Chat, Retrieval & Prediction

## 1. Overview

The Day 4 system integrates the AFL chat, retrieval, and prediction functionality using LangGraph.

The system uses an explicit intent router to classify user requests into four categories:

* `factual`
* `retrieval`
* `prediction`
* `off_topic`

The selected intent determines which branch of the graph is executed.

The main graph structure is:

```text
START
  |
  v
Router
  |
  +---- factual ------> Factual Node -----+
  |                                       |
  +---- retrieval ----> Retrieval Node ---+
  |                                       |
  +---- prediction ---> Prediction Node --+--> Validation
  |                                       |
  +---- off_topic ---> Off-topic Node ----+
                                          |
                                          v
                                  Validation Routing
                                   /       |       \
                                  /        |        \
                                 v         v         v
                            Response  Clarification Unsupported
                                 \        |        /
                                  \       |       /
                                   v      v      v
                                      END
```

This design makes the behavior of the application explicit and separates different types of AFL requests.

---

## 2. State Design

The shared `AgentState` is defined in `src/state.py`.

It contains the main information required by the graph:

### User and conversation information

```text
user_query
conversation_history
```

These fields contain the current request and previous conversation context.

### Routing information

```text
intent
```

The intent is restricted to:

```text
factual
retrieval
prediction
off_topic
```

### Prediction information

```text
prediction_type
prediction_input
resolved_entities
```

These fields provide a place for prediction-specific inputs and resolved entities.

### Retrieval information

```text
retrieval_input
```

This stores information required by the retrieval branch.

### Tool execution

```text
tool_result
error
```

These fields store the result of a tool operation and any error produced during execution.

### Validation

```text
validation_result
validation_error
```

These fields allow the graph to decide whether to continue normally, request clarification, or report an unsupported request.

### Final response

```text
final_response
```

This contains the final user-facing answer.

---

## 3. Router

The router node is implemented in `src/nodes.py`.

It calls the intent classifier and stores the resulting intent in the shared state.

The graph then uses `route_by_intent()` in `src/graph.py` to determine which branch should execute.

The four supported routes are:

| Intent       | Graph Branch    |
| ------------ | --------------- |
| `factual`    | Factual node    |
| `retrieval`  | Retrieval node  |
| `prediction` | Prediction node |
| `off_topic`  | Off-topic node  |

This explicit routing prevents every request from being handled by one unrestricted agent.

---

## 4. Retrieval Path

Retrieval requests are sent to the retrieval node.

The retrieval node supports several retrieval types:

* Player season statistics
* Player match statistics
* Team-vs-team records

The node checks that required information is available before calling the retrieval functions.

For example, player match statistics require:

```text
player_name
season
round_number
```

If required information is missing, the node returns a clarification error rather than guessing.

The retrieval path is:

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
  +---- success ----------> Response
  |
  +---- missing/error ----> Clarification
```

---

## 5. Prediction Path

Prediction requests are sent to the prediction node.

The prediction node supports:

* Match-winner predictions
* Top-player predictions

The prediction tools are called through the LangGraph prediction branch.

The prediction path is:

```text
Router
  |
  v
Prediction Node
  |
  v
Prediction Tool
  |
  v
Validation
  |
  v
Response Formatting
```

Prediction responses are explicitly framed as model predictions rather than guaranteed outcomes.

For match predictions, the response includes the predicted winner and the win probabilities for both teams.

For example, the response formatter uses language such as:

```text
This is a model-based prediction, not a certainty.
```

For top-player predictions, the response similarly states that the results are model predictions and not guaranteed outcomes.

---

## 6. Validation and Fallback Handling

The validation node checks the result produced by the previous graph node.

It distinguishes between:

```text
success
clarification_needed
unsupported
```

### Successful result

A valid result proceeds to the response node.

### Missing or ambiguous information

The graph routes to the clarification node.

The clarification response asks the user to provide the missing AFL information instead of guessing.

### Unsupported request

The graph routes to the unsupported node.

This is used for requests that are understood but outside the currently supported prediction/retrieval capabilities.

This provides a controlled fallback rather than generating an unsupported prediction.

---

## 7. End-to-End Test Cases

The evaluation suite contains 10 representative test cases.

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

The tests cover factual questions, retrieval requests, retrieval failures, match prediction, top-player prediction, unsupported prediction requests, missing information, off-topic requests, and follow-up conversation.

---

## 8. Routing Evaluation Result

The end-to-end evaluation was executed using:

```text
python -m evaluation.test_end_to_end
```

The test suite successfully executed all 10 test cases.

However, during the evaluation, the external LLM router reached its configured free-model daily rate limit.

The returned error was:

```text
RateLimitError: 429
Rate limit exceeded: free-models-per-day
```

The endpoint reported:

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

The only passing case was the off-topic request:

```text
Expected: off_topic
Actual:   off_topic
```

### Important Evaluation Limitation

The observed `1/10` result should **not** be interpreted as the actual routing accuracy of the LangGraph router.

The failures occurred while the external LLM router was unavailable because the daily free-model request limit had been exhausted.

Therefore, the evaluation demonstrates that the test suite and fallback behavior execute correctly, but it does not provide a valid measurement of the router's classification accuracy under normal LLM availability.

The test suite can be rerun after the model endpoint becomes available again.

---

## 9. Representative State Traces

### Trace A: Factual Question

```text
User:
Who is Nick Daicos?

        |
        v

Router
intent = factual

        |
        v

Factual Node

        |
        v

Validation
validation_result = success

        |
        v

Response Node

        |
        v

Final Response
```

The factual request follows the direct-answer branch and does not require a prediction tool.

---

### Trace B: Retrieval Request

```text
User:
What were Nick Daicos' stats last round?

        |
        v

Router
intent = retrieval

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
        +---- success ----> Response
        |
        +---- failure ----> Clarification
```

The retrieval branch separates statistics retrieval from general factual answering. This reduces the risk of producing unsupported statistics when the required information is unavailable.

---

### Trace C: Prediction Request

```text
User:
Will Collingwood beat Geelong this week?

        |
        v

Router
intent = prediction

        |
        v

Prediction Node

        |
        v

Match Prediction Tool

        |
        v

Validation

        |
        v

Response Node

        |
        v

Probabilistic Prediction
```

The prediction branch ensures that prediction results are handled separately and are presented as probabilities rather than certain outcomes.

---

## 10. LangGraph vs a Monolithic LangChain Agent

A monolithic LangChain agent would allow one general-purpose agent to decide which tools to use for every request. This can make routing and response behavior less predictable because the same agent is responsible for factual answers, retrieval, prediction, and refusal behavior.

The LangGraph design makes these decisions explicit. Factual questions, retrieval requests, prediction requests, and off-topic requests follow controlled paths, while prediction requests receive dedicated validation and probabilistic response formatting.

---

## 11. Day 4 Deliverable Status

| Requirement                              | Status                                       |
| ---------------------------------------- | -------------------------------------------- |
| State schema                             | Complete                                     |
| Explicit intent router                   | Complete                                     |
| Factual route                            | Implemented                                  |
| Retrieval route                          | Implemented                                  |
| Prediction route                         | Implemented                                  |
| Off-topic route                          | Implemented                                  |
| Validation node                          | Implemented                                  |
| Clarification fallback                   | Implemented                                  |
| Unsupported-request fallback             | Implemented                                  |
| Prediction probability formatting        | Implemented                                  |
| Prediction uncertainty disclaimer        | Implemented                                  |
| End-to-end test suite                    | Implemented                                  |
| Representative test cases                | 10 cases                                     |
| Routing evaluation                       | Executed with external rate-limit limitation |
| State-trace documentation                | Documented                                   |
| LangGraph vs monolithic-agent comparison | Documented                                   |

---

## 12. Conclusion

The Day 4 implementation connects the AFL assistant's factual, retrieval, and prediction capabilities through an explicit LangGraph workflow.

The system separates intent routing, tool execution, validation, fallback handling, and response formatting. This provides more predictable control over prediction requests and makes it possible to prevent unsupported or ambiguous requests from being answered by guessing.

The end-to-end evaluation was successfully executed, although the external LLM router's daily free-model rate limit prevented a meaningful measurement of routing accuracy during this run.
