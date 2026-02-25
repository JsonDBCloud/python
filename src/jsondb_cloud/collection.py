"""Collection classes for interacting with a jsondb.cloud collection."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, cast

from ._http import AsyncHTTPClient, SyncHTTPClient
from .models import BulkResult, ListResult


def _build_query_string(
    *,
    filter: Optional[Dict[str, Any]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    select: Optional[Sequence[str]] = None,
    count: bool = False,
) -> str:
    """Build a URL query string from list/query parameters.

    The ``filter`` dict supports two shapes per field:

    * Equality: ``{"role": "admin"}`` -> ``filter[role]=admin``
    * Operator:  ``{"age": {"$gte": 21}}`` -> ``filter[age][gte]=21``

    Returns:
        Query string **without** the leading ``?``, or empty string if no params.
    """
    parts: List[str] = []

    if filter:
        for field, value in filter.items():
            if isinstance(value, dict):
                # Operator filter: {"$gte": 21, "$lt": 65}
                for op_key, op_val in value.items():
                    # Strip leading $ from operator key
                    op_name = op_key.lstrip("$")
                    if op_name == "eq":
                        parts.append(f"filter[{field}]={_encode(op_val)}")
                    elif op_name == "in" and isinstance(op_val, (list, tuple)):
                        parts.append(f"filter[{field}][in]={','.join(str(v) for v in op_val)}")
                    else:
                        parts.append(f"filter[{field}][{op_name}]={_encode(op_val)}")
            else:
                # Simple equality filter
                parts.append(f"filter[{field}]={_encode(value)}")

    if sort is not None:
        parts.append(f"sort={sort}")
    if limit is not None:
        parts.append(f"limit={limit}")
    if offset is not None:
        parts.append(f"offset={offset}")
    if select is not None:
        parts.append(f"select={','.join(select)}")
    if count:
        parts.append("count=true")

    return "&".join(parts)


def _encode(value: Any) -> str:
    """Encode a filter value as a string suitable for a query parameter."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class Collection:
    """Synchronous interface to a single jsondb.cloud collection.

    Obtain instances via :meth:`JsonDB.collection` rather than constructing
    directly.

    Example::

        db = JsonDB(api_key="jdb_sk_live_...")
        users = db.collection("users")
        alice = users.create({"name": "Alice", "email": "alice@example.com"})
    """

    def __init__(self, name: str, project: str, http: SyncHTTPClient) -> None:
        self._name = name
        self._project = project
        self._http = http

    @property
    def name(self) -> str:
        """The collection name."""
        return self._name

    def _path(self, suffix: str = "") -> str:
        """Build the API path for this collection."""
        base = f"/{self._project}/{self._name}"
        if suffix:
            return f"{base}/{suffix}"
        return base

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, data: Dict[str, Any], *, id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new document."""
        path = self._path(id) if id else self._path()
        return cast(Dict[str, Any], self._http.request("POST", path, json=data))

    def get(self, id: str) -> Dict[str, Any]:
        """Get a single document by ID."""
        return cast(Dict[str, Any], self._http.request("GET", self._path(id)))

    def list(
        self,
        *,
        filter: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        select: Optional[Sequence[str]] = None,
    ) -> ListResult:
        """List documents with optional filtering, sorting, and pagination."""
        qs = _build_query_string(
            filter=filter, sort=sort, limit=limit, offset=offset, select=select,
        )
        path = self._path()
        if qs:
            path = f"{path}?{qs}"
        data = self._http.request("GET", path)
        return ListResult.from_dict(data)

    def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace a document entirely."""
        return cast(Dict[str, Any], self._http.request("PUT", self._path(id), json=data))

    def patch(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge-patch a document (partial update)."""
        return cast(Dict[str, Any], self._http.request(
            "PATCH", self._path(id), json=data,
            headers={"Content-Type": "application/merge-patch+json"},
        ))

    def json_patch(self, id: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply JSON Patch operations (RFC 6902) to a document."""
        return cast(Dict[str, Any], self._http.request(
            "PATCH", self._path(id), json=operations,
            headers={"Content-Type": "application/json-patch+json"},
        ))

    def delete(self, id: str) -> None:
        """Delete a document by ID."""
        self._http.request("DELETE", self._path(id))

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def bulk_create(self, docs: List[Dict[str, Any]]) -> BulkResult:
        """Create multiple documents in a single request."""
        operations = [{"method": "POST", "body": doc} for doc in docs]
        data = self._http.request("POST", self._path("_bulk"), json={"operations": operations})
        return BulkResult.from_dict(data)

    def bulk(self, operations: List[Dict[str, Any]]) -> BulkResult:
        """Execute mixed bulk operations (POST/PUT/PATCH/DELETE)."""
        data = self._http.request("POST", self._path("_bulk"), json={"operations": operations})
        return BulkResult.from_dict(data)

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    def count(self, *, filter: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching an optional filter."""
        qs = _build_query_string(filter=filter, count=True)
        path = f"{self._path()}?{qs}"
        data = self._http.request("GET", path)
        return cast(int, data["count"])

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get the JSON Schema for this collection."""
        data = self._http.request("GET", self._path("_schema"))
        return cast(Optional[Dict[str, Any]], data.get("schema"))

    def set_schema(self, schema: Dict[str, Any]) -> None:
        """Set a JSON Schema for this collection."""
        self._http.request("PUT", self._path("_schema"), json=schema)

    def remove_schema(self) -> None:
        """Remove the schema from this collection."""
        self._http.request("DELETE", self._path("_schema"))

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a document against the collection schema without storing it."""
        return cast(Dict[str, Any], self._http.request("POST", self._path("_validate"), json=data))

    # ------------------------------------------------------------------
    # Version history
    # ------------------------------------------------------------------

    def list_versions(self, id: str) -> Dict[str, Any]:
        """List all versions of a document."""
        return cast(Dict[str, Any], self._http.request("GET", self._path(f"{id}/versions")))

    def get_version(self, id: str, version: int) -> Dict[str, Any]:
        """Get a document at a specific version."""
        return cast(Dict[str, Any], self._http.request("GET", self._path(f"{id}/versions/{version}")))

    def restore_version(self, id: str, version: int) -> Dict[str, Any]:
        """Restore a document to a specific version."""
        return cast(Dict[str, Any], self._http.request("POST", self._path(f"{id}/versions/{version}/restore")))

    def diff_versions(self, id: str, from_version: int, to_version: int) -> Dict[str, Any]:
        """Diff two versions of a document (Pro feature)."""
        return cast(Dict[str, Any], self._http.request(
            "GET", self._path(f"{id}/versions/diff?from={from_version}&to={to_version}")
        ))

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    def create_webhook(
        self, *, url: str, events: List[str],
        description: Optional[str] = None, secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a webhook on this collection."""
        body: Dict[str, Any] = {"url": url, "events": events}
        if description is not None:
            body["description"] = description
        if secret is not None:
            body["secret"] = secret
        return cast(Dict[str, Any], self._http.request("POST", self._path("_webhooks"), json=body))

    def list_webhooks(self) -> Dict[str, Any]:
        """List all webhooks for this collection."""
        return cast(Dict[str, Any], self._http.request("GET", self._path("_webhooks")))

    def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Get webhook details including recent deliveries."""
        return cast(Dict[str, Any], self._http.request("GET", self._path(f"_webhooks/{webhook_id}")))

    def update_webhook(self, webhook_id: str, **kwargs: Any) -> Dict[str, Any]:
        """Update a webhook."""
        return cast(Dict[str, Any], self._http.request("PUT", self._path(f"_webhooks/{webhook_id}"), json=kwargs))

    def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook."""
        self._http.request("DELETE", self._path(f"_webhooks/{webhook_id}"))

    def test_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Send a test event to a webhook."""
        return cast(Dict[str, Any], self._http.request("POST", self._path(f"_webhooks/{webhook_id}/test")))

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def import_documents(
        self, documents: List[Dict[str, Any]], *,
        on_conflict: Optional[str] = None, id_field: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Import documents into this collection."""
        parts: List[str] = []
        if on_conflict is not None:
            parts.append(f"onConflict={on_conflict}")
        if id_field is not None:
            parts.append(f"idField={id_field}")
        qs = f"?{'&'.join(parts)}" if parts else ""
        return cast(Dict[str, Any], self._http.request("POST", self._path(f"_import{qs}"), json=documents))

    def export_documents(self, *, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Export all documents from this collection."""
        qs = _build_query_string(filter=filter) if filter else ""
        path = self._path("_export")
        if qs:
            path = f"{path}?{qs}"
        return cast(List[Dict[str, Any]], self._http.request("GET", path))


class AsyncCollection:
    """Asynchronous interface to a single jsondb.cloud collection.

    Obtain instances via :meth:`AsyncJsonDB.collection` rather than
    constructing directly.

    Example::

        db = AsyncJsonDB(api_key="jdb_sk_live_...")
        users = db.collection("users")
        alice = await users.create({"name": "Alice", "email": "alice@example.com"})
    """

    def __init__(self, name: str, project: str, http: AsyncHTTPClient) -> None:
        self._name = name
        self._project = project
        self._http = http

    @property
    def name(self) -> str:
        """The collection name."""
        return self._name

    def _path(self, suffix: str = "") -> str:
        """Build the API path for this collection."""
        base = f"/{self._project}/{self._name}"
        if suffix:
            return f"{base}/{suffix}"
        return base

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create(self, data: Dict[str, Any], *, id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new document."""
        path = self._path(id) if id else self._path()
        return cast(Dict[str, Any], await self._http.request("POST", path, json=data))

    async def get(self, id: str) -> Dict[str, Any]:
        """Get a single document by ID."""
        return cast(Dict[str, Any], await self._http.request("GET", self._path(id)))

    async def list(
        self, *,
        filter: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        select: Optional[Sequence[str]] = None,
    ) -> ListResult:
        """List documents with optional filtering, sorting, and pagination."""
        qs = _build_query_string(
            filter=filter, sort=sort, limit=limit, offset=offset, select=select,
        )
        path = self._path()
        if qs:
            path = f"{path}?{qs}"
        data = await self._http.request("GET", path)
        return ListResult.from_dict(data)

    async def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace a document entirely."""
        return cast(Dict[str, Any], await self._http.request("PUT", self._path(id), json=data))

    async def patch(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge-patch a document (partial update)."""
        return cast(Dict[str, Any], await self._http.request(
            "PATCH", self._path(id), json=data,
            headers={"Content-Type": "application/merge-patch+json"},
        ))

    async def json_patch(self, id: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply JSON Patch operations (RFC 6902) to a document."""
        return cast(Dict[str, Any], await self._http.request(
            "PATCH", self._path(id), json=operations,
            headers={"Content-Type": "application/json-patch+json"},
        ))

    async def delete(self, id: str) -> None:
        """Delete a document by ID."""
        await self._http.request("DELETE", self._path(id))

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    async def bulk_create(self, docs: List[Dict[str, Any]]) -> BulkResult:
        """Create multiple documents in a single request."""
        operations = [{"method": "POST", "body": doc} for doc in docs]
        data = await self._http.request(
            "POST", self._path("_bulk"), json={"operations": operations}
        )
        return BulkResult.from_dict(data)

    async def bulk(self, operations: List[Dict[str, Any]]) -> BulkResult:
        """Execute mixed bulk operations (POST/PUT/PATCH/DELETE)."""
        data = await self._http.request(
            "POST", self._path("_bulk"), json={"operations": operations}
        )
        return BulkResult.from_dict(data)

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    async def count(self, *, filter: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching an optional filter."""
        qs = _build_query_string(filter=filter, count=True)
        path = f"{self._path()}?{qs}"
        data = await self._http.request("GET", path)
        return cast(int, data["count"])

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    async def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get the JSON Schema for this collection."""
        data = await self._http.request("GET", self._path("_schema"))
        return cast(Optional[Dict[str, Any]], data.get("schema"))

    async def set_schema(self, schema: Dict[str, Any]) -> None:
        """Set a JSON Schema for this collection."""
        await self._http.request("PUT", self._path("_schema"), json=schema)

    async def remove_schema(self) -> None:
        """Remove the schema from this collection."""
        await self._http.request("DELETE", self._path("_schema"))

    async def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a document against the collection schema without storing it."""
        return cast(Dict[str, Any], await self._http.request("POST", self._path("_validate"), json=data))

    # ------------------------------------------------------------------
    # Version history
    # ------------------------------------------------------------------

    async def list_versions(self, id: str) -> Dict[str, Any]:
        """List all versions of a document."""
        return cast(Dict[str, Any], await self._http.request("GET", self._path(f"{id}/versions")))

    async def get_version(self, id: str, version: int) -> Dict[str, Any]:
        """Get a document at a specific version."""
        return cast(Dict[str, Any], await self._http.request("GET", self._path(f"{id}/versions/{version}")))

    async def restore_version(self, id: str, version: int) -> Dict[str, Any]:
        """Restore a document to a specific version."""
        return cast(Dict[str, Any], await self._http.request("POST", self._path(f"{id}/versions/{version}/restore")))

    async def diff_versions(self, id: str, from_version: int, to_version: int) -> Dict[str, Any]:
        """Diff two versions of a document (Pro feature)."""
        return cast(Dict[str, Any], await self._http.request(
            "GET", self._path(f"{id}/versions/diff?from={from_version}&to={to_version}")
        ))

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    async def create_webhook(
        self, *, url: str, events: List[str],
        description: Optional[str] = None, secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a webhook on this collection."""
        body: Dict[str, Any] = {"url": url, "events": events}
        if description is not None:
            body["description"] = description
        if secret is not None:
            body["secret"] = secret
        return cast(Dict[str, Any], await self._http.request("POST", self._path("_webhooks"), json=body))

    async def list_webhooks(self) -> Dict[str, Any]:
        """List all webhooks for this collection."""
        return cast(Dict[str, Any], await self._http.request("GET", self._path("_webhooks")))

    async def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Get webhook details including recent deliveries."""
        return cast(Dict[str, Any], await self._http.request("GET", self._path(f"_webhooks/{webhook_id}")))

    async def update_webhook(self, webhook_id: str, **kwargs: Any) -> Dict[str, Any]:
        """Update a webhook."""
        return cast(Dict[str, Any], await self._http.request("PUT", self._path(f"_webhooks/{webhook_id}"), json=kwargs))

    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook."""
        await self._http.request("DELETE", self._path(f"_webhooks/{webhook_id}"))

    async def test_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Send a test event to a webhook."""
        return cast(Dict[str, Any], await self._http.request("POST", self._path(f"_webhooks/{webhook_id}/test")))

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    async def import_documents(
        self, documents: List[Dict[str, Any]], *,
        on_conflict: Optional[str] = None, id_field: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Import documents into this collection."""
        parts: List[str] = []
        if on_conflict is not None:
            parts.append(f"onConflict={on_conflict}")
        if id_field is not None:
            parts.append(f"idField={id_field}")
        qs = f"?{'&'.join(parts)}" if parts else ""
        return cast(Dict[str, Any], await self._http.request("POST", self._path(f"_import{qs}"), json=documents))

    async def export_documents(self, *, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Export all documents from this collection."""
        qs = _build_query_string(filter=filter) if filter else ""
        path = self._path("_export")
        if qs:
            path = f"{path}?{qs}"
        return cast(List[Dict[str, Any]], await self._http.request("GET", path))
