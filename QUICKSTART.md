# 🚀 Quick Start Guide

## Get Started in 3 Steps

### Step 1: Set Environment Variables
```powershell
$env:AIRTABLE_TOKEN = "patXXXXXXXXXXXXXXXX"
$env:AIRTABLE_BASE_ID = "appXXXXXXXXXXXXXXX"
```

### Step 2: Start the Server
```powershell
.\.venv\Scripts\python.exe server.py
```

### Step 3: Open Your Browser
Navigate to: http://localhost:5000

---

## 🎯 What You Can Do

### ✅ Allowed Operations
- **View** all tables and their schemas
- **Create** new records with a user-friendly form
- **Read** all records (with automatic pagination)
- **Update** field values in existing records
- **Delete** records (with confirmation)

### ❌ Not Allowed (By Design)
- Cannot create or delete tables
- Cannot add or remove fields
- Cannot change field types
- Structure management stays in Airtable

---

## 💡 Key Features

### Smart Forms
- Automatically generates forms based on field types
- Different inputs for text, numbers, dates, checkboxes, etc.
- Filters out computed fields (formulas, rollups)

### Interactive Dashboard
- Auto-loads all your tables on page load
- Shows statistics: tables, fields, views counts
- Click "View Records" to see data from any table
- Click "Add Record" to create new entries
- Edit or delete records with easy buttons

### REST API
All operations available via REST API:
- `GET /api/tables` - List all tables
- `POST /api/tables/<table>/records` - Create record
- `PUT /api/tables/<table>/records/<id>` - Update record
- `DELETE /api/tables/<table>/records/<id>` - Delete record

---

## 🔐 Required Token Scopes

Your Airtable Personal Access Token needs:
- ✅ `data.records:read`
- ✅ `data.records:write`
- ✅ `schema.bases:read`

Create token at: https://airtable.com/create/tokens

---

## 🚨 Troubleshooting

### SSL Errors?
If you're behind a corporate proxy:
```powershell
$env:AIRTABLE_VERIFY_SSL = "0"
$env:AIRTABLE_SUPPRESS_SSL_WARNINGS = "1"
```

### Tables Not Loading?
- Check your token has the required scopes
- Verify base ID is correct
- Look at terminal output for errors

### Can't Edit a Field?
Some fields are read-only:
- Formula fields
- Rollup fields
- Created time / Last modified time
- Auto number fields

---

## 📚 Full Documentation

For complete details, see:
- **PROJECT_SUMMARY.md** - Full feature list and architecture
- **PERMISSIONS.md** - Detailed permission model
- **SERVER_GUIDE.md** - Setup and troubleshooting
- **CAPABILITIES.md** - Feature capabilities

---

## 🎉 That's It!

You now have a fully functional Airtable client server that allows safe record management while protecting table structures. Happy data managing! 🚀

**Need help?** Check the documentation files or look at the terminal output for error details.
