from .router import classify_intent
from .prediction_tools import (
    predict_match,
    predict_top_players,
)

from .retrieval import (
    get_player_season_stats,
    get_player_match_stats,
    get_team_vs_team_record,
)

from .state import AgentState


# -------------------------------------------------------------------
# Router node
# -------------------------------------------------------------------

def router_node(state: AgentState) -> AgentState:
    """
    Classify the user's query and store the detected intent.
    """

    query = state["user_query"]

    intent = classify_intent(query)

    return {
        **state,
        "intent": intent,
    }


# -------------------------------------------------------------------
# Factual node
# -------------------------------------------------------------------

def factual_node(state: AgentState) -> AgentState:
    """
    Handle general AFL questions.

    This is currently a placeholder for the Day 3 chat component.
    """

    return {
        **state,
        "tool_result": {
            "type": "factual",
            "message": (
                "Factual AFL answering will be connected to the "
                "Day 3 chat component here."
            ),
        },
        "error": None,
    }


# -------------------------------------------------------------------
# Retrieval node
# -------------------------------------------------------------------

def retrieval_node(state: AgentState) -> AgentState:
    """
    Handle AFL statistics and historical-data requests.

    The retrieval type and required parameters are expected to be
    present in the state. If required information is missing, the
    node returns a clarification error rather than guessing.
    """

    retrieval_input = state.get("retrieval_input")

    # ---------------------------------------------------------------
    # Missing retrieval information
    # ---------------------------------------------------------------

    if not retrieval_input:
        return {
            **state,
            "tool_result": None,
            "error": (
                "Retrieval details could not be extracted from "
                "the user's request."
            ),
            "error_type": "clarification",
        }

    retrieval_type = retrieval_input.get("retrieval_type")

    try:

        # -----------------------------------------------------------
        # Player season statistics
        # -----------------------------------------------------------

        if retrieval_type == "player_season":

            required_fields = [
                "player_name",
                "season",
            ]

            if any(
                retrieval_input.get(field) is None
                for field in required_fields
            ):
                return {
                    **state,
                    "tool_result": None,
                    "error": (
                        "Player name and season are required "
                        "for season statistics."
                    ),
                    "error_type": "clarification",
                }

            result = get_player_season_stats(
                player_name=retrieval_input["player_name"],
                season=int(retrieval_input["season"]),
                is_finals=retrieval_input.get("is_finals", False),
            )

            return {
                **state,
                "tool_result": result,
                "error": None,
                "error_type": None,
            }

        # -----------------------------------------------------------
        # Player match statistics
        # -----------------------------------------------------------

        if retrieval_type == "player_match":

            required_fields = [
                "player_name",
                "season",
                "round_number",
            ]

            if any(
                retrieval_input.get(field) is None
                for field in required_fields
            ):
                return {
                    **state,
                    "tool_result": None,
                    "error": (
                        "Player name, season, and round number "
                        "are required for match statistics."
                    ),
                    "error_type": "clarification",
                }

            result = get_player_match_stats(
                player_name=retrieval_input["player_name"],
                season=int(retrieval_input["season"]),
                round_number=str(
                    retrieval_input["round_number"]
                ),
            )

            return {
                **state,
                "tool_result": result,
                "error": None,
                "error_type": None,
            }

        # -----------------------------------------------------------
        # Team vs team record
        # -----------------------------------------------------------

        if retrieval_type == "team_vs_team":

            required_fields = [
                "team_name",
                "opponent_name",
            ]

            if any(
                retrieval_input.get(field) is None
                for field in required_fields
            ):
                return {
                    **state,
                    "tool_result": None,
                    "error": (
                        "Both team names are required for a "
                        "team-vs-team record."
                    ),
                    "error_type": "clarification",
                }

            result = get_team_vs_team_record(
                team_name=retrieval_input["team_name"],
                opponent_name=retrieval_input["opponent_name"],
            )

            return {
                **state,
                "tool_result": result,
                "error": None,
                "error_type": None,
            }

        # -----------------------------------------------------------
        # Unsupported retrieval type
        # -----------------------------------------------------------

        return {
            **state,
            "tool_result": None,
            "error": (
                "This retrieval type is not currently supported."
            ),
            "error_type": "unsupported",
        }

    except Exception as exc:

        return {
            **state,
            "tool_result": None,
            "error": str(exc),
            "error_type": "clarification",
        }


