"""Tests for JsonDB, AsyncJsonDB, Collection, and AsyncCollection using mocked HTTP."""

import pytest
import httpx
import respx

from jsondb_cloud import (
    AsyncJsonDB,
    JsonDB,
    ListResult,
    BulkResult,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


API_KEY = "jdb_sk_test_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
BASE_URL = "https://api.jsondb.cloud"
PROJECT = "v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coll_url(collection: str, suffix: str = "") -> str:
    """Build the full API URL for a collection endpoint."""
    base = f"{BASE_URL}/{PROJECT}/{collection}"
    if suffix:
        return f"{base}/{suffix}"
    return base


def _doc_response(doc_id: str = "abc123", **fields: object) -> dict:
    """Build a typical document response body."""
    return {
        "_id": doc_id,
        "$createdAt": "2025-01-01T00:00:00.000Z",
        "$updatedAt": "2025-01-01T00:00:00.000Z",
        "$version": 1,
        **fields,
    }


def _list_response(docs: list, total: int = 1, limit: int = 25, offset: int = 0) -> dict:
    """Build a typical list response body."""
    return {
        "data": docs,
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "hasMore": total > offset + limit,
        },
    }


# ---------------------------------------------------------------------------
# JsonDB client construction
# ---------------------------------------------------------------------------

class TestJsonDBClient:
    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="api_key is required"):
            JsonDB(api_key="")

    def test_collection_returns_collection(self) -> None:
        db = JsonDB(api_key=API_KEY)
        coll = db.collection("users")
        assert coll.name == "users"

    def test_context_manager(self) -> None:
        with JsonDB(api_key=API_KEY) as db:
            coll = db.collection("users")
            assert coll.name == "users"


class TestAsyncJsonDBClient:
    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="api_key is required"):
            AsyncJsonDB(api_key="")

    def test_collection_returns_async_collection(self) -> None:
        db = AsyncJsonDB(api_key=API_KEY)
        coll = db.collection("users")
        assert coll.name == "users"

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        async with AsyncJsonDB(api_key=API_KEY) as db:
            coll = db.collection("users")
            assert coll.name == "users"


# ---------------------------------------------------------------------------
# Sync Collection CRUD
# ---------------------------------------------------------------------------

