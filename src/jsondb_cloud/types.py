"""Type aliases and TypedDicts for the jsondb.cloud Python SDK."""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Sequence, Union

if sys.version_info >= (3, 11):
    from typing import TypedDict, NotRequired
else:
    from typing_extensions import TypedDict, NotRequired


# ---------------------------------------------------------------------------
# Filter types
# ---------------------------------------------------------------------------

class FilterOperators(TypedDict, total=False):
    """Operator-based filter for a single field.

    Keys use the ``$``-prefixed syntax familiar from the JS SDK.  Example::

        {"$gte": 21, "$lt": 65}
    """

    # mypy doesn't allow ``$`` in identifiers, so we keep them as string keys
    # accessed via dict subscript. The TypedDict here documents the schema.


# Because TypedDict doesn't support ``$``-prefixed keys cleanly, we use a
# plain Dict type alias for operator filters.
OperatorFilter = Dict[str, Any]
"""A dict mapping ``$op`` strings to values, e.g. ``{"$gte": 21}``."""

FilterValue = Union[str, int, float, bool, OperatorFilter]
"""A filter value is either a literal (equality) or an operator dict."""

FilterParam = Dict[str, FilterValue]
"""Mapping of field names to filter values."""


# ---------------------------------------------------------------------------
# Bulk operation types
# ---------------------------------------------------------------------------

class BulkOperationItem(TypedDict, total=False):
    """A single operation inside a ``_bulk`` request."""

    method: str  # "POST" | "PUT" | "PATCH" | "DELETE"
    id: str
    body: Dict[str, Any]


class BulkResultItem(TypedDict, total=False):
    """Result of a single bulk operation."""

    status: int
    _id: str
    ok: bool
    error: str


class BulkSummary(TypedDict):
    """Summary counts for a bulk operation."""

    total: int
    succeeded: int
    failed: int


# ---------------------------------------------------------------------------
# JSON Patch (RFC 6902)
# ---------------------------------------------------------------------------

class JsonPatchOperation(TypedDict, total=False):
    """A single JSON Patch operation per RFC 6902."""

    op: str  # "add" | "remove" | "replace" | "move" | "copy" | "test"
    path: str
    value: Any
    from_: str  # mapped from "from" in serialization


# ---------------------------------------------------------------------------
# List / query options
# ---------------------------------------------------------------------------

class ListParams(TypedDict, total=False):
    """Parameters for listing documents (used internally)."""

    filter: FilterParam
    sort: str
    limit: int
    offset: int
    select: str
    count: str


# ---------------------------------------------------------------------------
# Meta information from list responses
# ---------------------------------------------------------------------------

class MetaDict(TypedDict):
    """Shape of the ``meta`` object in a list response."""

    total: int
    limit: int
    offset: int
    hasMore: bool


# ---------------------------------------------------------------------------
# Document type
# ---------------------------------------------------------------------------

Document = Dict[str, Any]
"""A stored document, including ``_id``, ``$createdAt``, ``$updatedAt``, ``$version``."""


# ---------------------------------------------------------------------------
# Client configuration
# ---------------------------------------------------------------------------

class ClientConfig(TypedDict, total=False):
    """Configuration options for ``JsonDB`` / ``AsyncJsonDB``."""

    api_key: str
    project: str
    base_url: str
    max_retries: int
    retry_base_delay: float
    retry_max_delay: float
    timeout: float
    headers: Dict[str, str]
