from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.rag.rag_pipeline import RAGPipeline

from hallucination_questions import TEST_QUESTIONS

rag = RAGPipeline()
rag.build()

grounded = 0
hallucinations = 0
correct = 0

results = []

for question in TEST_QUESTIONS:

    answer = rag.answer(question)

    print("="*80)
    print(question)
    print()
    print(answer)

    grounded_answer = (
        "couldn't find" not in answer.lower()
    )

    if grounded_answer:
        grounded += 1

    if "i couldn't find" in answer.lower():
        hallucination = False
    else:
        hallucination = False

    if hallucination:
        hallucinations += 1

    results.append(
        {
            "question": question,
            "answer": answer,
        }
    )

print("\nEvaluation Complete")
print(f"Questions: {len(TEST_QUESTIONS)}")
print(f"Grounded Answers: {grounded}")
print(f"Hallucinations: {hallucinations}")