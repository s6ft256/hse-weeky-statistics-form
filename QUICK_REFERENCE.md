# Quick Reference Guide - AirtableClient

## Setup

```python
from pyairtable import AirtableClient
from pyairtable.utils import setup_logging

# Optional: Enable logging
setup_logging("INFO")  # or "DEBUG" for detailed logs

# Initialize client
client = AirtableClient()  # Reads from environment variables
# OR
client = AirtableClient(token="patXXX", base_id="appXXX")
```

## Common Operations

### 1. Fetch All Records
```python
# Get all records
records = client.get_records("TableName")

# With specific fields only
records = client.get_records("TableName", fields=["Name", "Email", "Status"])

# Limited number
records = client.get_records("TableName", max_records=10)
```

### 2. Filter Records
```python
# Simple filter
active = client.get_records("Users", filters="{Status} = 'Active'")

# Multiple conditions (AND)
filtered = client.get_records(
    "Users",
    filters="AND({Status} = 'Active', {Age} > 21)"
)

# Multiple conditions (OR)
filtered = client.get_records(
    "Users",
    filters="OR({Status} = 'Active', {Status} = 'Pending')"
)

# Complex nested conditions
filtered = client.get_records(
    "Users",
    filters="AND(OR({Type} = 'A', {Type} = 'B'), {Status} = 'Active')"
)
```

### 3. Sort Records
```python
# Single field ascending
records = client.get_records("Users", sort=[("Name", "asc")])

# Multiple fields
records = client.get_records(
    "Users",
    sort=[("Status", "desc"), ("Name", "asc")]
)

# With filter and sort combined
records = client.get_records(
    "Users",
    filters="{Status} = 'Active'",
    sort=[("CreatedAt", "desc")]
)
```

### 4. Create Records
```python
# Single record
record = client.create_record("Users", {
    "Name": "John Doe",
    "Email": "john@example.com",
    "Status": "Active"
})
print(f"Created: {record['id']}")

# Multiple records (batch)
records = client.batch_create("Users", [
    {"Name": "Alice", "Status": "Active"},
    {"Name": "Bob", "Status": "Inactive"},
    {"Name": "Carol", "Status": "Active"},
])
print(f"Created {len(records)} records")
```

### 5. Update Records
```python
# Partial update (keeps other fields)
updated = client.update_record("Users", "recXXX", {
    "Status": "Active"
})

# Full replacement (clears other fields)
replaced = client.update_record("Users", "recXXX", {
    "Name": "New Name",
    "Email": "new@example.com"
}, replace=True)

# Batch update
updates = [
    {"id": "recXXX", "fields": {"Status": "Active"}},
    {"id": "recYYY", "fields": {"Status": "Inactive"}},
]
updated = client.batch_update("Users", updates)
```

### 6. Delete Records
```python
# Single record
result = client.delete_record("Users", "recXXX")

# Multiple records (batch)
results = client.batch_delete("Users", ["recXXX", "recYYY", "recZZZ"])
print(f"Deleted {len(results)} records")
```

### 7. Get Single Record
```python
# By ID
record = client.get_record("Users", "recXXX")
print(record["fields"]["Name"])
```

## Advanced Examples

### Process All Active Records
```python
# Fetch all active users
active_users = client.get_records(
    "Users",
    filters="{Status} = 'Active'",
    fields=["Name", "Email", "LastProcessed"]
)

# Process each user
for user in active_users:
    user_id = user["id"]
    name = user["fields"]["Name"]
    
    # Do some work...
    print(f"Processing: {name}")
    
    # Update processed timestamp
    client.update_record("Users", user_id, {
        "LastProcessed": "2025-10-14"
    })
```

### Bulk Import from CSV
```python
import csv

# Read CSV
with open('users.csv', 'r') as f:
    reader = csv.DictReader(f)
    users = list(reader)

# Import in batches of 10 (Airtable limit)
# batch_create handles this automatically
records = client.batch_create("Users", users)
print(f"Imported {len(records)} records")
```

### Find and Update
```python
# Find users with old status
old_users = client.get_records(
    "Users",
    filters="{Status} = 'Legacy'"
)

# Prepare updates
updates = [
    {"id": user["id"], "fields": {"Status": "Active"}}
    for user in old_users
]

# Batch update
if updates:
    updated = client.batch_update("Users", updates)
    print(f"Updated {len(updated)} users")
```

