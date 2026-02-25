"""Exception hierarchy for jsondb.cloud API errors."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class JsonDBError(Exception):
    """Base error class for all jsondb.cloud API errors.

    Attributes:
        message: Human-readable error message.
        code: Machine-readable error code (e.g. ``"DOCUMENT_NOT_FOUND"``).
        status: HTTP status code that triggered this error.
        details: Additional error details from the API response.
    """

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN",
        status: int = 0,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.details: Dict[str, Any] = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r}, status={self.status})"


class NotFoundError(JsonDBError):
    """Raised when a requested document or resource is not found (HTTP 404)."""

    def __init__(self, message: str = "Not found", document_id: Optional[str] = None) -> None:
        super().__init__(message, code="DOCUMENT_NOT_FOUND", status=404)
        self.document_id = document_id


class ConflictError(JsonDBError):
    """Raised when a write conflicts with an existing document (HTTP 409)."""

    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, code="CONFLICT", status=409)


class ValidationError(JsonDBError):
    """Raised when a document fails schema validation (HTTP 400).

    Attributes:
        errors: List of individual validation errors with path, message, and keyword.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        super().__init__(message, code="VALIDATION_FAILED", status=400, details={"errors": errors or []})
        self.errors: List[Dict[str, str]] = errors or []


class UnauthorizedError(JsonDBError):
    """Raised when the API key is missing or invalid (HTTP 401)."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, code="UNAUTHORIZED", status=401)


class ForbiddenError(JsonDBError):
    """Raised when the API key lacks the required scope (HTTP 403)."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, code="FORBIDDEN", status=403)


class QuotaExceededError(JsonDBError):
    """Raised when a plan quota is exceeded (HTTP 429 with QUOTA_EXCEEDED code).

    Attributes:
        limit: The maximum allowed value for the quota.
        current: The current usage value.
    """

    def __init__(
        self,
        message: str = "Quota exceeded",
        limit: Optional[int] = None,
        current: Optional[int] = None,
    ) -> None:
        details: Dict[str, Any] = {}
        if limit is not None:
            details["limit"] = limit
        if current is not None:
            details["current"] = current
        super().__init__(message, code="QUOTA_EXCEEDED", status=429, details=details)
        self.limit = limit
        self.current = current


class RateLimitError(JsonDBError):
    """Raised when the rate limit is exceeded (HTTP 429 with RATE_LIMITED code)."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message, code="RATE_LIMITED", status=429)


class DocumentTooLargeError(JsonDBError):
    """Raised when a document exceeds the maximum allowed size (HTTP 413)."""

    def __init__(self, message: str = "Document too large") -> None:
        super().__init__(message, code="DOCUMENT_TOO_LARGE", status=413)


class ServerError(JsonDBError):
    """Raised when the server encounters an internal error (HTTP 5xx)."""

    def __init__(self, message: str = "Internal server error") -> None:
        super().__init__(message, code="INTERNAL_ERROR", status=500)


def create_error(status: int, body: Dict[str, Any]) -> JsonDBError:
    """Convert an API error response into the appropriate exception class.

    Args:
        status: HTTP status code from the response.
        body: Parsed JSON body from the error response. Expected shape::

            {"error": {"code": "...", "message": "...", "details": {...}}}

    Returns:
        An instance of the appropriate ``JsonDBError`` subclass.
    """
    error_data = body.get("error", {})
    if not isinstance(error_data, dict):
        error_data = {}

    code: str = error_data.get("code", "UNKNOWN")
    message: str = error_data.get("message", "Unknown error")
    details: Dict[str, Any] = error_data.get("details", {})

    if status == 401:
        return UnauthorizedError(message)
    elif status == 403:
        return ForbiddenError(message)
    elif status == 404:
        doc_id = details.get("documentId") or details.get("document_id")
        return NotFoundError(message, document_id=doc_id)
    elif status == 409:
        return ConflictError(message)
    elif status == 413:
        return DocumentTooLargeError(message)
    elif status == 429:
        if code == "RATE_LIMITED":
            return RateLimitError(message)
        return QuotaExceededError(
            message,
            limit=details.get("limit"),
            current=details.get("current"),
        )
    elif status == 400:
        if code == "VALIDATION_FAILED":
            return ValidationError(message, errors=details.get("errors", []))
        return JsonDBError(message, code=code, status=400, details=details)
    elif status >= 500:
        return ServerError(message)
    else:
        return JsonDBError(message, code=code, status=status, details=details)
