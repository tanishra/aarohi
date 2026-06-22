import asyncio
import time

from core.circuit_breaker import CircuitBreaker, CircuitState


def _run(coro):
    return asyncio.run(coro)


def test_initial_state():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert _run(cb.allow_request()) is True


def test_allow_request_when_closed():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    assert _run(cb.allow_request()) is True


def test_opens_after_threshold_failures():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    _run(cb.record_failure())
    assert _run(cb.allow_request()) is True
    _run(cb.record_failure())
    assert _run(cb.allow_request()) is True
    _run(cb.record_failure())
    assert cb.state == CircuitState.OPEN
    assert _run(cb.allow_request()) is False


def test_success_resets_counter():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    _run(cb.record_failure())
    _run(cb.record_failure())
    assert cb.failure_count == 2
    _run(cb.record_success())
    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED


def test_half_open_after_recovery():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)
    _run(cb.record_failure())
    assert cb.state == CircuitState.OPEN
    assert _run(cb.allow_request()) is False
    time.sleep(0.02)
    assert _run(cb.allow_request()) is True


def test_success_in_half_open_closes():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)
    _run(cb.record_failure())
    time.sleep(0.02)
    assert _run(cb.allow_request()) is True  # transitions to HALF_OPEN
    _run(cb.record_success())
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_failure_in_half_open_reopens():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)
    _run(cb.record_failure())
    time.sleep(0.02)
    assert _run(cb.allow_request()) is True  # transitions to HALF_OPEN
    _run(cb.record_failure())
    assert cb.state == CircuitState.OPEN
    assert _run(cb.allow_request()) is False


def test_custom_threshold():
    cb = CircuitBreaker(name="test", failure_threshold=5, recovery_timeout=60)
    for _ in range(4):
        _run(cb.record_failure())
    assert cb.state != CircuitState.OPEN
    _run(cb.record_failure())
    assert cb.state == CircuitState.OPEN


def test_custom_timeout():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.5)
    _run(cb.record_failure())
    assert _run(cb.allow_request()) is False
    time.sleep(0.6)
    assert _run(cb.allow_request()) is True


def test_explicit_config():
    cb = CircuitBreaker(name="explicit-test", failure_threshold=4, recovery_timeout=120)
    assert cb.failure_threshold == 4
    assert cb.recovery_timeout == 120


def test_zero_threshold_opens_immediately():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)
    _run(cb.record_failure())
    assert cb.state == CircuitState.OPEN


def test_record_success_after_open():
    cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)
    _run(cb.record_failure())
    assert cb.state == CircuitState.OPEN
    _run(cb.record_success())
    assert cb.state == CircuitState.CLOSED


def test_multiple_open_close_cycles():
    cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.01)
    for _ in range(3):
        for _ in range(2):
            _run(cb.record_failure())
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        _run(cb.record_success())
        assert cb.state == CircuitState.CLOSED


def test_failure_count_tracking():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
    assert cb.failure_count == 0
    _run(cb.record_failure())
    assert cb.failure_count == 1
    _run(cb.record_failure())
    assert cb.failure_count == 2
    _run(cb.record_success())
    assert cb.failure_count == 0
