# Integrating LiveKit for telephony

```python
                 REAL PHONE / VOICE
                         │
                         ▼
                    ┌─────────┐
                    │ LiveKit │
                    └────┬────┘
                         │
                         ▼
                Voice Agent Worker
                         │
             ┌───────────┴───────────┐
             │                       │
             ▼                       ▼
           STT                     TTS
       Deepgram                   Edge-TTS
             │                       ▲
             └──────────┬────────────┘
                        │
                        ▼
                 LangGraph Agent
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
       RAG          Property DB       Memory
        │               │                │
        └───────────────┼────────────────┘
                        │
                        ▼
                    Tools
             ┌──────────┼──────────┐
             ▼          ▼          ▼
          Calendar     Email       CRM


```

The eventual flow could be:
```python
Phone
 ↓
LiveKit/SIP
 ↓
Deepgram STT
 ↓
LangGraph
 ↓
Edge-TTS
 ↓
LiveKit
 ↓
Phone
```
