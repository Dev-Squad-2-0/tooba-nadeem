## Deepgram STT Notes (Day 3)

Issue:
- Streaming worked but transcripts were mostly empty.

Root Cause:
- Deepgram configuration was using an unsuitable model/language combination.
- Domain-specific acronyms (e.g. DHA) also required keyterm prompting.

Resolution:
- Model: nova-3
- Language: ur
- Added keyterms for real estate terminology.

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
