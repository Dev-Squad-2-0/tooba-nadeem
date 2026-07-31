import operator
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import TypedDict, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from .config import (
    LLM_BASE_URL,
    LLM_API_KEY,
    PRIMARY_MODEL,
    FALLBACK_MODELS,
)
from .prompts import SYSTEM_PROMPT, PREDICTION_DISCLAIMER
from .tools import AFL_TOOLS
from .logging_utils import log_event
from .guardrails import (
    check_input_size,
    check_rate_limit,
    RateLimitError,
    InputTooLargeError,
)

# Prediction tools whose output must always carry the uncertainty disclaimer
PREDICTION_TOOL_NAMES = {"predict_match", "predict_top_players"}

# Max time allowed for a single tool call before it's treated as failed.
# Local pandas/sklearn calls are normally sub-second; this is a safety net.
TOOL_TIMEOUT_SECONDS = 10

_tool_executor = ThreadPoolExecutor(max_workers=4)


def create_llm(model_name: str):
    return ChatOpenAI(
        model=model_name,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0,
        timeout=30,
        max_retries=0,
    )


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    model_name: str
    tool_call_log: Annotated[list, operator.add]

# Primary model first, then fallbacks
MODEL_NAMES = list(dict.fromkeys([PRIMARY_MODEL] + FALLBACK_MODELS))


# Create one tool-enabled LLM for each model
LLMS_WITH_TOOLS = {
    model_name: create_llm(model_name).bind_tools(AFL_TOOLS)
    for model_name in MODEL_NAMES
}


def _invoke_with_fallback(prompt_messages, preferred_model: str = ""):
    """Try the preferred model first (if any), then fall back through
    the remaining models in MODEL_NAMES. This is used for BOTH the
    first call in a conversation and any later "reuse" calls, so a
    previously-successful model failing later doesn't crash the agent.
    """

    if preferred_model and preferred_model in LLMS_WITH_TOOLS:
        try_order = [preferred_model] + [
            m for m in MODEL_NAMES if m != preferred_model
        ]
    else:
        try_order = MODEL_NAMES

    last_error = None

    for model_name in try_order:
        label = "Reusing" if model_name == preferred_model else "Trying"
        print(f"[LLM] {label} model: {model_name}")

        try:
            model = LLMS_WITH_TOOLS[model_name]
            response = model.invoke(prompt_messages)

            print(f"[LLM] Success: {model_name}")

            return response, model_name

        except Exception as error:
            print(f"[LLM] Failed: {model_name} ({type(error).__name__})")
            last_error = error

    raise last_error


def call_model(state: AgentState):
    """Call the LLM, falling back through MODEL_NAMES whenever a call fails
    - whether this is the first call in the conversation or a later one."""

    messages = state["messages"]

    prompt_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *messages,
    ]

    preferred_model = state.get("model_name", "")

    response, model_name = _invoke_with_fallback(
        prompt_messages, preferred_model=preferred_model
    )

    return {
        "messages": [response],
        "model_name": model_name,
    }


def _invoke_tool_with_timeout(selected_tool, tool_args: dict):
    """Run a single tool call with a hard timeout so one slow/hung tool
    can't stall the whole conversation."""

    future = _tool_executor.submit(selected_tool.invoke, tool_args)
    return future.result(timeout=TOOL_TIMEOUT_SECONDS)


