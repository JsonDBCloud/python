"""Low-level HTTP client wrappers with auto-retry for the jsondb.cloud API."""

from __future__ import annotations

import asyncio
import math
import time
from typing import Any, Dict, Optional

import httpx

from .errors import JsonDBError, create_error


# HTTP status codes that should trigger an automatic retry.
_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


def _backoff_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    """Calculate exponential backoff delay with jitter cap.

    Args:
        attempt: Zero-based attempt index (0 = first retry).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.

    Returns:
        Delay in seconds before the next retry.
    """
    return min(base_delay * math.pow(2, attempt), max_delay)


class SyncHTTPClient:
    """Synchronous HTTP client wrapper around ``httpx.Client``.

    Handles Bearer token auth, automatic retries on 429/5xx with exponential
    backoff, and translation of error responses into ``JsonDBError`` subclasses.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.jsondb.cloud",
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 10.0,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._retry_max_delay = retry_max_delay

        default_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            default_headers.update(headers)

        self._client = httpx.Client(
            base_url=self._base_url,
            headers=default_headers,
            timeout=httpx.Timeout(timeout),
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute an HTTP request with automatic retry.

        Args:
            method: HTTP method (``GET``, ``POST``, ``PUT``, ``PATCH``, ``DELETE``).
            path: URL path relative to ``base_url`` (should start with ``/``).
            json: JSON-serializable request body (for POST/PUT/PATCH).
            headers: Extra headers to merge for this request only.

        Returns:
            Parsed JSON response body, or ``None`` for 204 responses.

        Raises:
            JsonDBError: On non-retryable API errors.
        """
        max_attempts = self._max_retries + 1
        last_error: Optional[Exception] = None

        for attempt in range(max_attempts):
            try:
                response = self._client.request(
                    method,
                    path,
                    json=json,
                    headers=headers,
                )

                # Retry on retryable status codes
                if response.status_code in _RETRYABLE_STATUSES and attempt < max_attempts - 1:
                    delay = _backoff_delay(attempt, self._retry_base_delay, self._retry_max_delay)
                    time.sleep(delay)
                    continue

                # No content
                if response.status_code == 204:
                    return None

                data = response.json()

                if not response.is_success:
                    raise create_error(response.status_code, data)

                return data

            except JsonDBError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < max_attempts - 1:
                    delay = _backoff_delay(attempt, self._retry_base_delay, self._retry_max_delay)
                    time.sleep(delay)
                    continue

        if last_error is not None:
            raise last_error
        raise JsonDBError("Request failed after retries")  # pragma: no cover


class AsyncHTTPClient:
    """Asynchronous HTTP client wrapper around ``httpx.AsyncClient``.

    Handles Bearer token auth, automatic retries on 429/5xx with exponential
    backoff, and translation of error responses into ``JsonDBError`` subclasses.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.jsondb.cloud",
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 10.0,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._retry_max_delay = retry_max_delay

        default_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            default_headers.update(headers)

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=default_headers,
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        """Close the underlying async HTTP client."""
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute an async HTTP request with automatic retry.

        Args:
            method: HTTP method (``GET``, ``POST``, ``PUT``, ``PATCH``, ``DELETE``).
            path: URL path relative to ``base_url`` (should start with ``/``).
            json: JSON-serializable request body (for POST/PUT/PATCH).
            headers: Extra headers to merge for this request only.

        Returns:
            Parsed JSON response body, or ``None`` for 204 responses.

        Raises:
            JsonDBError: On non-retryable API errors.
        """
        max_attempts = self._max_retries + 1
        last_error: Optional[Exception] = None

        for attempt in range(max_attempts):
            try:
                response = await self._client.request(
                    method,
                    path,
                    json=json,
                    headers=headers,
                )

                # Retry on retryable status codes
                if response.status_code in _RETRYABLE_STATUSES and attempt < max_attempts - 1:
                    delay = _backoff_delay(attempt, self._retry_base_delay, self._retry_max_delay)
                    await asyncio.sleep(delay)
                    continue

                # No content
                if response.status_code == 204:
                    return None

                data = response.json()

                if not response.is_success:
                    raise create_error(response.status_code, data)

                return data

            except JsonDBError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < max_attempts - 1:
                    delay = _backoff_delay(attempt, self._retry_base_delay, self._retry_max_delay)
                    await asyncio.sleep(delay)
                    continue

        if last_error is not None:
            raise last_error
        raise JsonDBError("Request failed after retries")  # pragma: no cover
