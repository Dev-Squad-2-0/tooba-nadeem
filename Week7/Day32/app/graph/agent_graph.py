"""
agent_graph.py
---------------

Per-turn orchestration for the conversational voice/chat agent.

Combines, for a single incoming buyer message:
  1. Slot extraction + memory update  (app/graph/slot_extractor.py, state.py)
  2. Objection detection              (app/tools/objection_handler.py)
  3. RAG retrieval                    (app/rag/retriever.py — REUSED, Day 1)
  4. Structured recommendation/lookup (app/recommendation/recommender.py,
                                        database/sql_retriever.py — REUSED, Day 2)
  5. Grounded, persona-driven response generation (app/llm/client.py)

Retriever and PropertyRecommender are cached as module-level singletons —
Retriever() loads the Chroma store and PropertyRecommender() opens a
SQLite-backed retriever on init, and re-doing that on every single voice
turn would blow the <2s latency budget for no benefit.
"""

import logging

from app import config
from app.rag.retriever import Retriever
from app.recommendation.recommender import PropertyRecommender
from app.llm.client import generate_chat_response
from app.llm.prompts import SALES_SYSTEM_PROMPT
from app.graph import memory_store
from app.graph.slot_extractor import extract_and_apply
from app.tools import objection_handler

logger = logging.getLogger(__name__)

_retriever: Retriever | None = None
_recommender: PropertyRecommender | None = None


def _get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def _get_recommender() -> PropertyRecommender:
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


def _sql_context_for_recommendations(state) -> tuple[str, list[dict]]:
    """
    Uses the Day 2 recommender, driven by whatever slots are currently
    known in state. Returns (formatted_text, property_ids_shown).
    """

    recommender = _get_recommender()

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


def _sql_context_for_current_property(state) -> str:
    """
    When the buyer is discussing a specific named project, pull its exact
    price/availability/size/agent info directly rather than relying only
    on the recommender's filters.

    NOTE: matches on exact project_name (case-insensitive) since that's
    what sql_retriever.py's queries support. If the buyer's phrasing
    doesn't exactly match a project_name (e.g. "Skyline" vs "Skyline
    Residency"), this will find nothing and the RAG context / recommender
    results still cover the gap. Fuzzy project-name matching would be a
    good follow-up improvement but is out of scope here.
    """

    recommender = _get_recommender()
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

    # Look up property_id to fetch the assigned agent, matching the same
    # pattern recommender.py uses (direct _query call via the shared
    # SQLRetriever instance).
    id_rows = sql._query(
        "SELECT property_id FROM properties WHERE LOWER(project_name)=LOWER(?)",
        (name,),
    )
    if id_rows:
        agent_rows = sql.get_property_agent(id_rows[0]["property_id"])
        if agent_rows:
            ag = agent_rows[0]
            lines.append(
                f"Assigned agent: {ag['name']} ({ag['phone']}, {ag['email']})"
            )

    return "\n".join(lines)


def handle_turn(session_id: str, message: str) -> str:
    """
    Main entry point: process one buyer message and return the agent's
    spoken/text response. Called by both the text /chat endpoint and the
    voice pipeline (after Deepgram produces a final transcript).
    """

    state = memory_store.get_or_create(session_id)

    # 1. Update long-term slot memory from this message only.
    extract_and_apply(state, message)

    # 2. Detect objection type (if any) to steer retrieval + instructions.
    objection_type = objection_handler.detect_objection(message)
    query_hint = objection_handler.get_query_hint(objection_type)
    objection_instruction = objection_handler.get_instruction(objection_type)

    # 3. RAG retrieval (Day 1, reused as-is) — query enriched with buyer
    #    context and objection hints so retrieval surfaces the right facts.
    rag_query_parts = [message]
    if state.current_property:
        rag_query_parts.append(state.current_property)
    if query_hint:
        rag_query_parts.append(query_hint)
    rag_query = " ".join(rag_query_parts)

    rag_docs = _get_retriever().retrieve(rag_query)
    rag_context = "\n\n".join(doc.page_content for doc in rag_docs) or (
        "No relevant passages found in the knowledge base."
    )

    # 4. Structured data (Day 2, reused as-is).
    if state.current_property:
        sql_context = _sql_context_for_current_property(state)
        if not sql_context:
            # Fall back to filtered recommendations if the exact project
            # name didn't match any row.
            sql_context, shown_ids = _sql_context_for_recommendations(state)
            state.record_recommendations(shown_ids)
    else:
        if state.has_any_preference():
            sql_context, shown_results = _sql_context_for_recommendations(state)
            state.record_recommendations(shown_results)
        else:
            sql_context = "No buyer preferences captured yet."

    # 5. Build the persona prompt, with the objection instruction appended
    #    (kept as a separate trailing block so SALES_SYSTEM_PROMPT stays
    #    reusable/unmodified per-turn — we're not rewriting the template).
    system_content = SALES_SYSTEM_PROMPT.format(
        buyer_preferences=state.preferences_summary(),
        rag_context=rag_context,
        sql_context=sql_context,
    )
    if objection_instruction:
        system_content += f"\n\n## This turn's objection-handling guidance\n{objection_instruction}\n"

    messages = [{"role": "system", "content": system_content}]
    messages.extend(state.history)  # bounded short-term history
    messages.append({"role": "user", "content": message})

    response_text = generate_chat_response(messages)

    # 6. Persist this exchange to short-term history, then save state.
    state.add_turn("user", message)
    state.add_turn("assistant", response_text)
    memory_store.save(state)

    return response_text