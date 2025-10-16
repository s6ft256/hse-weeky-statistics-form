#!/usr/bin/env python3
"""
Simple Airtable Dashboard
A clean, minimal interface for Airtable data management
"""

import os
import ssl
import urllib3
from flask import Flask, render_template_string, request, jsonify
from pyairtable import Api
from airtable_helpers import normalize_field_name, coerce_payload_to_body

# Disable SSL warnings and verification for corporate proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['AIRTABLE_VERIFY_SSL'] = '0'

# Configuration
AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN') or os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID') or os.getenv('AIRTABLE_ENTERPRISE_ID')

app = Flask(__name__)

# Initialize Airtable API
try:
    print("Initializing Airtable connection...")
    api = Api(AIRTABLE_TOKEN)
    base = api.base(AIRTABLE_BASE_ID)
    print("Connected to Airtable successfully")
except Exception as e:
    print(f"❌ Failed to connect to Airtable: {e}")
    exit(1)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get all tables from the base
        tables_info = []
        base_metadata = api.base(AIRTABLE_BASE_ID).schema()
        
        for table_info in base_metadata.tables:
            table_name = table_info.name
            table_id = table_info.id
            
            # Get record count
            try:
                table = base.table(table_name)
                records = table.all(max_records=1)
                record_count = len(table.all())
            except Exception as e:
                print(f"Warning: Could not get records for {table_name}: {e}")
                record_count = 0
            
            tables_info.append({
                'name': table_name,
                'id': table_id,
                'count': record_count
            })
        
        return render_template_string(DASHBOARD_TEMPLATE, tables=tables_info)
    except Exception as e:
        return f"Error loading dashboard: {e}", 500

@app.route('/api/tables/<table_name>/records')
def get_table_records(table_name):
    """Get records for a specific table"""
    try:
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/tables/<table_name>/records/<record_id>', methods=['PUT'])
def update_record(table_name, record_id):
    """Update a specific record"""
    try:
        data = request.get_json()
        table = base.table(table_name)
        
        # Update the record
        updated_record = table.update(record_id, data)
        return jsonify(updated_record)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tables/<table_name>/records', methods=['POST'])
def create_record(table_name):
    """Create a new record"""
    try:
        data = request.get_json()
        table = base.table(table_name)
        # Map incoming payload keys (sometimes nested as {fields: {...}})
        fields = data.get('fields') if isinstance(data, dict) and data.get('fields') else data

        # Best-effort: build simple meta from first record or schema if available
        meta_fields = []
        try:
            meta = api.base(AIRTABLE_BASE_ID).schema()
            t = next((x for x in meta.tables if x.name == table_name), None)
            if t and hasattr(t, 'fields'):
                for f in t.fields:
                    name = getattr(f, 'name', None) or getattr(f, 'id', '')
                    ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                    choices = []
                    if hasattr(f, 'options') and getattr(f, 'options'):
                        choices = [getattr(c, 'name', c) for c in getattr(f.options, 'choices', []) or []]
                    required = bool(getattr(f, 'required', False) or getattr(f, 'isRequired', False))
                    meta_fields.append({'name': name, 'type': ftype, 'choices': choices, 'required': required})
        except Exception:
            meta_fields = []

        # Normalize input keys -> actual field names (try normalized match)
        mapped = {}
        if isinstance(fields, dict):
            for k, v in fields.items():
                # try exact match
                if any(normalize_field_name(k) == normalize_field_name(m['name']) for m in meta_fields if 'name' in m):
                    matched = next((m['name'] for m in meta_fields if normalize_field_name(m['name']) == normalize_field_name(k)), None)
                    mapped[matched or k] = v
                else:
                    mapped[k] = v
        else:
            mapped = fields

        # Coerce values according to meta
        body, errors = coerce_payload_to_body(mapped, meta_fields)
        if errors:
            return jsonify({'error': 'Validation failed', 'errors': errors}), 400

        # Create the record
        new_record = table.create(body)
        return jsonify(new_record)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tables/<table_name>/records/<record_id>', methods=['DELETE'])
