# jsondb-cloud

The official Python SDK for [jsondb.cloud](https://jsondb.cloud) — a hosted JSON document database.

[![PyPI version](https://img.shields.io/pypi/v/jsondb-cloud)](https://pypi.org/project/jsondb-cloud/)
[![Downloads](https://img.shields.io/pypi/dm/jsondb-cloud)](https://pypi.org/project/jsondb-cloud/)
[![CI](https://github.com/JsonDBCloud/python/actions/workflows/ci.yml/badge.svg)](https://github.com/JsonDBCloud/python/actions)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-blue)](https://python.org)
[![GitHub stars](https://img.shields.io/github/stars/JsonDBCloud/python)](https://github.com/JsonDBCloud/python)
[![Last commit](https://img.shields.io/github/last-commit/JsonDBCloud/python)](https://github.com/JsonDBCloud/python)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jsondb-cloud)](https://pypi.org/project/jsondb-cloud/)

## Install

```bash
pip install jsondb-cloud
```

## Quick Start

```python
from jsondb_cloud import JsonDB

db = JsonDB(api_key="jdb_sk_live_xxxx")
users = db.collection("users")

# Create
user = users.create({"name": "Alice", "email": "alice@example.com"})

# Read
user = users.get(user["_id"])

# List with filtering
admins = users.list(filter={"role": "admin", "age": {"$gte": 21}}, sort="-createdAt", limit=10)

# Update
users.update(user["_id"], {"name": "Alice Updated", "email": "alice@example.com"})

# Patch (partial update)
users.patch(user["_id"], {"age": 31})

# Delete
users.delete(user["_id"])
```

## Configuration

```python
db = JsonDB(
    api_key="jdb_sk_live_xxxx",  # required
    project="v1",                 # project namespace (default: "v1")
    base_url="https://api.jsondb.cloud",  # API endpoint
    timeout=30.0,                 # request timeout in seconds
    max_retries=3,                # retries on 429/5xx errors
    headers={"X-Custom": "val"},  # extra headers for every request
)
```

`AsyncJsonDB` accepts the same options and supports `async with` for automatic cleanup.

## API

All methods are available on both `Collection` (sync) and `AsyncCollection` (async).

| Category | Methods |
|----------|---------|
| **CRUD** | `create`, `get`, `list`, `update`, `patch`, `json_patch`, `delete` |
| **Bulk** | `bulk_create`, `bulk` |
| **Count** | `count` |
| **Schema** | `get_schema`, `set_schema`, `remove_schema`, `validate` |
| **Versioning** | `list_versions`, `get_version`, `restore_version`, `diff_versions` |
| **Webhooks** | `create_webhook`, `list_webhooks`, `get_webhook`, `update_webhook`, `delete_webhook`, `test_webhook` |
| **Import/Export** | `import_documents`, `export_documents` |

See the [full API reference](https://jsondb.cloud/docs/sdks/python) for details.

## Async Usage

```python
from jsondb_cloud import AsyncJsonDB

async with AsyncJsonDB(api_key="jdb_sk_live_xxxx") as db:
    users = db.collection("users")
    user = await users.create({"name": "Alice"})
    page = await users.list(filter={"role": "admin"})
```

## Error Handling

```python
from jsondb_cloud import JsonDB, NotFoundError, QuotaExceededError, JsonDBError

try:
    user = users.get("nonexistent")
except NotFoundError as e:
    print(f"Not found: {e.document_id}")
except QuotaExceededError as e:
    print(f"Limit: {e.limit}, Current: {e.current}")
except JsonDBError as e:
    print(f"Error: {e.code} - {e.message} (HTTP {e.status})")
```

## Documentation

Full documentation at [jsondb.cloud/docs/sdks/python](https://jsondb.cloud/docs/sdks/python).

## Related Packages

| Package | Description |
|---------|-------------|
| [@jsondb-cloud/client](https://www.npmjs.com/package/@jsondb-cloud/client) | JavaScript/TypeScript SDK |
| [@jsondb-cloud/mcp](https://www.npmjs.com/package/@jsondb-cloud/mcp) | MCP server for AI agents |
| [@jsondb-cloud/cli](https://www.npmjs.com/package/@jsondb-cloud/cli) | CLI tool |
| [jsondb-cloud](https://pypi.org/project/jsondb-cloud/) (PyPI) | Python SDK |

## License

MIT
