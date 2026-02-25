"""jsondb-cloud — The official Python SDK for jsondb.cloud.

Quick start::

    from jsondb_cloud import JsonDB

    db = JsonDB(api_key="jdb_sk_live_xxxx")
    users = db.collection("users")

    user = users.create({"name": "Alice", "email": "alice@example.com"})
    print(user["_id"])

Async usage::

    from jsondb_cloud import AsyncJsonDB

    async with AsyncJsonDB(api_key="jdb_sk_live_xxxx") as db:
        users = db.collection("users")
        user = await users.create({"name": "Alice"})
"""

from .client import AsyncJsonDB, JsonDB
from .collection import AsyncCollection, Collection
from .errors import (
    ConflictError,
    DocumentTooLargeError,
    ForbiddenError,
    JsonDBError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
    UnauthorizedError,
    ValidationError,
    create_error,
)
from .models import BulkResult, BulkResultSummary, ListResult, Meta

__all__ = [
    # Clients
    "JsonDB",
    "AsyncJsonDB",
    # Collections
    "Collection",
    "AsyncCollection",
    # Response models
    "ListResult",
    "Meta",
    "BulkResult",
    "BulkResultSummary",
    # Errors
    "JsonDBError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "UnauthorizedError",
    "ForbiddenError",
    "QuotaExceededError",
    "RateLimitError",
    "DocumentTooLargeError",
    "ServerError",
    "create_error",
]

__version__ = "1.0.0"
