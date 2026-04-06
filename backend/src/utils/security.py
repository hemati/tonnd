"""
Shared security utilities for Lambda handlers.
Provides event sanitization, input validation, and OAuth state management.
"""

import hashlib
import hmac
import logging
import os
import re
import secrets
import time
import warnings
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# State token secret - MUST be set via environment variable in production
STATE_SECRET = os.environ.get("STATE_SECRET")
if not STATE_SECRET:
    warnings.warn(
        "STATE_SECRET not set! Using random value. Set via SSM in production."
    )
    STATE_SECRET = secrets.token_urlsafe(32)

STATE_EXPIRY_SECONDS = 600  # 10 minutes


def sanitize_event_for_logging(event: dict) -> dict:
    """
    Remove sensitive data from API Gateway event before logging.

    Redacts:
    - Authorization headers
    - Cookie headers
    - JWT claims in requestContext

    Args:
        event: API Gateway event dict

    Returns:
        Sanitized copy of the event
    """
    sanitized = event.copy()

    # Redact authorization and cookie headers
    if "headers" in sanitized:
        headers = sanitized["headers"].copy()
        sensitive_headers = ["authorization", "Authorization", "cookie", "Cookie"]
        for key in sensitive_headers:
            if key in headers:
                headers[key] = "[REDACTED]"
        sanitized["headers"] = headers

    # Redact JWT claims from requestContext
    if "requestContext" in sanitized:
        rc = sanitized["requestContext"].copy()
        if "authorizer" in rc:
            rc["authorizer"] = "[REDACTED]"
        sanitized["requestContext"] = rc

    return sanitized


def generate_secure_state(user_id: str) -> str:
    """
    Generate a cryptographically secure OAuth state parameter.

    Format: user_id:timestamp:nonce:signature
    - Signature prevents tampering
    - Timestamp prevents replay attacks
    - Nonce adds additional entropy

    Args:
        user_id: User ID to embed in state

    Returns:
        Secure state string
    """
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(8)

    message = f"{user_id}:{timestamp}:{nonce}"
    signature = hmac.new(
        STATE_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()[:16]

    return f"{message}:{signature}"


def validate_secure_state(state: str) -> Tuple[str, bool]:
    """
    Validate an OAuth state parameter and extract the user_id.

    Args:
        state: State string to validate

    Returns:
        Tuple of (user_id, is_valid)
    """
    try:
        parts = state.split(":")
        if len(parts) != 4:
            logger.warning("Invalid state format: wrong number of parts")
            return "", False

        user_id, timestamp_str, nonce, provided_signature = parts

        # Check timestamp (prevent replay attacks)
        timestamp = int(timestamp_str)
        current_time = int(time.time())
        if current_time - timestamp > STATE_EXPIRY_SECONDS:
            logger.warning(f"State expired: {current_time - timestamp} seconds old")
            return "", False

        # Verify HMAC signature
        message = f"{user_id}:{timestamp_str}:{nonce}"
        expected_signature = hmac.new(
            STATE_SECRET.encode(), message.encode(), hashlib.sha256
        ).hexdigest()[:16]

        if not hmac.compare_digest(provided_signature, expected_signature):
            logger.warning("State signature mismatch")
            return "", False

        return user_id, True

    except Exception as e:
        logger.warning(f"State validation error: {e}")
        return "", False


def validate_date_format(date_str: str) -> bool:
    """
    Validate date string format YYYY-MM-DD.

    Args:
        date_str: Date string to validate

    Returns:
        True if valid, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_integer_param(
    value: Optional[str],
    default: int,
    min_val: int = 1,
    max_val: int = 100,
) -> int:
    """
    Safely parse and validate an integer parameter.

    Args:
        value: String value to parse
        default: Default value if parsing fails
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Validated integer within bounds
    """
    if value is None:
        return default
    try:
        parsed = int(value)
        return max(min_val, min(parsed, max_val))
    except (ValueError, TypeError):
        return default
