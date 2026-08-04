"""
test_task3.py

Test structured (SQL) retrieval vs semantic (RAG) retrieval.
"""

from database.database import PropertyDatabase
from database.sql_retriever import SQLRetriever
from app.rag.rag_pipeline import RAGPipeline


def main():

    print("=" * 70)
    print("TASK 3 TEST")
    print("=" * 70)

    # --------------------------
    # Build SQL database
    # --------------------------

    print("\nBuilding SQL database...")

    db = PropertyDatabase()
    db.build_database()

    sql = SQLRetriever()

    rag = RAGPipeline()
    rag.build()

    # ---------------------------------------------------
    # SQL TESTS
    # ---------------------------------------------------

    print("\nSQL TESTS")
    print("-" * 70)

    print("\nPrices")
    print(sql.get_prices())

    print("\nAvailability")
    print(sql.get_availability())

    print("\nPlot Sizes")
    print(sql.get_plot_sizes())

    print("\nAgents")
    print(sql.get_agents())

    # ---------------------------------------------------
    # VECTOR TESTS
    # ---------------------------------------------------

    print("\n")
    print("=" * 70)
    print("VECTOR TESTS")
    print("=" * 70)

    questions = [

        "Tell me about Skyline Residency.",

        "What is Meridian Homes?",

        "Explain the payment plan for Emerald Gardens.",

        "What legal documents should buyers verify?",

        "How do I book a property?"
    ]

    for question in questions:

        print("\nQuestion:")
        print(question)

        answer = rag.answer(question)

        print("\nAnswer:")
        print(answer)

        print("-" * 70)


if __name__ == "__main__":
    main()