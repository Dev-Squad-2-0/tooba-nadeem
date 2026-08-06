"""
slot_extractor.py
------------------

Extracts a JSON diff of buyer preferences mentioned in the LATEST message
only, and merges it into the session's ConversationState.

This runs once per conversational turn, BEFORE retrieval, so that the
updated preferences (e.g. a newly stated budget) are available to shape the
RAG/SQL queries for that same turn.
"""

import logging

from app.llm.client import extract_json
from app.llm.prompts import SLOT_EXTRACTION_PROMPT
from app.graph.state import ConversationState

logger = logging.getLogger(__name__)


def extract_and_apply(state: ConversationState, message: str) -> dict:
    """
    Returns the diff that was applied (useful for logging/eval), and
    mutates `state` in place.
    """

    prompt = SLOT_EXTRACTION_PROMPT.format(
        prior_state=state.preferences_summary(),
        message=message,
    )

    updates = extract_json(prompt)

    if updates:
        logger.info("Slot update for session %s: %s", state.session_id, updates)
        state.apply_updates(updates)
    else:
        logger.info(
            "No slot updates extracted for session %s", state.session_id
        )

    return updates