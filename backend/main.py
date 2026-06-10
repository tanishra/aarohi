from __future__ import annotations

import logging
import os
import time
from dotenv import load_dotenv

from config.logging import configure_logging, session_id_var

configure_logging()

from config.settings import load_settings
from core.agents import IntakeAgent
from core.context import SessionContext
from core.database import init_db
from core.instrumented_llm import InstrumentedOpenAILLM
from core.sarvam_tts import SarvamTTS
from core.metrics import sessions_active, sessions_total, turn_count

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
from livekit.plugins import deepgram, silero, ai_coustics
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.spatius import AvatarSession

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)

# Start Prometheus metrics HTTP server (separate thread)
_prometheus_port = int(os.getenv("METRICS_PORT", "9090"))
try:
    from prometheus_client import start_http_server as _start_metrics

    _start_metrics(_prometheus_port)
    logger.info("Metrics HTTP server started on port %d", _prometheus_port)
except Exception as exc:
    logger.warning("Prometheus metrics server not available: %s", exc)

# High-level Agent Server Pattern
server = AgentServer()


@server.rtc_session(agent_name="voice-assistant")
async def entrypoint(ctx: JobContext) -> None:
    settings = load_settings()
    session_start_time = time.monotonic()

    # Initialize the local database
    try:
        init_db()
    except Exception as exc:
        logger.warning("Database init failed: %s", exc)

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

    # 5. Attach SpatialReal Avatar
    if settings.spatius.enabled:
        try:
            avatar = AvatarSession()
            await avatar.start(session, room=ctx.room)
        except Exception as exc:
            session_ctx.log_error(f"Avatar startup failed: {exc}")
            logger.warning("SpatialReal avatar startup failed: %s", exc)

    # 6. Start the Session with Persona and Audio Enhancement
    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_L
                ),
            ),
        ),
    )

    # 7. Dynamic Initial Greet using LLM
    from prompts.persona import get_opening_message

    await session.generate_reply(
        instructions=f"Greet the user warmly. Context for the greeting: {get_opening_message()}"
    )

    # Session lifecycle continues in the LiveKit agent server;
    # metrics and session_id correlation are active for the session's duration.


if __name__ == "__main__":
    agents.cli.run_app(server)