# -------------------------------------------------------------------
# Prediction node
# -------------------------------------------------------------------

def prediction_node(state: AgentState) -> AgentState:
    """
    Handle prediction requests.

    The prediction tools are responsible for:
    - resolving team aliases
    - validating team names
    - calling the ML models
    - returning probabilities/predictions
    """

    prediction_input = state.get("prediction_input")

    # ---------------------------------------------------------------
    # Missing prediction information
    # ---------------------------------------------------------------

    if not prediction_input:
        return {
            **state,
            "tool_result": None,
            "error": (
                "Prediction details could not be extracted from "
                "the user's request."
            ),
            "error_type": "clarification",
        }

    prediction_type = prediction_input.get("prediction_type")

    try:

        # -----------------------------------------------------------
        # Match winner prediction
        # -----------------------------------------------------------

        if prediction_type == "match":

            result = predict_match.invoke({
                "match_date": prediction_input["match_date"],
                "home_team": prediction_input["home_team"],
                "away_team": prediction_input["away_team"],
            })

            return {
                **state,
                "tool_result": result,
                "error": None,
            }

        # -----------------------------------------------------------
        # Top-player prediction
        # -----------------------------------------------------------

        if prediction_type == "top_player":

            result = predict_top_players.invoke({
                "match_date": prediction_input["match_date"],
                "team_a": prediction_input["team_a"],
                "team_b": prediction_input["team_b"],
                "top_k": prediction_input.get("top_k", 5),
            })

            return {
                **state,
                "tool_result": result,
                "error": None,
            }

        # -----------------------------------------------------------
        # Unsupported prediction type
        # -----------------------------------------------------------

        return {
            **state,
            "tool_result": None,
            "error": (
                "This prediction type is not currently supported."
            ),
            "error_type": "unsupported",
        }

    except KeyError as exc:

        return {
            **state,
            "tool_result": None,
            "error": (
                f"Missing prediction information: {exc}"
            ),
            "error_type": "clarification",
        }

    except Exception as exc:

        return {
            **state,
            "tool_result": None,
            "error": str(exc),
        }


# -------------------------------------------------------------------
# Off-topic node
# -------------------------------------------------------------------

def off_topic_node(state: AgentState) -> AgentState:
    """
    Handle requests outside the scope of the AFL assistant.
    """

    return {
        **state,
        "tool_result": {
            "type": "off_topic",
        },
        "error": None,
    }


# -------------------------------------------------------------------
# Validation node
# -------------------------------------------------------------------

def validation_node(state: AgentState) -> AgentState:
    """
    Validate the result produced by the previous node.

    The validation layer distinguishes between:
    - successful tool execution
    - missing or ambiguous information
    - unsupported requests

    The system must never guess when required information is missing.
    """

    tool_result = state.get("tool_result")
    error = state.get("error")

    # ---------------------------------------------------------------
    # Explicit unsupported request
    # ---------------------------------------------------------------

    if state.get("error_type") == "unsupported":
        return {
            **state,
            "validation_result": "unsupported",
            "validation_error": error,
        }

    # ---------------------------------------------------------------
    # Tool execution failed
    # ---------------------------------------------------------------

    if error:
        return {
            **state,
            "validation_result": "clarification_needed",
            "validation_error": error,
        }

    # ---------------------------------------------------------------
    # Tool returned nothing
    # ---------------------------------------------------------------

    if tool_result is None:
        return {
            **state,
            "validation_result": "clarification_needed",
            "validation_error": (
                "The requested tool did not return a result."
            ),
        }

    # ---------------------------------------------------------------
    # Retrieval/prediction tool explicitly says data was not found
    # ---------------------------------------------------------------

    if isinstance(tool_result, dict):

        if tool_result.get("found") is False:
            return {
                **state,
                "validation_result": "clarification_needed",
                "validation_error": tool_result.get(
                    "message",
                    "The requested information was not found.",
                ),
            }

    # ---------------------------------------------------------------
    # Successful result
    # ---------------------------------------------------------------

    return {
        **state,
        "validation_result": "success",
        "validation_error": None,
    }