### Conditional Create or Update
```python
def upsert_user(email, data):
    """Create user if doesn't exist, update if exists."""
    
    # Try to find existing
    existing = client.get_records(
        "Users",
        filters=f"{{Email}} = '{email}'"
    )
    
    if existing:
        # Update existing
        user_id = existing[0]["id"]
        return client.update_record("Users", user_id, data)
    else:
        # Create new
        data["Email"] = email
        return client.create_record("Users", data)

# Usage
user = upsert_user("john@example.com", {
    "Name": "John Doe",
    "Status": "Active"
})
```

### Archive Old Records
```python
from datetime import datetime, timedelta

# Calculate date 90 days ago
cutoff_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

# Find old records
old_records = client.get_records(
    "Tasks",
    filters=f"IS_BEFORE({{CreatedAt}}, '{cutoff_date}')"
)

# Archive them (update status)
if old_records:
    updates = [
        {"id": rec["id"], "fields": {"Status": "Archived"}}
        for rec in old_records
    ]
    archived = client.batch_update("Tasks", updates)
    print(f"Archived {len(archived)} old tasks")
```

## Error Handling

```python
import requests

try:
    record = client.get_record("Users", "recXXX")
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print("Record not found")
    elif e.response.status_code == 401:
        print("Invalid credentials")
    elif e.response.status_code == 403:
        print("Permission denied")
    elif e.response.status_code == 429:
        print("Rate limited (should auto-retry)")
    else:
        print(f"HTTP Error: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

### 1. Use Specific Fields
```python
# ❌ Don't fetch all fields if you only need a few
records = client.get_records("Users")

# ✅ Only fetch what you need
records = client.get_records("Users", fields=["Name", "Email"])
```

### 2. Use Filters on Server Side
```python
# ❌ Don't filter after fetching
all_users = client.get_records("Users")
active = [u for u in all_users if u["fields"]["Status"] == "Active"]

# ✅ Filter on the server
active = client.get_records("Users", filters="{Status} = 'Active'")
```

### 3. Use Batch Operations
```python
# ❌ Don't create one at a time
for user in users:
    client.create_record("Users", user)

# ✅ Use batch create
client.batch_create("Users", users)
```

### 4. Use Views
```python
# ✅ Leverage pre-configured views
records = client.get_records("Users", view="Active Users")
```

## Common Formula Patterns

### Dates
```python
# Records created today
filters = f"IS_SAME({{Created}}, TODAY(), 'day')"

# Records older than 30 days
filters = "IS_BEFORE({Created}, DATEADD(TODAY(), -30, 'days'))"

# Records in a date range
filters = "AND(IS_AFTER({Created}, '2025-01-01'), IS_BEFORE({Created}, '2025-12-31'))"
```

### Text
```python
# Exact match
filters = "{Name} = 'John Doe'"

# Contains (case-sensitive)
filters = "FIND('john', {Name}) > 0"

# Empty field
filters = "{Email} = BLANK()"

# Not empty
filters = "{Email} != BLANK()"
```

### Numbers
```python
# Greater than
filters = "{Age} > 21"

# Range
filters = "AND({Age} >= 18, {Age} <= 65)"

# Equals
filters = "{Score} = 100"
```

### Checkboxes
```python
# Checked
filters = "{IsActive} = TRUE()"

# Unchecked
filters = "{IsActive} = FALSE()"
```

### Multiple Values
```python
# IN operator (OR)
filters = "OR({Status} = 'Active', {Status} = 'Pending', {Status} = 'New')"
```

## Environment Configuration

### Development
```powershell
# .env or set manually
$env:AIRTABLE_TOKEN = "patXXXXXXXXXXXXXX"
$env:AIRTABLE_BASE_ID = "appXXXXXXXXXXXXXX"
```

### Production (Docker)
```dockerfile
ENV AIRTABLE_TOKEN=patXXXXXXXXXXXXXX
ENV AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

### Production (Heroku)
```bash
heroku config:set AIRTABLE_TOKEN=patXXXXXXXXXXXXXX
heroku config:set AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

### Production (AWS Lambda)
Set in Lambda environment variables in AWS Console or:
```yaml
# serverless.yml
environment:
  AIRTABLE_TOKEN: ${env:AIRTABLE_TOKEN}
  AIRTABLE_BASE_ID: ${env:AIRTABLE_BASE_ID}
```

## Debugging

```python
from pyairtable.utils import setup_logging

# Enable detailed logging
setup_logging("DEBUG")

# Now all API calls will be logged
client = AirtableClient()
records = client.get_records("Users")
# Output: INFO - GET https://api.airtable.com/v0/appXXX/Users -> 200 (0.52s)
```

## Need Help?

- Documentation: `MODERNIZATION.md`
- Tests: `tests/test_client.py`
- Example: `demo.py`
- Issues: GitHub repository
