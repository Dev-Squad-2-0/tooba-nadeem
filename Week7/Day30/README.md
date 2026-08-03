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
├── docs/
│   ├── 01_Executive_Report.pdf
│   ├── 02_System_Architecture.pdf
│   ├── 03_API_Documentation.pdf
│   ├── 04_Admin_Guide.pdf
│   ├── 05_User_Guide.pdf
│   ├── 06_Monitoring_Plan.pdf
│   ├── 07_Demo_Script.pdf
│   └── 08_Slide_Deck.pptx
|
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
