"""
FastAPI wrapper for the Week 6 AFL agent (src/agent.py).

Run locally (Windows-friendly, no shell-specific syntax required):

    uvicorn main:app --reload --port 8000

Then either open http://127.0.0.1:8000/docs for the interactive Swagger UI,
or POST directly:

    POST http://127.0.0.1:8000/chat
    {
        "message": "Will Collingwood beat Geelong this week?",
        "conversation_id": "demo-1"
    }
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.agent import ask_agent

app = FastAPI(
    title="AFL Assistant API",
    description="Domain-scoped AFL chat, retrieval, and prediction agent.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message.")
    conversation_id: str = Field(
        default="default",
        description=(
            "Stable identifier for the conversation. Reusing the same "
            "conversation_id across calls preserves multi-turn memory "
            "(e.g. follow-up questions like 'what were his stats?')."
        ),
    )


class ToolCallRecord(BaseModel):
    name: str
    status: str
    latency_ms: float
    error: str | None = None


class PredictionMetadata(BaseModel):
    used_prediction_tool: bool
    tools_called: list[ToolCallRecord] = []


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    status: str
    model_used: str | None = None
    latency_ms: float | None = None
    prediction_metadata: PredictionMetadata
    error: str | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Single conversational turn. Preserves history per conversation_id.

    Status values:
      - "ok"            : normal successful turn
      - "tool_error"     : agent responded, but one or more tool calls failed
                            (e.g. unrecognized team name) -- not a server error
      - "rate_limited"   : conversation_id exceeded the request-rate guardrail
      - "invalid_input"  : message failed basic validation (e.g. too long)
      - "agent_error"    : unexpected failure; response is a safe fallback message
    """

    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="message must not be empty.")

    result = ask_agent(request.message, thread_id=request.conversation_id)

    return ChatResponse(
        response=result["response"],
        conversation_id=request.conversation_id,
        status=result["status"],
        model_used=result.get("model_used"),
        latency_ms=result.get("latency_ms"),
        prediction_metadata=PredictionMetadata(
            used_prediction_tool=result.get("used_prediction_tool", False),
            tools_called=[
                ToolCallRecord(**call) for call in result.get("tools_called", [])
            ],
        ),
        error=result.get("error"),
    )


@app.get("/health")
def health():
    """Basic liveness check for uptime monitoring."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Minimal optional UI (single static page, no build step -- keeps this
# runnable on Windows with just `uvicorn main:app`)
# ---------------------------------------------------------------------------

_UI_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>AFL Assistant</title>
  <meta charset="utf-8" />
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; background:#0f172a; color:#e2e8f0; }
    h1 { font-size: 1.3rem; }
    #log { border: 1px solid #334155; border-radius: 8px; padding: 12px; height: 420px; overflow-y: auto; background:#1e293b; }
    .msg { margin: 8px 0; padding: 8px 12px; border-radius: 8px; max-width: 80%; }
    .user { background:#2563eb; margin-left:auto; text-align:right; }
    .bot { background:#334155; }
    .meta { font-size: 0.75rem; color:#94a3b8; margin-top:4px; }
    form { display:flex; gap:8px; margin-top:12px; }
    input { flex:1; padding:8px; border-radius:6px; border:1px solid #334155; background:#0f172a; color:#e2e8f0; }
    button { padding:8px 16px; border-radius:6px; border:none; background:#2563eb; color:white; cursor:pointer; }
  </style>
</head>
<body>
  <h1>AFL Assistant (Week 6 Day 5 demo)</h1>
  <div id="log"></div>
  <form id="f">
    <input id="msg" placeholder="Ask about AFL teams, players, stats, or predictions..." autocomplete="off" />
    <button type="submit">Send</button>
  </form>
  <script>
    const conversationId = "ui-" + Math.random().toString(36).slice(2);
    const log = document.getElementById('log');
    const form = document.getElementById('f');
    const input = document.getElementById('msg');

    function addMsg(text, cls, meta) {
      const div = document.createElement('div');
      div.className = 'msg ' + cls;
      div.textContent = text;
      if (meta) {
        const m = document.createElement('div');
        m.className = 'meta';
        m.textContent = meta;
        div.appendChild(m);
      }
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      addMsg(text, 'user');
      input.value = '';

      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: text, conversation_id: conversationId})
        });
        const data = await res.json();
        const meta = `status=${data.status} | model=${data.model_used || 'n/a'} | latency=${data.latency_ms ?? 'n/a'}ms`;
        addMsg(data.response, 'bot', meta);
      } catch (err) {
        addMsg('Request failed: ' + err, 'bot');
      }
    });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def ui():
    return _UI_HTML
