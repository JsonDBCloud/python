# README Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align README.md with the jsondb-cloud README guideline — add badges, configuration, API reference, related packages, and license sections.

**Architecture:** Single-file edit to `README.md`. No code changes. All content derived from the existing source code and the shared guideline template.

**Tech Stack:** Markdown

---

### Task 1: Add badges after the one-liner

**Files:**
- Modify: `README.md:1-3`

**Step 1: Insert badge row after the one-liner**

Add this block between the one-liner and `## Install`:

```markdown
[![PyPI version](https://img.shields.io/pypi/v/jsondb-cloud)](https://pypi.org/project/jsondb-cloud/)
[![Downloads](https://img.shields.io/pypi/dm/jsondb-cloud)](https://pypi.org/project/jsondb-cloud/)
[![CI](https://github.com/JsonDBCloud/python/actions/workflows/ci.yml/badge.svg)](https://github.com/JsonDBCloud/python/actions)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
```

**Step 2: Verify**

Visually confirm badges sit between the one-liner and Install heading with a blank line above and below.

---

### Task 2: Add Configuration section after Quick Start

**Files:**
- Modify: `README.md` (insert after the Quick Start code block, before Async Usage)

**Step 1: Insert Configuration section**

```markdown
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
```

**Step 2: Verify**

Confirm section appears between Quick Start and Async Usage.

---

### Task 3: Add API section after Configuration

**Files:**
- Modify: `README.md` (insert after Configuration, before Async Usage)

**Step 1: Insert API section**

```markdown
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
```

**Step 2: Verify**

Confirm section appears between Configuration and Async Usage.

---

### Task 4: Fix Documentation wording + add Related Packages and License

**Files:**
- Modify: `README.md` (end of file)

**Step 1: Fix Documentation section**

Change:
```
Full documentation is available at [jsondb.cloud/docs/sdks/python](https://jsondb.cloud/docs/sdks/python).
```
To:
```
Full documentation at [jsondb.cloud/docs/sdks/python](https://jsondb.cloud/docs/sdks/python).
```

**Step 2: Add Related Packages section after Documentation**

```markdown
## Related Packages

| Package | Description |
|---------|-------------|
| [@jsondb-cloud/client](https://github.com/JsonDBCloud/node) | JavaScript/TypeScript SDK |
| [@jsondb-cloud/mcp](https://github.com/JsonDBCloud/mcp) | MCP server for AI agents |
| [@jsondb-cloud/cli](https://github.com/JsonDBCloud/cli) | CLI tool |
| [jsondb-cloud](https://github.com/JsonDBCloud/python) (PyPI) | Python SDK |
```

**Step 3: Add License section at the end**

```markdown
## License

MIT
```

**Step 4: Verify**

Confirm final section order matches the guideline: Documentation > Related Packages > License.

---

### Task 5: Commit

**Step 1: Commit the changes**

```bash
git add README.md
git commit -m "docs: align README with jsondb-cloud guideline"
```
