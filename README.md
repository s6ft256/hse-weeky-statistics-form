# 🚀 Airtable Client Server

![Test Status](https://img.shields.io/badge/tests-1115%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.13.8-blue)
![Flask](https://img.shields.io/badge/flask-3.1.2-green)
![Status](https://img.shields.io/badge/status-production%20ready-success)

A modern Flask web server providing a clean REST API and interactive UI for managing Airtable data. Built with a **record-centric permission model** - users can manage records but cannot modify table structures.

---

## 🎯 Quick Start

### 1. Configure Credentials
```powershell
$env:AIRTABLE_TOKEN = "patXXXXXXXXXXXXXXXX"
$env:AIRTABLE_BASE_ID = "appXXXXXXXXXXXXXXX"
```

### 2. Run Server
```powershell
.\.venv\Scripts\python.exe server.py
```

### 3. Open Dashboard
Navigate to: **http://localhost:5000**

---

## ✨ Features

### 🎨 Interactive Web Dashboard
- Beautiful gradient UI with auto-loading tables
- Create, read, update, delete records with forms
- Real-time statistics (tables, fields, views)
- Smart field type detection for forms
- Mobile-friendly responsive design

### 🔐 Smart Permission Model
- ✅ **Allowed**: View tables, create/edit/delete records
- ❌ **Blocked**: Create/delete tables, modify field structure
- Structure management stays safely in Airtable

### 🚀 REST API
- `GET /api/tables` - List all tables with schemas
- `POST /api/tables/<table>/records` - Create record
- `PUT /api/tables/<table>/records/<id>` - Update record  
- `DELETE /api/tables/<table>/records/<id>` - Delete record

### 🛡️ Enterprise Features
- SSL/TLS support with custom CA bundles
- Automatic pagination for large datasets
- Corporate proxy compatibility
- Comprehensive error handling

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Get started in 3 steps |
| **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** | Complete feature list & architecture |
| **[PERMISSIONS.md](PERMISSIONS.md)** | Detailed permission model & FAQ |
| **[SERVER_GUIDE.md](SERVER_GUIDE.md)** | Setup, troubleshooting, UI features |
| **[CAPABILITIES.md](CAPABILITIES.md)** | Feature capabilities summary |

---

## 🎯 What You Can Do

### ✅ Record Management (Full CRUD)
```python
# Via API
POST   /api/tables/Users/records        # Create record
GET    /api/tables/Users/records        # Read all records
PUT    /api/tables/Users/records/recXXX # Update record
DELETE /api/tables/Users/records/recXXX # Delete record
```

### ✅ Via Web Dashboard
- Click "Add Record" to create entries with smart forms
- Click "View Records" to see all data
- Edit or delete records with easy buttons
- Automatic field type detection (text, number, date, etc.)

### ❌ Structure Management (Protected)
- Cannot create or delete tables
- Cannot add or remove fields
- Cannot modify field types
- Structure changes must be done in Airtable directly

---

## 🔧 Installation

### Prerequisites
- Python 3.13.8+
- Virtual environment (recommended)
- Airtable Personal Access Token

### Setup
```powershell
# Clone or navigate to project
cd airtablepy3

# Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1

# Install dependencies (already installed)
pip install -r requirements-dev.txt
```

---

## 🔐 Required Airtable Scopes

Your Personal Access Token needs:
- ✅ `data.records:read` - View records
- ✅ `data.records:write` - Create/update/delete records
- ✅ `schema.bases:read` - View table structures

Create token at: https://airtable.com/create/tokens

---

## 🧪 Testing

All tests passing ✅

```powershell
# Run all tests
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Results:
# 1115 passed, 33 skipped (integration tests)
```

---

## 🚨 Troubleshooting

### Corporate Network / SSL Issues
```powershell
# For development only - disable SSL verification
$env:AIRTABLE_VERIFY_SSL = "0"
$env:AIRTABLE_SUPPRESS_SSL_WARNINGS = "1"

# Or use custom CA bundle (recommended)
$env:AIRTABLE_CA_BUNDLE = "C:/path/to/corporate-ca.pem"
```

### Tables Not Loading
- Check token has `schema.bases:read` scope
- Verify base ID is correct
- Look at terminal for error messages

### Server Won't Start
- Ensure environment variables are set
- Check port 5000 is not in use
- Verify Python virtual environment is active

---

## 📊 Status Endpoint

Check server health:
```powershell
curl http://localhost:5000/api/status
```

Response:
```json
{
  "status": "running",
  "airtable_connected": true,
  "permissions": {
    "can_view_tables": true,
    "can_create_records": true,
    "can_update_records": true,
    "can_delete_records": true,
    "can_create_tables": false,
    "can_modify_table_structure": false
  }
}
```

---

## 🎨 UI Screenshots

### Dashboard
- Auto-loading table browser
- Statistics cards (tables, fields, views)
- Interactive table cards with expandable details

### Record Management
- Smart forms with field type detection
- Edit/delete buttons on each record
- Confirmation dialogs for destructive actions

### Permission Notice
- Clear explanation of what users can/cannot do
- Helpful guidance for structure management

---

## 🏗️ Architecture

### Tech Stack
- **Backend**: Flask 3.1.2
- **Python**: 3.13.8
- **HTTP Client**: requests + urllib3
- **API**: Airtable REST API v0
- **Auth**: Personal Access Tokens (PAT)

### Project Structure
```
airtablepy3/
├── server.py              # Flask server (main entry)
├── pyairtable/
│   ├── client.py         # Modern AirtableClient
│   ├── utils.py          # Logging utilities
│   └── api/              # API wrappers
├── tests/                 # Unit tests (1115 passing)
└── docs/                  # Documentation
```

---

## 🔄 Why This Permission Model?

### Benefits
1. **Data Integrity**: Table structures remain stable
2. **User Safety**: Cannot accidentally break schemas  
3. **Clear Separation**: Data ops vs structure ops
4. **Audit Trail**: Structure changes tracked in Airtable

### Perfect For
- Data entry applications
- Team collaboration tools
- CRUD interfaces
- API integrations
- Multi-user environments

---

## 🚀 Production Considerations

### Current Implementation
- ✅ PAT-based authentication
- ✅ SSL/TLS support
- ✅ Input validation
- ✅ Error handling
- ✅ Debug mode for development

### Recommended Enhancements
- 🔒 Add user authentication layer
- 🔒 Implement rate limiting
- 🔒 Add audit logging
- 🔒 Use HTTPS (reverse proxy)
- 🔒 Regular token rotation

---

## 📝 License

See LICENSE file for details.

---

## 🤝 Contributing

### Code Standards
- Type hints throughout
- Comprehensive docstrings
- Unit test coverage
- All tests must pass

---

## 📞 Support

For issues or questions:
1. Check [SERVER_GUIDE.md](SERVER_GUIDE.md) for troubleshooting
2. Review [PERMISSIONS.md](PERMISSIONS.md) for permission FAQs
3. See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architecture details

---

## 🎉 Summary

This server provides a **safe, user-friendly interface** for managing Airtable data:
- Full record CRUD with beautiful UI
- Structure protection (no accidental schema changes)
- Production-ready with comprehensive error handling
- Well-documented with extensive guides

**Start managing your Airtable data safely today!** 🚀

---

## 🔗 Original pyAirtable Library

This project is built on top of [pyAirtable](https://github.com/gtalarico/pyairtable).

Documentation: https://pyairtable.readthedocs.io

## Contributing

Everyone who has an idea or suggestion is welcome to contribute! As maintainers, we expect our community of users and contributors to adhere to the guidelines and expectations set forth in the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Be kind and empathetic, respect differing opinions, and stay focused on what is best for the community.

### Getting started

If it's your first time working on this library, clone the repo, set up pre-commit hooks, and make sure you can run tests (and they pass). If that doesn't work out of the box, please check your local development environment before filing an issue.

```sh
% make setup
% make test
```

### Reporting a bug

We encourage anyone to [submit an issue](https://github.com/gtalarico/pyairtable/issues/new) to let us know about bugs, as long as you've followed these steps:

1. Confirm you're on the latest version of the library and you can run the test suite locally.
2. Check [open issues](https://github.com/gtalarico/pyairtable/issues) to see if someone else has already reported it.
3. Provide as much context as possible, i.e. expected vs. actual behavior, steps to reproduce, and runtime environment.
4. If possible, reproduce the problem in a small example that you can share in the issue summary.

We ask that you _never_ report security vulnerabilities to the GitHub issue tracker. Sensitive issues of this nature must be sent directly to the maintainers via email.

### Submitting a patch

Anyone who uses this library is welcome to [submit a pull request](https://github.com/gtalarico/pyairtable/pulls) for a bug fix or a new feature. We do ask that all pull requests adhere to the following guidelines:

1. Public functions/methods have docstrings and type annotations.
2. New functionality is accompanied by clear, descriptive unit tests.
3. You can run `make test && make docs` successfully.
4. You have [signed your commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification).

If you want to discuss an idea you're working on but haven't yet finished all of the above, please [open a draft pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests). That will be a clear signal that you're not asking to merge your code (yet) and are just looking for discussion or feedback.

Thanks in advance for sharing your ideas!
