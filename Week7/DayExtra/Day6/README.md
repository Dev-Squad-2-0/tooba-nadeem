# Integrating LiveKit for telephony

```python
                 📞 REAL PHONE CALL
                         │
                         ▼
                    ┌─────────┐
                    │ LiveKit │
                    │Telephony│
                    └────┬────┘
                         │
                   audio stream
                         │
                         ▼
                    ┌─────────┐
                    │ Deepgram│
                    │   STT   │
                    └────┬────┘
                         │
                   spoken → text
                         │
                         ▼
                  ┌─────────────┐
                  │  LangGraph  │
                  │ AI Agent    │
                  └──────┬──────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
             RAG      Property    Memory
                        DB
              │          │
              └──────────┼──────────┘
                         ▼
                       Tools
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Calendar    Email       CRM
                         │
                         ▼
                  response text
                         │
                         ▼
                    ┌─────────┐
                    │ Edge-TTS│
                    │   TTS   │
                    └────┬────┘
                         │
                    generated audio
                         │
                         ▼
                    ┌─────────┐
                    │ LiveKit │
                    └────┬────┘
                         │
                         ▼
                       📞 CALLER

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

and the responsibilities would roughly be:
```python
| Component       | What it does                                                                  |
| --------------- | ----------------------------------------------------------------------------- |
| **LiveKit**     | Connects the caller, streams audio, handles realtime voice sessions/telephony |
| **Deepgram**    | Converts caller's speech → text                                               |
| **LangGraph**   | Decides what the agent should do                                              |
| **RAG**         | Provides factual company/property knowledge                                   |
| **Property DB** | Property information                                                          |
| **Memory**      | Remembers conversation/customer information                                   |
| **Calendar**    | Books/reschedules/cancels                                                     |
| **Email**       | Sends notifications                                                           |
| **CRM**         | Stores customer/lead information                                              |
| **Edge-TTS**    | Converts agent's response text → speech                                       |
| **LiveKit**     | Sends that generated speech back to the caller                                |

```
