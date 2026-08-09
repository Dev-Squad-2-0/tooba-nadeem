"""
Standalone test for app.graph.agent_graph
"""

from app.graph.agent_graph import handle_turn


SESSION_ID = "test_voice_session"

queries = [
    "مجھے لاہور میں تین بیڈ روم کا اپارٹمنٹ چاہیے",
    "میرا بجٹ 80 لاکھ ہے",
    "DHA میں ہونا چاہیے",
    "سوئمنگ پول بھی ہونا چاہیے",
    "آپ کیا ریکمینڈ کریں گے؟",
    "اس سے سستا کوئی آپشن ہے؟",
    "پہلے آپ نے کون سی پراپرٹی ریکمینڈ کی تھی؟",
]

for i, query in enumerate(queries, start=1):
    print("=" * 70)
    print(f"TURN {i}")
    print("USER:", query)

    response = handle_turn(SESSION_ID, query)

    print("\nASSISTANT:")
    print(response)
    print()