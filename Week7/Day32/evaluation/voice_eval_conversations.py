"""
voice_eval_conversations.py
-----------------------------

Scripted multi-turn test conversations for evaluation, mirroring the
pattern used in evaluation/hallucination_questions.py.

Each scenario is a list of buyer turns run in order through the SAME
session_id, so agent_graph.handle_turn()'s memory (slots + short-term
history) carries across turns exactly as it would on a real call.
"""

EVAL_CONVERSATIONS = {

    "memory_budget_update": [
        "Assalam o Alaikum, mujhe Lahore mein ghar dekhna hai.",
        "Budget 3 crore hai.",
        "DHA mein kya options hain?",
        "Us se sasti koi option hai?",
        "Budget ab 5 crore hai.",
    ],

    "price_objection": [
        "Skyline Residency ka price kya hai?",
        "Yeh to bohat mehnga hai, itna zyada kyun?",
    ],

    "trust_objection": [
        "Al-Noor Valley ke baare mein batayein.",
        "Yeh builder reliable hai? Mujhe pata nahi inke baare mein.",
    ],

    "location_objection": [
        "Horizon Business Bay Karachi mein hai?",
        "Location achi nahi lag rahi mujhe, kya nearby facilities hain?",
    ],

    "investment_objection": [
        "Mein investment ke liye property dekh raha hoon Islamabad mein.",
        "Is mein return kitna milega?",
    ],

    "general_multiturn": [
        "Mujhe Karachi mein 2 bedroom apartment chahiye.",
        "Ready for possession hona chahiye.",
        "Ocean Breeze Towers ke amenities kya hain?",
        "Iska agent kaun hai, mujhe baat karni hai?",
    ],
}