class TestSyncCollectionCreate:
    @respx.mock
    def test_create_auto_id(self) -> None:
        doc = _doc_response(name="Alice")
        respx.post(_coll_url("users")).mock(
            return_value=httpx.Response(201, json=doc)
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").create({"name": "Alice"})

        assert result["_id"] == "abc123"
        assert result["name"] == "Alice"

    @respx.mock
    def test_create_explicit_id(self) -> None:
        doc = _doc_response(doc_id="custom-id", name="Bob")
        respx.post(_coll_url("users", "custom-id")).mock(
            return_value=httpx.Response(201, json=doc)
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").create({"name": "Bob"}, id="custom-id")

        assert result["_id"] == "custom-id"


class TestSyncCollectionGet:
    @respx.mock
    def test_get_document(self) -> None:
        doc = _doc_response(name="Alice")
        respx.get(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=doc)
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").get("abc123")

        assert result["_id"] == "abc123"
        assert result["name"] == "Alice"

    @respx.mock
    def test_get_not_found_raises(self) -> None:
        respx.get(_coll_url("users", "nonexistent")).mock(
            return_value=httpx.Response(404, json={
                "error": {"code": "DOCUMENT_NOT_FOUND", "message": "not found"}
            })
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            with pytest.raises(NotFoundError):
                db.collection("users").get("nonexistent")


class TestSyncCollectionList:
    @respx.mock
    def test_list_basic(self) -> None:
        docs = [_doc_response(name="Alice")]
        respx.get(_coll_url("users")).mock(
            return_value=httpx.Response(200, json=_list_response(docs))
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").list()

        assert isinstance(result, ListResult)
        assert len(result.data) == 1
        assert result.meta.total == 1
        assert result.meta.has_more is False

    @respx.mock
    def test_list_with_filter(self) -> None:
        docs = [_doc_response(name="Alice", role="admin")]
        route = respx.get(url__startswith=_coll_url("users")).mock(
            return_value=httpx.Response(200, json=_list_response(docs))
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").list(filter={"role": "admin"})

        assert len(result.data) == 1
        request = route.calls[0].request
        assert "filter[role]=admin" in str(request.url)

    @respx.mock
    def test_list_with_operator_filter(self) -> None:
        docs = [_doc_response(name="Alice", age=30)]
        route = respx.get(url__startswith=_coll_url("users")).mock(
            return_value=httpx.Response(200, json=_list_response(docs))
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").list(filter={"age": {"$gte": 21}})

        request = route.calls[0].request
        assert "filter[age][gte]=21" in str(request.url)

    @respx.mock
    def test_list_with_sort(self) -> None:
        route = respx.get(url__startswith=_coll_url("users")).mock(
            return_value=httpx.Response(200, json=_list_response([]))
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            db.collection("users").list(sort="-createdAt")

        request = route.calls[0].request
        assert "sort=-createdAt" in str(request.url)

    @respx.mock
    def test_list_with_pagination(self) -> None:
        route = respx.get(url__startswith=_coll_url("users")).mock(
            return_value=httpx.Response(200, json=_list_response([], total=100, limit=10, offset=20))
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").list(limit=10, offset=20)

        request = route.calls[0].request
        assert "limit=10" in str(request.url)
        assert "offset=20" in str(request.url)
        assert result.meta.total == 100
        assert result.meta.has_more is True

    @respx.mock
    def test_list_with_select(self) -> None:
        route = respx.get(url__startswith=_coll_url("users")).mock(
            return_value=httpx.Response(200, json=_list_response([]))
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            db.collection("users").list(select=["name", "email"])

        request = route.calls[0].request
        assert "select=name,email" in str(request.url)

    @respx.mock
    def test_list_iterable(self) -> None:
        docs = [_doc_response(doc_id="a"), _doc_response(doc_id="b")]
        respx.get(_coll_url("users")).mock(
            return_value=httpx.Response(200, json=_list_response(docs, total=2))
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").list()

        ids = [doc["_id"] for doc in result]
        assert ids == ["a", "b"]
        assert result[0]["_id"] == "a"


class TestSyncCollectionUpdate:
    @respx.mock
    def test_update(self) -> None:
        doc = _doc_response(name="Alice Updated")
        respx.put(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=doc)
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").update("abc123", {"name": "Alice Updated"})

        assert result["name"] == "Alice Updated"


class TestSyncCollectionPatch:
    @respx.mock
    def test_merge_patch(self) -> None:
        doc = _doc_response(name="Alice", age=31)
        route = respx.patch(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=doc)
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").patch("abc123", {"age": 31})

        assert result["age"] == 31
        request = route.calls[0].request
        assert request.headers["content-type"] == "application/merge-patch+json"

    @respx.mock
    def test_json_patch(self) -> None:
        doc = _doc_response(name="Alice", age=31, verified=True)
        route = respx.patch(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=doc)
        )

        ops = [
            {"op": "replace", "path": "/age", "value": 31},
            {"op": "add", "path": "/verified", "value": True},
        ]

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").json_patch("abc123", ops)

        assert result["verified"] is True
        request = route.calls[0].request
        assert request.headers["content-type"] == "application/json-patch+json"


class TestSyncCollectionDelete:
    @respx.mock
    def test_delete(self) -> None:
        respx.delete(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(204)
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").delete("abc123")

        assert result is None


class TestSyncCollectionBulk:
    @respx.mock
    def test_bulk_create(self) -> None:
        bulk_response = {
            "results": [
                {"status": 201, "_id": "id1", "ok": True},
                {"status": 201, "_id": "id2", "ok": True},
            ],
            "summary": {"total": 2, "succeeded": 2, "failed": 0},
        }
        route = respx.post(_coll_url("users", "_bulk")).mock(
            return_value=httpx.Response(200, json=bulk_response)
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").bulk_create([
                {"name": "Charlie"},
                {"name": "Dana"},
            ])

        assert isinstance(result, BulkResult)
        assert result.summary.total == 2
        assert result.summary.succeeded == 2
        assert result.summary.failed == 0
        assert len(result.results) == 2

        # Verify the request body shape
        import json
        request = route.calls[0].request
        body = json.loads(request.content)
        assert "operations" in body
        assert len(body["operations"]) == 2
        assert body["operations"][0]["method"] == "POST"
        assert body["operations"][0]["body"] == {"name": "Charlie"}


# ---------------------------------------------------------------------------
# Auth header
# ---------------------------------------------------------------------------

class TestAuthHeader:
    @respx.mock
    def test_bearer_token_sent(self) -> None:
        route = respx.get(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=_doc_response())
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            db.collection("users").get("abc123")

        request = route.calls[0].request
        assert request.headers["authorization"] == f"Bearer {API_KEY}"

    @respx.mock
    def test_401_raises_unauthorized(self) -> None:
        respx.get(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(401, json={
                "error": {"code": "UNAUTHORIZED", "message": "Invalid API key"}
            })
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            with pytest.raises(UnauthorizedError):
                db.collection("users").get("abc123")


# ---------------------------------------------------------------------------
# Custom project
# ---------------------------------------------------------------------------

class TestCustomProject:
    @respx.mock
    def test_custom_project_in_url(self) -> None:
        url = f"{BASE_URL}/myns/users/abc123"
        respx.get(url).mock(
            return_value=httpx.Response(200, json=_doc_response())
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL, project="myns") as db:
            result = db.collection("users").get("abc123")

        assert result["_id"] == "abc123"


# ---------------------------------------------------------------------------
# Async Collection CRUD
# ---------------------------------------------------------------------------

class TestAsyncCollectionCreate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_create_auto_id(self) -> None:
        doc = _doc_response(name="Alice")
        respx.post(_coll_url("users")).mock(
            return_value=httpx.Response(201, json=doc)
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").create({"name": "Alice"})

        assert result["_id"] == "abc123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_explicit_id(self) -> None:
        doc = _doc_response(doc_id="custom-id", name="Bob")
        respx.post(_coll_url("users", "custom-id")).mock(
            return_value=httpx.Response(201, json=doc)
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").create({"name": "Bob"}, id="custom-id")

        assert result["_id"] == "custom-id"


class TestAsyncCollectionGet:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_document(self) -> None:
        doc = _doc_response(name="Alice")
        respx.get(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=doc)
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").get("abc123")

        assert result["name"] == "Alice"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_not_found(self) -> None:
        respx.get(_coll_url("users", "missing")).mock(
            return_value=httpx.Response(404, json={
                "error": {"code": "DOCUMENT_NOT_FOUND", "message": "not found"}
            })
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            with pytest.raises(NotFoundError):
                await db.collection("users").get("missing")


class TestAsyncCollectionList:
    @pytest.mark.asyncio
    @respx.mock
    async def test_list_with_filter(self) -> None:
        docs = [_doc_response(name="Alice", role="admin")]
        route = respx.get(url__startswith=_coll_url("users")).mock(
            return_value=httpx.Response(200, json=_list_response(docs))
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").list(filter={"role": "admin"})

        assert len(result.data) == 1
        request = route.calls[0].request
        assert "filter[role]=admin" in str(request.url)


class TestAsyncCollectionUpdate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_update(self) -> None:
        doc = _doc_response(name="Updated")
        respx.put(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=doc)
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").update("abc123", {"name": "Updated"})

        assert result["name"] == "Updated"


class TestAsyncCollectionPatch:
    @pytest.mark.asyncio
    @respx.mock
    async def test_merge_patch(self) -> None:
        doc = _doc_response(age=31)
        route = respx.patch(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=doc)
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").patch("abc123", {"age": 31})

        assert result["age"] == 31
        request = route.calls[0].request
        assert request.headers["content-type"] == "application/merge-patch+json"

    @pytest.mark.asyncio
    @respx.mock
    async def test_json_patch(self) -> None:
        doc = _doc_response(verified=True)
        route = respx.patch(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=doc)
        )

        ops = [{"op": "add", "path": "/verified", "value": True}]

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").json_patch("abc123", ops)

        assert result["verified"] is True
        request = route.calls[0].request
        assert request.headers["content-type"] == "application/json-patch+json"


class TestAsyncCollectionDelete:
    @pytest.mark.asyncio
    @respx.mock
    async def test_delete(self) -> None:
        respx.delete(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(204)
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").delete("abc123")

        assert result is None


class TestAsyncCollectionBulk:
    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_create(self) -> None:
        bulk_response = {
            "results": [
                {"status": 201, "_id": "id1", "ok": True},
            ],
            "summary": {"total": 1, "succeeded": 1, "failed": 0},
        }
        respx.post(_coll_url("users", "_bulk")).mock(
            return_value=httpx.Response(200, json=bulk_response)
        )

        async with AsyncJsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = await db.collection("users").bulk_create([{"name": "Charlie"}])

        assert isinstance(result, BulkResult)
        assert result.summary.succeeded == 1


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    @respx.mock
    def test_validation_error(self) -> None:
        respx.post(_coll_url("users")).mock(
            return_value=httpx.Response(400, json={
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "Schema validation failed",
                    "details": {
                        "errors": [
                            {"path": "/email", "message": "is required", "keyword": "required"}
                        ],
                    },
                }
            })
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            with pytest.raises(ValidationError) as exc_info:
                db.collection("users").create({"name": "Alice"})

        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["path"] == "/email"


# ---------------------------------------------------------------------------
# Custom headers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Count
# ---------------------------------------------------------------------------

class TestSyncCount:
    @respx.mock
    def test_count_basic(self) -> None:
        route = respx.get(url__startswith=_coll_url("users")).mock(
            return_value=httpx.Response(200, json={"count": 42})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").count()
        assert result == 42
        request = route.calls[0].request
        assert "count=true" in str(request.url)

    @respx.mock
    def test_count_with_filter(self) -> None:
        route = respx.get(url__startswith=_coll_url("users")).mock(
            return_value=httpx.Response(200, json={"count": 5})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").count(filter={"role": "admin"})
        assert result == 5
        request = route.calls[0].request
        assert "count=true" in str(request.url)
        assert "filter[role]=admin" in str(request.url)


# ---------------------------------------------------------------------------
# List collections
# ---------------------------------------------------------------------------

class TestSyncListCollections:
    @respx.mock
    def test_list_collections(self) -> None:
        respx.get(f"{BASE_URL}/{PROJECT}").mock(
            return_value=httpx.Response(200, json={"data": ["users", "posts"]})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.list_collections()
        assert result == ["users", "posts"]


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestSyncSchema:
    @respx.mock
    def test_get_schema(self) -> None:
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        respx.get(_coll_url("users", "_schema")).mock(
            return_value=httpx.Response(200, json={"collection": "users", "schema": schema})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").get_schema()
        assert result["type"] == "object"

    @respx.mock
    def test_set_schema(self) -> None:
        schema = {"type": "object", "required": ["name"]}
        respx.put(_coll_url("users", "_schema")).mock(
            return_value=httpx.Response(200, json={"collection": "users", "schema": schema})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            db.collection("users").set_schema(schema)

    @respx.mock
    def test_remove_schema(self) -> None:
        respx.delete(_coll_url("users", "_schema")).mock(
            return_value=httpx.Response(200, json={"collection": "users", "schema": None})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            db.collection("users").remove_schema()

    @respx.mock
    def test_validate(self) -> None:
        respx.post(_coll_url("users", "_validate")).mock(
            return_value=httpx.Response(200, json={"collection": "users", "valid": True, "errors": []})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").validate({"name": "Alice"})
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Version history
# ---------------------------------------------------------------------------

class TestSyncVersions:
    @respx.mock
    def test_list_versions(self) -> None:
        respx.get(_coll_url("users", "doc1/versions")).mock(
            return_value=httpx.Response(200, json={"versions": [{"version": 1, "action": "create"}]})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").list_versions("doc1")
        assert len(result["versions"]) == 1

    @respx.mock
    def test_get_version(self) -> None:
        respx.get(_coll_url("users", "doc1/versions/1")).mock(
            return_value=httpx.Response(200, json={"_id": "doc1", "name": "old", "$version": 1})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").get_version("doc1", 1)
        assert result["name"] == "old"

    @respx.mock
    def test_restore_version(self) -> None:
        respx.post(_coll_url("users", "doc1/versions/1/restore")).mock(
            return_value=httpx.Response(200, json={"_id": "doc1", "name": "restored", "$version": 3})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").restore_version("doc1", 1)
        assert result["name"] == "restored"

    @respx.mock
    def test_diff_versions(self) -> None:
        diff = {"added": {}, "removed": {}, "changed": {"name": {"from": "a", "to": "b"}}}
        respx.get(url__startswith=_coll_url("users", "doc1/versions/diff")).mock(
            return_value=httpx.Response(200, json=diff)
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").diff_versions("doc1", 1, 2)
        assert result["changed"]["name"]["to"] == "b"


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

class TestSyncWebhooks:
    @respx.mock
    def test_create_webhook(self) -> None:
        webhook = {"_id": "wh1", "url": "https://example.com/hook", "events": ["document.created"], "status": "active"}
        respx.post(_coll_url("users", "_webhooks")).mock(
            return_value=httpx.Response(201, json=webhook)
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").create_webhook(url="https://example.com/hook", events=["document.created"])
        assert result["_id"] == "wh1"

    @respx.mock
    def test_list_webhooks(self) -> None:
        respx.get(_coll_url("users", "_webhooks")).mock(
            return_value=httpx.Response(200, json={"data": [{"_id": "wh1"}]})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").list_webhooks()
        assert len(result["data"]) == 1

    @respx.mock
    def test_get_webhook(self) -> None:
        respx.get(_coll_url("users", "_webhooks/wh1")).mock(
            return_value=httpx.Response(200, json={"_id": "wh1", "recentDeliveries": []})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").get_webhook("wh1")
        assert result["_id"] == "wh1"

    @respx.mock
    def test_update_webhook(self) -> None:
        respx.put(_coll_url("users", "_webhooks/wh1")).mock(
            return_value=httpx.Response(200, json={"_id": "wh1", "url": "https://new.com/hook"})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").update_webhook("wh1", url="https://new.com/hook")
        assert result["url"] == "https://new.com/hook"

    @respx.mock
    def test_delete_webhook(self) -> None:
        respx.delete(_coll_url("users", "_webhooks/wh1")).mock(
            return_value=httpx.Response(204)
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            db.collection("users").delete_webhook("wh1")

    @respx.mock
    def test_test_webhook(self) -> None:
        respx.post(_coll_url("users", "_webhooks/wh1/test")).mock(
            return_value=httpx.Response(200, json={"_id": "del1", "statusCode": 200})
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").test_webhook("wh1")
        assert result["statusCode"] == 200


# ---------------------------------------------------------------------------
# Import / Export
# ---------------------------------------------------------------------------

class TestSyncImportExport:
    @respx.mock
    def test_import_documents(self) -> None:
        result = {"results": [{"status": 201, "document": {"_id": "d1"}}]}
        route = respx.post(url__startswith=_coll_url("users", "_import")).mock(
            return_value=httpx.Response(207, json=result)
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            res = db.collection("users").import_documents([{"name": "Alice"}], on_conflict="skip")
        assert len(res["results"]) == 1
        request = route.calls[0].request
        assert "onConflict=skip" in str(request.url)

    @respx.mock
    def test_export_documents(self) -> None:
        docs = [{"_id": "d1", "name": "Alice"}]
        respx.get(url__startswith=_coll_url("users", "_export")).mock(
            return_value=httpx.Response(200, json=docs)
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").export_documents()
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Bulk (mixed operations)
# ---------------------------------------------------------------------------

class TestSyncBulkMixed:
    @respx.mock
    def test_bulk_mixed(self) -> None:
        bulk_response = {
            "results": [{"status": 201, "_id": "d1", "ok": True}],
            "summary": {"total": 1, "succeeded": 1, "failed": 0},
        }
        respx.post(_coll_url("users", "_bulk")).mock(
            return_value=httpx.Response(200, json=bulk_response)
        )
        with JsonDB(api_key=API_KEY, base_url=BASE_URL) as db:
            result = db.collection("users").bulk([
                {"method": "POST", "body": {"name": "Alice"}},
                {"method": "DELETE", "id": "old-doc"},
            ])
        assert isinstance(result, BulkResult)
        assert result.summary.total == 1


# ---------------------------------------------------------------------------
# Custom headers (existing)
# ---------------------------------------------------------------------------

class TestCustomHeaders:
    @respx.mock
    def test_custom_headers_sent(self) -> None:
        route = respx.get(_coll_url("users", "abc123")).mock(
            return_value=httpx.Response(200, json=_doc_response())
        )

        with JsonDB(api_key=API_KEY, base_url=BASE_URL, headers={"X-Custom": "value"}) as db:
            db.collection("users").get("abc123")

        request = route.calls[0].request
        assert request.headers["x-custom"] == "value"
