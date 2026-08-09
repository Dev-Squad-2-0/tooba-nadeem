# Voice Agent Evaluation Rubric

Each metric is scored 1-5 by a human evaluator listening to (or reading the
transcript of) a conversation. This rubric accompanies the auto-generated
report from `evaluation/evaluate_voice.py`.

## 1. Naturalness (1-5)
How much does the agent sound like a real Pakistani property sales
executive, versus a scripted bot?

| Score | Description |
|---|---|
| 1 | Robotic, clearly templated, no natural speech markers |
| 2 | Mostly stiff; occasional natural phrasing |
| 3 | Reasonably natural but noticeably repetitive fillers/patterns |
| 4 | Natural Urdu/English code-switching, fillers used sparingly and appropriately |
| 5 | Indistinguishable from a real experienced sales executive on a call |

## 2. Persuasiveness (1-5)
Does the agent make a compelling, honest case without being pushy or
inventing claims?

| Score | Description |
|---|---|
| 1 | No attempt to address buyer's interest/concern, or oversells with invented claims |
| 2 | Weak engagement with the objection/interest, generic response |
| 3 | Addresses the concern with real facts but flatly, no persuasive framing |
| 4 | Grounded, confident, addresses the real concern with relevant facts |
| 5 | Compelling and grounded, acknowledges concern, uses only real data, moves conversation forward naturally |

## 3. Fluency (1-5)
Grammatical correctness and coherence of the Urdu/English code-switched
output.

| Score | Description |
|---|---|
| 1 | Broken grammar, incoherent code-switching |
| 2 | Frequent grammar issues |
| 3 | Understandable with occasional awkward phrasing |
| 4 | Fluent, minor awkwardness at most |
| 5 | Fully fluent, natural code-switching throughout |

## 4. Latency (1-5)
Measured automatically by `evaluate_voice.py` as text-orchestration time
(retrieval + recommendation + LLM generation), reported in seconds, then
scored:

| Score | Text-orchestration latency |
|---|---|
| 5 | < 1.0s |
| 4 | 1.0s - 1.5s |
| 3 | 1.5s - 2.0s |
| 2 | 2.0s - 3.0s |
| 1 | > 3.0s |

Note: this measures the RAG + recommender + LLM portion only. Full
end-to-end voice latency also includes Deepgram STT endpointing (~300ms)
and Edge-TTS first-audio-chunk time (typically 300-500ms) — these must be
measured separately with a live microphone test since they require actual
audio I/O, not a scripted harness. See "Manual Voice Latency Test" below.

## 5. Conversation Flow (1-5)
Does the agent correctly use memory (budget/city/etc. persisting across
turns) and stay coherent across a multi-turn exchange?

| Score | Description |
|---|---|
| 1 | Forgets prior context every turn |
| 2 | Partial memory, frequently drops preferences |
| 3 | Remembers most preferences but occasionally loses one |
| 4 | Reliable memory across the conversation, minor slips |
| 5 | Perfect preference retention and correct updates (e.g. "budget ab 5 crore hai" updates only budget) |

## Scoring Table Template

| Scenario | Naturalness | Persuasiveness | Fluency | Latency | Flow | Notes |
|---|---|---|---|---|---|---|
| Memory / budget update | | | | | | |
| Price objection | | | | | | |
| Trust objection | | | | | | |
| Location objection | | | | | | |
| Investment objection | | | | | | |
| General multi-turn query | | | | | | |