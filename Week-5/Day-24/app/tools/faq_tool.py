"""
FAQ retrieval tool.

Deliberately uses simple keyword overlap rather than embeddings/vector DB:
this keeps the project's only "external data source" free, local, and
dependency-light (satisfies the assignment's local-JSON external-source
requirement) while still being swappable for a real vector store later
without touching any node code -- only this file would change.
"""
import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

with open(os.path.join(_DATA_DIR, "faq.json"), encoding="utf-8") as f:
    _FAQS = json.load(f)["faqs"]


def retrieve_faq(ticket_text: str, project_key: str, top_k: int = 2) -> list[dict]:
    """Returns up to top_k FAQ entries ranked by keyword overlap with the ticket text.

    Project-specific FAQs are boosted so a Blokkplay refund question doesn't
    surface a GemLaunch answer, while 'general' FAQs remain eligible for any
    project.
    """
    lowered = ticket_text.lower()
    scored = []
    for faq in _FAQS:
        hits = sum(1 for kw in faq["keywords"] if kw in lowered)
        if hits == 0:
            continue
        boost = 1.5 if faq["project"] == project_key else (1.0 if faq["project"] == "general" else 0.5)
        scored.append((hits * boost, faq))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [faq for _, faq in scored[:top_k]]