def execute_tools(state: AgentState):
    """Execute any tools requested by the model.

    Every tool call is isolated: a bad input (e.g. an unknown team name,
    which predict.py deliberately raises ValueError for), a slow call, or
    any other exception is caught and turned into a normal ToolMessage
    describing the problem, rather than crashing the whole agent run.
    The model then gets a chance to explain the issue to the user
    (e.g. "I don't recognize that team name") instead of a 500 error.
    """

    messages = state["messages"]
    last_message = messages[-1]

    tool_messages = []
    tool_call_log = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        start = time.perf_counter()
        status = "ok"
        error_text = None

        try:
            selected_tool = next(
                (tool for tool in AFL_TOOLS if tool.name == tool_name),
                None,
            )

            if selected_tool is None:
                raise ValueError(f"Unknown tool requested: '{tool_name}'")

            result = _invoke_tool_with_timeout(selected_tool, tool_args)
            content = str(result)

        except FutureTimeoutError:
            status = "timeout"
            error_text = (
                f"Tool '{tool_name}' timed out after "
                f"{TOOL_TIMEOUT_SECONDS}s."
            )
            content = (
                "This request took too long to process. Please try again, "
                "or provide more specific details (exact team names and date)."
            )

        except Exception as exc:
            status = "error"
            error_text = f"{type(exc).__name__}: {exc}"
            # Surface the tool's own message (e.g. "Unknown team: 'X'.")
            # so the model can relay something useful to the user instead
            # of guessing or apologizing vaguely.
            content = f"Tool error: {exc}"

        latency_ms = (time.perf_counter() - start) * 1000

        tool_call_log.append({
            "name": tool_name,
            "args": tool_args,
            "status": status,
            "latency_ms": round(latency_ms, 2),
            "error": error_text,
        })

        tool_messages.append(
            ToolMessage(
                content=content,
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": tool_messages, "tool_call_log": tool_call_log}


def should_continue(state: AgentState):
    """Decide whether the model needs a tool or can answer directly."""

    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return END


graph = StateGraph(AgentState)

graph.add_node("model", call_model)
graph.add_node("tools", execute_tools)

graph.add_edge(START, "model")

graph.add_conditional_edges(
    "model",
    should_continue,
    {
        "tools": "tools",
        END: END,
    },
)

graph.add_edge("tools", "model")

memory = MemorySaver()

agent = graph.compile(
    checkpointer=memory
)

def _looks_like_prediction_response(tool_call_log: list) -> bool:
    return any(
        call.get("name") in PREDICTION_TOOL_NAMES
        and call.get("status") == "ok"
        for call in tool_call_log
    )


def _ensure_disclaimer(text: str) -> str:
    """Append the standard disclaimer if a prediction was made and the
    model's own response doesn't already read like it included one."""

    lowered = text.lower()
    already_has_disclaimer = (
        "not a certainty" in lowered
        or "not guaranteed" in lowered
        or "model-based prediction" in lowered
        or "model prediction" in lowered
    )

    if already_has_disclaimer:
        return text

    return text + PREDICTION_DISCLAIMER


def ask_agent(message: str, thread_id: str = "afl-demo") -> dict:
    """Send one message while preserving conversation history for the
    given thread_id.

    Returns a dict (not just a string) so callers such as the FastAPI
    wrapper can surface prediction metadata, latency, and error status
    without re-deriving it:

    {
        "response": str,
        "model_used": str | None,
        "tools_called": [ {name, status, latency_ms, error}, ... ],
        "used_prediction_tool": bool,
        "latency_ms": float,
        "status": "ok" | "rate_limited" | "invalid_input" | "agent_error",
        "error": str | None,
    }
    """

    turn_start = time.perf_counter()

    def _elapsed_ms() -> float:
        return (time.perf_counter() - turn_start) * 1000

    # -----------------------------------------------------------------
    # Input validation / abuse guardrails
    # -----------------------------------------------------------------
    try:
        check_input_size(message)
        check_rate_limit(thread_id)
    except (InputTooLargeError, RateLimitError) as exc:
        status = (
            "invalid_input"
            if isinstance(exc, InputTooLargeError)
            else "rate_limited"
        )
        log_event(
            conversation_id=thread_id,
            query=message,
            status=status,
            error=str(exc),
            total_latency_ms=_elapsed_ms(),
        )
        return {
            "response": str(exc),
            "model_used": None,
            "tools_called": [],
            "used_prediction_tool": False,
            "latency_ms": round(_elapsed_ms(), 2),
            "status": status,
            "error": str(exc),
        }

    # -----------------------------------------------------------------
    # Run the agent
    # -----------------------------------------------------------------
    try:
        result = agent.invoke(
            {
                "messages": [HumanMessage(content=message)],
                "tool_call_log": [],
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            },
        )

        response_text = result["messages"][-1].content
        tool_call_log = result.get("tool_call_log", [])
        model_used = result.get("model_name")
        used_prediction_tool = _looks_like_prediction_response(tool_call_log)

        if used_prediction_tool:
            response_text = _ensure_disclaimer(response_text)

        any_tool_errors = any(
            call.get("status") != "ok" for call in tool_call_log
        )
        status = "ok" if not any_tool_errors else "tool_error"

    except Exception as exc:
        status = "agent_error"
        response_text = (
            "Sorry, something went wrong while processing that request. "
            "Please try again."
        )
        error_text = f"{type(exc).__name__}: {exc}"

        log_event(
            conversation_id=thread_id,
            query=message,
            status=status,
            error=error_text,
            total_latency_ms=_elapsed_ms(),
        )

        return {
            "response": response_text,
            "model_used": None,
            "tools_called": [],
            "used_prediction_tool": False,
            "latency_ms": round(_elapsed_ms(), 2),
            "status": status,
            "error": error_text,
        }

    log_event(
        conversation_id=thread_id,
        query=message,
        status=status,
        tools_called=tool_call_log,
        total_latency_ms=_elapsed_ms(),
        model_used=model_used,
    )

    return {
        "response": response_text,
        "model_used": model_used,
        "tools_called": tool_call_log,
        "used_prediction_tool": used_prediction_tool,
        "latency_ms": round(_elapsed_ms(), 2),
        "status": status,
        "error": None,
    }