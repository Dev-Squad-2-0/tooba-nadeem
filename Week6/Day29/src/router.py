import warnings

warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings",
)

from typing import Literal

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from .config import (
    LLM_BASE_URL,
    LLM_API_KEY,
    PRIMARY_MODEL,
)
from .prompts import ROUTER_SYSTEM_PROMPT


# -------------------------------------------------------------------
# Structured router output
# -------------------------------------------------------------------

class RouterDecision(BaseModel):
    """Structured output returned by the intent classifier."""

    intent: Literal[
        "factual",
        "retrieval",
        "prediction",
        "off_topic",
    ] = Field(
        description="The detected intent of the user's AFL request."
    )


# -------------------------------------------------------------------
# LLM
# -------------------------------------------------------------------

def build_router():
    """Create the LLM used for intent classification."""

    llm = ChatOpenAI(
        model=PRIMARY_MODEL,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=0,
    )

    return llm.with_structured_output(RouterDecision)


# -------------------------------------------------------------------
# Router function
# -------------------------------------------------------------------

def classify_intent(query: str) -> str:
    """
    Classify a user query into one of the supported intents.

    The router first attempts structured classification. If the
    provider returns malformed structured output, it retries once
    with an explicit formatting instruction.

    Returns:
        factual
        retrieval
        prediction
        off_topic
    """

    router = build_router()

    messages = [
        {
            "role": "system",
            "content": ROUTER_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": query,
        },
    ]

    # ---------------------------------------------------------------
    # First attempt
    # ---------------------------------------------------------------

    try:
        response = router.invoke(messages)

        if isinstance(response, RouterDecision):
            return response.intent

    except Exception as exc:
        print("ROUTER ERROR:", type(exc).__name__, str(exc))

    # ---------------------------------------------------------------
    # Retry with stricter instruction
    # ---------------------------------------------------------------

    retry_messages = [
        {
            "role": "system",
            "content": ROUTER_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                f"{query}\n\n"
                "Classify this request now. "
                "The required field is exactly 'intent'. "
                "The value must be exactly one of: "
                "factual, retrieval, prediction, off_topic."
            ),
        },
    ]

    try:
        response = router.invoke(retry_messages)

        if isinstance(response, RouterDecision):
            return response.intent

    except Exception:
        pass

    # ---------------------------------------------------------------
    # Safe fallback
    # ---------------------------------------------------------------

    return "off_topic"