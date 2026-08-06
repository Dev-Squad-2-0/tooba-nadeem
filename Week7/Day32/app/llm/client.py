import json
import logging
import re

from openai import OpenAI

from app import config

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

# NEW — OpenRouter-specific request options, built once from config.
# - "models": ordered fallback list; if the primary (free) slug 404s from
#   shared rate-limit exhaustion, OpenRouter retries the next one server-side.
# - "reasoning.exclude": tells the provider not to inline/return reasoning
#   tokens, in case OPENAI_MODEL ever points at a reasoning-capable model.
#   No-op on the current non-reasoning model.
_OPENROUTER_EXTRA_BODY = {
    "models": config.OPENAI_MODEL_FALLBACKS,
    "reasoning": {"exclude": config.EXCLUDE_REASONING_TOKENS},
}

# NEW — belt-and-suspenders: strips any <think>...</think> block that
# slips through despite reasoning.exclude (e.g. a model that inlines it
# in content rather than honoring the API-level flag).
_THINK_TAG_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_reasoning(text: str) -> str:
    if not text:
        return text
    return _THINK_TAG_RE.sub("", text).strip()


def generate_answer(question: str, context: str) -> str:
    """
    Day 1 — strict single-shot grounded RAG answer.
    Used by app/rag/rag_pipeline.py.
    """

    from app.llm.prompts import RAG_SYSTEM_PROMPT

    messages = [
        {
            "role": "system",
            "content": RAG_SYSTEM_PROMPT.format(
                context=context
            ),
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=0,
        extra_body=_OPENROUTER_EXTRA_BODY,
    )

    return _strip_reasoning(response.choices[0].message.content)


def generate_chat_response(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    Day 3 — conversational completion for the voice sales agent.

    `messages` is a full OpenAI-style message list (system + turns) built
    by app/graph/agent_graph.py. Kept as a thin wrapper so latency-relevant
    settings (temperature, max_tokens) are configurable per call without
    touching the graph logic.
    """

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=(
            temperature
            if temperature is not None
            else config.CHAT_TEMPERATURE
        ),
        max_tokens=(
            max_tokens
            if max_tokens is not None
            else config.CHAT_MAX_TOKENS
        ),
        extra_body=_OPENROUTER_EXTRA_BODY,
    )

    return _strip_reasoning(response.choices[0].message.content)


def extract_json(
    system_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    """
    Calls the LLM expecting a raw JSON object back (used by the slot
    extractor) and safely parses it.

    Never raises on malformed output — a bad extraction should degrade to
    "no slot update this turn", not crash the conversation. This matters
    especially on a live voice call where a crash means dead air.
    """

    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            temperature=(
                temperature
                if temperature is not None
                else config.SLOT_EXTRACTION_TEMPERATURE
            ),
            max_tokens=(
                max_tokens
                if max_tokens is not None
                else config.SLOT_EXTRACTION_MAX_TOKENS
            ),
            extra_body=_OPENROUTER_EXTRA_BODY,
        )

        raw = _strip_reasoning(response.choices[0].message.content.strip())

        # Some models wrap JSON in ```json fences despite instructions —
        # strip defensively rather than trusting prompt compliance.
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    except (json.JSONDecodeError, IndexError, KeyError) as exc:
        logger.warning("Slot extraction JSON parse failed: %s", exc)
        return {}
    except Exception as exc:  # noqa: BLE001 — never let extraction kill the call
        logger.warning("Slot extraction call failed: %s", exc)
        return {}