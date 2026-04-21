from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value


def optional(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return value


@dataclass(frozen=True)
class LiveKitConfig:
    url: str
    api_key: str
    api_secret: str


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str


@dataclass(frozen=True)
class DeepgramConfig:
    api_key: str
    stt_model: str
    stt_language: str
    tts_model: str


@dataclass(frozen=True)
class SpatialRealConfig:
    enabled: bool = True

@dataclass(frozen=True)
class AgentConfig:
    name: str
    default_room: str
    language: str


@dataclass(frozen=True)
class Settings:
    livekit: LiveKitConfig
    openai: OpenAIConfig
    deepgram: DeepgramConfig
    spatialreal: SpatialRealConfig
    agent: AgentConfig


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        livekit=LiveKitConfig(
            url=require("LIVEKIT_URL"),
            api_key=require("LIVEKIT_API_KEY"),
            api_secret=require("LIVEKIT_API_SECRET"),
        ),
        openai=OpenAIConfig(
            api_key=require("OPENAI_API_KEY"),
            model=optional("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
        ),
        deepgram=DeepgramConfig(
            api_key=require("DEEPGRAM_API_KEY"),
            stt_model=optional("STT_MODEL", "nova-3") or "nova-3",
            stt_language=optional("STT_LANGUAGE", "multi") or "multi",
            tts_model=optional("TTS_VOICE", "aura-asteria-en") or "aura-asteria-en",
        ),
        spatialreal=SpatialRealConfig(
            enabled=(optional("SPATIALREAL_ENABLED", "true") or "true").lower() != "false",
        ),
        agent=AgentConfig(
            name=optional("LIVEKIT_AGENT_NAME", "voice-assistant") or "voice-assistant",
            default_room=optional("DEFAULT_ROOM_NAME", "voice-agent-room") or "voice-agent-room",
            language=optional("DEFAULT_LANGUAGE", "en") or "en",
        ),
    )
