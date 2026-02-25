"""Tests for the jsondb_cloud.errors module."""


from jsondb_cloud.errors import (
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


# ---------------------------------------------------------------------------
# JsonDBError base class
# ---------------------------------------------------------------------------

class TestJsonDBError:
    def test_basic_attributes(self) -> None:
        err = JsonDBError("something broke", code="TEST_CODE", status=418, details={"foo": "bar"})
        assert str(err) == "something broke"
        assert err.message == "something broke"
        assert err.code == "TEST_CODE"
        assert err.status == 418
        assert err.details == {"foo": "bar"}

    def test_defaults(self) -> None:
        err = JsonDBError("oops")
        assert err.code == "UNKNOWN"
        assert err.status == 0
        assert err.details == {}

    def test_is_exception(self) -> None:
        err = JsonDBError("test")
        assert isinstance(err, Exception)

    def test_repr(self) -> None:
        err = JsonDBError("test", code="X", status=400)
        r = repr(err)
        assert "JsonDBError" in r
        assert "test" in r
        assert "400" in r


# ---------------------------------------------------------------------------
# Subclass construction
# ---------------------------------------------------------------------------

class TestNotFoundError:
    def test_defaults(self) -> None:
        err = NotFoundError()
        assert err.status == 404
        assert err.code == "DOCUMENT_NOT_FOUND"
        assert err.document_id is None

    def test_with_document_id(self) -> None:
        err = NotFoundError("not found", document_id="abc123")
        assert err.document_id == "abc123"
        assert str(err) == "not found"

    def test_is_jsondb_error(self) -> None:
        assert isinstance(NotFoundError(), JsonDBError)


class TestConflictError:
    def test_defaults(self) -> None:
        err = ConflictError()
        assert err.status == 409
        assert err.code == "CONFLICT"

    def test_custom_message(self) -> None:
        err = ConflictError("already exists")
        assert str(err) == "already exists"


class TestValidationError:
    def test_defaults(self) -> None:
        err = ValidationError()
        assert err.status == 400
        assert err.code == "VALIDATION_FAILED"
        assert err.errors == []

    def test_with_errors(self) -> None:
        errors = [{"path": "/name", "message": "required", "keyword": "required"}]
        err = ValidationError("validation failed", errors=errors)
        assert err.errors == errors
        assert err.details["errors"] == errors


class TestUnauthorizedError:
    def test_defaults(self) -> None:
        err = UnauthorizedError()
        assert err.status == 401
        assert err.code == "UNAUTHORIZED"
        assert str(err) == "Unauthorized"


class TestForbiddenError:
    def test_defaults(self) -> None:
        err = ForbiddenError()
        assert err.status == 403
        assert err.code == "FORBIDDEN"


class TestQuotaExceededError:
    def test_defaults(self) -> None:
        err = QuotaExceededError()
        assert err.status == 429
        assert err.code == "QUOTA_EXCEEDED"
        assert err.limit is None
        assert err.current is None

    def test_with_limits(self) -> None:
        err = QuotaExceededError("too many docs", limit=1000, current=1001)
        assert err.limit == 1000
        assert err.current == 1001
        assert err.details["limit"] == 1000
        assert err.details["current"] == 1001


class TestRateLimitError:
    def test_defaults(self) -> None:
        err = RateLimitError()
        assert err.status == 429
        assert err.code == "RATE_LIMITED"


class TestDocumentTooLargeError:
    def test_defaults(self) -> None:
        err = DocumentTooLargeError()
        assert err.status == 413
        assert err.code == "DOCUMENT_TOO_LARGE"


class TestServerError:
    def test_defaults(self) -> None:
        err = ServerError()
        assert err.status == 500
        assert err.code == "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# create_error factory
# ---------------------------------------------------------------------------

class TestCreateError:
    def test_401_returns_unauthorized(self) -> None:
        err = create_error(401, {"error": {"code": "UNAUTHORIZED", "message": "bad key"}})
        assert isinstance(err, UnauthorizedError)
        assert str(err) == "bad key"

    def test_403_returns_forbidden(self) -> None:
        err = create_error(403, {"error": {"code": "FORBIDDEN", "message": "no access"}})
        assert isinstance(err, ForbiddenError)
        assert str(err) == "no access"

    def test_404_returns_not_found(self) -> None:
        err = create_error(404, {"error": {"code": "DOCUMENT_NOT_FOUND", "message": "gone"}})
        assert isinstance(err, NotFoundError)

    def test_404_with_document_id(self) -> None:
        err = create_error(404, {
            "error": {
                "code": "DOCUMENT_NOT_FOUND",
                "message": "not found",
                "details": {"documentId": "abc"},
            }
        })
        assert isinstance(err, NotFoundError)
        assert err.document_id == "abc"

    def test_409_returns_conflict(self) -> None:
        err = create_error(409, {"error": {"code": "CONFLICT", "message": "dup"}})
        assert isinstance(err, ConflictError)

    def test_413_returns_doc_too_large(self) -> None:
        err = create_error(413, {"error": {"code": "DOCUMENT_TOO_LARGE", "message": "big"}})
        assert isinstance(err, DocumentTooLargeError)

    def test_429_rate_limited(self) -> None:
        err = create_error(429, {"error": {"code": "RATE_LIMITED", "message": "slow down"}})
        assert isinstance(err, RateLimitError)

    def test_429_quota_exceeded(self) -> None:
        err = create_error(429, {"error": {"code": "QUOTA_EXCEEDED", "message": "over limit"}})
        assert isinstance(err, QuotaExceededError)

    def test_400_validation(self) -> None:
        err = create_error(400, {
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "invalid",
                "details": {
                    "errors": [{"path": "/name", "message": "required", "keyword": "required"}],
                },
            }
        })
        assert isinstance(err, ValidationError)
        assert len(err.errors) == 1

    def test_400_generic(self) -> None:
        err = create_error(400, {"error": {"code": "BAD_REQUEST", "message": "bad"}})
        assert isinstance(err, JsonDBError)
        assert not isinstance(err, ValidationError)
        assert err.status == 400

    def test_500_returns_server_error(self) -> None:
        err = create_error(500, {"error": {"message": "boom"}})
        assert isinstance(err, ServerError)

    def test_502_returns_server_error(self) -> None:
        err = create_error(502, {"error": {"message": "gateway"}})
        assert isinstance(err, ServerError)

    def test_unknown_status(self) -> None:
        err = create_error(418, {"error": {"code": "TEAPOT", "message": "I'm a teapot"}})
        assert isinstance(err, JsonDBError)
        assert err.status == 418
        assert err.code == "TEAPOT"

    def test_missing_error_key(self) -> None:
        err = create_error(500, {})
        assert isinstance(err, ServerError)
        assert str(err) == "Unknown error"

    def test_empty_body(self) -> None:
        err = create_error(404, {"error": {}})
        assert isinstance(err, NotFoundError)

    def test_inheritance_chain(self) -> None:
        """All error subclasses should be catchable as JsonDBError."""
        classes = [
            NotFoundError, ConflictError, ValidationError, UnauthorizedError,
            ForbiddenError, QuotaExceededError, RateLimitError,
            DocumentTooLargeError, ServerError,
        ]
        for cls in classes:
            err = cls()
            assert isinstance(err, JsonDBError)
            assert isinstance(err, Exception)
