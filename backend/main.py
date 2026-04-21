from __future__ import annotations

import logging
import os
from dotenv import load_dotenv
from config.settings import load_settings
from core.agents import IntakeAgent
from core.context import SessionContext
from core.database import init_db

from livekit import agents
from livekit.agents import (
    AgentServer,
    AgentSession,
    AutoSubscribe,
    JobContext,
    TurnHandlingOptions,
    room_io,
    cli,
)
from livekit.plugins import deepgram, openai, silero, ai_coustics, google
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.spatialreal import AvatarSession

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)

# High-level Agent Server Pattern
server = AgentServer()

@server.rtc_session(agent_name="voice-assistant")
async def entrypoint(ctx: JobContext) -> None:
    settings = load_settings()
    
    # Initialize the local database
    init_db()

    # 1. Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info("Participant joined: %s", participant.identity)

    # 2. Setup Session Context and Agent
    session_ctx = SessionContext(
        language=settings.agent.language,
    )
    
    # Create the agent instance first so we can access its tools
    agent = IntakeAgent(ctx)
    registered_tools = agent.get_tool_list()
    logger.info(f"Registering {len(registered_tools)} tools: {[t.info.name for t in registered_tools]}")

    # 3. Initialize Agent Session with Advanced Options
    session = AgentSession(
        stt=deepgram.STT(
            model=settings.deepgram.stt_model,
            language=settings.deepgram.stt_language,
            api_key=settings.deepgram.api_key,
        ),
        llm=openai.LLM(
            model=settings.openai.model,
            api_key=settings.openai.api_key,
            parallel_tool_calls=False, # Force sequential for reliable nurse workflow
        ),
        tts=deepgram.TTS(
            model=settings.deepgram.tts_model,
            api_key=settings.deepgram.api_key,
        ),
        vad=silero.VAD.load(),
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
        ),
        # Removed redundant tools registration here as they are inside the agent
        max_tool_steps=5, # Allow more steps if summary + submission are handled
        userdata=session_ctx,
    )

    # 4. Attach SpatialReal Avatar
    if settings.spatialreal.enabled:
        try:
            avatar = AvatarSession()
            await avatar.start(session, room=ctx.room)
        except Exception as exc:
            logger.warning("SpatialReal avatar startup failed: %s", exc)

    # 5. Start the Session with Persona and Audio Enhancement
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

    # 6. Dynamic Initial Greet using LLM
    from prompts.persona import get_opening_message
    await session.generate_reply(
        instructions=f"Greet the user warmly. Context for the greeting: {get_opening_message()}"
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
