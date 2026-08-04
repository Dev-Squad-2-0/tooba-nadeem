"""
test_rag.py
-----------

Standalone test for the RAG pipeline.

Run:
    python test_rag.py
"""

import logging

from app.rag.rag_pipeline import RAGPipeline

# ---------------------------------------------------------------------
# Configure logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    print("=" * 70)
    print("REAL ESTATE RAG PIPELINE TEST")
    print("=" * 70)

    pipeline = RAGPipeline()

    print("\nBuilding vector database...")

    chunk_count = pipeline.build()

    print(f"✓ Indexed {chunk_count} chunks.")

    print("\n")

    while True:

        query = input("Ask a question (or 'exit'): ").strip()

        if query.lower() == "exit":
            break

        print("\nSearching...\n")

        answer = pipeline.answer(query)

        print()

        print("=" * 70)
        print("ANSWER")
        print("=" * 70)

        print(answer)

        print()

        print("=" * 70)
        print()


if __name__ == "__main__":
    main()