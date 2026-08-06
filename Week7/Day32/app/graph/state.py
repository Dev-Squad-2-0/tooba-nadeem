"""
state.py
--------

Defines ConversationState: the per-session memory object tracked across a
voice/chat conversation. This is intentionally a plain dataclass rather than
a Pydantic model — it's mutated every turn in-process and never serialized
across a network boundary directly (memory_store.py handles persistence).
"""

import time
from dataclasses import dataclass, field, asdict


LIST_FIELDS = {"amenities"}

SCALAR_FIELDS = {
    "budget",
    "city",
    "area",
    "property_type",
    "bedrooms",
    "purpose",
    "investment_intent",
    "current_property",
}

ALL_SLOT_FIELDS = SCALAR_FIELDS | LIST_FIELDS

# Short-term dialogue coherence, separate from long-term slot memory.
# Kept small on purpose: 3 exchanges is enough for "us se sasti koi option?"
# style follow-ups without bloating every prompt / hurting voice latency.
MAX_HISTORY_TURNS = 3


@dataclass
class ConversationState:
    session_id: str

    # Buyer preference slots (long-term, durable across the whole call)
    budget: int | None = None
    city: str | None = None
    area: str | None = None
    property_type: str | None = None
    bedrooms: int | None = None
    purpose: str | None = None
    amenities: list[str] = field(default_factory=list)
    investment_intent: bool | None = None

    # Conversation-tracked entities
    recommended_properties: list[str] = field(default_factory=list)
    recommended_property_names: list[str] = field(default_factory=list)
    current_property: str | None = None

    # Short-term rolling dialogue history: list of {"role": ..., "content": ...}
    history: list[dict] = field(default_factory=list)

    # Bookkeeping
    last_updated: float = field(default_factory=time.time)

    def apply_updates(self, updates: dict) -> None:
        for key, value in updates.items():

            if key not in ALL_SLOT_FIELDS:
                continue

            if value in (None, "", []):
                continue

            if key in LIST_FIELDS:
                existing = set(getattr(self, key) or [])
                existing.update(v.lower() for v in value)
                setattr(self, key, sorted(existing))
            else:
                setattr(self, key, value)

        self.last_updated = time.time()

    def record_recommendations(self, properties: list[dict]) -> None:  # CHANGED signature
        for p in properties:
            pid = p.get("property_id")
            name = p.get("project_name") or pid
            if pid and pid not in self.recommended_properties:
                self.recommended_properties.append(pid)
                self.recommended_property_names.append(name)

    def has_any_preference(self) -> bool:  # NEW
        return bool(
            self.budget or self.city or self.area or self.property_type
            or self.bedrooms or self.purpose or self.amenities
            or self.investment_intent or self.current_property
        )

    def add_turn(self, role: str, content: str) -> None:
        """
        Append one turn and trim to the last MAX_HISTORY_TURNS exchanges
        (an exchange = 1 user + 1 assistant message, so we keep at most
        2 * MAX_HISTORY_TURNS messages).
        """
        self.history.append({"role": role, "content": content})
        max_messages = MAX_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def to_dict(self) -> dict:
        return asdict(self)

    def preferences_summary(self) -> str:
        parts = []

        if self.budget:
            parts.append(f"Budget: PKR {self.budget:,}")
        if self.city:
            parts.append(f"City: {self.city}")
        if self.area:
            parts.append(f"Area: {self.area}")
        if self.property_type:
            parts.append(f"Property type: {self.property_type}")
        if self.bedrooms:
            parts.append(f"Bedrooms: {self.bedrooms}")
        if self.purpose:
            parts.append(f"Purpose: {self.purpose}")
        if self.amenities:
            parts.append(f"Wanted amenities: {', '.join(self.amenities)}")
        if self.investment_intent:
            parts.append("Buyer is investment-focused")
        if self.current_property:
            parts.append(f"Currently discussing: {self.current_property}")
        if self.recommended_properties:
            parts.append(
                "Previously recommended: "
                + ", ".join(self.recommended_property_names)
            )

        return "\n".join(parts) if parts else "No preferences captured yet."