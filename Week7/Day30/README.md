# Production-Grade AI Voice Agent for Real Estate 
_Conversational AI • Voice • RAG • Workflows • Scheduling • Human-like UrduLish_

## What are we building?
something like this: 
```python
Phone Call
↓
STT (Deepgram)
↓
LangGraph Agent
↓
Intent Detection
↓
- Property Search
- Calendar
- Email
- CRM
- RAG
↓
LLM
↓
TTS (Fish Audio)
↓
Caller
```


## Planned folder structure
```python
real-estate-agent/

app/
│
├── api/
│
├── graph/
│   ├── state.py
│   ├── nodes.py
│   ├── router.py
│   └── graph.py
│
├── rag/
│
├── voice/
│   ├── stt.py
│   ├── tts.py
│   └── streaming.py
│
├── tools/
│   ├── calendar.py
│   ├── email.py
│   ├── property_search.py
│   ├── crm.py
│   └── availability.py
│
├── workflows/
│
├── prompts/
│
├── database/
│
├── evaluation/
│
└── main.py
```
