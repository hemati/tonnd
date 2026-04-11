"""Audit log writer — fire-and-forget logging of API access."""

import logging

from starlette.requests import Request
from starlette.responses import Response

from src.database import async_session_maker
from src.models.api_models import AuditLog

logger = logging.getLogger(__name__)


async def log_api_access(request: Request, response: Response) -> None:
    """Write an audit log entry for an API request."""
    # Extract user/token info from request state (set by auth dependency)
    user_id = getattr(request.state, "audit_user_id", None)
    token_id = getattr(request.state, "audit_token_id", None)

    # Derive action from path
    path = request.url.path
    method = request.method
    action = f"api.{method.lower()}"

    # Client info
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")[:256]

    async with async_session_maker() as session:
        entry = AuditLog(
            user_id=user_id,
            token_id=token_id,
            action=action,
            resource=path,
            method=method,
            ip_address=ip,
            user_agent=ua,
            status_code=response.status_code,
        )
        session.add(entry)
        await session.commit()
