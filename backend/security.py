from __future__ import annotations

import logging
import time
import uuid
from typing import Callable, Awaitable
from pyproj import CRS, Transformer
from shapely import wkt
from shapely.errors import WKTReadingError

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# ── Structured JSON Logger ───────────────────────────────────────────────────
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger("sentinelx.api")


# ── Middleware ───────────────────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects OWASP recommended security headers into every response.
    """
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming request with a unique trace ID and execution time.
    """
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        start_time = time.time()
        
        # We don't log the body here because it consumes the stream.
        # Action-specific logging should happen inside the route handlers.
        logger.info("request_started", 
            trace_id=trace_id, 
            method=request.method, 
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown"
        )
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger.info("request_finished", 
                trace_id=trace_id, 
                status_code=response.status_code, 
                process_time_ms=f"{process_time:.2f}"
            )
            response.headers["X-Trace-Id"] = trace_id
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error("request_failed", 
                trace_id=trace_id, 
                error=str(e), 
                process_time_ms=f"{process_time:.2f}"
            )
            raise


# ── WKT Sanitization ─────────────────────────────────────────────────────────
def sanitize_wkt(wkt_str: str) -> str:
    """
    Validates that a WKT string is mathematically valid and represents a Polygon/MultiPolygon.
    Raises ValueError if invalid, mitigating SQL injection via PostGIS geometry functions.
    """
    try:
        geom = wkt.loads(wkt_str)
    except WKTReadingError:
        raise ValueError("Invalid WKT format.")
        
    if not geom.is_valid:
        geom = geom.buffer(0) # Attempt self-intersection fix
        if not geom.is_valid:
            raise ValueError("Geometry is topologically invalid (e.g., self-intersecting).")

    if geom.geom_type not in ["Polygon", "MultiPolygon"]:
        raise ValueError(f"Only Polygon and MultiPolygon are supported, got {geom.geom_type}.")

    # Restrict total vertices to prevent ReDoS / CPU exhaustion in PostGIS
    coords = list(geom.exterior.coords) if geom.geom_type == "Polygon" else []
    if geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            coords.extend(list(poly.exterior.coords))
            
    if len(coords) > 500:
        raise ValueError("Geometry contains too many vertices (max 500).")

    return geom.wkt
