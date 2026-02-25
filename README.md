# jsondb-cloud

The official Python SDK for [jsondb.cloud](https://jsondb.cloud) — a hosted JSON document database.

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

Full documentation is available at [jsondb.cloud/docs/sdks/python](https://jsondb.cloud/docs/sdks/python).
