from __future__ import annotations

import base64
from typing import Any

import aiohttp
from livekit.agents import (
    APIConnectOptions,
    APIConnectionError,
    APIStatusError,
    DEFAULT_API_CONNECT_OPTIONS,
    tts,
    utils,
)
from livekit.agents.tts import AudioEmitter


class SarvamTTS(tts.TTS):
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "bulbul:v3",
        speaker: str = "priya",
        target_language_code: str = "hi-IN",
        sample_rate: int = 24000,
        pace: float = 0.92,
        temperature: float = 0.6,
        base_url: str = "https://api.sarvam.ai/text-to-speech",
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )
        self._api_key = api_key
        self._model = model
        self._speaker = speaker
        self._target_language_code = target_language_code
        self._pace = pace
        self._temperature = temperature
        self._base_url = base_url
        self._session = http_session

    @property
    def model(self) -> str:
        return self._model

    @property
    def provider(self) -> str:
        return "Sarvam"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return _SarvamChunkedStream(tts=self, input_text=text, conn_options=conn_options)

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = utils.http_context.http_session()
        return self._session

    async def aclose(self) -> None:
        return None


class _SarvamChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        *,
        tts: SarvamTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts: SarvamTTS = tts

    async def _run(self, output_emitter: AudioEmitter) -> None:
        session = self._tts._ensure_session()
        payload: dict[str, Any] = {
            "text": self.input_text,
            "target_language_code": self._language_for_text(self.input_text),
            "speaker": self._tts._speaker,
            "model": self._tts._model,
            "speech_sample_rate": self._tts.sample_rate,
            "output_audio_codec": "wav",
            "pace": self._tts._pace,
            "temperature": self._tts._temperature,
        }

        try:
            async with session.post(
                self._tts._base_url,
                headers={
                    "api-subscription-key": self._tts._api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self._conn_options.timeout),
            ) as response:
                if response.status < 200 or response.status >= 300:
                    body = await response.text()
                    raise APIStatusError(
                        "sarvam tts request failed",
                        status_code=response.status,
                        request_id=response.headers.get("x-request-id"),
                        body=body,
                        retryable=response.status in {429, 500, 502, 503, 504},
                    )

                data = await response.json()
        except aiohttp.ClientError as exc:
            raise APIConnectionError("sarvam tts connection failed") from exc

        audio_items = data.get("audios") if isinstance(data, dict) else None
        if not audio_items:
            raise APIStatusError("sarvam tts response did not include audio", body=data)

        audio = base64.b64decode(audio_items[0])
        request_id = str(data.get("request_id") or "sarvam-tts")
        output_emitter.initialize(
            request_id=request_id,
            sample_rate=self._tts.sample_rate,
            num_channels=self._tts.num_channels,
            mime_type="audio/wav",
        )
        output_emitter.push(audio)

    def _language_for_text(self, text: str) -> str:
        configured_language = self._tts._target_language_code
        if configured_language.lower() != "auto":
            return configured_language

        script_languages = [
            ("\u0900", "\u097f", "hi-IN"),  # Devanagari: Hindi/Marathi fallback
            ("\u0980", "\u09ff", "bn-IN"),
            ("\u0a00", "\u0a7f", "pa-IN"),
            ("\u0a80", "\u0aff", "gu-IN"),
            ("\u0b00", "\u0b7f", "od-IN"),
            ("\u0b80", "\u0bff", "ta-IN"),
            ("\u0c00", "\u0c7f", "te-IN"),
            ("\u0c80", "\u0cff", "kn-IN"),
            ("\u0d00", "\u0d7f", "ml-IN"),
        ]
        for start, end, language_code in script_languages:
            if any(start <= char <= end for char in text):
                return language_code

        return "en-IN"
