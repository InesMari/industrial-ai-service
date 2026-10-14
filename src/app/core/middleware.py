from typing import override
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestIdMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:12])
        request.state.request_id = request_id

        logger.info(
            f"{request.method} {request.url.path}",
            extra={"request_id": request_id},
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response