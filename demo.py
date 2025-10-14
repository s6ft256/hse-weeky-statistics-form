#!/usr/bin/env python3
"""
Demo script for the modernized AirtableClient.

This script demonstrates how to use the AirtableClient for common CRUD operations:
- Fetching all records from a table
- Creating a new record
- Updating a record
- Deleting a record

Prerequisites:
    Set the following environment variables:
    - AIRTABLE_TOKEN: Your Personal Access Token
    - AIRTABLE_BASE_ID: Your base ID

    Or you can hardcode them in this script (not recommended for production).

Usage:
    python demo.py
"""

import json
import os
import sys
from typing import Any, Dict

from pyairtable import AirtableClient
from pyairtable.utils import setup_logging


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_record(record: Dict[str, Any], prefix: str = "") -> None:
    """Pretty print a record."""
    print(f"{prefix}Record ID: {record['id']}")
    print(f"{prefix}Created: {record.get('createdTime', 'N/A')}")
    print(f"{prefix}Fields:")
    for field, value in record.get("fields", {}).items():
        print(f"{prefix}  - {field}: {value}")


def main() -> int:
    """
    Main demo function demonstrating AirtableClient usage.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Enable logging to see what's happening
    setup_logging("INFO")
    
    print_section("Airtable Client Demo")
    
    # Configuration
    # You can hardcode these for testing, but using environment variables is recommended
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = "TestTable"  # Change this to match your table name
    
    # Validate credentials
    if not token:
        print("❌ Error: AIRTABLE_TOKEN environment variable not set")
        print("   Please set it with: export AIRTABLE_TOKEN='your_token'")
        return 1
    
    if not base_id:
        print("❌ Error: AIRTABLE_BASE_ID environment variable not set")
        print("   Please set it with: export AIRTABLE_BASE_ID='your_base_id'")
        return 1
    
    try:
        # Initialize the client
        print(f"🔌 Connecting to base: {base_id}")
        print(f"📋 Using table: {table_name}")
        
        client = AirtableClient(token=token, base_id=base_id)
        print(f"✅ Client initialized: {client}\n")
        
        # =====================================================================
        # STEP 1: Fetch all records
        # =====================================================================
        print_section("Step 1: Fetch All Records")
        
        records = client.get_records(table_name)
        print(f"📊 Found {len(records)} records in '{table_name}'")
        
        if records:
            print("\nShowing first 3 records:")
            for i, record in enumerate(records[:3], 1):
                print(f"\n--- Record {i} ---")
                print_record(record, prefix="  ")
        else:
            print("  (No records found)")
        
        # =====================================================================
        # STEP 2: Create a new record
        # =====================================================================
        print_section("Step 2: Create a New Record")
        
        new_record_data = {
            "Name": "Basante",
            "Status": "Active",
        }
        
        print(f"📝 Creating record with data:")
        print(f"   {json.dumps(new_record_data, indent=2)}")
        
        new_record = client.create_record(table_name, new_record_data)
        
        print(f"\n✅ Record created successfully!")
        print_record(new_record, prefix="  ")
        
        record_id = new_record["id"]
        
        # =====================================================================
        # STEP 3: Update the record
        # =====================================================================
        print_section("Step 3: Update the Record")
        
        update_data = {
            "Status": "Verified",
        }
        
        print(f"✏️  Updating record {record_id}")
        print(f"   New data: {json.dumps(update_data, indent=2)}")
        
        updated_record = client.update_record(table_name, record_id, update_data)
        
        print(f"\n✅ Record updated successfully!")
        print_record(updated_record, prefix="  ")
        
        # =====================================================================
        # STEP 4: Delete the record
        # =====================================================================
        print_section("Step 4: Delete the Record")
        
        print(f"🗑️  Deleting record {record_id}")
        
        delete_result = client.delete_record(table_name, record_id)
        
        print(f"\n✅ Record deleted successfully!")
        print(f"   Result: {json.dumps(delete_result, indent=2)}")
        
        # =====================================================================
        # Summary
        # =====================================================================
        print_section("Demo Complete")
        
        print("✅ All operations completed successfully!")
        print("\n📚 What we demonstrated:")
        print("   1. ✓ Fetched all records from the table")
        print("   2. ✓ Created a new record with Name='Basante' and Status='Active'")
        print("   3. ✓ Updated the record's Status to 'Verified'")
        print("   4. ✓ Deleted the record")
        
        print("\n💡 Next steps:")
        print("   - Try modifying the table_name variable to use your own table")
        print("   - Experiment with different filters in get_records()")
        print("   - Use batch operations for multiple records")
        print("   - Integrate this client into your Django or automation system")
        
        return 0
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        return 1
    
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        print(f"\nFull error details:")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
