from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend/ is on sys.path so "config", "core" etc. resolve
# regardless of whether you run from project root or backend/
_backend_dir = str(Path(__file__).parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from config.logging import configure_logging, session_id_var

# Load environment variables from .env first so logging config is picked up
load_dotenv()

configure_logging()

from config.settings import load_settings
from core.agents import IntakeAgent
from core.context import SessionContext
from core.database import init_db
from core.instrumented_llm import InstrumentedOpenAILLM
from core.sarvam_tts import SarvamTTS
from core.metrics import sessions_active, sessions_total, turn_count  # noqa: F811

from livekit import agents
from livekit.agents import (
    AgentServer,
    AgentSession,
    AutoSubscribe,
    JobContext,
    room_io,
    cli,
)
from livekit.agents.voice.turn import (
    EndpointingOptions,
    InterruptionOptions,
    TurnHandlingOptions,
)
from livekit.plugins import deepgram, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.spatius import AvatarSession

logger = logging.getLogger(__name__)

# Graceful shutdown flag
_shutting_down = False


def _handle_sigterm(signum: int, frame) -> None:
    global _shutting_down
    _shutting_down = True
    try:
        asyncio.get_running_loop().call_soon(_report_sigterm)
    except RuntimeError:
        pass


def _report_sigterm():
    logger.warning("Received SIGTERM, shutting down gracefully...")


signal.signal(signal.SIGTERM, _handle_sigterm)

# Initialize the local database once at startup
try:
    init_db()
except Exception as exc:
    logger.error("Database init failed: %s", exc)

async def entrypoint(ctx: JobContext) -> None:
    if _shutting_down:
        logger.warning("Server shutting down, rejecting new session")
        return

    settings = load_settings()
    session_start_time = time.monotonic()

    # 1. Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

    # 2. Setup Session Context
    session_ctx = SessionContext(
        language=settings.agent.language,
    )
    session_id_var.set(session_ctx.session_id)

    sessions_active.inc()
    sessions_total.labels(outcome="started").inc()

    logger.info(
        "Session started  id=%s room=%s participant=%s",
        session_ctx.session_id,
        ctx.room.name,
        participant.identity,
    )

    try:
        # 3. Create the agent instance
        agent = IntakeAgent(ctx)
        registered_tools = agent.get_tool_list()
        logger.info(
            "Registering %d tools: %s",
            len(registered_tools),
            [t.info.name for t in registered_tools],
        )

        # 4. Initialize Agent Session with Advanced Options
        session = AgentSession(
            stt=deepgram.STT(
                model=settings.deepgram.stt_model,
                language=settings.deepgram.stt_language,
                api_key=settings.deepgram.api_key,
            ),
            llm=InstrumentedOpenAILLM(
                model=settings.openai.model,
                api_key=settings.openai.api_key,
                parallel_tool_calls=False,
            ),
            tts=SarvamTTS(
                api_key=settings.sarvam.api_key,
                model=settings.sarvam.model,
                speaker=settings.sarvam.speaker,
                target_language_code=settings.sarvam.target_language_code,
                sample_rate=settings.sarvam.sample_rate,
                pace=settings.sarvam.pace,
                temperature=settings.sarvam.temperature,
                base_url=settings.sarvam.base_url,
                stream_base_url=settings.sarvam.stream_base_url,
            ),
            vad=silero.VAD.load(),
            turn_handling=TurnHandlingOptions(
                turn_detection=MultilingualModel(),
                endpointing=EndpointingOptions(
                    mode="fixed",
                    min_delay=0.8,
                ),
                interruption=InterruptionOptions(
                    enabled=True,
                    min_duration=0.3,
                    min_words=1,
                ),
            ),
            max_tool_steps=5,
            userdata=session_ctx,
        )

        # 5. Start the Session with Persona and Audio Enhancement
        await session.start(
            agent=agent,
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(),
            ),
        )

        # 6. Attach SpatialReal Avatar (after session start so the session is active)
        if settings.spatius.enabled:
            try:
                avatar = AvatarSession()
                await avatar.start(session, room=ctx.room)
            except Exception as exc:
                session_ctx.log_error(f"Avatar startup failed: {exc}")
                logger.warning("SpatialReal avatar startup failed: %s", exc)

        # 7. Dynamic Initial Greet using LLM
        from prompts.persona import get_opening_message

        await asyncio.wait_for(
            session.generate_reply(
                instructions=f"Greet the user warmly. Context for the greeting: {get_opening_message()}"
            ),
            timeout=30,
        )

        sessions_total.labels(outcome="finished").inc()
        turn_count.observe(session_ctx.turn_number)
    except Exception:
        sessions_total.labels(outcome="failed").inc()
        raise
    finally:
        sessions_active.dec()


if __name__ == "__main__":
    server = AgentServer()
    server.rtc_session(agent_name="voice-assistant")(entrypoint)
    agents.cli.run_app(server)
