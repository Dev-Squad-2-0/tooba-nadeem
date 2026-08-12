from app.graph.state import ConversationState
from app.graph.slot_extractor import extract_and_apply

state = ConversationState(session_id="test-slot-extraction")

msg = (
    "Ji mujhe DHA Lahore mein 3 bedroom apartment chahiye. "
    "Mera budget 3 crore hai aur main 15 August 2026 ko 2 baje "
    "property visit karna chahti hoon. Appointment book kar dein."
)

extract_and_apply(state, msg)

print("DATE:", state.requested_date)
print("TIME:", state.requested_time)