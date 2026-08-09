"""
app/graph/tools.py
---------------------

Thin wrappers around EXISTING business logic — no reimplementation.
Retriever and PropertyRecommender singletons moved here from
agent_graph.py so both nodes.py and the (now thin) agent_graph.py share
one cached instance instead of two.

Every function here calls a real, already-verified-working Day 1-4
function with the EXACT signature confirmed by reading the actual files
in this project (not assumed/reconstructed from memory).
"""

from __future__ import annotations

import logging

from app import config
from app.rag.retriever import Retriever
from app.recommendation.recommender import PropertyRecommender
from app.calendar.google_calendar import GoogleCalendarError, check_slot_availability
from app.workflows.appointment_manager import (
    book_appointment as _book_appointment,
    reschedule_appointment as _reschedule_appointment,
    cancel_appointment as _cancel_appointment,
)

logger = logging.getLogger(__name__)

_retriever: Retriever | None = None
_recommender: PropertyRecommender | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def get_recommender() -> PropertyRecommender:
    global _recommender
    if _recommender is None:
        _recommender = PropertyRecommender()
    return _recommender


def _format_pkr(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    if n >= 10_000_000:
        return f"PKR {n / 10_000_000:.2f} Crore"
    if n >= 100_000:
        return f"PKR {n / 100_000:.1f} Lakh"
    return f"PKR {n:,}"


# ---------------------------------------------------------------------------
# Search Property — identical logic to agent_graph.py's
# _sql_context_for_recommendations(), moved here so it's defined once.
# ---------------------------------------------------------------------------

def search_property(state) -> tuple[str, list[dict]]:
    recommender = get_recommender()

    investment_goal = None
    if state.investment_intent or (state.purpose or "").lower() == "investment":
        investment_goal = "investment"

    results = recommender.recommend(
        budget=state.budget,
        city=state.city,
        area=state.area,
        bedrooms=state.bedrooms,
        purpose=state.purpose,
        amenities=state.amenities or None,
        investment_goal=investment_goal,
    )

    results = results[: config.MAX_RECOMMENDATIONS]

    if not results:
        return "No matching properties found in the database for the current preferences.", []

    lines = []
    for p in results:
        lines.append(
            f"- {p.get('project_name')} | {p.get('city')} | "
            f"{p.get('property_type')} | Status: {p.get('status')} | "
            f"Price: {_format_pkr(p.get('price_range_min_pkr'))} to "
            f"{_format_pkr(p.get('price_range_max_pkr'))}"
        )

    return "\n".join(lines), results


def lookup_current_property(state) -> str:
    """Identical logic to agent_graph.py's _sql_context_for_current_property()."""

    recommender = get_recommender()
    sql = recommender.sql
    name = state.current_property

    price_rows = sql.get_property_price(name)
    availability_rows = sql.get_property_availability(name)
    size_rows = sql.get_plot_size(name)

    if not price_rows:
        return ""

    price = price_rows[0]
    lines = [
        f"{price['project_name']} — {price['city']}",
        f"Price: {_format_pkr(price['price_range_min_pkr'])} to "
        f"{_format_pkr(price['price_range_max_pkr'])}",
    ]

    if availability_rows:
        a = availability_rows[0]
        lines.append(f"Status: {a['status']} | Total units: {a['total_units']}")

    if size_rows:
        s = size_rows[0]
        lines.append(f"Size range: {s['size_range_sqft']} sq. ft.")

    id_rows = sql._query(
        "SELECT property_id FROM properties WHERE LOWER(project_name)=LOWER(?)",
        (name,),
    )
    if id_rows:
        agent_rows = sql.get_property_agent(id_rows[0]["property_id"])
        if agent_rows:
            ag = agent_rows[0]
            lines.append(f"Assigned agent: {ag['name']} ({ag['phone']}, {ag['email']})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# RAG Search
# ---------------------------------------------------------------------------

def rag_search(query: str) -> str:
    docs = get_retriever().retrieve(query)
    return "\n\n".join(doc.page_content for doc in docs) or (
        "No relevant passages found in the knowledge base."
    )


# ---------------------------------------------------------------------------
# Availability Checker
# ---------------------------------------------------------------------------

def check_availability(date: str, time_str: str) -> dict:
    try:
        available = check_slot_availability(date, time_str)
        return {"available": available, "error": None}
    except GoogleCalendarError as exc:
        logger.error("check_availability failed: %s", exc)
        return {"available": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Calendar / Email / CRM — via appointment_manager.py, confirmed current
# signatures: book_appointment(client_name, phone, property_name, date,
# time_str, budget=None, preferred_location=None, property_type=None,
# requirements="", notes="", transcript=None); reschedule_appointment(
# phone, new_date, new_time, notes=None); cancel_appointment(phone,
# notes=None).
# ---------------------------------------------------------------------------

def book_appointment_tool(**kwargs) -> dict:
    return _book_appointment(**kwargs)


def reschedule_appointment_tool(**kwargs) -> dict:
    return _reschedule_appointment(**kwargs)


def cancel_appointment_tool(**kwargs) -> dict:
    return _cancel_appointment(**kwargs)
