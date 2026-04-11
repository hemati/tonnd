"""Audit logging middleware — logs all /api/v1/ requests without blocking responses."""

import asyncio
import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.services.audit_service import log_api_access

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if request.url.path.startswith("/api/v1/"):
            # Fire-and-forget — don't block the response on the DB write
            asyncio.create_task(_safe_audit(request, response))

        return response


async def _safe_audit(request: Request, response: Response) -> None:
    try:
        await log_api_access(request, response)
    except Exception:
        logger.exception("Failed to write audit log")
