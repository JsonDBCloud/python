"""Client classes for the jsondb.cloud Python SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from ._http import AsyncHTTPClient, SyncHTTPClient
from .collection import AsyncCollection, Collection


class JsonDB:
    """Synchronous client for the jsondb.cloud API.

    Usage::

        from jsondb_cloud import JsonDB

        db = JsonDB(api_key="jdb_sk_live_xxxx")
        users = db.collection("users")

        # Create a document
        alice = users.create({"name": "Alice", "email": "alice@example.com"})

        # Read it back
        user = users.get(alice["_id"])

    Supports use as a context manager::

        with JsonDB(api_key="jdb_sk_live_xxxx") as db:
            users = db.collection("users")
            users.create({"name": "Alice"})

    Args:
        api_key: API key (``jdb_sk_live_*`` or ``jdb_sk_test_*``).
        project: Project name. Defaults to ``"v1"``.
        base_url: API base URL. Defaults to ``"https://api.jsondb.cloud"``.
        max_retries: Maximum number of retries on 429/5xx. Defaults to ``3``.
        retry_base_delay: Base delay in seconds for exponential backoff. Defaults to ``1.0``.
        retry_max_delay: Maximum delay in seconds for exponential backoff. Defaults to ``10.0``.
        timeout: Request timeout in seconds. Defaults to ``30.0``.
        headers: Optional extra headers to include with every request.
    """

    def __init__(
        self,
        api_key: str,
        *,
        project: str = "v1",
        base_url: str = "https://api.jsondb.cloud",
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 10.0,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._project = project
        self._http = SyncHTTPClient(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            retry_max_delay=retry_max_delay,
            timeout=timeout,
            headers=headers,
        )

    def collection(self, name: str) -> Collection:
        """Get a reference to a collection.

        Args:
            name: Collection name (e.g. ``"users"``, ``"posts"``).

        Returns:
            A :class:`Collection` instance bound to this client and project.
        """
        return Collection(name=name, project=self._project, http=self._http)

    def list_collections(self) -> List[str]:
        """List all collections in the project."""
        data = self._http.request("GET", f"/{self._project}")
        return cast(List[str], data.get("data", data) if isinstance(data, dict) else data)

    def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        self._http.close()

    def __enter__(self) -> "JsonDB":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncJsonDB:
    """Asynchronous client for the jsondb.cloud API.

    Usage::

        from jsondb_cloud import AsyncJsonDB

        db = AsyncJsonDB(api_key="jdb_sk_live_xxxx")
        users = db.collection("users")

        alice = await users.create({"name": "Alice", "email": "alice@example.com"})
        user = await users.get(alice["_id"])

    Supports use as an async context manager::

        async with AsyncJsonDB(api_key="jdb_sk_live_xxxx") as db:
            users = db.collection("users")
            await users.create({"name": "Alice"})

    Args:
        api_key: API key (``jdb_sk_live_*`` or ``jdb_sk_test_*``).
        project: Project name. Defaults to ``"v1"``.
        base_url: API base URL. Defaults to ``"https://api.jsondb.cloud"``.
        max_retries: Maximum number of retries on 429/5xx. Defaults to ``3``.
        retry_base_delay: Base delay in seconds for exponential backoff. Defaults to ``1.0``.
        retry_max_delay: Maximum delay in seconds for exponential backoff. Defaults to ``10.0``.
        timeout: Request timeout in seconds. Defaults to ``30.0``.
        headers: Optional extra headers to include with every request.
    """

    def __init__(
        self,
        api_key: str,
        *,
        project: str = "v1",
        base_url: str = "https://api.jsondb.cloud",
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 10.0,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._project = project
        self._http = AsyncHTTPClient(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            retry_max_delay=retry_max_delay,
            timeout=timeout,
            headers=headers,
        )

    def collection(self, name: str) -> AsyncCollection:
        """Get a reference to a collection.

        Args:
            name: Collection name (e.g. ``"users"``, ``"posts"``).

        Returns:
            An :class:`AsyncCollection` instance bound to this client and project.
        """
        return AsyncCollection(name=name, project=self._project, http=self._http)

    async def list_collections(self) -> List[str]:
        """List all collections in the project."""
        data = await self._http.request("GET", f"/{self._project}")
        return cast(List[str], data.get("data", data) if isinstance(data, dict) else data)

    async def close(self) -> None:
        """Close the underlying async HTTP client and release resources."""
        await self._http.close()

    async def __aenter__(self) -> "AsyncJsonDB":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
