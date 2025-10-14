# 🌐 Local Server Guide - Table Browser

## Server is Running! 🚀

Your local development server is now running at:
- **Main URL**: http://localhost:5000
- **API Status**: http://localhost:5000/api/status
- **Tables API**: http://localhost:5000/api/tables

---

## ✨ New Features Added

### 1. **Tables Browser UI**
The web interface now includes a dynamic table browser that shows:
- 📋 All tables in your Airtable base
- 🔍 Field definitions for each table
- 👁️ Available views
- 📊 Record viewer (first 10 records)

### 2. **Interactive Features**
- **Load Tables Button** - Fetches and displays all tables from your base
- **View Records Button** - Shows sample records from any table
- **Open API Button** - Opens the raw JSON API response
- **Expandable Details** - Click to view fields and views

### 3. **New API Endpoint**
```
GET /api/tables
```
Returns complete schema information for all tables including:
- Table ID, name, and description
- All fields with their types
- All views with their types

---

## 📝 How to Use

### Step 1: Configure Your Airtable Credentials

The server is currently in **demo mode** because Airtable credentials are not set.

**Set your credentials in PowerShell:**
```powershell
$env:AIRTABLE_TOKEN = "your_personal_access_token_here"
$env:AIRTABLE_BASE_ID = "your_base_id_here"
```

**Then restart the server:**
```powershell
# Press Ctrl+C to stop, then run:
.\.venv\Scripts\python.exe server.py
```

### Step 2: Access the Web Interface

Open your browser and go to:
```
http://localhost:5000
```

### Step 3: Browse Your Tables

1. Click the **"Load Tables"** button
2. The UI will fetch all tables from your Airtable base
3. For each table, you'll see:
   - Table name and ID
   - Number of fields and views
   - Expandable sections to view details

### Step 4: View Records

1. Click **"View Records"** on any table card
2. See the first 10 records with all their fields
3. Click **"← Back to Tables"** to return to the table list

---

## 🎨 UI Features

### Table Cards Display:
```
┌─────────────────────────────────────────┐
│ 📋 Table Name                            │
│ ID: tblXXXXXXXXXXXXXX                   │
│ Fields: 8 | Views: 3                     │
│                                          │
│ 🔍 View 8 Field(s) ▼                    │
│   ┌─────────────────┐                   │
│   │ Name            │                   │
│   │ singleLineText  │                   │
│   └─────────────────┘                   │
│                                          │
│ [📊 View Records] [🔗 Open API]         │
└─────────────────────────────────────────┘
```

### Record View:
```
┌─────────────────────────────────────────┐
│ [← Back to Tables]                       │
│                                          │
│ Records from: Users (showing 10)         │
│                                          │
│ 🔖 Record ID: recXXXXXXXXXXXXXX         │
│ Created: 2025-10-14T07:00:00.000Z       │
│                                          │
│ 📝 Fields ▼                              │
│ {                                        │
│   "Name": "John Doe",                   │
│   "Email": "john@example.com"           │
│ }                                        │
└─────────────────────────────────────────┘
```

---

## 🔧 API Endpoints

### List All Tables
```bash
curl http://localhost:5000/api/tables
```

**Response:**
```json
{
  "base_id": "appXXXXXXXXXXXXXX",
  "table_count": 3,
  "tables": [
    {
      "id": "tblXXXXXXXXXXXXXX",
      "name": "Users",
      "description": "User information",
      "fields": [...],
      "views": [...]
    }
  ]
}
```

### Get Table Records
```bash
curl "http://localhost:5000/api/tables/Users/records?max_records=10"
```

### Filter Records
```bash
curl "http://localhost:5000/api/tables/Users/records?filters={Status}='Active'"
```

---

## 🎯 Current Server Status

The server shows a warning because credentials are not configured:

```
⚠️  Airtable not configured: Airtable token is required.
   The server will run in demo mode.
```

**To connect to your Airtable:**

1. Get your Personal Access Token from: https://airtable.com/create/tokens
2. Find your Base ID from your Airtable URL: `https://airtable.com/appXXXXXXXXXXXXXX/...`
3. Set environment variables (see Step 1 above)
4. Restart the server

---

## 🌟 Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| Web UI | ✅ Running | Beautiful interface at localhost:5000 |
| Tables Browser | ✅ Added | View all tables with schema |
| Records Viewer | ✅ Added | View sample records from any table |
| Field Explorer | ✅ Added | See field names and types |
| View Explorer | ✅ Added | See available views |
| API Endpoints | ✅ Working | REST API for all operations |
| Auto-reload | ✅ Active | Changes auto-update (Flask debug mode) |

---

## 🚨 Troubleshooting

### Server Not Loading?
- Check that port 5000 is not in use
- Try accessing: http://127.0.0.1:5000

### Tables Not Loading?
- Verify your Airtable credentials are set
- Check that your token has permission to read base schema
- Look at terminal for error messages

### Corporate Network / SSL Errors?
- If you see certificate errors (self-signed proxy, etc.), point Requests at your company CA bundle:
  ```powershell
  $env:AIRTABLE_CA_BUNDLE = "C:/path/to/corporate-ca.pem"
  ```
- As a last resort for local development, you can temporarily disable TLS verification:
  ```powershell
  $env:AIRTABLE_VERIFY_SSL = "0"
  ```
  > ⚠️ Only use this on trusted networks. To silence the warning banner, add `$env:AIRTABLE_SUPPRESS_SSL_WARNINGS = "1"`.

### Can't See Records?
- Ensure you have read permissions on the table
- Try with a smaller max_records value
- Check the browser console for errors (F12)

---

## 📚 Next Steps

1. **Configure Credentials** - Set your Airtable token and base ID
2. **Browse Tables** - Explore your Airtable structure
3. **Test API** - Try the REST endpoints
4. **Integrate** - Use the API in your Django/Flask apps

---

## 🎉 You're All Set!

The server is running with:
- ✅ Modern UI with table browser
- ✅ Interactive record viewer
- ✅ Complete REST API
- ✅ Auto-reload on code changes
- ✅ Beautiful, responsive design

**Open http://localhost:5000 in your browser to get started!**

Press `Ctrl+C` in the terminal to stop the server when you're done.
