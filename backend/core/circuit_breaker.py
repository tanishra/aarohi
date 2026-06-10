from __future__ import annotations

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
        self.failure_threshold = failure_threshold or int(
            _env("CIRCUIT_BREAKER_THRESHOLD", "3")
        )
        self.recovery_timeout = recovery_timeout or float(
            _env("CIRCUIT_BREAKER_TIMEOUT", "300")
        )
        self.failure_count = 0
        self._last_failure_time = 0.0
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        self.failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self._last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            logger.warning(
                "Circuit breaker '%s' OPEN after %d failures (timeout=%.0fs)",
                self.name,
                self.failure_count,
                self.recovery_timeout,
            )
            self._state = CircuitState.OPEN
