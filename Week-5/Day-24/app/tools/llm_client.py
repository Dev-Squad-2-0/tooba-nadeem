"""
Thin wrapper around the company's OpenAI-compatible endpoint.

Design goals (why this file exists rather than calling the SDK directly
from every node):
  1. One place to swap models -- nodes never hardcode a model name.
  2. Automatic fallback across the model chain on error/timeout.
  3. A "mock" mode so the graph can be developed, unit-tested, and
     evaluated without live network access or spending real quota.
  4. Refusal detection -- if a model comes back with a generic refusal
     instead of doing the task, we treat that like an error and fall
     back, rather than silently passing garbage downstream.
"""
import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODE,
    LLM_TIMEOUT_SECONDS,
    MODEL_FALLBACK_CHAIN,
)

logger = logging.getLogger("triage_agent.llm_client")

_REFUSAL_MARKERS = (
    "i can't help with that",
    "i cannot help with that",
    "i'm not able to assist",
    "as an ai language model",
    "i cannot fulfill this request",
)


class LLMError(Exception):
    """Raised only when every model in the fallback chain has failed."""


@dataclass
class LLMResult:
    text: str
    model_used: str
    attempts: int
    latency_seconds: float
    degraded: bool  # True if we fell back from the primary model


def _looks_like_refusal(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _REFUSAL_MARKERS)


def _call_model_live(model: str, system_prompt: str, user_prompt: str) -> str:
    """Single call to the company endpoint for one model. Raises on any error."""
    from openai import OpenAI  # imported lazily so mock mode has no hard dependency

    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, timeout=LLM_TIMEOUT_SECONDS)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def _call_model_mock(model: str, system_prompt: str, user_prompt: str) -> str:
    """
    Deterministic offline stand-in used when LLM_MODE=mock. This is NOT meant
    to be smart -- it exists so the graph, API, and evaluation harness can
    run end-to-end in environments without egress to the company endpoint.
    Nodes fall back to the rule-based tools (see tools/classifier_rules.py)
    for real decision logic; this stub is only used where a node needs *a*
    string back rather than raising.
    """
    return f"[mock:{model}] acknowledged: {user_prompt[:60]}"


def chat_completion(system_prompt: str, user_prompt: str) -> LLMResult:
    """
    Try each model in MODEL_FALLBACK_CHAIN in order. Returns as soon as one
    succeeds and doesn't look like a refusal. Raises LLMError only if the
    entire chain is exhausted -- callers should catch this and degrade to
    the rule-based path (see failure-handling in each node).
    """
    start = time.monotonic()
    last_error: Optional[Exception] = None

    for attempt, model in enumerate(MODEL_FALLBACK_CHAIN, start=1):
        try:
            if LLM_MODE == "mock":
                text = _call_model_mock(model, system_prompt, user_prompt)
            else:
                text = _call_model_live(model, system_prompt, user_prompt)

            if not text.strip():
                raise LLMError(f"Model '{model}' returned empty content")
            if _looks_like_refusal(text):
                raise LLMError(f"Model '{model}' returned a refusal-like response")

            return LLMResult(
                text=text,
                model_used=model,
                attempts=attempt,
                latency_seconds=round(time.monotonic() - start, 3),
                degraded=attempt > 1,
            )
        except Exception as exc:  # noqa: BLE001 -- deliberately broad: any
            # failure mode (timeout, rate limit, 5xx, refusal) should trigger
            # fallback rather than crash the pipeline.
            logger.warning("Model '%s' failed (attempt %d): %s", model, attempt, exc)
            last_error = exc
            continue

    raise LLMError(
        f"All models in fallback chain exhausted: {MODEL_FALLBACK_CHAIN}. Last error: {last_error}"
    )
