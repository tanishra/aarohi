from __future__ import annotations

import asyncio
import logging
import os
import time
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        name: str = "",
        failure_threshold: int | None = None,
        recovery_timeout: float | None = None,
        env_prefix: str = "",
    ) -> None:
        def _env(key: str, default: str) -> str:
            return os.getenv(f"{env_prefix}_{key}" if env_prefix else key, default)

        self.name = name
        self.failure_threshold = max(1, failure_threshold if failure_threshold is not None else int(
            _env("CIRCUIT_BREAKER_THRESHOLD", "3")
        ))
        self.recovery_timeout = recovery_timeout or float(
            _env("CIRCUIT_BREAKER_TIMEOUT", "300")
        )
        self.failure_count = 0
        self._last_failure_time = 0.0
        self._state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
        self._probe_sent = False

    @property
    def state(self) -> CircuitState:
        return self._state

    async def allow_request(self) -> bool:
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._probe_sent = False
            if self._state == CircuitState.HALF_OPEN:
                if self._probe_sent:
                    return False
                self._probe_sent = True
                return True
            return self._state != CircuitState.OPEN

    async def record_success(self) -> None:
        async with self._lock:
            self.failure_count = 0
            self._state = CircuitState.CLOSED
            self._probe_sent = False

    async def record_failure(self) -> None:
        async with self._lock:
            self.failure_count += 1
            self._last_failure_time = time.monotonic()
            self._probe_sent = False
            if self.failure_count >= self.failure_threshold:
                logger.warning(
                    "Circuit breaker '%s' OPEN after %d failures (timeout=%.0fs)",
                    self.name,
                    self.failure_count,
                    self.recovery_timeout,
                )
                self._state = CircuitState.OPEN
