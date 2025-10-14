# Modernized Airtable Client

This document describes the modernized `AirtableClient` class that provides a clean, production-ready interface for interacting with Airtable's API using Personal Access Tokens (PAT).

## Overview

The modernized client offers:

- ✅ **PAT Authentication**: Uses modern Personal Access Token authentication instead of legacy API keys
- ✅ **Environment Variables**: Automatically reads credentials from `AIRTABLE_TOKEN` and `AIRTABLE_BASE_ID`
- ✅ **Automatic Pagination**: Handles pagination transparently when fetching records
- ✅ **Rate Limiting**: Built-in retry logic for HTTP 429 (rate limit) errors
- ✅ **Type Hints**: Full type annotations for better IDE support and type checking
- ✅ **Clean API**: Simplified method signatures that are easy to use and understand
- ✅ **Logging**: Comprehensive logging for debugging and monitoring
- ✅ **Error Handling**: Graceful error handling with helpful error messages

## Installation

Install the package in development mode:

```bash
pip install -e .
```

Or install from PyPI (once published):

```bash
pip install pyairtable
```

## Quick Start

### 1. Set Up Environment Variables

```bash
# Windows PowerShell
$env:AIRTABLE_TOKEN = "patXXXXXXXXXXXXXX"
$env:AIRTABLE_BASE_ID = "appXXXXXXXXXXXXXX"

# Linux/Mac
export AIRTABLE_TOKEN="patXXXXXXXXXXXXXX"
export AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"
```

### 2. Run the Demo

```bash
python demo.py
```

### 3. Use in Your Code

```python
from pyairtable import AirtableClient

# Initialize client (reads from environment variables)
client = AirtableClient()

# Or provide credentials explicitly
client = AirtableClient(
    token="patXXXXXXXXXXXXXX",
    base_id="appXXXXXXXXXXXXXX"
)

# Fetch all records
records = client.get_records("TableName")

# Create a record
new_record = client.create_record("TableName", {
    "Name": "John Doe",
    "Email": "john@example.com"
})

# Update a record
updated = client.update_record("TableName", "recXXXXXXXXXXXXXX", {
    "Status": "Active"
})

# Delete a record
client.delete_record("TableName", "recXXXXXXXXXXXXXX")
```

## API Reference

### AirtableClient

#### Constructor

```python
AirtableClient(
    token: Optional[str] = None,
    base_id: Optional[str] = None,
    *,
    timeout: Optional[tuple[int, int]] = None,
    enable_retries: bool = True,
    endpoint_url: str = "https://api.airtable.com"
)
```

**Parameters:**
- `token`: Personal Access Token (reads from `AIRTABLE_TOKEN` if not provided)
- `base_id`: Base ID starting with 'app' (reads from `AIRTABLE_BASE_ID` if not provided)
- `timeout`: Optional tuple of (connect_timeout, read_timeout) in seconds
- `enable_retries`: Enable automatic retry on rate limits (default: True)
- `endpoint_url`: API endpoint URL (for testing/proxying)

---

### Methods

#### get_records()

Fetch records from a table with optional filtering and sorting.

```python
records = client.get_records(
    table_name="Users",
    filters="{Status} = 'Active'",
    fields=["Name", "Email"],
    sort=[("Name", "asc")],
    max_records=100,
    view="Grid view"
)
```

**Parameters:**
- `table_name`: Name or ID of the table
- `filters`: Optional Airtable formula string for filtering
- `fields`: List of field names to retrieve (None = all fields)
- `sort`: List of (field_name, direction) tuples
- `max_records`: Maximum records to return
- `view`: Name of view to use

**Returns:** List of record dictionaries

---

#### create_record()

Create a single record.

```python
record = client.create_record(
    table_name="Users",
    data={"Name": "Alice", "Email": "alice@example.com"},
    typecast=False
)
```

**Parameters:**
- `table_name`: Name or ID of the table
- `data`: Dictionary of field names to values
- `typecast`: Let Airtable convert string values to appropriate types

**Returns:** Created record dictionary

---

#### update_record()

Update an existing record.

```python
updated = client.update_record(
    table_name="Users",
    record_id="recXXXXXXXXXXXXXX",
    data={"Status": "Active"},
    replace=False,
    typecast=False
)
```

**Parameters:**
- `table_name`: Name or ID of the table
- `record_id`: ID of record to update (starts with 'rec')
- `data`: Dictionary of fields to update
- `replace`: If True, replace all fields (clear unspecified fields)
- `typecast`: Let Airtable convert string values to appropriate types

**Returns:** Updated record dictionary

---

#### delete_record()

Delete a record.

```python
result = client.delete_record(
    table_name="Users",
    record_id="recXXXXXXXXXXXXXX"
)
```

**Parameters:**
- `table_name`: Name or ID of the table
- `record_id`: ID of record to delete

**Returns:** Dictionary with `{'id': 'recXXX', 'deleted': True}`

---

#### batch_create()

Create multiple records in batches (max 10 per request).

```python
records = client.batch_create(
    table_name="Users",
    records=[
        {"Name": "Alice", "Status": "Active"},
        {"Name": "Bob", "Status": "Inactive"},
    ],
    typecast=False
)
```

---

#### batch_update()

Update multiple records in batches.

```python
updated = client.batch_update(
    table_name="Users",
    updates=[
        {"id": "recXXX", "fields": {"Status": "Active"}},
        {"id": "recYYY", "fields": {"Status": "Inactive"}},
    ],
    replace=False,
    typecast=False
)
```

