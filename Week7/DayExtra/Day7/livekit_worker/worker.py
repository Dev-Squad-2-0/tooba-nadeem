"""
app/livekit_worker/worker.py
--------------------------------

LiveKit Agents worker entrypoint. This is a NEW, PARALLEL front door to
the existing agent -- app/voice/pipeline.py (the FastAPI WebSocket voice
path) is completely untouched and keeps working.

Bridges:
  STT:  livekit.plugins.deepgram (OFFICIAL plugin, no adapter needed) --
        reuses config.DEEPGRAM_API_KEY / DEEPGRAM_MODEL / DEEPGRAM_LANGUAGE,
        the exact same env vars app/voice/stt_deepgram.py already uses.
  Brain: RealEstateAgent.llm_node() below calls the EXISTING
        app.graph.agent_graph.handle_turn() directly -- the real
        LangGraph pipeline (RAG, recommendations, memory, appointment
        tools), completely unduplicated.
  TTS:  app/livekit_worker/tts_adapter.py:EdgeTTS -- wraps the EXISTING
        app/voice/tts_edge.py, since no official LiveKit Edge-TTS plugin
        exists (confirmed).

Run with (from project root, venv active):
    python -m app.livekit_worker.worker dev

NOT YET WIRED (flagging honestly, not silently skipping):
  - VAD: livekit-plugins-silero is NOT confirmed installed in your
    environment (only livekit-agents and livekit-plugins-deepgram were
    mentioned). Without a VAD, interruption handling (the user talking
    over the agent) will be degraded. Install with:
        pip install livekit-plugins-silero
    and uncomment the vad= line below once confirmed installed.
  - Turn detection model (livekit-plugins-turn-detector) -- same status,
    optional for a first connectivity test, recommended before real use.
"""

import logging

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, llm
from livekit.plugins import deepgram

# from livekit.plugins import silero  # uncomment once installed -- see docstring above

from app import config
from app.graph.agent_graph import handle_turn
from app.livekit_worker.tts_adapter import EdgeTTS

logger = logging.getLogger("livekit_worker")

server = AgentServer()


class _NoOpLLM(llm.LLM):
    """
    Minimal placeholder to satisfy AgentSession's hard requirement that
    session.llm is not None (see AgentActivity._generate_reply:
    `if self.llm is None: raise RuntimeError("trying to generate reply
    without an LLM model")` -- this check is unconditional and runs
    before any node logic, so it fires even with llm_node overridden).

    RealEstateAgent.llm_node() below is FULLY overridden and routes ALL
    real generation through the existing LangGraph handle_turn(). Per
    Agent.llm_node's own docstring, the default llm_node is what calls
    self.llm.chat() -- overriding it bypasses that call entirely. So
    this class's chat() should NEVER actually execute. It raises rather
    than silently no-op-ing specifically so that if this assumption is
    ever wrong, you get a clear, loud error pointing here -- not a
    silent wrong behavior somewhere else.
    """

    def chat(self, *, chat_ctx, tools=None, conn_options=None, **kwargs):
        raise NotImplementedError(
            "_NoOpLLM.chat() was called directly -- this should never "
            "happen, since RealEstateAgent.llm_node() is overridden and "
            "should intercept before LiveKit's pipeline reaches this "
            "point. If you're seeing this, the llm_node override isn't "
            "being invoked the way this fix assumed -- report the full "
            "traceback before changing anything else."
        )


# Static greeting spoken via TTS directly (AgentSession.say), NOT via
# generate_reply()/an LLM -- with no real LLM configured, there is
# nothing to generate this text FROM. This exact wording is new (matches
# the existing SALES_SYSTEM_PROMPT persona's tone, but doesn't come from
# prompts.py) -- if you want the greeting itself to flow through
# handle_turn() instead of being a fixed string, that's a separate,
# larger change from this checkpoint.
GREETING_TEXT = (
    "Assalam-o-Alaikum! Main Ahmed baat kar raha hoon Meridian Homes "
    "Pakistan se. Aap ko kis property mein interest hai?"
)


class RealEstateAgent(Agent):
    """
    Bridges LiveKit's pipeline to the EXISTING business logic. Overriding
    llm_node (LiveKit's documented, recommended pattern for fully custom
    "bring your own brain" logic) rather than implementing a full custom
    llm.LLM class -- this is the lighter-weight, officially recommended
    integration point for exactly this situation.
    """

    def __init__(self, room_name: str) -> None:
        super().__init__(
            instructions=(
                "You are Ahmed, a Meridian Homes Pakistan real estate "
                "sales executive."  # Not actually used for generation --
                # llm_node below bypasses LiveKit's own prompt construction
                # entirely and calls our real SALES_SYSTEM_PROMPT-driven
                # handle_turn() instead. Kept non-empty because Agent's
                # constructor requires SOME instructions string.
            )
        )
        # AgentSession has no `.room` attribute (confirmed via dir() --
        # not in its public API), so it can't be read back out inside
        # llm_node. ctx.room IS valid at entrypoint time (it's literally
        # what's passed into session.start(room=ctx.room, ...)), so it's
        # captured there and passed in directly instead.
        self._session_id = room_name

    async def llm_node(self, chat_ctx: llm.ChatContext, tools, model_settings=None):
        """
        Called by AgentSession once per user turn, after STT produces a
        final transcript. chat_ctx's last user message IS that
        transcript. Returns the reply as plain text -- LiveKit's session
        handles passing it to TTS.
        """
        session_id = self._session_id

        user_messages = [m for m in chat_ctx.items if getattr(m, "role", None) == "user"]
        if not user_messages:
            yield ""
            return

        last_message = user_messages[-1]
        message_text = getattr(last_message, "text_content", None) or str(last_message.content)

        logger.info("[LIVEKIT] session=%s user_message=%r", session_id, message_text)

        import asyncio
        response_text = await asyncio.to_thread(handle_turn, session_id, message_text)

        logger.info("[LIVEKIT] session=%s agent_response=%r", session_id, response_text)

        yield response_text


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        llm=_NoOpLLM(),
        stt=deepgram.STT(
            model=config.DEEPGRAM_MODEL,
            language=config.DEEPGRAM_LANGUAGE,
            api_key=config.DEEPGRAM_API_KEY,
        ),
        tts=EdgeTTS(),
        # vad=silero.VAD.load(),  # uncomment once livekit-plugins-silero is installed
    )

    await session.start(room=ctx.room, agent=RealEstateAgent(room_name=ctx.room.name))

    await session.say(GREETING_TEXT)


if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)