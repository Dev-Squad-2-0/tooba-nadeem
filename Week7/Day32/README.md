## Deepgram STT Notes (Day 3)

Issue:
- Streaming worked but transcripts were mostly empty.

Root Cause:
- Deepgram configuration was using an unsuitable model/language combination.
- Domain-specific acronyms (e.g. DHA) also required keyterm prompting.

Resolution:
- In .env file:
```python
DEEPGRAM_MODEL=nova-3
DEEPGRAM_LANGUAGE=ur
```
- and in stt_deepgram.py:
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
-then in function call:
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
