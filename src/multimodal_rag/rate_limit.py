"""SlowAPI limiter for the public API.

The limiter is attached to FastAPI in ``app.py``; individual routes use the
``@limiter.limit`` decorator. The default strategy is a per-IP sliding window
of ``RATE_LIMIT_PER_MINUTE`` requests; override per-route as needed.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from multimodal_rag.config import get_settings


def _get_limiter_key() -> str:
    """Return the configured limit as ``"N/minute"``."""
    s = get_settings()
    return f"{s.rate_limit_per_minute}/minute"


limiter = Limiter(key_func=get_remote_address, default_limits=[_get_limiter_key()])
