# Troubleshooting Guide - Form Fixes

## Common Issues & Solutions

### Issue 1: Still Seeing 422 Errors

#### Error: "Field 'Sr.no' cannot accept the provided value"

**Solution:**
1. Hard refresh browser: **Ctrl+Shift+R**
2. Close add-record modal if open
3. Click "+ Add Record" again
4. Check that **Sr.no field is NOT shown**
5. If still shown, restart Flask server

**Why**: Sr.no should be hidden, not shown in the form

---

#### Error: "Unknown field name: 'Type of NCR...'"

**Solution:**
1. Hard refresh: **Ctrl+Shift+R**
2. Clear browser cache: **Ctrl+Shift+Delete**
3. Reload the page
4. Try creating record again

**Why**: Field names with whitespace need normalization

---

### Issue 2: Form Shows Wrong Fields

#### Problem: See auto-increment or read-only fields in form

**Solution:**
1. **Check Flask server** - Is it running?
2. Look for `[+] Airtable client initialized` in terminal
3. If not running, restart: `python final_solution.py`
4. Wait for "Running on http://127.0.0.1:8080"
5. Refresh browser

**Why**: Field filtering requires fresh schema load

---

#### Problem: See confusing/unclear field names

**Solution:**
1. This should be fixed now with normalization
2. If still seeing escape sequences like `\r\n`, try:
   - Hard refresh: **Ctrl+Shift+R**
   - Restart Flask server
   - Check `FIELD_NAME_NORMALIZATION.md` for details

**Why**: Field names should be stripped of whitespace

---

### Issue 3: Record Creation Still Failing

#### Error: Generic 422 error

**Possible Causes & Fixes:**

**A) Invalid field value**
- Check that value matches field type
- For select fields, pick from dropdown only
- For numbers, enter valid numbers
- For dates, use valid date format

**B) Required field empty**
- Check fields marked with * (asterisk)
- Fill in all required fields
- Submit again

**C) Permission issue**
- Verify token has write access to table
- Check token is not expired
- Re-generate token if needed

**D) Field still uses old name**
- Clear browser cache completely
- Restart Flask server
- Try again

---

### Issue 4: Flask Server Won't Start

#### Error: "Address already in use"

**Solution:**
1. Find process using port 8080
2. Kill it or use different port
3. Restart Flask

**Commands:**
```powershell
# Find process on port 8080
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue

# Kill the process (replace PID with actual process ID)
Stop-Process -Id <PID> -Force

# Start Flask again
python final_solution.py
```

#### Error: "Module not found"

**Solution:**
1. Ensure virtual environment is activated
2. Run: `.\.venv\Scripts\Activate.ps1`
3. Install missing packages: `pip install -r requirements.txt`
4. Start Flask: `python final_solution.py`

---

### Issue 5: Browser Issues

#### Form not loading/rendering

**Solution:**
1. **Hard refresh**: Ctrl+Shift+R
2. **Clear cache**: Ctrl+Shift+Delete
3. **Try incognito mode**: Ctrl+Shift+N
4. **Wait 5 seconds** after opening modal
5. If still broken, check browser console (F12)

#### Form looks broken/misaligned

**Solution:**
1. Refresh the page: F5
2. Check if JavaScript errors in console (F12)
3. Try different browser (Chrome, Firefox)
4. Check browser zoom level (should be 100%)

---

### Issue 6: Checking Server Status

#### Verify server is running properly

**Check terminal output for:**
```
[+] Airtable client initialized        ← Good
[*] Starting Enhanced Airtable Dashboard on http://localhost:8080    ← Good
 * Running on http://127.0.0.1:8080    ← Good
 * Debugger is active!                 ← Good
```

#### If you see errors instead:

```
❌ [!] Airtable init error    → Token/Base ID problem
❌ ModuleNotFoundError         → Missing package
❌ Syntax error                → Code problem
```

**Fix**: 
1. Check `.env` file has AIRTABLE_TOKEN and AIRTABLE_BASE_ID
2. Ensure all packages installed
3. Verify no syntax errors (check recent changes)

---

### Issue 7: Specific Error Messages

#### "This field is required"

- Fill in all required fields (marked with *)
- Try again

#### "Invalid choice"

- Select from dropdown menu only
- Don't type custom values for select fields

#### "Invalid value"

- Check value type matches field type
- Numbers should be numeric
- Dates should be valid dates
- Trim extra whitespace

#### "You do not have permission"

- Check token permissions
- Try re-generating token
- Verify table access in Airtable

---

## Debugging Steps

### Step 1: Check Server Logs

