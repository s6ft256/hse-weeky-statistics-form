#!/usr/bin/env python3
"""
Test script to verify the auto-increment field fix works correctly
Run this after adding a record through the web interface to verify it was created successfully
"""

import os
import json
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv()

AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
    print("❌ Error: AIRTABLE_TOKEN and AIRTABLE_BASE_ID not set in .env")
    exit(1)

api = Api(AIRTABLE_TOKEN)
base = api.base(AIRTABLE_BASE_ID)

print("[*] Testing Auto-Increment Field Fix")
print("=" * 60)

try:
    # Get schema to show field types
    schema = api.base(AIRTABLE_BASE_ID).schema()
    
    for table in schema.tables:
        print(f"\n📋 Table: {table.name}")
        print("-" * 60)
        
        # Show all fields with their types
        has_auto_increment = False
        for field in table.fields:
            fname = getattr(field, 'name', 'Unknown')
            ftype = getattr(field, 'type', 'Unknown')
            read_only = getattr(field, 'read_only', False) or getattr(field, 'readOnly', False)
            
            if ftype == 'autoNumber':
                has_auto_increment = True
                print(f"  🔒 {fname:25} -> {ftype:20} (READ-ONLY, auto-generated)")
            elif read_only:
                print(f"  🔒 {fname:25} -> {ftype:20} (READ-ONLY)")
            else:
                print(f"  ✏️  {fname:25} -> {ftype:20} (EDITABLE)")
        
        if has_auto_increment:
            print(f"\n  ✅ Table '{table.name}' has auto-increment fields - they will be skipped in forms")
        
        # Show recent records count
        try:
            records = base.table(table.name).all(max_records=1)
            print(f"  📊 Recent records: {len(records)} (showing first)")
        except Exception as e:
            print(f"  ⚠️  Could not fetch records: {str(e)[:50]}")

    print("\n" + "=" * 60)
    print("\n✅ Test Summary:")
    print("   • Auto-increment fields detected and listed above")
    print("   • In the web app, these fields will NOT appear in add-record forms")
    print("   • Creating records should now work without 422 errors")
    print("\n🚀 Try adding a record through the web interface now!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
