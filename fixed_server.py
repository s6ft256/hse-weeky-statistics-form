#!/usr/bin/env python3
"""
Fixed Airtable Dashboard with direct HTML rendering
"""

import os
import ssl
import urllib3
import requests
from flask import Flask, render_template_string
from pyairtable import Api
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from unittest.mock import patch
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Disable SSL warnings and verification for corporate proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Monkey-patch requests library to always disable SSL verification
_original_request = requests.Session.request
def _patched_request(self, method, url, **kwargs):
    kwargs['verify'] = False
    return _original_request(self, method, url, **kwargs)
requests.Session.request = _patched_request

# Configuration - Load from environment variables
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# Validate required environment variables
if not AIRTABLE_TOKEN:
    raise ValueError("AIRTABLE_TOKEN environment variable is required")
if not AIRTABLE_BASE_ID:
    raise ValueError("AIRTABLE_BASE_ID environment variable is required")

app = Flask(__name__)

# Initialize Airtable API
try:
    print("[*] Initializing Airtable connection...")
    print(f"[*] Using Base ID: {AIRTABLE_BASE_ID}")
    print(f"[*] Token configured: {AIRTABLE_TOKEN is not None}")
    print(f"[*] Token starts with: {AIRTABLE_TOKEN[:10]}...")
    print("[*] SSL verification disabled for corporate proxy...")
    api = Api(AIRTABLE_TOKEN)
    print("[*] Testing connection to Airtable...")
    base = api.base(AIRTABLE_BASE_ID)
    try:
        # Try to get a list of tables
        schema = base.schema()
        tables = schema.tables
        print(f"[+] Successfully retrieved {len(tables)} tables from base")
        print(f"[+] Tables: {', '.join([t.name for t in tables])}")
    except Exception as schema_error:
        print(f"[!] Warning: Could not retrieve table list: {schema_error}")
    print("[+] Connected to Airtable successfully")
except Exception as e:
    print(f"[!] Failed to connect to Airtable: {e}")
    print("[!] This might be due to SSL certificate issues with corporate proxy")
    api = None
    base = None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        print("\n[*] Dashboard route accessed")
        print("[*] Rendering dashboard with tables...")
        if api is None:
            print("[!] API is None, returning error")
            return "Airtable API not initialized. Check server logs for SSL/connection issues.", 500
            
        # Get all tables from the base
        print("[*] Getting tables from base")
        tables_info = []
        base_metadata = api.base(AIRTABLE_BASE_ID).schema()
        print(f"[*] Retrieved metadata with {len(base_metadata.tables)} tables")
        
        for table_info in base_metadata.tables:
            table_name = table_info.name
            table_id = table_info.id
            print(f"[*] Processing table: {table_name}")
            
            # Get record count
            try:
                table = base.table(table_name)
                records = table.all()
                record_count = len(records)
                print(f"[+] Table {table_name}: {record_count} records")
            except Exception as e:
                print(f"[!] Warning: Could not get records for {table_name}: {e}")
                record_count = 0
            
            tables_info.append({
                'name': table_name,
                'id': table_id,
                'count': record_count
            })
        
        # Create a simple HTML response showing the tables directly
        print(f"[+] Rendering simplified dashboard with {len(tables_info)} tables")
        
        table_html = ""
        for table in tables_info:
            table_html += f"""
            <div class="table-card" onclick="viewTable('{table['name']}')">
                <h3>{table['name']}</h3>
                <p>Records: {table['count']}</p>
                <p>ID: {table['id']}</p>
            </div>
            """
        
        direct_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Airtable Tables</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #4285f4; }}
                .container {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                .table-card {{ 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    border-radius: 8px;
                    width: 250px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    cursor: pointer;
                }}
                .table-card:hover {{ 
                    background-color: #f5f5f5; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }}
                h3 {{ margin-top: 0; }}
            </style>
        </head>
        <body>
            <h1>Airtable Tables</h1>
            <p>Found {len(tables_info)} tables in your Airtable base.</p>
            <div class="container">
                {table_html}
            </div>
            <script>
                function viewTable(tableName) {{
                    alert('Viewing table: ' + tableName);
                    // In a real app, this would navigate to the table view
                }}
            </script>
        </body>
        </html>
        """
        
        return direct_html
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[!] Dashboard error: {error_details}")
        return f"Error loading dashboard: {str(e)}<br><pre>{error_details}</pre>", 500

if __name__ == '__main__':
    print("[*] Starting Fixed Airtable Dashboard...")
    print("[*] Dashboard available at: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)