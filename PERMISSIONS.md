# 🔒 Permission Model & Security

## Overview

This Airtable client server is designed with a **record-centric permission model**. Users can fully manage record data (CRUD operations) but **cannot modify table structures**.

---

## ✅ Allowed Operations

### Record Management (Full CRUD)
- **Create Records**: Add new records to existing tables with field values
- **Read Records**: View all records and their field values
- **Update Records**: Modify field values in existing records
- **Delete Records**: Remove records from tables

### Schema Viewing (Read-Only)
- **View Tables**: List all tables in the base
- **View Fields**: See field names, types, and descriptions
- **View Views**: See available views for each table

---

## ❌ Prohibited Operations

### Table Structure Modifications
- ❌ **Cannot create new tables**
- ❌ **Cannot delete tables**
- ❌ **Cannot rename tables**
- ❌ **Cannot modify table descriptions**

### Field Structure Modifications
- ❌ **Cannot add new fields**
- ❌ **Cannot delete fields**
- ❌ **Cannot rename fields**
- ❌ **Cannot change field types**
- ❌ **Cannot modify field options** (e.g., select options, validation rules)

### View Modifications
- ❌ **Cannot create views**
- ❌ **Cannot delete views**
- ❌ **Cannot modify view configurations**

---

## 🎯 Why This Model?

### Security Benefits
1. **Data Integrity**: Table structures remain stable and controlled
2. **Schema Governance**: Prevents accidental structure changes
3. **Separation of Concerns**: Data operations separate from schema management
4. **Audit Trail**: Structure changes require direct Airtable access (tracked)

### Use Cases
- **Data Entry Applications**: Allow users to add/edit records safely
- **CRUD Interfaces**: Build forms and dashboards without schema risk
- **API Integration**: Expose record operations without exposing structure
- **Multi-User Environments**: Let many users manage data, few manage schema

---

## 🛠️ How to Manage Table Structure

Table structure management must be done directly in Airtable:

1. **Go to Airtable**: https://airtable.com
2. **Open Your Base**: Navigate to the base you're working with
3. **Make Structure Changes**:
   - Add/remove fields by clicking the "+" button or field menu
   - Create tables using the "Add table" button
   - Modify field types through field settings

The server will automatically reflect these changes on the next request.

---

## 📋 API Endpoint Permissions

| Endpoint | Method | Operation | Allowed |
|----------|--------|-----------|---------|
| `/api/tables` | GET | List all tables | ✅ Yes |
| `/api/tables/<table>/records` | GET | Read records | ✅ Yes |
| `/api/tables/<table>/records` | POST | Create record | ✅ Yes |
| `/api/tables/<table>/records/<id>` | GET | Read single record | ✅ Yes |
| `/api/tables/<table>/records/<id>` | PUT | Update record | ✅ Yes |
| `/api/tables/<table>/records/<id>` | DELETE | Delete record | ✅ Yes |
| `/api/tables` | POST | Create table | ❌ **Not Implemented** |
| `/api/tables/<table>` | DELETE | Delete table | ❌ **Not Implemented** |
| `/api/tables/<table>/fields` | POST | Add field | ❌ **Not Implemented** |
| `/api/tables/<table>/fields/<id>` | DELETE | Delete field | ❌ **Not Implemented** |

---

## 🔐 Airtable Token Permissions

Your Airtable Personal Access Token must have these scopes:

### Required Scopes
- ✅ `data.records:read` - View records
- ✅ `data.records:write` - Create/update/delete records
- ✅ `schema.bases:read` - View table structures

### Optional Scopes (Not Used)
- ⚪ `schema.bases:write` - Not needed (we don't modify schemas)

---

## 💡 Field Value Editing

### Editable Field Types
Users can modify values for these field types:
- ✅ Single line text
- ✅ Long text
- ✅ Number
- ✅ Currency
- ✅ Percent
- ✅ Date
- ✅ Date/Time
- ✅ Checkbox
- ✅ Email
- ✅ URL
- ✅ Phone number
- ✅ Rating
- ✅ Single select
- ✅ Multiple select
- ✅ Attachments
- ✅ Link to another record

### Read-Only Field Types
These fields are computed and cannot be edited:
- 🔒 Formula
- 🔒 Rollup
- 🔒 Count
- 🔒 Created time
- 🔒 Last modified time
- 🔒 Created by
- 🔒 Last modified by
- 🔒 Auto number

The UI automatically filters out read-only fields from edit forms.

---

## 🚨 Error Handling

### Structure Modification Attempts
If a user attempts to modify table structure via the API, they will receive:

```json
{
  "error": "Operation not supported",
  "message": "Table structure modifications must be done directly in Airtable",
  "permission_model": "This server allows record CRUD but not schema modifications"
}
```

### Invalid Field Operations
Attempting to set values for computed fields returns:

```json
{
  "error": "Field is read-only",
  "field": "Formula Field Name",
  "message": "This field is computed and cannot be directly modified"
}
```

---

## 📚 Best Practices

### For Administrators
1. **Manage structure in Airtable**: Use the Airtable UI for all schema changes
2. **Document field purposes**: Add descriptions to help users understand fields
3. **Use validation**: Set up field validation in Airtable for data quality
4. **Monitor usage**: Check Airtable audit logs for structure changes

### For Users
1. **Focus on data**: Add and edit records through the server interface
2. **Request structure changes**: Ask admins to add/modify fields when needed
3. **Use existing fields**: Work within the current table structure
4. **Report issues**: Alert admins if fields or tables are missing

### For Developers
1. **Respect permissions**: Don't implement schema modification endpoints
2. **Cache schemas**: Reduce API calls by caching table structure
3. **Validate inputs**: Check field types before sending to Airtable
4. **Handle errors**: Provide clear messages for permission issues

---

## 🔄 Migration Path

If you need to enable schema modifications in the future:

1. **Update Token Scopes**: Add `schema.bases:write` to your token
2. **Implement Endpoints**: Add POST/PUT/DELETE for tables and fields
3. **Add Permission Checks**: Implement role-based access control
4. **Update UI**: Add table/field management interfaces
5. **Audit Everything**: Log all structure changes

For now, this server focuses on safe, reliable record management.

---

## ❓ FAQ

**Q: Why can't I add a new field through the UI?**  
A: Field addition requires modifying table structure. Please add fields directly in Airtable, and they will appear automatically in the server.

**Q: Can I change a field name?**  
A: No, field renaming is a structure change. Rename fields in Airtable directly.

**Q: What if I delete a table in Airtable?**  
A: The server will reflect this immediately. Records in that table become inaccessible.

**Q: Can I create a new table via the API?**  
A: Not through this server. Create tables in Airtable, and they will appear automatically.

**Q: How do I add a new select option?**  
A: Select field options are part of field structure. Add them in Airtable's field settings.

---

## 📝 Summary

| Category | Permission Level |
|----------|-----------------|
| **View Tables/Fields** | ✅ Full Access |
| **Read Records** | ✅ Full Access |
| **Create Records** | ✅ Full Access |
| **Update Records** | ✅ Full Access |
| **Delete Records** | ✅ Full Access |
| **Modify Structure** | ❌ No Access |

This model ensures data flexibility while maintaining structural integrity.
