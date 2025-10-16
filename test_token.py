#!/usr/bin/env python3
"""Test script to verify Airtable token permissions"""

import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('AIRTABLE_TOKEN')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')

if not TOKEN or not BASE_ID:
    print("❌ Missing AIRTABLE_TOKEN or AIRTABLE_BASE_ID in .env")
    exit(1)

print(f"Testing token: {TOKEN[:20]}...")
print(f"Base ID: {BASE_ID}\n")

try:
    api = Api(TOKEN)
    base = api.base(BASE_ID)
    
    # Try to get schema
    print("📋 Fetching schema...")
    meta = base.schema()
    
    print(f"✅ Schema access OK\n")
    print(f"📊 Found {len(meta.tables)} tables:\n")
    
    # Try to access each table
    for t in meta.tables:
        try:
            count = len(base.table(t.name).all())
            print(f"✅ {t.name:<40} ({count} records)")
        except Exception as e:
            error_msg = str(e)
            if 'permission' in error_msg.lower() or 'forbidden' in error_msg.lower():
                print(f"❌ {t.name:<40} (PERMISSION DENIED)")
            else:
                print(f"⚠️  {t.name:<40} ({str(e)[:50]}...)")
    
    print("\n✅ Token verification complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
