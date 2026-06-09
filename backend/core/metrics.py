from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

tts_latency = Histogram(
    "sarvam_tts_latency_seconds",
    "Time from TTS request start to first audio chunk received",
    buckets=(0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0),
)

llm_latency = Histogram(
    "openai_llm_latency_seconds",
    "Time for OpenAI LLM to respond",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0),
)

tool_calls = Counter(
    "agent_tool_calls_total",
    "Total tool calls by name and status",
    ["tool_name", "status"],
)

sessions_active = Gauge(
    "sessions_active",
    "Currently active voice agent sessions",
)

sessions_total = Counter(
    "sessions_total",
    "Total sessions started, tagged by outcome",
    ["outcome"],
)

turn_count = Histogram(
    "turns_per_session",
    "Number of turns per session",
    buckets=(1, 5, 10, 20, 50),
)