# -------------------------------------------------------------------
# Clarification node
# -------------------------------------------------------------------

def clarification_node(state: AgentState) -> AgentState:
    """
    Ask the user for missing or ambiguous information.

    The system must not guess when required AFL entities,
    players, teams, or dates cannot be resolved.
    """

    return {
        **state,
        "final_response": (
            "I need a little more information before I can answer "
            "that accurately. Please provide the specific AFL "
            "teams, player, match date, or other missing detail."
        ),
    }

# -------------------------------------------------------------------
# Unsupported request node
# -------------------------------------------------------------------

def unsupported_node(state: AgentState) -> AgentState:
    """
    Handle requests that are understood but outside the supported
    capabilities of the prediction/retrieval system.
    """

    return {
        **state,
        "final_response": (
            "I understand the AFL request, but that type of prediction "
            "is not currently supported by this system. I can currently "
            "handle match-winner predictions and top-player predictions."
        ),
    }


# -------------------------------------------------------------------
# Response formatting node
# -------------------------------------------------------------------

def response_node(state: AgentState) -> AgentState:
    """
    Convert the result produced by the graph into the final
    user-facing response.

    Prediction responses are deliberately formatted with
    probabilities so they are presented as predictions rather
    than certain outcomes.
    """

    intent = state.get("intent")
    result = state.get("tool_result")
    validation = state.get("validation_result")

    # ---------------------------------------------------------------
    # Validation failure
    # ---------------------------------------------------------------

    if validation == "clarification_needed":

        return {
            **state,
            "final_response": (
                "I couldn't determine the required AFL information "
                "from your request. Please provide the specific "
                "teams, player, match, or date you are asking about."
            ),
        }

    # ---------------------------------------------------------------
    # Off-topic
    # ---------------------------------------------------------------

    if intent == "off_topic":

        return {
            **state,
            "final_response": (
                "I'm an AFL-focused assistant, so I can help with "
                "AFL teams, players, matches, statistics, history, "
                "rules, and predictions."
            ),
        }

    # ---------------------------------------------------------------
    # Prediction
    # ---------------------------------------------------------------

    if intent == "prediction":

        if not isinstance(result, dict):

            return {
                **state,
                "final_response": (
                    "I couldn't generate the requested AFL prediction."
                ),
            }

        # -----------------------------------------------------------
        # Match prediction
        # -----------------------------------------------------------

        if "predicted_winner" in result:

            winner = result["predicted_winner"]
            home_probability = result["home_win_probability"]
            away_probability = result["away_win_probability"]

            home_team = result["home_team"]
            away_team = result["away_team"]

            return {
                **state,
                "final_response": (
                    f"Prediction: {winner} are the more likely winner.\n\n"
                    f"{home_team}: "
                    f"{home_probability * 100:.2f}% win probability\n"
                    f"{away_team}: "
                    f"{away_probability * 100:.2f}% win probability\n\n"
                    "This is a model-based prediction, not a certainty."
                ),
            }

        # -----------------------------------------------------------
        # Top-player prediction
        # -----------------------------------------------------------

        if "predictions" in result:

            lines = [
                "Predicted top fantasy performers:",
                "",
            ]

            for player in result["predictions"]:

                lines.append(
                    f"{player['rank']}. "
                    f"{player['player']} "
                    f"({player['team']}) - "
                    f"{player['predicted_fantasy_points']:.2f} "
                    "predicted fantasy points"
                )

            lines.append("")
            lines.append(
                "These are model predictions, not guaranteed outcomes."
            )

            return {
                **state,
                "final_response": "\n".join(lines),
            }

    # ---------------------------------------------------------------
    # Factual
    # ---------------------------------------------------------------

    if intent == "factual":

        if isinstance(result, dict) and "message" in result:

            return {
                **state,
                "final_response": result["message"],
            }

    # ---------------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------------

    if intent == "retrieval":

        if isinstance(result, dict) and "message" in result:

            return {
                **state,
                "final_response": result["message"],
            }

    # ---------------------------------------------------------------
    # Generic fallback
    # ---------------------------------------------------------------

    return {
        **state,
        "final_response": (
            "I wasn't able to produce a response for that request."
        ),
    }