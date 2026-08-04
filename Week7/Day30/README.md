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
real_estate_voice_agent/
│
├── app/
│   ├── config.py
│   ├── main.py
│   │
│   ├── rag/
│   │   ├── document_loader.py
│   │   ├── text_splitter.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── rag_pipeline.py
│   │
│   ├── graph/
│   ├── tools/
│   ├── prompts/
│   ├── database/
│   ├── voice/
│   └── workflows/
│
├── database/
│   ├── structured/
│   ├── knowledge/
│   └── chroma/
│
├── docs/
│
├── evaluation/
│
├── requirements.txt
├── .env.example
├── README.md
└── venv/
```
