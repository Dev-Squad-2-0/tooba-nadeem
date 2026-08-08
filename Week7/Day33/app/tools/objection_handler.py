"""
objection_handler.py
---------------------

Detects the type of sales objection in a buyer's message and provides:
  1. extra retrieval query terms, so RAG pulls in facts relevant to
     answering that specific objection (e.g. developer track record for a
     trust objection), and
  2. one targeted instruction line injected into the system prompt for
     that turn, so the model handles the objection correctly.

This module does NOT generate the response — app/llm prompts + the LLM do
that. This just makes sure the model has the right grounding and the right
instruction for the objection it's facing.
"""

import re

OBJECTION_KEYWORDS: dict[str, list[str]] = {
    "price": [
        "expensive", "too much", "too high", "mehnga", "mehngi",
        "zyada price", "price zyada", "afford", "cheap", "sasta", "sasti",
        "discount", "kam nahi",
    ],
    "trust": [
        "reliable", "trust", "bharosa", "fraud", "scam", "genuine",
        "legit", "verify", "verified", "authentic",
    ],
    "location": [
        "location achi nahi", "location theek nahi", "bad location",
        "door hai", "far from", "location acha nahi", "isolated",
        "remote area",
    ],
    "investment": [
        "return", "returns", "profit", "faida", "resale", "appreciate",
        "appreciation", "roi", "invest", "investment",
    ],
    "builder": [
        "builder", "developer reliable", "track record", "kaam kaisa",
        "previous projects", "delay", "delayed",
    ],
    "maintenance": [
        "maintenance", "society charges", "monthly charges", "upkeep",
        "maintenance fee", "maintenance cost",
    ],
}

# Extra terms appended to the RAG retrieval query for each objection type,
# so the right passages (developer profile, guides, brochures) get pulled
# in even if the buyer's phrasing doesn't literally match those documents.
OBJECTION_QUERY_HINTS: dict[str, str] = {
    "price": "payment plan installment options booking down payment",
    "trust": "developer registration license completed projects track record",
    "location": "nearby schools hospitals location amenities",
    "investment": "developer completed projects status under construction possession",
    "builder": "developer founded license completed projects ongoing projects",
    "maintenance": "amenities society maintenance charges facilities",
}

# One line injected into the system prompt telling the model exactly how
# to handle THIS objection type, on top of the general objection-handling
# rules already in SALES_SYSTEM_PROMPT.
OBJECTION_INSTRUCTIONS: dict[str, str] = {
    "price": (
        "The buyer has a PRICE concern. Acknowledge it, then offer the "
        "actual payment plan structure from the context (booking %, "
        "installment years/frequency) if available — do not offer an "
        "informal discount that isn't in the data."
    ),
    "trust": (
        "The buyer has a TRUST concern about the developer. Acknowledge "
        "it, then cite the developer's actual registration/license number "
        "and completed-project count from the context, if available."
    ),
    "location": (
        "The buyer has a LOCATION concern. Acknowledge it, then mention "
        "actual nearby schools/hospitals or area facts from the context, "
        "if available — do not invent proximity claims."
    ),
    "investment": (
        "The buyer has an INVESTMENT/RETURN concern. Acknowledge it. You "
        "may cite the project's actual status and the developer's "
        "completed-project history from the context, but you must NOT "
        "guarantee or estimate future profit, returns, or appreciation "
        "under any circumstance."
    ),
    "builder": (
        "The buyer has a concern about the BUILDER/DEVELOPER. Acknowledge "
        "it, then cite the developer's actual founding year, license "
        "number, and completed/ongoing project counts from the context."
    ),
    "maintenance": (
        "The buyer has a MAINTENANCE/CHARGES concern. Acknowledge it, "
        "then describe the actual amenities from the context — if exact "
        "maintenance fee amounts are not in the context, say so honestly "
        "rather than estimating a number."
    ),
}


def detect_objection(message: str) -> str | None:
    """
    Returns the objection type with the most keyword hits, or None if no
    objection keywords are found. Simple substring matching is sufficient
    here — this is a routing signal, not the final response.
    """

    text = message.lower()
    scores: dict[str, int] = {}

    for objection_type, keywords in OBJECTION_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count:
            scores[objection_type] = count

    if not scores:
        return None

    return max(scores, key=scores.get)


def get_query_hint(objection_type: str | None) -> str:
    if not objection_type:
        return ""
    return OBJECTION_QUERY_HINTS.get(objection_type, "")


def get_instruction(objection_type: str | None) -> str:
    if not objection_type:
        return ""
    return OBJECTION_INSTRUCTIONS.get(objection_type, "")