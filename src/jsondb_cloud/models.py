"""Response models for the jsondb.cloud Python SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Meta:
    """Pagination metadata from a list response.

    Attributes:
        total: Total number of documents matching the query.
        limit: Maximum number of documents returned per page.
        offset: Number of documents skipped.
        has_more: Whether more documents exist beyond this page.
    """

    __slots__ = ("total", "limit", "offset", "has_more")

    def __init__(self, total: int, limit: int, offset: int, has_more: bool) -> None:
        self.total = total
        self.limit = limit
        self.offset = offset
        self.has_more = has_more

    def __repr__(self) -> str:
        return (
            f"Meta(total={self.total}, limit={self.limit}, "
            f"offset={self.offset}, has_more={self.has_more})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Meta):
            return NotImplemented
        return (
            self.total == other.total
            and self.limit == other.limit
            and self.offset == other.offset
            and self.has_more == other.has_more
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Meta":
        """Create a ``Meta`` instance from the API ``meta`` dict."""
        return cls(
            total=data.get("total", 0),
            limit=data.get("limit", 25),
            offset=data.get("offset", 0),
            has_more=data.get("hasMore", False),
        )


class ListResult:
    """Paginated list of documents returned by ``collection.list()``.

    Attributes:
        data: List of document dicts.
        meta: Pagination metadata.
    """

    __slots__ = ("data", "meta")

    def __init__(self, data: List[Dict[str, Any]], meta: Meta) -> None:
        self.data = data
        self.meta = meta

    def __repr__(self) -> str:
        return f"ListResult(data=[...{len(self.data)} docs], meta={self.meta!r})"

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):  # type: ignore[override]
        return iter(self.data)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        return self.data[index]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListResult":
        """Create a ``ListResult`` from a raw API response dict."""
        return cls(
            data=data.get("data", []),
            meta=Meta.from_dict(data.get("meta", {})),
        )


class BulkResultSummary:
    """Summary counts for a bulk operation.

    Attributes:
        total: Total number of operations attempted.
        succeeded: Number of operations that succeeded.
        failed: Number of operations that failed.
    """

    __slots__ = ("total", "succeeded", "failed")

    def __init__(self, total: int, succeeded: int, failed: int) -> None:
        self.total = total
        self.succeeded = succeeded
        self.failed = failed

    def __repr__(self) -> str:
        return (
            f"BulkResultSummary(total={self.total}, "
            f"succeeded={self.succeeded}, failed={self.failed})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BulkResultSummary):
            return NotImplemented
        return (
            self.total == other.total
            and self.succeeded == other.succeeded
            and self.failed == other.failed
        )


class BulkResult:
    """Result of a bulk operation.

    Attributes:
        results: List of per-operation result dicts with ``status``, ``_id``, ``ok``, and
            optionally ``error``.
        summary: Aggregated counts.
    """

    __slots__ = ("results", "summary")

    def __init__(
        self,
        results: List[Dict[str, Any]],
        summary: BulkResultSummary,
    ) -> None:
        self.results = results
        self.summary = summary

    def __repr__(self) -> str:
        return f"BulkResult(results=[...{len(self.results)}], summary={self.summary!r})"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BulkResult":
        """Create a ``BulkResult`` from a raw API response dict."""
        summary_data = data.get("summary", {})
        return cls(
            results=data.get("results", []),
            summary=BulkResultSummary(
                total=summary_data.get("total", 0),
                succeeded=summary_data.get("succeeded", 0),
                failed=summary_data.get("failed", 0),
            ),
        )
