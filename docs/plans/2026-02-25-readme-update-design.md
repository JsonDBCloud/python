# README Update Design

Align `README.md` with the jsondb-cloud README guideline.

## Changes

### Add: Badges (after one-liner)
- PyPI version, PyPI downloads, CI (`ci.yml`), Python >= 3.9, License: MIT

### Keep: Install, Quick Start
No changes needed.

### Add: Configuration section
Show `JsonDB` constructor options in a table:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | *(required)* | API key (`jdb_sk_live_*` or `jdb_sk_test_*`) |
| `project` | `"v1"` | Project name |
| `base_url` | `"https://api.jsondb.cloud"` | API base URL |
| `timeout` | `30.0` | Request timeout in seconds |
| `max_retries` | `3` | Retries on 429/5xx |
| `headers` | `None` | Extra headers for every request |

Note: `AsyncJsonDB` accepts the same options.

### Add: API / Features section
One-line descriptions grouped by category:
- CRUD: `create`, `get`, `list`, `update`, `patch`, `json_patch`, `delete`
- Bulk: `bulk_create`, `bulk`
- Count: `count`
- Schema: `get_schema`, `set_schema`, `remove_schema`, `validate`
- Versioning: `list_versions`, `get_version`, `restore_version`, `diff_versions`
- Webhooks: `create_webhook`, `list_webhooks`, `get_webhook`, `update_webhook`, `delete_webhook`, `test_webhook`
- Import/Export: `import_documents`, `export_documents`

### Keep: Async Usage, Error Handling
No changes needed. Position after API section.

### Tweak: Documentation
Change "Full documentation is available at" to "Full documentation at".

### Add: Related Packages
Standard cross-reference table from guideline.

### Add: License
`MIT`

## Final section order
1. Title + one-liner
2. Badges
3. Install
4. Quick Start
5. Configuration
6. API
7. Async Usage
8. Error Handling
9. Documentation
10. Related Packages
11. License
