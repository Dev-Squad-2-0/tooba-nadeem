# Task 1: Graph Design for the Full System

## State Schema

The LangGraph system uses a shared `AgentState` object containing:

- `user_query`: the current user request.
- `conversation_history`: previous conversation messages used for context.
- `intent`: the detected request type:
  - `factual`
  - `retrieval`
  - `prediction`
  - `off_topic`
- `prediction_type`: identifies the type of prediction being requested.
- `resolved_entities`: stores resolved teams, players, dates, or other entities.
- `tool_result`: result returned by the selected tool or node.
- `validation_status`: whether the tool result passed validation.
- `validation_error`: error information when validation fails.
- `final_response`: the formatted response shown to the user.

## Graph Structure

The graph follows this flow:

START
  ↓
Router
  ↓
 ┌───────────────┬────────────────┬────────────────┐
 ↓               ↓                ↓                ↓
Factual       Retrieval       Prediction       Off-topic
 └───────────────┴────────────────┴────────────────┘
                         ↓
                    Validation
                         ↓
                    Response
                         ↓
                        END

The router determines the user's intent and sends the request to the appropriate branch.

The factual branch handles general AFL questions.

The retrieval branch is intended for questions requiring specific AFL statistics or historical data.

The prediction branch calls the prediction tools from Day 2.

The off-topic branch refuses requests outside the AFL assistant's scope.

All branches converge on the validation node before reaching the final response node.

## Why Explicit Routing Is Safer

Explicit routing with LangGraph provides more control than allowing one generic agent to decide everything freely.

Each type of request follows a known path and can have its own rules and validation.

This is especially important for predictions. A prediction should never be presented as a guaranteed fact. By forcing prediction requests through the prediction branch, the system can consistently include model probabilities and clearly state that the result is probabilistic.

Explicit routing also makes the system easier to debug because we can inspect which intent was detected, which branch was executed, what tool result was produced, and whether validation succeeded.

A generic agent has more freedom to choose tools and response styles, which makes incorrect tool selection and inconsistent prediction framing more likely.