"""Retry with exponential backoff for provider API calls."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")

# Exceptions that indicate a transient failure worth retrying.
# Provider-specific exceptions (e.g., openai.RateLimitError) are added
# to the tuple by each caller rather than imported here to avoid coupling.
TRANSIENT_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    retryable: tuple[type[Exception], ...] = TRANSIENT_NETWORK_ERRORS,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
) -> T:
    """Call ``fn()`` up to ``max_attempts`` times with exponential backoff.

    Only exceptions matching ``retryable`` trigger a retry.  All other
    exceptions propagate immediately.

    Returns the result of ``fn()`` on success.

    Raises the last caught exception if all attempts are exhausted.
    """
    last_exc: Exception | None = None
    delay = base_delay

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retryable as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            log.warning(
                "Attempt %d/%d failed (%s: %s); retrying in %.1fs",
                attempt,
                max_attempts,
                type(exc).__name__,
                exc,
                delay,
            )
            time.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)

    # All attempts exhausted — re-raise the last exception.
    assert last_exc is not None
    raise last_exc