def delete_record(table_name, record_id):
    """Delete a specific record"""
    try:
        table = base.table(table_name)
        table.delete(record_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# HTML Template
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Airtable Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #334155;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #1e293b;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #64748b;
            font-size: 1.1rem;
        }
        
        .tables-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .table-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .table-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        .table-name {
            font-size: 1.25rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
        }
        
        .table-count {
            color: #64748b;
            font-size: 0.9rem;
        }
        
        .records-section {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
            display: none;
        }
        
        .records-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 15px;
        }
        
        .records-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1e293b;
        }
        
        .back-btn {
            background: #64748b;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .back-btn:hover {
            background: #475569;
        }
        
        .records-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .records-table th,
        .records-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .records-table th {
            background: #f8fafc;
            font-weight: 600;
            color: #475569;
        }
        
        .records-table tr:hover {
            background: #f8fafc;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #64748b;
        }
        
        .error {
            color: #dc2626;
            text-align: center;
            padding: 20px;
            background: #fef2f2;
            border-radius: 8px;
            border: 1px solid #fecaca;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Airtable Dashboard</h1>
            <p>Manage your data with ease</p>
        </div>
        
        <div id="tables-view">
            <div class="tables-grid">
                {% for table in tables %}
                <div class="table-card" onclick="loadTable('{{ table.name }}')">
                    <div class="table-name">{{ table.name }}</div>
                    <div class="table-count">{{ table.count }} records</div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div id="records-view" class="records-section">
            <div class="records-header">
                <div class="records-title" id="table-title">Table Records</div>
                <button class="back-btn" onclick="showTables()">← Back to Tables</button>
            </div>
            <div id="records-content"></div>
        </div>
    </div>

    <script>
        let currentTable = null;
        
        function showTables() {
            document.getElementById('tables-view').style.display = 'block';
            document.getElementById('records-view').style.display = 'none';
            currentTable = null;
        }
        
        function showRecords() {
            document.getElementById('tables-view').style.display = 'none';
            document.getElementById('records-view').style.display = 'block';
        }
        
        async function loadTable(tableName) {
            currentTable = tableName;
            showRecords();
            
            document.getElementById('table-title').textContent = `${tableName} Records`;
            document.getElementById('records-content').innerHTML = '<div class="loading">Loading records...</div>';
            
            try {
                const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records`);
                const records = await response.json();
                
                if (response.ok) {
                    displayRecords(records);
                } else {
                    throw new Error(records.error || 'Failed to load records');
                }
            } catch (error) {
                document.getElementById('records-content').innerHTML = 
                    `<div class="error">Error loading records: ${error.message}</div>`;
            }
        }
        
        function displayRecords(records) {
            if (!records || records.length === 0) {
                document.getElementById('records-content').innerHTML = 
                    '<div class="loading">No records found</div>';
                return;
            }
            
            // Get all unique field names
            const fields = new Set();
            records.forEach(record => {
                Object.keys(record.fields || {}).forEach(field => fields.add(field));
            });
            
            const fieldArray = Array.from(fields);
            
            let html = '<table class="records-table">';
            html += '<thead><tr>';
            fieldArray.forEach(field => {
                html += `<th>${field}</th>`;
            });
            html += '</tr></thead><tbody>';
            
            records.forEach(record => {
                html += '<tr>';
                fieldArray.forEach(field => {
                    const value = record.fields[field];
                    let displayValue = '';
                    
                    if (value !== undefined && value !== null) {
                        if (Array.isArray(value)) {
                            displayValue = value.join(', ');
                        } else if (typeof value === 'object') {
                            displayValue = JSON.stringify(value);
                        } else {
                            displayValue = String(value);
                        }
                    }
                    
                    html += `<td>${displayValue}</td>`;
                });
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            document.getElementById('records-content').innerHTML = html;
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Starting Airtable Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)