from __future__ import annotations

import time

from livekit.plugins import openai
from livekit.agents.llm import ChatContext, ToolContext

from .metrics import llm_latency


class InstrumentedOpenAILLM(openai.LLM):
    async def chat(
        self,
        *,
        chat_ctx: ChatContext,
        fnc_ctx: ToolContext | None = None,
        temperature: float | None = None,
        n: int | None = 1,
        parallel_tool_calls: bool | None = None,
    ) -> openai.LLMStream:
        start = time.monotonic()
        stream = await super().chat(
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
            temperature=temperature,
            n=n,
            parallel_tool_calls=parallel_tool_calls,
        )
        llm_latency.observe(time.monotonic() - start)
        return stream