**Watch for messages like:**
```
[!] Error creating record: ...    ← Problem details
[*] Skipping table: permission    ← Permission issue
- Detected change... reloading    ← Code updated
```

### Step 2: Check Browser Console

**Press F12 and click "Console" tab**

Look for:
- **Red errors** - JavaScript problems
- **Yellow warnings** - Usually safe
- **Network failures** - API communication issues

**Example error:**
```
Failed to fetch /add_record_ajax/... - Check network response
```

### Step 3: Test Specific Table

1. Go to dashboard: http://localhost:8080
2. Click specific table (start with 6.NCR Tracker)
3. Try to add record
4. Note exact error message
5. Check error message against this guide

### Step 4: Clear Everything

If nothing works:
1. **Clear browser**: Ctrl+Shift+Delete (all time)
2. **Restart server**: Stop with Ctrl+C, then `python final_solution.py`
3. **Wait 10 seconds** for full restart
4. **Reload page**: F5
5. **Try again**

---

## Verification Checklist

Use this to verify everything is working:

- [ ] **Server running** - See "Running on http://127.0.0.1:8080"
- [ ] **Dashboard loads** - http://localhost:8080 works
- [ ] **Table shows** - Can click into a table with records
- [ ] **Add button visible** - "+ Add Record" button shows
- [ ] **Modal opens** - Click button, modal appears
- [ ] **Fields show** - Form has editable fields
- [ ] **Sr.no hidden** - Auto-increment fields not in form
- [ ] **Field names clean** - No escape sequences visible
- [ ] **Form submits** - Can fill fields and click Create
- [ ] **Record created** - Modal closes, record appears
- [ ] **Success message** - Toast shows "Record created"
- [ ] **Multiple tables** - Works in different tables

---

## Contact Support

If you can't resolve the issue:

1. **Check documentation**:
   - `COMPLETE_FORM_FIXES.md` - Overview
   - `AUTO_INCREMENT_FIX.md` - Auto-increment details
   - `FIELD_NAME_NORMALIZATION.md` - Whitespace fix
   - `FORM_FIX_SUMMARY.md` - Technical details

2. **Review error message** - See what it says exactly

3. **Check terminal logs** - What does Flask show?

4. **Check browser console** - Are there JavaScript errors?

5. **Restart everything**:
   - Close browser
   - Stop Flask (Ctrl+C)
   - Restart Flask
   - Open fresh browser window
   - Clear cache
   - Try again

---

## Quick Fixes (Try These First)

**Not working?** Try these in order:

1. **Hard refresh**: Ctrl+Shift+R ← Do this first!
2. **Clear cache**: Ctrl+Shift+Delete, then F5
3. **Try incognito**: Ctrl+Shift+N
4. **Restart server**: Ctrl+C, then `python final_solution.py`
5. **Restart browser**: Close all tabs, reopen
6. **Check documentation**: Read the relevant .md file

---

## When to Restart Server

**Restart if you see:**
- [ ] Changes aren't taking effect
- [ ] Form still shows non-editable fields
- [ ] Server stops responding
- [ ] Error messages about modules
- [ ] After editing code files

**How to restart:**
1. Press Ctrl+C in terminal (stops server)
2. Wait 2 seconds
3. Run: `python final_solution.py`
4. Wait for "Running on http://..."
5. Refresh browser

---

## Success Indicators

You'll know it's working when:

✅ **Dashboard loads** - No errors, clean interface
✅ **Tables list** - All accessible tables shown
✅ **Add Record modal** - Opens cleanly
✅ **Form displays** - Shows only editable fields
✅ **No Sr.no** - Auto-increment fields hidden
✅ **Field names clear** - No escape sequences visible
✅ **Form fills** - Can enter values
✅ **Submit works** - Can click Create
✅ **Record appears** - New row added to table
✅ **Success message** - Toast notification shows

**If all above are ✅, you're good!**

---

## FAQ

**Q: Why doesn't Sr.no show in the form?**
A: Because it's auto-generated by Airtable. You can't set it manually.

**Q: Why are my field names showing escape sequences?**
A: Old cache/browser data. Clear cache and refresh.

**Q: Can I manually enter a Sr.no value?**
A: No, Airtable auto-generates it. The API rejects manual values.

**Q: Will this work in production?**
A: Yes, all fixes are production-ready.

**Q: Do I need to update Airtable?**
A: No, this is purely on the application side.

---

## Support Resources

- **Server logs** - Terminal window
- **Browser console** - F12
- **Documentation** - See .md files in folder
- **Code** - `final_solution.py`
- **Errors** - Read them carefully, they usually explain what's wrong

Most issues can be resolved with:
1. Hard refresh
2. Clear cache  
3. Restart server

**Try these before anything else!**
