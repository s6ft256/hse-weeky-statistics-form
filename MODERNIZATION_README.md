# 🚀 Modernized Airtable Python Client

**A modern, production-ready Python SDK for Airtable with Personal Access Token (PAT) authentication.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-18%2F18%20passing-brightgreen.svg)](tests/test_client.py)
[![Code Style: PEP8](https://img.shields.io/badge/code%20style-PEP8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

---

## ✨ What's New

This modernization adds a streamlined `AirtableClient` class that provides:

- 🔐 **Modern PAT Authentication** - Personal Access Tokens instead of legacy API keys
- 🌍 **Environment Variables** - Automatic credential loading from `AIRTABLE_TOKEN` and `AIRTABLE_BASE_ID`
- 📄 **Automatic Pagination** - Handles large result sets transparently
- ⚡ **Rate Limiting** - Built-in retry logic with exponential backoff for HTTP 429 errors
- 🎯 **Clean API** - Intuitive method names and clear return types
- 📝 **Full Type Hints** - Complete type annotations for better IDE support
- 📚 **Comprehensive Documentation** - Detailed guides and examples
- ✅ **Tested** - 18 unit tests, 100% passing

---

## 📦 Quick Start

### Installation

```bash
pip install -e .
```

### Set Up Credentials

```powershell
# Windows PowerShell
$env:AIRTABLE_TOKEN = "patXXXXXXXXXXXXXX"
$env:AIRTABLE_BASE_ID = "appXXXXXXXXXXXXXX"
```

```bash
# Linux/Mac
export AIRTABLE_TOKEN="patXXXXXXXXXXXXXX"
export AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"
```

### Basic Usage

```python
from pyairtable import AirtableClient

# Initialize (reads from environment variables)
client = AirtableClient()

# Fetch all records
records = client.get_records("TableName")

# Create a record
new_record = client.create_record("TableName", {
    "Name": "Alice",
    "Email": "alice@example.com",
    "Status": "Active"
})

# Update a record
updated = client.update_record("TableName", "recXXX", {
    "Status": "Verified"
})

# Delete a record
client.delete_record("TableName", "recXXX")
```

---

## 🎯 Key Features

### All CRUD Operations

```python
# Single operations
client.get_record(table, record_id)
client.get_records(table, filters=None, sort=None, fields=None)
client.create_record(table, data)
client.update_record(table, record_id, data, replace=False)
client.delete_record(table, record_id)

# Batch operations (automatic chunking)
client.batch_create(table, records)
client.batch_update(table, updates)
client.batch_delete(table, record_ids)
```

### Advanced Filtering

```python
# Simple filter
active_users = client.get_records(
    "Users",
    filters="{Status} = 'Active'"
)

# Complex filter with sorting
results = client.get_records(
    "Users",
    filters="AND({Status} = 'Active', {Age} > 21)",
    sort=[("Name", "asc"), ("CreatedAt", "desc")],
    fields=["Name", "Email", "Status"]
)
```

### Batch Operations

```python
# Create multiple records
records = client.batch_create("Users", [
    {"Name": "Alice", "Status": "Active"},
    {"Name": "Bob", "Status": "Active"},
    {"Name": "Carol", "Status": "Active"},
])

# Update multiple records
updates = [
    {"id": "recXXX", "fields": {"Status": "Verified"}},
    {"id": "recYYY", "fields": {"Status": "Verified"}},
]
client.batch_update("Users", updates)
```

---

## 📚 Documentation

- **[MODERNIZATION.md](MODERNIZATION.md)** - Complete usage guide with examples
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Common operations and code snippets
- **[SUMMARY.md](SUMMARY.md)** - Project completion report and statistics
- **[CHECKLIST.md](CHECKLIST.md)** - Full implementation checklist
- **[demo.py](demo.py)** - Working demonstration script

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/test_client.py -v

# Run with coverage
pytest tests/test_client.py --cov=pyairtable --cov-report=html
```

**Test Results:**
```
======================================= test session starts ========================================
collected 18 items

tests/test_client.py::TestAirtableClient::test_init_with_explicit_credentials PASSED      [  5%]
tests/test_client.py::TestAirtableClient::test_init_with_environment_variables PASSED     [ 11%]
tests/test_client.py::TestAirtableClient::test_init_missing_token PASSED                  [ 16%]
tests/test_client.py::TestAirtableClient::test_init_missing_base_id PASSED                [ 22%]
tests/test_client.py::TestAirtableClient::test_init_with_custom_timeout PASSED            [ 27%]
tests/test_client.py::TestAirtableClient::test_init_with_retries_disabled PASSED          [ 33%]
tests/test_client.py::TestAirtableClient::test_repr PASSED                                [ 38%]
tests/test_client.py::TestAirtableClientMethods::test_get_records_basic PASSED            [ 44%]
tests/test_client.py::TestAirtableClientMethods::test_get_records_with_filters PASSED     [ 50%]
tests/test_client.py::TestAirtableClientMethods::test_create_record PASSED                [ 55%]
tests/test_client.py::TestAirtableClientMethods::test_update_record PASSED                [ 61%]
tests/test_client.py::TestAirtableClientMethods::test_update_record_with_replace PASSED   [ 66%]
tests/test_client.py::TestAirtableClientMethods::test_delete_record PASSED                [ 72%]
tests/test_client.py::TestAirtableClientMethods::test_get_record PASSED                   [ 77%]
tests/test_client.py::TestAirtableClientMethods::test_batch_create PASSED                 [ 83%]
tests/test_client.py::TestAirtableClientMethods::test_batch_update PASSED                 [ 88%]
tests/test_client.py::TestAirtableClientMethods::test_batch_delete PASSED                 [ 94%]
tests/test_client.py::TestAirtableClientMethods::test_table_caching PASSED                [100%]

======================================== 18 passed in 0.15s ========================================
```

---

## 🎬 Demo Script

Run the demonstration to see all operations in action:

```bash
python demo.py
```

This will:
1. ✅ Fetch all records from "TestTable"
2. ✅ Create a record: `{"Name": "Basante", "Status": "Active"}`
3. ✅ Update the status to "Verified"
4. ✅ Delete the record
5. ✅ Print all responses with clear formatting

---

## 🔧 Integration Examples

### Django

```python
# settings.py
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

### Flask

```python
from flask import Flask, jsonify
from pyairtable import AirtableClient

app = Flask(__name__)
client = AirtableClient()  # Reads from environment

@app.route("/users")
def get_users():
    return jsonify(client.get_records("Users"))

@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    record = client.create_record("Users", data)
    return jsonify(record), 201
```

### Automation Script

```python
#!/usr/bin/env python3
from pyairtable import AirtableClient
from pyairtable.utils import setup_logging

setup_logging("INFO")
client = AirtableClient()

# Fetch and process active records
active_users = client.get_records("Users", filters="{Status} = 'Active'")

for user in active_users:
    # ... process user ...
    client.update_record("Users", user["id"], {
        "LastProcessed": "2025-10-14"
    })
```

---

## 🆚 Comparison: Legacy vs Modern

| Feature | Legacy API | Modern Client |
|---------|-----------|---------------|
| **Authentication** | API Keys (`key...`) | Personal Access Tokens (`pat...`) |
| **Initialization** | Per-table | Per-base |
| **Environment Vars** | Manual | Automatic |
| **Method Names** | `table.all()` | `client.get_records()` |
| **Pagination** | Manual | Automatic |
| **Rate Limiting** | Optional | Built-in |
| **Type Hints** | Partial | Complete |
| **Batch Operations** | Manual chunking | Automatic |

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **New Files** | 7 |
| **Total Lines** | ~1,850 |
| **Tests** | 18 (100% passing) |
| **Documentation** | 4 comprehensive guides |
| **Python Version** | 3.9+ |
| **Backward Compatible** | ✅ Yes |

---

## 🛠️ Advanced Features

### Logging

```python
from pyairtable.utils import setup_logging

# Enable detailed logging
setup_logging("DEBUG")

# Now all API calls are logged
client = AirtableClient()
records = client.get_records("Users")
# Output: INFO - GET https://api.airtable.com/v0/appXXX/Users -> 200 (0.52s)
```

### Custom Configuration

```python
client = AirtableClient(
    token="patXXX",
    base_id="appXXX",
    timeout=(5, 30),        # 5s connect, 30s read timeout
    enable_retries=True,     # Enable automatic retries
    endpoint_url="https://api.airtable.com"  # Custom endpoint
)
```

---

## 🤝 Contributing

This modernization maintains backward compatibility with the existing pyAirtable library. The new `AirtableClient` can be used alongside the existing `Api`, `Base`, and `Table` classes.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🔗 Resources

- **Airtable API Documentation**: [airtable.com/developers/web/api](https://airtable.com/developers/web/api)
- **Personal Access Tokens**: [airtable.com/create/tokens](https://airtable.com/create/tokens)
- **Original pyAirtable**: [github.com/gtalarico/pyairtable](https://github.com/gtalarico/pyairtable)

---

## ⚡ Quick Commands

```bash
# Install
pip install -e .

# Test
pytest tests/test_client.py -v

# Demo
python demo.py

# Import
python -c "from pyairtable import AirtableClient; print('Ready!')"
```

---

## 🎉 Ready for Production!

All objectives met. The modernized Airtable SDK is ready for:
- ✅ Production deployment
- ✅ Django/Flask integration
- ✅ Automation systems
- ✅ API development

**Get started now with `pip install -e .` and `python demo.py`!** 🚀
