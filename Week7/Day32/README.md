## Deepgram STT Notes (Day 3)

Issue:
- Streaming worked but transcripts were mostly empty.

Root Cause:
- Deepgram configuration was using an unsuitable model/language combination.
- Domain-specific acronyms (e.g. DHA) also required keyterm prompting.

Resolution:
- In `.env` file:
```python
DEEPGRAM_MODEL=nova-3
DEEPGRAM_LANGUAGE=ur
```
-  and in `stt_deepgram.py`:
```python
# Domain-specific terms Deepgram's general language model won't reliably
# recognize on its own (Pakistani real-estate abbreviations, area names,
# and this project's own developer/project names). Keyterm Prompting
# biases the acoustic model toward these at inference time without
# retraining. Confirmed compatible with Nova-3 + language=ur.
REAL_ESTATE_KEYTERMS = [
    "DHA", "Bahria Town", "Gulberg", "Askari", "Model Town",
    "Skyline Residency", "Emerald Gardens", "Ocean Breeze Towers",
    "Horizon Business Bay", "Capital Greens Enclave", "The Pearl Heights",
    "Al-Noor Valley", "Al-Noor Business Square",
]
```
- then in function call:
```python
        self._connection_ctx = self._client.listen.v1.connect(
            model=config.DEEPGRAM_MODEL,
            language=config.DEEPGRAM_LANGUAGE,
            smart_format=True,
            interim_results=True,
            # Voice-agent turn-taking: Deepgram flags a final segment once
            # ~endpointing ms of silence is detected. 300ms keeps latency
            # low without cutting the buyer off mid-thought.
            endpointing=300, # back to 300 -- the 100ms recommendation from Deepgram's docs was specifically for `language=multi` code-switching; you're on monolingual `ur` now, so the standard default applies
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            **keyterm=REAL_ESTATE_KEYTERMS,**
        )
```

Result:
- Verified accurate transcription of real Pakistani Urdu speech.


## LLM Integration Improvements (Day 3)

During testing, the voice agent exhibited two major issues:

- Some reasoning-capable models exposed their internal reasoning before the final answer.
- Responses were sometimes cut off (e.g., "Ji... Ji bilkul...") because reasoning tokens consumed the available token budget.

### Root Cause

The issue was not caused by prompt engineering.

Some OpenRouter models are **reasoning-enabled**, and by default they may return internal reasoning in the response. These reasoning tokens count toward the response token limit, leaving fewer tokens available for the final user-facing answer.

### Solution

The fix was implemented at the **API configuration level** rather than the prompt level.

#### 1. Server-side fallback models

An ordered fallback model list was introduced so that if the primary free model becomes unavailable, OpenRouter automatically retries a secondary model without failing the request.

```python
OPENAI_MODEL_FALLBACKS = [
    OPENAI_MODEL,
    "meta-llama/llama-3.3-70b-instruct",
]
```

#### 2. Excluding reasoning tokens

A configuration flag was added to explicitly prevent reasoning tokens from being returned.

```python
EXCLUDE_REASONING_TOKENS = True
```

This setting is passed to every OpenRouter request:

```python
extra_body={
    "models": config.OPENAI_MODEL_FALLBACKS,
    "reasoning": {
        "exclude": config.EXCLUDE_REASONING_TOKENS
    }
}
```

#### 3. Defensive output sanitization

As an additional safeguard, every model response passes through a lightweight post-processing step that removes any accidental `<think>...</think>` blocks before being used by the application.

```python
_THINK_TAG_RE = re.compile(
    r"<think>.*?</think>",
    re.DOTALL | re.IGNORECASE
)
```

### Outcome

After these changes:

- No reasoning text is exposed to users.
- Responses are complete and no longer truncated.
- The voice agent behaves consistently across supported OpenRouter models.
- Temporary failures of free models are handled automatically through server-side model fallback.


## Human Evaluation

The voice agent was evaluated manually by conducting multiple sample conversations covering property search, follow-up questions, context retention, recommendations, and objection handling.

| Metric | Score (5.0) | Observation |
|---------|:-----------:|-------------|
| Naturalness | ⭐⭐⭐⭐☆ (4.5/5) | Responses sounded conversational and used UrduLish naturally with acknowledgements such as "Ji bilkul" and "Acha". |
| Persuasiveness | ⭐⭐⭐⭐☆ (4.4/5) | Property recommendations were relevant and supported with project information retrieved from the knowledge base and structured database. |
| Fluency | ⭐⭐⭐⭐⭐ (4.8/5) | Responses were coherent, grammatically correct, and maintained a consistent conversational flow. |
| Latency | ⭐⭐⭐⭐☆ (4.3/5) | End-to-end pipeline (STT → LLM → TTS) responded within the expected range for local testing. |
| Conversation Flow | ⭐⭐⭐⭐⭐ (4.7/5) | Context memory successfully preserved buyer preferences, budget, location, and previous recommendations across multiple conversation turns. |

### Test Scenarios Performed

- ✅ Property recommendation based on city and budget
- ✅ Multi-turn conversation with memory retention
- ✅ Slot extraction and preference updates
- ✅ RAG-based knowledge retrieval
- ✅ SQL-based structured property lookup
- ✅ Recommendation engine integration
- ✅ Objection handling
- ✅ Deepgram Speech-to-Text integration
- ✅ Edge-TTS speech synthesis
- ✅ Complete voice pipeline testing using WebSocket communication

### Overall Result

The Day 3 voice agent successfully integrates streaming speech recognition, conversational memory, retrieval-augmented generation (RAG), structured property recommendations, objection handling, and speech synthesis into a single end-to-end pipeline. The system behaves like a conversational Pakistani real estate sales representative while maintaining context across multiple dialogue turns.


## Final End-to-End Voice Pipeline Test

The complete voice pipeline was successfully tested using `test_voice_pipeline.py`.

### Pipeline Flow

Sample Audio (.wav)
→ FastAPI WebSocket
→ Deepgram Speech-to-Text
→ Transcript Corrections
→ Agent Graph
→ Conversation Memory
→ Recommendation Engine
→ RAG Retrieval
→ LLM Response Generation
→ Edge TTS
→ Response Audio (.mp3)

### Test Result

| Component | Status |
|-----------|--------|
| FastAPI WebSocket | ✅ Passed |
| Deepgram STT | ✅ Passed |
| Transcript Corrections | ✅ Passed |
| Agent Graph | ✅ Passed |
| Memory Integration | ✅ Passed |
| Recommendation Engine | ✅ Passed |
| RAG Pipeline | ✅ Passed |
| LLM Response | ✅ Passed |
| Edge TTS | ✅ Passed |
| Audio Generation | ✅ Passed |

### Sample Output

**Transcript**
