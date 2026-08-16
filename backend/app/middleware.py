"""Middleware de seguridad: rate limiting por IP + request ID tracking."""

import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("carnetruck.security")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter simple en memoria (suficiente para una instancia).
    
    Para producción con múltiples instancias, usar Redis o API Gateway.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        now = time.time()
        cutoff = now - self.window_seconds

        # Limpiar requests viejos
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > cutoff
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas peticiones. Intenta de nuevo en un minuto."},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Agrega X-Request-Id a cada respuesta para trazabilidad."""

    async def dispatch(self, request: Request, call_next):
        import uuid

        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4())[:8])
        start = time.time()

        response = await call_next(request)

        duration_ms = round((time.time() - start) * 1000, 1)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} "
            f"({duration_ms}ms) [{request_id}]"
        )
        return response
