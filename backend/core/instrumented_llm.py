from __future__ import annotations

import asyncio
import logging
import os
import random
import time

from livekit.agents import APIConnectionError, APIStatusError
from livekit.plugins import openai
from livekit.agents.llm import ChatContext, ChatChunk, ToolContext

from .circuit_breaker import CircuitBreaker
from .guardrails import validate_llm_output
from .metrics import llm_latency

logger = logging.getLogger(__name__)


class _GuardedStream:
    """Wraps an LLMStream to validate text output against guardrails."""

    def __init__(self, inner: openai.LLMStream):
        self._inner = inner
        self._text_buffer: list[str] = []

    def __aiter__(self):
        return self._guard()

    async def _guard(self):
        async for chunk in self._inner:
            if chunk.content:
                self._text_buffer.append(chunk.content)
                full_text = "".join(self._text_buffer)
                is_safe, category, desc = validate_llm_output(full_text)
                if not is_safe:
                    logger.error(
                        "Guardrail blocked LLM output [%s]: %s. Text so far: %s",
                        category, desc, full_text[:200],
                    )
                    await self._inner.aclose()
                    yield ChatChunk(
                        content=" I apologise, I am unable to respond to that. Let me refocus on your health intake."
                    )
                    return
            yield chunk

    async def aclose(self) -> None:
        await self._inner.aclose()


class InstrumentedOpenAILLM(openai.LLM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._breaker = CircuitBreaker(
            name="openai-llm",
            failure_threshold=int(os.getenv("LLM_CIRCUIT_BREAKER_THRESHOLD", "5")),
            recovery_timeout=float(os.getenv("LLM_CIRCUIT_BREAKER_TIMEOUT", "60")),
        )

    async def chat(
        self,
        *,
        chat_ctx: ChatContext,
        fnc_ctx: ToolContext | None = None,
        temperature: float | None = None,
        n: int | None = 1,
        parallel_tool_calls: bool | None = None,
    ) -> openai.LLMStream:
        if not await self._breaker.allow_request():
            raise APIConnectionError("llm circuit breaker open")

        max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
        base_delay = float(os.getenv("LLM_RETRY_BASE_DELAY", "1.0"))

        for attempt in range(max_retries):
            start = time.monotonic()
            try:
                stream = await super().chat(
                    chat_ctx=chat_ctx,
                    fnc_ctx=fnc_ctx,
                    temperature=temperature,
                    n=n,
                    parallel_tool_calls=parallel_tool_calls,
                )
                llm_latency.observe(time.monotonic() - start)
                await self._breaker.record_success()
                return _GuardedStream(stream)
            except (APIStatusError, APIConnectionError) as exc:
                is_retryable = isinstance(exc, APIConnectionError) or (
                    isinstance(exc, APIStatusError)
                    and exc.status_code in {429, 500, 502, 503, 504}
                )
                if is_retryable and attempt < max_retries - 1:
                    delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        "LLM attempt %d/%d failed: %s. Retrying in %.2fs...",
                        attempt + 1,
                        max_retries,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                await self._breaker.record_failure()
                raise

        await self._breaker.record_failure()
        raise APIConnectionError("llm chat failed after all retries")