---

#### batch_delete()

Delete multiple records in batches.

```python
deleted = client.batch_delete(
    table_name="Users",
    record_ids=["recXXX", "recYYY", "recZZZ"]
)
```

---

#### get_record()

Retrieve a single record by ID.

```python
record = client.get_record(
    table_name="Users",
    record_id="recXXXXXXXXXXXXXX"
)
```

---

## Advanced Features

### Logging

Enable detailed logging to debug API requests:

```python
from pyairtable.utils import setup_logging

# Enable DEBUG level logging
setup_logging("DEBUG")

# Now all API calls will be logged
client = AirtableClient()
records = client.get_records("Users")  # This will be logged
```

### Custom Timeouts

Configure connection and read timeouts:

```python
client = AirtableClient(
    timeout=(5, 30)  # 5 seconds to connect, 30 seconds to read
)
```

### Disable Retries

Disable automatic retry logic:

```python
client = AirtableClient(enable_retries=False)
```

### Using Filters

Use Airtable formulas to filter records:

```python
# Simple filter
records = client.get_records(
    "Users",
    filters="{Status} = 'Active'"
)

# Complex filter
records = client.get_records(
    "Users",
    filters="AND({Status} = 'Active', {Age} > 21, {City} = 'New York')"
)

# Using OR
records = client.get_records(
    "Users",
    filters="OR({Status} = 'Active', {Status} = 'Pending')"
)
```

### Sorting Records

Sort by one or more fields:

```python
# Sort by single field
records = client.get_records(
    "Users",
    sort=[("Name", "asc")]
)

# Sort by multiple fields
records = client.get_records(
    "Users",
    sort=[("Status", "desc"), ("Name", "asc")]
)
```

## Integration Examples

### Django Integration

```python
# settings.py
import os

AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# views.py
from django.conf import settings
from pyairtable import AirtableClient

client = AirtableClient(
    token=settings.AIRTABLE_TOKEN,
    base_id=settings.AIRTABLE_BASE_ID
)

def get_users(request):
    users = client.get_records("Users", filters="{Status} = 'Active'")
    return JsonResponse({"users": users})
```

### Flask Integration

```python
from flask import Flask, jsonify
from pyairtable import AirtableClient
import os

app = Flask(__name__)
client = AirtableClient(
    token=os.getenv("AIRTABLE_TOKEN"),
    base_id=os.getenv("AIRTABLE_BASE_ID")
)

@app.route("/users")
def get_users():
    users = client.get_records("Users")
    return jsonify(users)

@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    record = client.create_record("Users", data)
    return jsonify(record), 201
```

### Automation Script

```python
#!/usr/bin/env python3
"""
Daily automation script to sync data with Airtable.
"""
from pyairtable import AirtableClient
from pyairtable.utils import setup_logging
import os

setup_logging("INFO")
client = AirtableClient()

# Fetch active users
active_users = client.get_records(
    "Users",
    filters="{Status} = 'Active'"
)

# Process and update
for user in active_users:
    user_id = user["id"]
    # ... do some processing ...
    client.update_record("Users", user_id, {
        "LastProcessed": "2025-10-14"
    })

print(f"Processed {len(active_users)} users")
```

## Migration Guide

### From Legacy API

If you're currently using the older API, here's how to migrate:

**Old Code:**
```python
from pyairtable import Api

api = Api("keyXXXXXXXXXXXXXX")  # Old API key
table = api.table("appXXX", "TableName")
records = table.all()
record = table.create({"Name": "Alice"})
```

**New Code:**
```python
from pyairtable import AirtableClient

client = AirtableClient(
    token="patXXXXXXXXXXXXXX",  # Personal Access Token
    base_id="appXXX"
)
records = client.get_records("TableName")
record = client.create_record("TableName", {"Name": "Alice"})
```

### Key Differences

1. **Authentication**: Use PAT (`pat...`) instead of API keys (`key...`)
2. **Base-Level Client**: Initialize with base_id instead of accessing per-table
3. **Method Names**: More intuitive method names (`get_records` vs `all`)
4. **Environment Variables**: Built-in support for env vars

## Error Handling

```python
import requests
from pyairtable import AirtableClient

client = AirtableClient()

try:
    record = client.get_record("Users", "recXXXXXXXXXXXXXX")
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print("Record not found")
    elif e.response.status_code == 401:
        print("Invalid token")
    elif e.response.status_code == 429:
        print("Rate limited (should auto-retry)")
    else:
        print(f"HTTP Error: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Best Practices

1. **Use Environment Variables**: Never hardcode tokens in your code
2. **Enable Logging**: Use `setup_logging()` during development
3. **Use Batch Operations**: For multiple records, use `batch_*` methods
4. **Handle Errors**: Always wrap API calls in try/except blocks
5. **Set Timeouts**: Configure appropriate timeouts for your use case
6. **Use Filters**: Filter on the server side rather than fetching all records

## Support

For issues and questions:
- GitHub Issues: [github.com/gtalarico/pyairtable](https://github.com/gtalarico/pyairtable)
- Documentation: [pyairtable.rtfd.org](https://pyairtable.rtfd.org)
- Airtable API Docs: [airtable.com/developers/web/api](https://airtable.com/developers/web/api)

## License

MIT License - See LICENSE file for details.
