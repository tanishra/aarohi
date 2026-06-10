from __future__ import annotations

import asyncio
import logging
import os
import random
import time

from livekit.agents import APIConnectionError, APIStatusError
from livekit.plugins import openai
from livekit.agents.llm import ChatContext, ToolContext

from .circuit_breaker import CircuitBreaker
from .metrics import llm_latency

logger = logging.getLogger(__name__)


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
        if not self._breaker.allow_request():
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
                self._breaker.record_success()
                return stream
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
                self._breaker.record_failure()
                raise
