from __future__ import annotations

import logging
import struct
import time
from typing import Any
from uuid import uuid4

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

from .metrics import tts_latency

logger = logging.getLogger(__name__)


def _parse_wav_header(data: bytes) -> tuple[int, int, int, int]:
    if len(data) < 12:
        raise ValueError("Buffer too small for WAV header")
    if data[0:4] != b"RIFF":
        raise ValueError("Not a WAV file: missing RIFF")
    if data[8:12] != b"WAVE":
        raise ValueError("Not a WAV file: missing WAVE")

    sample_rate = 16000
    num_channels = 1
    bits_per_sample = 16
    data_offset = 0

    offset = 12
    while offset + 8 <= len(data):
        chunk_id = data[offset : offset + 4]
        chunk_size = struct.unpack_from("<I", data, offset + 4)[0]
        if chunk_id == b"fmt ":
            if offset + 24 <= len(data):
                num_channels = struct.unpack_from("<H", data, offset + 10)[0]
                sample_rate = struct.unpack_from("<I", data, offset + 12)[0]
                bits_per_sample = struct.unpack_from("<H", data, offset + 22)[0]
        elif chunk_id == b"data":
            data_offset = offset + 8
            break
        offset += 8 + chunk_size
        if chunk_size % 2:
            offset += 1

    if data_offset == 0:
        raise ValueError("No data chunk found in WAV header")

    return sample_rate, num_channels, bits_per_sample, data_offset


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
        stream_base_url: str = "https://api.sarvam.ai/text-to-speech/stream",
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=True),
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
        self._stream_base_url = stream_base_url
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

        text_preview = self.input_text[:80]
        logger.info("Starting TTS stream for text=%r", text_preview)

        request_start = time.monotonic()

        try:
            async with session.post(
                self._tts._stream_base_url,
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
                        "sarvam tts stream request failed",
                        status_code=response.status,
                        request_id=response.headers.get("x-request-id"),
                        body=body,
                        retryable=response.status in {429, 500, 502, 503, 504},
                    )

                request_id = str(uuid4())
                header_parsed = False

                async for chunk in response.content.iter_chunked(65536):
                    if not chunk:
                        continue
                    if not header_parsed:
                        ttfa = time.monotonic() - request_start
                        tts_latency.observe(ttfa)
                        logger.info(
                            "TTS first audio chunk received in %.3fs for text=%r",
                            ttfa,
                            text_preview,
                        )

                        sample_rate, num_channels, _, data_offset = _parse_wav_header(chunk)
                        output_emitter.initialize(
                            request_id=request_id,
                            sample_rate=sample_rate,
                            num_channels=num_channels,
                            mime_type="audio/L16",
                        )
                        pcm_data = chunk[data_offset:]
                        if pcm_data:
                            output_emitter.push(pcm_data)
                        header_parsed = True
                    else:
                        output_emitter.push(chunk)

                logger.info("TTS stream finished for text=%r", text_preview)
        except aiohttp.ClientError as exc:
            logger.error("TTS stream connection error for text=%r: %s", text_preview, exc)
            raise APIConnectionError("sarvam tts connection failed") from exc

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
