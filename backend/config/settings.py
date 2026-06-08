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
class SarvamConfig:
    api_key: str
    model: str
    speaker: str
    target_language_code: str
    sample_rate: int
    pace: float
    temperature: float
    base_url: str
    stream_base_url: str


@dataclass(frozen=True)
class SpatiusConfig:
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
    sarvam: SarvamConfig
    spatius: SpatiusConfig
    agent: AgentConfig
    jwt_secret_key: str


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
        sarvam=SarvamConfig(
            api_key=require("SARVAM_API_KEY"),
            model=optional("SARVAM_TTS_MODEL", "bulbul:v3") or "bulbul:v3",
            speaker=optional("SARVAM_TTS_SPEAKER", "priya") or "priya",
            target_language_code=optional("SARVAM_TTS_LANGUAGE", "auto") or "auto",
            sample_rate=int(optional("SARVAM_TTS_SAMPLE_RATE", "24000") or "24000"),
            pace=float(optional("SARVAM_TTS_PACE", "0.92") or "0.92"),
            temperature=float(optional("SARVAM_TTS_TEMPERATURE", "0.6") or "0.6"),
            base_url=optional("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")
            or "https://api.sarvam.ai/text-to-speech",
            stream_base_url=optional(
                "SARVAM_TTS_STREAM_URL", "https://api.sarvam.ai/text-to-speech/stream"
            )
            or "https://api.sarvam.ai/text-to-speech/stream",
        ),
        spatius=SpatiusConfig(
            enabled=(optional("SPATIUS_ENABLED", "true") or "true").lower() != "false",
        ),
        agent=AgentConfig(
            name=optional("LIVEKIT_AGENT_NAME", "voice-assistant") or "voice-assistant",
            default_room=optional("DEFAULT_ROOM_NAME", "voice-agent-room") or "voice-agent-room",
            language=optional("DEFAULT_LANGUAGE", "en") or "en",
        ),
        jwt_secret_key=require("JWT_SECRET_KEY"),
    )
