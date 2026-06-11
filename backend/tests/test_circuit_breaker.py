import os
import time
from unittest.mock import patch

from core.circuit_breaker import CircuitBreaker, CircuitState


def test_initial_state():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.allow_request() is True


def test_allow_request_when_closed():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    assert cb.allow_request() is True


def test_opens_after_threshold_failures():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    cb.record_failure()
    assert cb.allow_request() is True
    cb.record_failure()
    assert cb.allow_request() is True
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False


def test_success_resets_counter():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    cb.record_failure()
    cb.record_failure()
    assert cb.failure_count == 2
    cb.record_success()
    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED


def test_half_open_after_recovery():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False
    time.sleep(0.02)
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.allow_request() is True


def test_success_in_half_open_closes():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)
    cb.record_failure()
    time.sleep(0.02)
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_failure_in_half_open_reopens():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)
    cb.record_failure()
    time.sleep(0.02)
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False


def test_custom_threshold():
    cb = CircuitBreaker(name="test", failure_threshold=5, recovery_timeout=60)
    for _ in range(4):
        cb.record_failure()
    assert cb.state != CircuitState.OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN


def test_custom_timeout():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.5)
    cb.record_failure()
    assert cb.allow_request() is False
    time.sleep(0.6)
    assert cb.allow_request() is True


def test_env_based_config():
    with patch.dict(os.environ, {
        "MYAPP_CIRCUIT_BREAKER_THRESHOLD": "4",
        "MYAPP_CIRCUIT_BREAKER_TIMEOUT": "120",
    }):
        cb = CircuitBreaker(name="env-test", env_prefix="MYAPP")
        assert cb.failure_threshold == 4
        assert cb.recovery_timeout == 120


def test_zero_threshold_opens_immediately():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN


def test_record_success_after_open():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_multiple_open_close_cycles():
    cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.01)
    for _ in range(3):
        for _ in range(2):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        cb.record_success()
        assert cb.state == CircuitState.CLOSED


def test_failure_count_tracking():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    assert cb.failure_count == 0
    cb.record_failure()
    assert cb.failure_count == 1
    cb.record_failure()
    assert cb.failure_count == 2
    cb.record_success()
    assert cb.failure_count == 0
