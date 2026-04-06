from __future__ import annotations

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI

# Use Redis for distributed rate limiting if configured
# In-memory fallback if Redis is unavailable
REDIS_URL = os.environ.get("REDIS_URL")

if REDIS_URL:
    limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)
else:
    limiter = Limiter(key_func=get_remote_address)


# ── Rate Limit Presets ───────────────────────────────────────────────────────
GLOBAL_LIMIT = os.getenv("RATE_LIMIT_GLOBAL", "60/minute")
DETECT_LIMIT = os.getenv("RATE_LIMIT_DETECT", "5/minute")
AUTH_LIMIT = os.getenv("RATE_LIMIT_AUTH", "10/minute")


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting for the entire FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
