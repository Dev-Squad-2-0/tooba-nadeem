"""
app/tests/day6/test_rag_accuracy.py
----------------------------------------

Day 6, Task 3 — RAG accuracy.

REAL-API TEST (technically: real Chroma vector store + real embedding
model, no LLM call needed since this tests retrieval, not generation).

HONESTY NOTE: this file is written against the REAL app.rag.retriever
.Retriever, deliberately NOT using app/tests/day6/_harness.py's mocks
(which stub out langchain_chroma/langchain_huggingface entirely). It
CANNOT be executed in the sandbox this project was audited in --
chromadb and sentence-transformers/langchain-huggingface are not
installed there, and the real Chroma vector store built from
database/knowledge/ is not present either. This has NOT been run by the
assistant that wrote it. Run it yourself with your real environment
(after RAGPipeline().build() has been run at least once, e.g. via normal
app startup) and report the actual numbers -- do not assume it passes.

Dataset built ONLY from facts that actually exist in
database/knowledge/ (brochures, developer profiles, guides, faqs) per
this project's earlier-generated knowledge base -- nothing invented.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.rag.retriever import Retriever  # noqa: E402

# (query, expected_substring_in_at_least_one_retrieved_chunk)
# Substrings chosen to match content genuinely present in the generated
# knowledge base documents (brochures/skyline_residency.md,
# developers/silk_developers*.md, guides/*, faqs/*).
RAG_DATASET = [
    ("Skyline Residency ke amenities kya hain?", "Skyline Residency"),
    ("Skyline Residency kis developer ne banaya?", "Silk Developers"),
    ("Skyline Residency ka payment plan kya hai?", "Skyline Residency"),
    ("Emerald Gardens kahan hai?", "Emerald Gardens"),
    ("Property buy karne ka process kya hai?", "buying"),
    ("Overseas Pakistani property invest kar sakte hain?", "overseas"),
    ("DHA Lahore ke nearby schools konse hain?", "school"),
    ("Booking amount kitna hota hai?", "booking"),
    ("Al-Noor Estates kab founded hui?", "Al-Noor"),
    ("Property tax ke baare mein bataein.", "tax"),
]


def run():
    print(f"Running {len(RAG_DATASET)} RAG accuracy checks against the REAL vector store...\n")

    retriever = Retriever()  # will raise if the real vector store isn't built -- intentional, not caught

    correct = 0
    misses = []
    for query, expected_substring in RAG_DATASET:
        docs = retriever.retrieve(query)
        combined = "\n".join(d.page_content for d in docs)
        hit = expected_substring.lower() in combined.lower()
        status = "OK" if hit else "MISS"
        print(f"[{status}] {query!r} -> expected substring {expected_substring!r}")
        if hit:
            correct += 1
        else:
            misses.append((query, expected_substring))

    total = len(RAG_DATASET)
    accuracy = correct / total if total else 0.0
    print()
    print(f"RAG tests:          {total}")
    print(f"Correct retrievals: {correct}")
    print(f"Misses:             {len(misses)}")
    print(f"Accuracy:           {accuracy:.1%}")
    if misses:
        print("\nMissed queries:")
        for q, exp in misses:
            print(f"  - {q!r} (expected {exp!r} not found in top-k)")

    return correct, total


if __name__ == "__main__":
    correct, total = run()
    sys.exit(0 if correct == total else 1)
