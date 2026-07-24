import logging
import time

from app.state import TicketState
from app.logging_config import log_event
from app.tools import classifier_rules
from app.tools.llm_client import LLMError, chat_completion

logger = logging.getLogger("triage_agent.nodes.identify_project")

_VALID_KEYS = {p["key"] for p in classifier_rules._PROJECTS}  # noqa: SLF001

_SYSTEM_PROMPT = (
    "You are a support-ticket classifier for Web3Geeks, a blockchain studio "
    "with these products: Blockworker, Blokkplay, DarkMaze, Fight Club Network, "
    "GemLaunch, GT Verse, MBX Finance, StatBreak, Stellar Void, and an Incubator "
    "program. Reply with ONLY the single lowercase_snake_case project key that "
    "best matches the ticket, one of: "
    + ", ".join(sorted(_VALID_KEYS))
    + ". If none clearly match, reply 'general'. Reply with nothing else."
)


def identify_project(state: TicketState) -> dict:
    """
    Failure scenario handled here: TOOL/MODEL ERROR.
    Tries the LLM classifier first; on any LLMError (timeout, rate limit,
    refusal) falls back to the deterministic keyword matcher so the ticket
    still gets routed instead of stalling the pipeline.
    """
    start = time.monotonic()
    ticket_text = f"{state.get('subject', '')}\n{state.get('description', '')}"
    warnings = list(state.get("warnings", []))
    source = "llm"

    try:
        result = chat_completion(_SYSTEM_PROMPT, ticket_text)
        candidate = result.text.strip().lower()
        if candidate not in _VALID_KEYS:
            raise LLMError(f"Model returned unrecognized project key: '{candidate}'")
        project_key = candidate
        confidence = 0.9 if not result.degraded else 0.75
        if result.degraded:
            warnings.append(f"identify_project: used fallback model '{result.model_used}'")
    except LLMError as exc:
        logger.warning("identify_project falling back to rule-based classifier: %s", exc)
        warnings.append(f"identify_project: LLM path failed ({exc}); used rule-based fallback")
        project_key, confidence = classifier_rules.identify_project(ticket_text)
        source = "rule_based_fallback"

    display_name = classifier_rules.get_project_display_name(project_key)
    latency_ms = round((time.monotonic() - start) * 1000, 1)

    log_event(
        logger, "identify_project",
        ticket_id=state.get("ticket_id"), project_key=project_key,
        confidence=confidence, source=source, latency_ms=latency_ms,
    )

    return {
        "project_key": project_key,
        "project_display_name": display_name,
        "project_confidence": confidence,
        "classification_source": source,
        "warnings": warnings,
        "trace": state.get("trace", []) + [{
            "node": "identify_project", "source": source,
            "project_key": project_key, "latency_ms": latency_ms,
        }],
    }
