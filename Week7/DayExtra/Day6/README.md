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
