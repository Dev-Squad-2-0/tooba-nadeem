# Web3Geeks Intelligent Support Triage Agent — Presentation Outline
*(5–7 minutes, ~9 slides)*

**Slide 1 — Title**
Web3Geeks Intelligent Support Triage Agent
Automating first-line support triage across 9 products, with a human always in control of consequential actions.

**Slide 2 — The Problem**
- One shared support inbox, nine products, growing ticket volume.
- Every ticket needs a human to read it, figure out which product, judge urgency, and route it — before any reply goes out.
- That manual step doesn't scale, and it delays low-risk tickets (FAQ-answerable questions) as much as high-risk ones (refunds, account recovery).

**Slide 3 — What We Built**
- An agent that reads a ticket, identifies the product, classifies the issue, sets priority, routes to the right team, and drafts a reply — automatically.
- Refunds, billing disputes, and account recovery always stop for human sign-off before anything is sent.
- Wrapped as a real API: submit a ticket, check its status, approve/reject.

**Slide 4 — Architecture (walk the diagram)**
- Validate → Identify Product → Classify Issue → Prioritize/Route → Retrieve FAQ → Draft Reply → [Human Gate if sensitive] → Finalize.
- Local FAQ + product-routing data as the knowledge source (no external paid services required).
- Every classification step tries the LLM first, falls back to a rule-based classifier automatically if the model is slow, rate-limited, or refuses.

**Slide 5 — Why LangGraph (not CrewAI)**
- This is a fixed decision sequence with one branch and one approval checkpoint — a state machine, not a negotiation between multiple AI "roles."
- LangGraph gives us typed state, conditional routing, and a checkpointer that can pause a run and resume it later — exactly what the human-approval gate needs.
- The gate is enforced in code, not by asking the model for permission — verified against a prompt-injection test case that tried to auto-approve a refund; it still stopped for human review.

**Slide 6 — Evaluation**
- 10 test cases, including a prompt-injection attempt and a malformed-input case.
- 100% routing accuracy, 100% human-checkpoint correctness, 4.4/5 average response quality.
- Found and fixed a real gap during testing (fallback classifier missed phrases like "reward wasn't recorded") — before/after numbers included in the eval report.
- *(Note for delivery: mention this run used the offline fallback path due to a sandbox network restriction; the live-endpoint run is the next step.)*

**Slide 7 — Guardrails in Place**
- Input validation rejects malformed tickets before spending a model call.
- Automatic fallback on model timeout/rate-limit/refusal — no stalled tickets.
- Hard-coded human checkpoint for anything consequential — never bypassable by ticket content.

**Slide 8 — Known Limitations & Next Steps**
- Needs a live-endpoint evaluation run, a persistent (not in-memory) checkpoint store, and basic API auth before production.
- Recommended: a simple reviewer queue UI, PII redaction in logs, monitoring dashboard using the logging already in place.

**Slide 9 — Questions**
Thank you — happy to walk through the code, the graph, or the eval results in more detail.
