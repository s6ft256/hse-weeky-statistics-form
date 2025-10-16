#!/usr/bin/env python3
"""
Clean Airtable Dashboard - Fixed Version
"""

import os
import ssl
import urllib3
import requests
import re
from flask import Flask, render_template_string, request, jsonify
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
STATISTICS_API = os.getenv("STATISTICS_API")

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
    api = Api(AIRTABLE_TOKEN, timeout=(30, 30))
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
        print("[*] Dashboard route accessed")
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
        error_msg = str(e)
        if 'SSL' in error_msg or 'certificate' in error_msg.lower():
            return f"""
            <h1>SSL Certificate Error</h1>
            <p>Unable to connect to Airtable API due to certificate verification issues.</p>
            <p>This is likely due to a corporate proxy with self-signed certificates.</p>
            <h3>Error Details:</h3>
            <pre>{error_msg}</pre>
            <h3>Attempted Fixes:</h3>
            <ul>
                <li>SSL verification has been disabled globally</li>
                <li>All certificate verification bypassed</li>
                <li>Corporate proxy SSL workarounds applied</li>
            </ul>
            <p>Check the server terminal for more details.</p>
            """, 500
        return f"Error loading dashboard: {error_msg}<br><br><pre>{error_details}</pre>", 500

@app.route('/api/tables/<table_name>/records')
def get_table_records(table_name):
    """Get records for a specific table"""
    try:
        if base is None:
            return jsonify({'error': 'Airtable connection not initialized'}), 500
            
        table = base.table(table_name)
        records = table.all()
        
        # Format records for display
        formatted_records = []
        for record in records:
            formatted_record = {
                'id': record['id'],
                'fields': record.get('fields', {})
            }
            formatted_records.append(formatted_record)
        
        return jsonify(formatted_records)
    except Exception as e:
        print(f"[!] Error fetching records for {table_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/base-metadata')
def get_base_metadata():
    """Get metadata about the base including tables and fields"""
    try:
        if api is None:
            return jsonify({'error': 'Airtable connection not initialized'}), 500
        
        print(f"[*] Fetching base metadata for base ID: {AIRTABLE_BASE_ID}")
        
        # Get the base metadata 
        base_metadata = api.base(AIRTABLE_BASE_ID).schema()
        
        # Format the metadata for the frontend
        tables = []
        for table_info in base_metadata.tables:
            print(f"[*] Found table: {table_info.name} (ID: {table_info.id})")
            fields = []
            
            for field_info in table_info.fields:
                field_data = {
                    'id': field_info.id,
                    'name': field_info.name,
                    'type': field_info.type,
                }
                
                # Include options for select fields
                if field_info.type in ['singleSelect', 'multipleSelect'] and hasattr(field_info, 'options'):
                    field_data['options'] = {
                        'choices': [{'name': choice.name} for choice in field_info.options.choices]
                    }
                
                fields.append(field_data)
                print(f"  - Field: {field_info.name} (Type: {field_info.type})")
            
            tables.append({
                'id': table_info.id,
                'name': table_info.name,
                'fields': fields
            })
        
        print(f"[+] Returning metadata for {len(tables)} tables")
        return jsonify({
            'baseId': AIRTABLE_BASE_ID,
            'tables': tables
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[!] Error fetching base metadata: {e}")
        print(f"[!] Traceback: {error_details}")
        
        error_message = str(e)
        
        # Try to provide more specific error messages
        if "NOT_FOUND" in error_message or "404" in error_message:
            error_message = "Base not found. Please check your base ID."
        elif "AUTHENTICATION_REQUIRED" in error_message or "401" in error_message:
            error_message = "Authentication failed. Please check your Airtable token."
        elif "permission" in error_message.lower() or "403" in error_message:
            error_message = "Permission denied. Your token may not have access to this base."
            
        return jsonify({'error': error_message}), 500

# Add favicon route to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    return '', 204

# Clean HTML Template
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Airtable Dashboard v2.1</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        :root {
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-tertiary: #94a3b8;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --accent-light: #eef2ff;
            --border: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --radius: 12px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        [data-theme="dark"] {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-tertiary: #64748b;
            --border: #334155;
            --accent-light: #1e293b;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            transition: var(--transition);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .header-left {
            flex: 1;
        }
        
        .header h1 {
            color: var(--text-primary);
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header h1::before {
            content: '📊';
            font-size: 2rem;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }
        
        .header-right {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .theme-toggle {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
            font-size: 1.25rem;
        }
        
        .theme-toggle:hover {
            background: var(--bg-tertiary);
            transform: scale(1.05);
        }
        
        .stats-bar {
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px 20px;
            flex: 1;
            min-width: 200px;
            box-shadow: var(--shadow-sm);
        }
        
        .stat-label {
            color: var(--text-tertiary);
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        
        .stat-value {
            color: var(--text-primary);
            font-size: 1.75rem;
            font-weight: 700;
        }
        
        .search-container {
            margin-bottom: 24px;
            position: relative;
        }
        
        .search-box {
            width: 100%;
            padding: 14px 48px 14px 48px;
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: var(--radius);
            font-size: 1rem;
            color: var(--text-primary);
            transition: var(--transition);
        }
        
        .search-box:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-light);
        }
        
        .search-icon {
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-tertiary);
            font-size: 1.25rem;
        }
        
        .clear-search {
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: var(--text-tertiary);
            cursor: pointer;
            font-size: 1.25rem;
            display: none;
        }
        
        .clear-search:hover {
            color: var(--text-primary);
        }
        
        .tables-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .table-card {
            background: var(--bg-secondary);
            border-radius: var(--radius);
            padding: 24px;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border);
            cursor: pointer;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }
        
        .table-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent), #06b6d4);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.3s ease;
        }
        
        .table-card:hover::before {
            transform: scaleX(1);
        }
        
        .table-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-4px);
            border-color: var(--accent);
        }
        
        .table-card:active {
            transform: translateY(-2px);
        }
        
        .table-icon {
            width: 48px;
            height: 48px;
            background: var(--accent-light);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 16px;
        }
        
        .table-name {
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .table-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
        }
        
        .table-count {
            color: var(--text-secondary);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .table-count::before {
            content: '�';
            font-size: 0.95rem;
        }
        
        .table-badge {
            background: var(--accent-light);
            color: var(--accent);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .no-results {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-tertiary);
        }
        
        .no-results::before {
            content: '🔍';
            display: block;
            font-size: 3rem;
            margin-bottom: 16px;
        }
        
        .records-section {
            background: var(--bg-secondary);
            border-radius: var(--radius);
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border);
            display: none;
            animation: slideIn 0.4s ease;
            overflow: hidden;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .table-header {
            padding: 16px 24px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-secondary);
        }
        
        .table-title-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .table-title-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .back-icon {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            background: var(--bg-tertiary);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
            font-size: 1.1rem;
        }
        
        .back-icon:hover {
            background: var(--border);
        }
        
        .table-name-display {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .table-tabs {
            display: flex;
            gap: 2px;
            border-bottom: 2px solid var(--border);
            overflow-x: auto;
        }
        
        .tab {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
            transition: var(--transition);
            white-space: nowrap;
        }
        
        .tab:hover {
            color: var(--text-primary);
            background: var(--bg-tertiary);
        }
        
        .tab.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }
        
        .records-actions {
            display: flex;
            gap: 8px;
        }
        
        .btn {
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--accent);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:hover {
            background: var(--border);
        }
        
        .view-controls {
            padding: 12px 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }
        
        .view-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .view-toggle {
            display: flex;
            gap: 4px;
            background: var(--bg-tertiary);
            border-radius: 6px;
            padding: 4px;
        }
        
        .view-btn {
            padding: 6px 12px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 0.85rem;
            border-radius: 4px;
            transition: var(--transition);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .view-btn:hover {
            color: var(--text-primary);
        }
        
        .view-btn.active {
            background: var(--bg-secondary);
            color: var(--text-primary);
            box-shadow: var(--shadow-sm);
        }
        
        .view-actions {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .icon-btn {
            width: 28px;
            height: 28px;
            background: transparent;
            border: 0;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .icon-btn:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border-color: var(--accent);
        }

        /* hide pseudo-elements in view-actions; keep glyph font-size so inline icons remain visible */
        .view-actions .icon-btn { padding: 0; font-size: inherit; }
        .view-actions .icon-btn::before, .view-actions .icon-btn::after { display: none }
        
        .icon-btn.active {
            background: var(--accent-light);
            color: var(--accent);
            border-color: var(--accent);
        }
        
        .toolbar {
            padding: 12px 24px;
            background: var(--bg-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }
        
        .toolbar-left {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .sort-select {
            padding: 6px 10px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 0.85rem;
            cursor: pointer;
        }
        
        .pagination {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .page-btn {
            padding: 6px 12px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 0.85rem;
            transition: var(--transition);
        }
        
        .page-btn:hover:not(:disabled) {
            background: var(--bg-tertiary);
            border-color: var(--accent);
        }
        
        .page-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        
        .page-info {
            color: var(--text-secondary);
            font-size: 0.85rem;
            padding: 0 8px;
        }
        
        .table-container {
            overflow: auto;
            height: calc(100vh - 400px);
            min-height: 400px;
        }
        
        .records-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }
        
        .records-table th,
        .records-table td {
            padding: 12px 16px;
            text-align: left;
            border-right: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
            min-width: 150px;
            max-width: 400px;
        }
        
        .records-table th:first-child,
        .records-table td:first-child {
            position: sticky;
            left: 0;
            z-index: 5;
            background: var(--bg-secondary);
            border-left: 1px solid var(--border);
            min-width: 50px;
            max-width: 50px;
            text-align: center;
            padding: 12px 8px;
        }
        
        .records-table th {
            background: var(--bg-tertiary);
            font-weight: 600;
            color: var(--text-primary);
            font-size: 0.8rem;
            position: sticky;
            top: 0;
            z-index: 10;
            white-space: nowrap;
            border-top: 1px solid var(--border);
        }
        
        .records-table th:first-child {
            z-index: 15;
            border-left: 1px solid var(--border);
        }
        
        .records-table th .header-content {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .records-table th .field-icon {
            font-size: 0.75rem;
            opacity: 0.7;
        }
        
        .records-table td {
            font-size: 0.875rem;
            color: var(--text-primary);
            background: var(--bg-secondary);
            word-wrap: break-word;
        }
        
        .records-table tbody tr:hover td {
            background: var(--bg-tertiary);
        }
        
        .row-number {
            color: var(--text-tertiary);
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .cell-content {
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .cell-empty {
            color: var(--text-tertiary);
            font-style: italic;
        }
        
        .cell-array {
            color: var(--accent);
        }
        
        .cell-boolean {
            font-size: 1.2rem;
        }
        
        .cell-number {
            font-variant-numeric: tabular-nums;
        }
        
        .add-field-btn,
        .add-row-btn {
            background: transparent;
            border: 1px dashed var(--border);
            border-radius: 4px;
            color: var(--text-tertiary);
            cursor: pointer;
            font-size: 1.2rem;
            padding: 4px 12px;
            transition: var(--transition);
        }
        
        .add-field-btn:hover,
        .add-row-btn:hover {
            background: var(--bg-tertiary);
            color: var(--accent);
            border-color: var(--accent);
        }
        
        .add-row {
            background: var(--bg-secondary);
        }
        
        .add-row td {
            padding: 8px;
            border-bottom: none;
        }
        
        .add-row-btn {
            width: 100%;
            text-align: left;
            padding: 8px 16px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        input[type="checkbox"] {
            cursor: pointer;
            width: 16px;
            height: 16px;
        }
        
        .loading {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-tertiary);
            font-size: 1.1rem;
        }
        
        .loading::before {
            content: '⏳';
            display: block;
            font-size: 3rem;
            margin-bottom: 16px;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }
        
        .error {
            color: var(--error);
            text-align: center;
            padding: 30px;
            background: var(--bg-secondary);
            border-radius: var(--radius);
            border: 2px solid var(--error);
            margin: 20px 0;
        }
        
        .error::before {
            content: '⚠️';
            display: block;
            font-size: 2.5rem;
            margin-bottom: 12px;
        }
        
        .no-records {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-tertiary);
            font-size: 1.1rem;
        }
        
        .no-records::before {
            content: '📝';
            display: block;
            font-size: 3rem;
            margin-bottom: 16px;
        }
        
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px 24px;
            box-shadow: var(--shadow-lg);
            z-index: 1000;
            animation: slideUp 0.3s ease;
            max-width: 400px;
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .toast-success {
            border-left: 4px solid var(--success);
        }
        
        .toast-error {
            border-left: 4px solid var(--error);
        }
        
        .toast-warning {
            border-left: 4px solid var(--warning);
        }
        
        .kbd {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 2px 6px;
            font-family: monospace;
            font-size: 0.85em;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .tooltip {
            position: relative;
            cursor: help;
        }
        
        .tooltip::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--text-primary);
            color: var(--bg-primary);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s;
            margin-bottom: 8px;
        }
        
        .tooltip:hover::after {
            opacity: 1;
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .tables-grid {
                grid-template-columns: 1fr;
            }
            
            .toolbar {
                flex-direction: column;
                align-items: stretch;
            }
            
            .records-header {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body data-theme="light">
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>Airtable Dashboard</h1>
                <p>Powerful data management made simple</p>
            </div>
            <div class="header-right">
                <button class="theme-toggle" onclick="toggleTheme()" data-tooltip="Toggle theme (T)" title="Toggle dark mode">
                    <span id="theme-icon">🌙</span>
                </button>
            </div>
        </div>
        
        <div id="main-view">
            <div class="stats-bar">
                <div class="stat-card">
                    <div class="stat-label">Total Tables</div>
                    <div class="stat-value">{{ tables|length }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Records</div>
                    <div class="stat-value" id="total-records">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Visible Tables</div>
                    <div class="stat-value" id="visible-tables">{{ tables|length }}</div>
                </div>
            </div>
            
            <div class="search-container">
                <span class="search-icon">🔍</span>
                <input 
                    type="text" 
                    class="search-box" 
                    id="table-search" 
                    placeholder="Search tables... (Press / to focus)" 
                    oninput="filterTables(this.value)"
                    onkeydown="handleSearchKeydown(event)"
                />
                <button class="clear-search" id="clear-search" onclick="clearSearch()">✕</button>
            </div>
            
            <div class="tables-grid" id="tables-grid">
                {% for table in tables %}
                <div class="table-card" onclick="viewTable('{{ table.name }}')" data-table-name="{{ table.name|lower }}" data-record-count="{{ table.count }}">
                    <div class="table-icon">📋</div>
                    <div class="table-name">{{ table.name }}</div>
                    <div class="table-meta">
                        <div class="table-count">{{ table.count }} records</div>
                        {% if table.count > 100 %}
                        <span class="table-badge">Large</span>
                        {% elif table.count > 0 %}
                        <span class="table-badge">Active</span>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
            <div id="no-results" class="no-results" style="display: none;">
                No tables found matching your search
            </div>
        </div>
        
        <div id="table-view" class="records-section">
            <div class="table-header">
                <div class="table-title-row">
                    <div class="table-title-left">
                        <div class="back-icon" onclick="goBack()" title="Back to tables">←</div>
                        <div class="table-name-display" id="table-title-text">Table Name</div>
                    </div>
                    <div class="records-actions">
                        <button class="btn btn-secondary" onclick="addRecord()">+ Add Record</button>
                        <button class="btn btn-primary" onclick="refreshTable()">🔄 Refresh</button>
                    </div>
                </div>
                
                <div class="table-tabs" id="table-tabs">
                    <button class="tab active" data-view="grid">Grid view</button>
                    <button class="tab" data-view="form">Form view</button>
                    <button class="tab" data-view="calendar">Calendar</button>
                    <button class="tab" data-view="gallery">Gallery</button>
                </div>
            </div>
            
            <div class="view-controls">
                <div class="view-left">
                    <div class="view-toggle">
                        <button class="view-btn active" onclick="setView('grid')">
                            <span>☷</span>
                            <span>Grid view</span>
                        </button>
                    </div>
                </div>
                <div class="view-actions">
                    <button class="icon-btn" onclick="toggleFilter()" title="Filter" data-tooltip="Filter" aria-label="Filter">⚡</button>
                    <button class="icon-btn" onclick="toggleGroup()" title="Group" data-tooltip="Group" aria-label="Group">⚏</button>
                    <button class="icon-btn" onclick="toggleSort()" title="Sort" data-tooltip="Sort" aria-label="Sort">⇅</button>
                    <button class="icon-btn" onclick="hideFields()" title="Hide fields" data-tooltip="Hide fields" aria-label="Hide fields">👁</button>
                </div>
            </div>
            
            <div class="toolbar">
                <div class="toolbar-left">
                    <select class="sort-select" id="sort-field" onchange="sortRecords()">
                        <option value="">Sort by field...</option>
                    </select>
                    <span class="page-info" id="record-count">0 records</span>
                </div>
                <div class="pagination">
                    <button class="page-btn" onclick="previousPage()" id="prev-btn" disabled>←</button>
                    <span class="page-info" id="page-info">Page 1</span>
                    <button class="page-btn" onclick="nextPage()" id="next-btn" disabled>→</button>
                </div>
            </div>
            
            <div id="table-content"></div>
        </div>
    </div>
    
    <div id="toast-container"></div>

    <script>
        // State management
        let currentTableName = null;
        let allRecords = [];
        let currentPage = 1;
        let recordsPerPage = 50;
        let currentSortField = '';
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            calculateTotalRecords();
            initializeKeyboardShortcuts();
            loadTheme();
        });
        
        // Theme management
        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            body.setAttribute('data-theme', newTheme);
            document.getElementById('theme-icon').textContent = newTheme === 'light' ? '🌙' : '☀️';
            localStorage.setItem('theme', newTheme);
            showToast('Theme changed to ' + newTheme + ' mode', 'success');
        }
        
        function loadTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
            document.getElementById('theme-icon').textContent = savedTheme === 'light' ? '🌙' : '☀️';
        }
        
        // Keyboard shortcuts
        function initializeKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                // / to focus search
                if (e.key === '/' && e.target.tagName !== 'INPUT') {
                    e.preventDefault();
                    document.getElementById('table-search').focus();
                }
                // Escape to clear search or go back
                if (e.key === 'Escape') {
                    if (document.getElementById('table-view').style.display === 'block') {
                        goBack();
                    } else {
                        clearSearch();
                    }
                }
                // T for theme toggle
                if (e.key === 't' || e.key === 'T') {
                    if (e.target.tagName !== 'INPUT') {
                        toggleTheme();
                    }
                }
                // R for refresh (when viewing table)
                if ((e.key === 'r' || e.key === 'R') && e.target.tagName !== 'INPUT') {
                    if (currentTableName) {
                        refreshTable();
                    }
                }
            });
        }
        
        // Calculate total records
        function calculateTotalRecords() {
            const cards = document.querySelectorAll('.table-card');
            let total = 0;
            cards.forEach(card => {
                const count = parseInt(card.getAttribute('data-record-count')) || 0;
                total += count;
            });
            document.getElementById('total-records').textContent = total.toLocaleString();
        }
        
        // Navigation
        function goBack() {
            document.getElementById('main-view').style.display = 'block';
            document.getElementById('table-view').style.display = 'none';
            currentTableName = null;
            allRecords = [];
            currentPage = 1;
        }
        
        function showTableView() {
            document.getElementById('main-view').style.display = 'none';
            document.getElementById('table-view').style.display = 'block';
        }
        
        // Search and filter
        function filterTables(query) {
            const searchTerm = query.toLowerCase().trim();
            const cards = document.querySelectorAll('.table-card');
            const clearBtn = document.getElementById('clear-search');
            const noResults = document.getElementById('no-results');
            let visibleCount = 0;
            
            clearBtn.style.display = searchTerm ? 'block' : 'none';
            
            cards.forEach(card => {
                const tableName = card.getAttribute('data-table-name');
                if (tableName.includes(searchTerm)) {
                    card.style.display = 'block';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });
            
            document.getElementById('visible-tables').textContent = visibleCount;
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
        }
        
        function clearSearch() {
            const searchBox = document.getElementById('table-search');
            searchBox.value = '';
            filterTables('');
            searchBox.focus();
        }
        
        function handleSearchKeydown(event) {
            if (event.key === 'Escape') {
                clearSearch();
            }
        }
        
        // Toast notifications
        function showToast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
        
        // Table view functions
        async function viewTable(tableName) {
            console.log('viewTable called with:', tableName);
            currentTableName = tableName;
            currentPage = 1;
            showTableView();
            
            // Update title
            const titleElement = document.getElementById('table-title-text');
            console.log('Title element:', titleElement);
            if (titleElement) {
                titleElement.textContent = tableName;
            }
            
            // Show loading
            const contentElement = document.getElementById('table-content');
            console.log('Content element:', contentElement);
            if (contentElement) {
                contentElement.innerHTML = '<div class="loading">Loading records...</div>';
            }
            
            try {
                console.log('Fetching records for:', tableName);
                const response = await fetch('/api/tables/' + encodeURIComponent(tableName) + '/records');
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error('Failed to fetch records');
                }
                
                allRecords = await response.json();
                console.log('Loaded records:', allRecords.length);
                populateSortOptions();
                displayCurrentPage();
                showToast('Loaded ' + allRecords.length + ' records', 'success');
                
            } catch (error) {
                console.error('Error loading table:', error);
                if (contentElement) {
                    contentElement.innerHTML = '<div class="error">Error loading records: ' + error.message + '</div>';
                }
                showToast('Error loading records', 'error');
            }
        }
        
        function refreshTable() {
            if (currentTableName) {
                showToast('Refreshing data...', 'success');
                viewTable(currentTableName);
            }
        }
        
        function populateSortOptions() {
            if (allRecords.length === 0) return;
            
            const sortSelect = document.getElementById('sort-field');
            sortSelect.innerHTML = '<option value="">Sort by...</option>';
            
            const fields = new Set();
            allRecords.forEach(record => {
                if (record.fields) {
                    Object.keys(record.fields).forEach(field => fields.add(field));
                }
            });
            
            Array.from(fields).sort().forEach(field => {
                const option = document.createElement('option');
                option.value = field;
                option.textContent = field;
                sortSelect.appendChild(option);
            });
        }
        
        function sortRecords() {
            const sortField = document.getElementById('sort-field').value;
            if (!sortField) return;
            
            currentSortField = sortField;
            allRecords.sort((a, b) => {
                const aVal = a.fields?.[sortField] || '';
                const bVal = b.fields?.[sortField] || '';
                return String(aVal).localeCompare(String(bVal));
            });
            
            currentPage = 1;
            displayCurrentPage();
            showToast('Sorted by ' + sortField, 'success');
        }
        
        // Pagination
        function displayCurrentPage() {
            const start = (currentPage - 1) * recordsPerPage;
            const end = start + recordsPerPage;
            const pageRecords = allRecords.slice(start, end);
            
            displayTableRecords(pageRecords);
            updatePaginationControls();
        }
        
        function updatePaginationControls() {
            const totalPages = Math.ceil(allRecords.length / recordsPerPage);
            
            document.getElementById('record-count').textContent = 
                `${allRecords.length} records (${recordsPerPage} per page)`;
            document.getElementById('page-info').textContent = 
                `Page ${currentPage} of ${totalPages || 1}`;
            
            document.getElementById('prev-btn').disabled = currentPage === 1;
            document.getElementById('next-btn').disabled = currentPage >= totalPages;
        }
        
        function previousPage() {
            if (currentPage > 1) {
                currentPage--;
                displayCurrentPage();
            }
        }
        
        function nextPage() {
            const totalPages = Math.ceil(allRecords.length / recordsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                displayCurrentPage();
            }
        }
        
        function displayTableRecords(records) {
            const contentElement = document.getElementById('table-content');
            if (!contentElement) return;
            
            if (!records || records.length === 0) {
                contentElement.innerHTML = '<div class="no-records">No records found in this table</div>';
                return;
            }
            
            // Get all unique field names
            const allFields = new Set();
            records.forEach(record => {
                if (record.fields) {
                    Object.keys(record.fields).forEach(field => allFields.add(field));
                }
            });
            
            const fieldNames = Array.from(allFields);
            
            if (fieldNames.length === 0) {
                contentElement.innerHTML = '<div class="no-records">No fields found in records</div>';
                return;
            }
            
            // Build table HTML with container
            let tableHtml = '<div class="table-container">';
            tableHtml += '<table class="records-table">';
            tableHtml += '<thead><tr>';
            
            // Add checkbox and row number column header
            tableHtml += '<th><div class="header-content"><input type="checkbox" id="select-all" style="margin-right:8px;"><span class="row-number">#</span></div></th>';
            
            // Add field headers with icons
            fieldNames.forEach(fieldName => {
                const icon = getFieldIcon(fieldName);
                tableHtml += '<th><div class="header-content">';
                tableHtml += '<span class="field-icon">' + icon + '</span>';
                tableHtml += '<span>' + escapeHtml(fieldName) + '</span>';
                tableHtml += '</div></th>';
            });
            
            // Add + column for adding fields
            tableHtml += '<th><div class="header-content"><button class="add-field-btn" onclick="addField()" title="Add field">+</button></div></th>';
            
            tableHtml += '</tr></thead><tbody>';
            
            const startIndex = (currentPage - 1) * recordsPerPage;
            records.forEach((record, index) => {
                tableHtml += '<tr>';
                
                // Add checkbox and row number
                tableHtml += '<td><input type="checkbox" class="row-select" style="margin-right:8px;"><span class="row-number">' + (startIndex + index + 1) + '</span></td>';
                
                fieldNames.forEach(fieldName => {
                    const fieldValue = record.fields ? record.fields[fieldName] : null;
                    let displayValue = '';
                    let cellClass = '';
                    
                    if (fieldValue !== null && fieldValue !== undefined) {
                        if (Array.isArray(fieldValue)) {
                            displayValue = fieldValue.join(', ');
                            cellClass = 'cell-array';
                        } else if (typeof fieldValue === 'object') {
                            displayValue = JSON.stringify(fieldValue);
                            cellClass = 'cell-object';
                        } else if (typeof fieldValue === 'boolean') {
                            displayValue = fieldValue ? '✓' : '✗';
                            cellClass = 'cell-boolean';
                        } else if (!isNaN(fieldValue) && fieldValue !== '' && typeof fieldValue !== 'string') {
                            displayValue = Number(fieldValue).toLocaleString();
                            cellClass = 'cell-number';
                        } else {
                            displayValue = String(fieldValue);
                        }
                    } else {
                        displayValue = '—';
                        cellClass = 'cell-empty';
                    }
                    
                    tableHtml += `<td class="${cellClass}"><div class="cell-content">` + escapeHtml(displayValue) + '</div></td>';
                });
                
                // Add empty cell for + column
                tableHtml += '<td></td>';
                tableHtml += '</tr>';
            });
            
            // Add row for adding new record
            tableHtml += '<tr class="add-row">';
            tableHtml += '<td colspan="' + (fieldNames.length + 2) + '">';
            tableHtml += '<button class="add-row-btn" onclick="addRecord()">+ Add record</button>';
            tableHtml += '</td></tr>';
            
            tableHtml += '</tbody></table></div>';
            contentElement.innerHTML = tableHtml;
        }
        
        function getFieldIcon(fieldName) {
            const name = fieldName.toLowerCase();
            if (name.includes('name') || name.includes('term')) return '≡';
            if (name.includes('date') || name.includes('time')) return '📅';
            if (name.includes('email')) return '✉';
            if (name.includes('phone')) return '☎';
            if (name.includes('url') || name.includes('link')) return '🔗';
            if (name.includes('status') || name.includes('state')) return '◉';
            if (name.includes('number') || name.includes('count') || name.includes('total')) return '#';
            if (name.includes('description') || name.includes('definition') || name.includes('note')) return '📝';
            return '—';
        }
        
        function switchTab(tabName) {
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            const viewName = event.target.getAttribute('data-view') || tabName;
            showToast('Switched to ' + viewName + ' view', 'success');
        }
        
        function setView(viewType) {
            const btns = document.querySelectorAll('.view-btn');
            btns.forEach(btn => btn.classList.remove('active'));
            event.target.closest('.view-btn').classList.add('active');
        }
        
        function toggleFilter() {
            showToast('Filter feature coming soon', 'warning');
        }
        
        function toggleGroup() {
            showToast('Group feature coming soon', 'warning');
        }
        
        function toggleSort() {
            showToast('Use the sort dropdown above', 'success');
        }
        
        function hideFields() {
            showToast('Hide fields feature coming soon', 'warning');
        }
        
        async function addRecord() {
            if (!currentTableName) {
                showToast('Please select a table first.', 'warning');
                return;
            }

            // Show loading toast
            showToast('Loading table fields...', 'success');

            // Create modal container styles if not exists
            if (!document.getElementById('modal-styles')) {
                const styles = document.createElement('style');
                styles.id = 'modal-styles';
                styles.innerHTML = `
                    .modal-backdrop {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: rgba(0, 0, 0, 0.5);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        z-index: 1000;
                    }
                    .modal-content {
                        background: var(--bg-secondary);
                        border-radius: var(--radius);
                        box-shadow: var(--shadow-lg);
                        width: 90%;
                        max-width: 600px;
                        max-height: 90vh;
                        overflow-y: auto;
                    }
                    .modal-header {
                        padding: 16px 24px;
                        border-bottom: 1px solid var(--border);
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .modal-body {
                        padding: 24px;
                        max-height: 60vh;
                        overflow-y: auto;
                    }
                    .modal-footer {
                        padding: 16px 24px;
                        border-top: 1px solid var(--border);
                        display: flex;
                        justify-content: flex-end;
                        gap: 12px;
                    }
                    .modal-close-btn {
                        background: none;
                        border: none;
                        font-size: 1.5rem;
                        cursor: pointer;
                        color: var(--text-secondary);
                    }
                    .form-group {
                        margin-bottom: 16px;
                    }
                    .form-group label {
                        display: block;
                        margin-bottom: 8px;
                        font-weight: 500;
                        color: var(--text-primary);
                    }
                    .form-group input, .form-group textarea, .form-group select {
                        width: 100%;
                        padding: 10px;
                        border: 1px solid var(--border);
                        border-radius: 6px;
                        background: var(--bg-primary);
                        color: var(--text-primary);
                        font-family: inherit;
                        font-size: 0.9rem;
                    }
                    .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
                        outline: none;
                        border-color: var(--accent);
                        box-shadow: 0 0 0 2px var(--accent-light);
                    }
                    .modal-loading {
                        text-align: center;
                        padding: 30px;
                        color: var(--text-secondary);
                    }
                `;
                document.head.appendChild(styles);
            }
            
            // Create a modal for adding a record
            const modal = document.createElement('div');
            modal.className = 'modal-backdrop';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Add New Record to ${currentTableName}</h3>
                        <button class="modal-close-btn">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="modal-loading">Loading fields...</div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="cancel-add-record">Cancel</button>
                        <button class="btn btn-primary" id="submit-add-record" disabled>Save Record</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Event listeners for the modal
            modal.querySelector('.modal-close-btn').addEventListener('click', () => modal.remove());
            modal.querySelector('#cancel-add-record').addEventListener('click', () => modal.remove());
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
            
            // Fetch table fields from the API
            try {
                // Get the full table metadata
                const response = await fetch('/api/base-metadata');
                if (!response.ok) {
                    throw new Error('Failed to load table metadata');
                }
                
                const data = await response.json();
                window.tableMetadata = data; // Cache it
                
                // Find the current table
                const table = data.tables.find(t => t.name === currentTableName);
                if (!table) {
                    throw new Error(`Table "${currentTableName}" not found in metadata`);
                }
                
                // Generate form HTML with fields
                let formHtml = '<form id="add-record-form">';
                if (table.fields && table.fields.length > 0) {
                    const editableFields = table.fields.filter(field => 
                        !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(field.type)
                    );
                    
                    if (editableFields.length > 0) {
                        editableFields.forEach(field => {
                            // Replace spaces with dashes and make lowercase for the ID
                            const fieldId = field.name.replace(/ /g, '-').toLowerCase();
                            let inputType = 'text';
                            let placeholder = 'Enter value...';
                            
                            // Special handling for Training table - force all fields to text inputs to prevent #REF/#N/A errors
                            const isTrainingTable = table.name === '4b.Training & comptency Registe';
                            
                            // Set appropriate input type and placeholder based on field type
                            if (isTrainingTable) {
                                // For Training table: always use text input regardless of field type
                                inputType = 'text';
                                placeholder = `Enter ${field.name.toLowerCase()}...`;
                                if (field.type === 'singleSelect' || field.type === 'multipleSelect') {
                                    placeholder += ' (Note: Enter text directly to avoid #REF/#N/A errors)';
                                }
                            } else {
                                // Normal field type handling for other tables
                                switch(field.type) {
                                    case 'date':
                                    case 'dateTime':
                                        inputType = 'date';
                                        placeholder = 'YYYY-MM-DD';
                                        break;
                                    case 'number':
                                        inputType = 'number';
                                        placeholder = 'Enter number...';
                                        break;
                                    case 'email':
                                        inputType = 'email';
                                        placeholder = 'Enter email...';
                                        break;
                                    case 'url':
                                        inputType = 'url';
                                        placeholder = 'Enter URL...';
                                        break;
                                    case 'phoneNumber':
                                        inputType = 'tel';
                                        placeholder = 'Enter phone number...';
                                        break;
                                    case 'singleSelect':
                                        // Create dropdown for single select fields
                                        let selectOptions = '<option value="">Choose an option...</option>';
                                        if (field.options && field.options.choices) {
                                            field.options.choices.forEach(choice => {
                                                selectOptions += `<option value="${choice.name}">${choice.name}</option>`;
                                            });
                                        }
                                        formHtml += `
                                            <div class="form-group">
                                                <label for="field-${fieldId}">${field.name} <span style="color: #666;">(${field.type})</span></label>
                                                <select id="field-${fieldId}" name="${field.name}">
                                                    ${selectOptions}
                                                </select>
                                            </div>
                                        `;
                                        return; // Skip the input creation below
                                    case 'multipleSelect':
                                        // Create multi-select for multiple select fields
                                        let multiSelectOptions = '';
                                        if (field.options && field.options.choices) {
                                            field.options.choices.forEach(choice => {
                                                multiSelectOptions += `<option value="${choice.name}">${choice.name}</option>`;
                                            });
                                        }
                                        formHtml += `
                                            <div class="form-group">
                                                <label for="field-${fieldId}">${field.name} <span style="color: #666;">(${field.type})</span></label>
                                                <select id="field-${fieldId}" name="${field.name}" multiple>
                                                    ${multiSelectOptions}
                                                </select>
                                                <small style="color: #666;">Hold Ctrl/Cmd to select multiple options</small>
                                            </div>
                                        `;
                                        return; // Skip the input creation below
                                    case 'longText':
                                        // Use textarea for long text
                                        formHtml += `
                                            <div class="form-group">
                                                <label for="field-${fieldId}">${field.name} <span style="color: #666;">(${field.type})</span></label>
                                                <textarea id="field-${fieldId}" name="${field.name}" 
                                                         placeholder="${placeholder}" rows="3"></textarea>
                                            </div>
                                        `;
                                        return; // Skip the input creation below
                                    default:
                                        placeholder = `Enter ${field.type || 'value'}...`;
                                }
                            }
                            
                            formHtml += `
                                <div class="form-group">
                                    <label for="field-${fieldId}">${field.name} <span style="color: #666;">(${field.type})</span></label>
                                    <input type="${inputType}" id="field-${fieldId}" name="${field.name}" 
                                           placeholder="${placeholder}"/>
                                </div>
                            `;
                        });
                    } else {
                        formHtml += '<p>No editable fields found in this table.</p>';
                    }
                } else {
                    // Fallback to getting fields from records if the schema doesn't have them
                    const fieldNames = new Set();
                    allRecords.forEach(record => {
                        if (record.fields) {
                            Object.keys(record.fields).forEach(field => fieldNames.add(field));
                        }
                    });
                    
                    Array.from(fieldNames).forEach(fieldName => {
                        // Replace spaces with dashes and make lowercase for the ID
                        const fieldId = fieldName.replace(/ /g, '-').toLowerCase();
                        formHtml += `
                            <div class="form-group">
                                <label for="field-${fieldId}">${fieldName}</label>
                                <input type="text" id="field-${fieldId}" name="${fieldName}" 
                                       placeholder="Enter value..."/>
                            </div>
                        `;
                    });
                    
                    if (fieldNames.size === 0) {
                        formHtml += '<p>No fields found. Please add at least one field in Airtable first.</p>';
                    }
                }
                formHtml += '</form>';
                
                // Update modal with form
                modal.querySelector('.modal-body').innerHTML = formHtml;
                modal.querySelector('#submit-add-record').disabled = false;
                
                // Add submit event listener
                modal.querySelector('#submit-add-record').addEventListener('click', async () => {
                    const form = document.getElementById('add-record-form');
                    const formData = new FormData(form);
                    const fields = {};
                    
                    // Only include non-empty fields
                    for (let [name, value] of formData.entries()) {
                        if (value && value.trim() !== '') {
                            fields[name] = value.trim();
                        }
                    }
                    
                    // Check if we have at least one field to submit
                    if (Object.keys(fields).length === 0) {
                        showToast('Please fill in at least one field before submitting.', 'warning');
                        return;
                    }
                    
                    try {
                        // Show processing message
                        modal.querySelector('#submit-add-record').disabled = true;
                        modal.querySelector('#submit-add-record').textContent = 'Processing...';
                        showToast('Processing request...', 'success');
                        
                        // Get the table ID or use table name as fallback
                        const tableId = table.id || currentTableName;
                        console.log('Using table ID/name:', tableId);
                        
                        // Process and validate fields before submitting
                        const processedFields = {};
                        let hasErrors = false;
                        let errorMessages = [];
                        
                        // Process each field based on its type
                        for (let [name, value] of Object.entries(fields)) {
                            // Skip empty fields
                            if (!value || value.trim() === '') {
                                continue;
                            }
                            
                            // Find the field definition
                            const fieldInfo = table.fields.find(f => f.name === name);
                            if (!fieldInfo) {
                                processedFields[name] = value; // Just pass it through if not found
                                continue;
                            }
                            
                            // Format values based on field type
                            try {
                                switch(fieldInfo.type) {
                                    case 'dateTime':
                                    case 'date':
                                        // Convert DD/MM/YYYY to YYYY-MM-DD for Airtable date fields
                                        if (value.match(/^\\d{1,2}\\/\\d{1,2}\\/\\d{4}$/)) {
                                            const parts = value.split('/');
                                            // Ensure we have day, month, year in the right order and format
                                            if (parts.length === 3) {
                                                const day = parts[0].padStart(2, '0');
                                                const month = parts[1].padStart(2, '0');
                                                const year = parts[2];
                                                processedFields[name] = `${year}-${month}-${day}`;
                                                console.log(`Converted date ${value} to ${processedFields[name]}`);
                                            } else {
                                                processedFields[name] = value; // Keep original if format is unexpected
                                            }
                                                        } else if (value.match(/^\\\\d{4}-\\\\d{1,2}-\\\\d{1,2}$/)) {
                                            // Already in YYYY-MM-DD format
                                            processedFields[name] = value;
                                        } else {
                                            // Try to parse as date and format properly
                                            try {
                                                const dateObj = new Date(value);
                                                if (!isNaN(dateObj.getTime())) {
                                                    const year = dateObj.getFullYear();
                                                    const month = (dateObj.getMonth() + 1).toString().padStart(2, '0');
                                                    const day = dateObj.getDate().toString().padStart(2, '0');
                                                    processedFields[name] = `${year}-${month}-${day}`;
                                                    console.log(`Parsed date ${value} to ${processedFields[name]}`);
                                                } else {
                                                    throw new Error('Invalid date');
                                                }
                                            } catch (e) {
                                                errorMessages.push(`Field "${name}" has an invalid date format. Please use YYYY-MM-DD.`);
                                                hasErrors = true;
                                            }
                                        }
                                        break;
                                    case 'number':
                                        // Ensure number fields contain valid numbers
                                        if (!isNaN(parseFloat(value))) {
                                            processedFields[name] = parseFloat(value);
                                        } else {
                                            errorMessages.push(`Field "${name}" must be a number.`);
                                            hasErrors = true;
                                        }
                                        break;
                                    default:
                                        processedFields[name] = value;
                                }
                            } catch (error) {
                                console.error(`Error processing field ${name}:`, error);
                                processedFields[name] = value; // Use original value as fallback
                            }
                        }
                        
                        console.log('Processed fields being submitted:', processedFields);
                        
                        // If validation errors, show them and abort submission
                        if (hasErrors) {
                            modal.querySelector('#submit-add-record').disabled = false;
                            modal.querySelector('#submit-add-record').textContent = 'Save Record';
                            showToast(`Validation error: ${errorMessages.join(' ')}`, 'error');
                            return;
                        }
                        
                        const submitResponse = await fetch('/api/add_record', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ tableId, fields: processedFields })
                        });

                        // Even if we get an error status, we try to parse the JSON
                        let result;
                        try {
                            result = await submitResponse.json();
                        } catch (parseError) {
                            console.error('Error parsing response:', parseError);
                            result = { 
                                success: false, 
                                error: 'Could not parse server response. See console for details.' 
                            };
                        }
                        
                        // Reset button state
                        modal.querySelector('#submit-add-record').disabled = false;
                        modal.querySelector('#submit-add-record').textContent = 'Save Record';
                        
                        if (result.success) {
                            showToast('Record added successfully!', 'success');
                            modal.remove();
                            // Refresh the current table view
                            refreshTable();
                        } else {
                            const errorMsg = result.error || 'Unknown error occurred';
                            showToast(`Error: ${errorMsg}`, 'error');
                            console.error('Server returned error:', result);
                        }
                    } catch (error) {
                        // Reset button state
                        modal.querySelector('#submit-add-record').disabled = false;
                        modal.querySelector('#submit-add-record').textContent = 'Save Record';
                        
                        showToast('Error adding record: ' + error.message, 'error');
                        console.error('Error adding record:', error);
                    }
                });
                
            } catch (error) {
                console.error('Error loading table metadata:', error);
                // Display error in the modal
                modal.querySelector('.modal-body').innerHTML = `
                    <div class="error">
                        Error loading table fields: ${error.message}<br>
                        Try refreshing the page or check the server logs.
                    </div>
                `;
                modal.querySelector('#submit-add-record').disabled = true;
                showToast('Error loading fields: ' + error.message, 'error');
            }
        }
        
        // Helper function to get table ID by name (used as a fallback)
        async function getTableIdByName(tableName) {
            try {
                // Check if we have table metadata cached
                if (!window.tableMetadata) {
                    // If not, fetch it from the server
                    const response = await fetch(`/api/base-metadata`);
                    if (!response.ok) {
                        return tableName; // Use the name as fallback
                    }
                    const data = await response.json();
                    window.tableMetadata = data;
                }
                
                // Find the table by name
                const table = window.tableMetadata?.tables?.find(t => t.name === tableName);
                return table ? table.id : tableName; // Return the ID if found, name as fallback
            } catch (error) {
                console.error('Error getting table ID:', error);
                return tableName; // Use the name as fallback
            }
        }

    function addField(tableId) {
            showToast('Add field feature coming soon', 'warning');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
'''

from airtable_helpers import normalize_field_name, coerce_payload_to_body


def get_airtable_api():
    """Returns the global Airtable API instance."""
    global api
    if api is None:
        raise Exception("Airtable API not initialized")
    return api

@app.route('/api/add_record', methods=['POST'])
def add_record_route():
    """Adds a new record to a table."""
    try:
        data = request.get_json()
        print(f"[*] Received data: {data}")
        
        # Get tableId and fields from the request
        table_id_or_name = data.get('tableId')
        fields = data.get('fields')

        if not table_id_or_name or not fields:
            return jsonify({'success': False, 'error': 'Missing tableId or fields'}), 400

        # Check if the API is initialized
        if api is None:
            return jsonify({'success': False, 'error': 'Airtable API not initialized'}), 500
        
        # Handle the table_id - it could be an ID or a name
        print(f"[*] Processing table identifier: {table_id_or_name}")
        
        # Get table schema for field type validation
        base_metadata = api.base(AIRTABLE_BASE_ID).schema()
        found_table = None
        
        # Find the correct table
        for table in base_metadata.tables:
            if table.id == table_id_or_name or table.name == table_id_or_name:
                found_table = table
                break
        
        if not found_table:
            error_msg = f"Table '{table_id_or_name}' not found in base. Available tables: {', '.join([t.name for t in base_metadata.tables])}"
            print(f"[!] {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 404

        # Process fields based on their types
        processed_fields = {}
        for key, value in fields.items():
            # Handle empty values
            if value == '' or value is None:
                continue  # Skip empty fields entirely
                
            # If value is a string, strip whitespace
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    continue  # Skip empty fields entirely
            
            # Find field definition for type-specific processing
            field_def = next((f for f in found_table.fields if f.name == key), None)
            if field_def:
                try:
                    # Process based on field type
                    if field_def.type in ['date', 'dateTime']:
                        # Handle date conversion
                        from datetime import datetime
                        import re
                        
                        # Try different date formats
                        date_formats = [
                            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
                            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
                            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
                        ]
                        
                        date_converted = False
                        for fmt in date_formats:
                            match = re.match(fmt, str(value))
                            if match:
                                if len(match.group(1)) == 4:  # YYYY format
                                    year, month, day = match.groups()
                                elif '/' in str(value):  # Assume DD/MM/YYYY
                                    day, month, year = match.groups()
                                else:  # DD-MM-YYYY
                                    day, month, year = match.groups()
                                
                                # Validate date
                                try:
                                    datetime(int(year), int(month), int(day))
                                    processed_fields[key] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                    date_converted = True
                                    break
                                except ValueError:
                                    continue
                        
                        if not date_converted:
                            return jsonify({'success': False, 'error': f'Invalid date format for field "{key}". Please use DD/MM/YYYY, YYYY-MM-DD, or DD-MM-YYYY format.'}), 400
                            
                    elif field_def.type == 'number':
                        # Convert to number
                        try:
                            if '.' in str(value):
                                processed_fields[key] = float(value)
                            else:
                                processed_fields[key] = int(value)
                        except ValueError:
                            return jsonify({'success': False, 'error': f'Field "{key}" must be a valid number.'}), 400
                            
                    elif field_def.type == 'singleSelect':
                        # Special handling for Training table - skip validation and treat as text
                        if found_table.name == '4b.Training & comptency Registe':
                            # For Training table: accept any text value for select fields
                            processed_fields[key] = value
                        else:
                            # Normal validation for other tables
                            if hasattr(field_def, 'options') and hasattr(field_def.options, 'choices'):
                                valid_options = [choice.name for choice in field_def.options.choices]
                                if str(value) not in valid_options:
                                    return jsonify({
                                        'success': False, 
                                        'error': f'Invalid option "{value}" for field "{key}". Valid options are: {", ".join(valid_options)}'
                                    }), 400
                            processed_fields[key] = value
                        
                    elif field_def.type == 'multipleSelect':
                        # Special handling for Training table - skip validation and treat as text
                        if found_table.name == '4b.Training & comptency Registe':
                            # For Training table: accept any text value for select fields
                            processed_fields[key] = value
                        else:
                            # Normal validation for other tables
                            if hasattr(field_def, 'options') and hasattr(field_def.options, 'choices'):
                                valid_options = [choice.name for choice in field_def.options.choices]
                                # Handle both single values and arrays
                                values_to_check = value if isinstance(value, list) else [value]
                                for val in values_to_check:
                                    if str(val) not in valid_options:
                                        return jsonify({
                                            'success': False, 
                                            'error': f'Invalid option "{val}" for field "{key}". Valid options are: {", ".join(valid_options)}'
                                        }), 400
                            processed_fields[key] = value
                        
                    elif field_def.type == 'autoNumber':
                        # Skip auto-number fields
                        continue
                        
                    elif field_def.type in ['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy']:
                        # Skip computed fields
                        continue
                        
                    else:
                        # Keep original value for other field types
                        processed_fields[key] = value
                        
                except Exception as e:
                    print(f"[!] Error processing field {key}: {e}")
                    processed_fields[key] = value  # Fallback to original value
            else:
                # Field not found in schema, keep original value
                processed_fields[key] = value
                
        print(f"[*] Adding record to table '{found_table.name}' with fields: {processed_fields}")
        print(f"[*] Using table name: {found_table.name}")
        # Create table instance using the base and table name
        base_instance = api.base(AIRTABLE_BASE_ID)
        table = base_instance.table(found_table.name)

        # Before creating, attempt a final normalization/coercion pass using helpers
        try:
            # Build meta_fields for coercion
            meta_fields = []
            if found_table and hasattr(found_table, 'fields'):
                for f in found_table.fields:
                    name = getattr(f, 'name', None) or getattr(f, 'id', '')
                    ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                    choices = []
                    if hasattr(f, 'options') and getattr(f, 'options'):
                        choices = [getattr(c, 'name', c) for c in getattr(f.options, 'choices', []) or []]
                    required = bool(getattr(f, 'required', False) or getattr(f, 'isRequired', False))
                    meta_fields.append({'name': name, 'type': ftype, 'choices': choices, 'required': required})

            # Map keys by normalized match
            mapped = {}
            for k, v in processed_fields.items():
                matched = next((m['name'] for m in meta_fields if normalize_field_name(m['name']) == normalize_field_name(k)), None)
                mapped[matched or k] = v

            body, errors = coerce_payload_to_body(mapped, meta_fields)
            if errors:
                return jsonify({'success': False, 'error': 'Validation failed', 'errors': errors}), 400

            new_record = table.create(body)
            print(f"[+] Record added successfully with ID: {new_record['id']}")
            return jsonify({'success': True, 'record': new_record})
        except Exception as create_error:
            error_msg = str(create_error)
            print(f"[!] Error creating record: {error_msg}")
            
            # Extract more detailed information from error message
            error_details = error_msg
            specific_field = None
            specific_error = None
            
            # Provide more helpful error messages based on common Airtable errors
            if "INVALID_VALUE_FOR_COLUMN" in error_msg:
                error_details = "One or more field values are invalid. Please check field types and formats."
            elif "UNKNOWN_FIELD_NAME" in error_msg:
                valid_fields = [f.name for f in found_table.fields if f.type not in ['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber']]
                error_details = f"Unknown field name. Valid editable fields are: {', '.join(valid_fields)}"
            elif "INVALID_MULTIPLE_CHOICE_OPTIONS" in error_msg:
                # Extract field name and invalid option from error message
                import re
                option_match = re.search(r'create new select option["\s]+([^"\']+)', error_msg)
                if option_match:
                    invalid_option = option_match.group(1).strip()
                    error_details = f"Invalid option '{invalid_option}' for a select field. Please choose from the available dropdown options only. You cannot create new options through this interface."
                else:
                    error_details = "Invalid selection for a single/multiple select field. Please choose from available dropdown options only."
            elif "NOT_FOUND" in error_msg:
                error_details = f"Table '{found_table.name}' not found or you don't have permission to access it."
            elif "AUTHENTICATION_REQUIRED" in error_msg:
                error_details = "Authentication failed. Please check your Airtable token."
            elif "permission" in error_msg.lower() or "FORBIDDEN" in error_msg:
                error_details = "Permission denied. Your token may not have write access to this table."
            else:
                # Try to extract field name for more specific errors
                import re
                field_match = re.search(r'for field["\s]+([^"\'}\s]+)', error_msg)
                if field_match:
                    specific_field = field_match.group(1).strip()
                    error_details = f"Invalid value for field '{specific_field}'. Please check the field type and format requirements."
                
            return jsonify({'success': False, 'error': error_details}), 400
                
    except Exception as e:
        import traceback
        error_message = str(e)
        print(f"[!] Error adding record: {error_message}")
        print(f"[!] Traceback: {traceback.format_exc()}")
        
        # Attempt to parse a more specific error from Airtable's response
        try:
            if isinstance(e.args, tuple) and len(e.args) > 0:
                error_details = str(e.args[0])
                if 'INVALID_VALUE_FOR_COLUMN' in error_details:
                    error_message = "Invalid value for a column. Please check the data you entered."
                elif 'UNKNOWN_FIELD_NAME' in error_details:
                    error_message = "One or more field names are incorrect."
                elif 'NOT_FOUND' in error_details or '404' in error_details:
                    error_message = "Table not found. Please check the table name or ID."
                elif 'AUTHENTICATION_REQUIRED' in error_details or '401' in error_details:
                    error_message = "Authentication failed. Please check your Airtable token."
                elif 'permission' in error_details.lower() or '403' in error_details:
                    error_message = "Permission denied. Your token may not have access to this table."
        except Exception as parse_error:
            print(f"[!] Error parsing Airtable error: {str(parse_error)}")
            
        return jsonify({'success': False, 'error': error_message}), 500

@app.route('/api/config')
def get_config():
    """Returns current configuration status (without sensitive data)"""
    return jsonify({
        'airtable_connected': api is not None,
        'base_id': AIRTABLE_BASE_ID,
        'token_configured': AIRTABLE_TOKEN is not None,
        'statistics_api_configured': STATISTICS_API is not None,
        'statistics_api_length': len(STATISTICS_API) if STATISTICS_API else 0
    })

if __name__ == '__main__':
    print("[*] Starting Clean Airtable Dashboard...")
    print("[*] Dashboard available at: http://localhost:5000")
    print("[*] Press Ctrl+C to stop")
    
    app.run(debug=True, host='0.0.0.0', port=5000)