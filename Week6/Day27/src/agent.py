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
from .prompts import SYSTEM_PROMPT
from .tools import AFL_TOOLS


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


def execute_tools(state: AgentState):
    """Execute any tools requested by the model."""

    messages = state["messages"]
    last_message = messages[-1]

    tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        selected_tool = next(
            tool for tool in AFL_TOOLS
            if tool.name == tool_name
        )

        result = selected_tool.invoke(tool_args)

        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": tool_messages}


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

def ask_agent(message: str, thread_id: str = "afl-demo"):
    """Send one message while preserving conversation history for the given thread_id."""

    result = agent.invoke(
        {
            "messages": [
                HumanMessage(content=message)
            ],
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        },
    )

    return result["messages"][-1].content