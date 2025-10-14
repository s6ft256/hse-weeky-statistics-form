#!/usr/bin/env python3
"""
Working Airtable Dashboard - Simplified Version
Based on the successful sidebar server but optimized
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, render_template_string
from pyairtable import Api

# Setup SSL bypass for corporate networks
os.environ['AIRTABLE_VERIFY_SSL'] = '0'

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize Airtable connection
api_token = os.getenv('AIRTABLE_API_TOKEN')
base_id = "app1t04ZYvX3rWAM1"

if not api_token:
    print("❌ AIRTABLE_API_TOKEN not found in environment variables")
    print("💡 Set it with: $env:AIRTABLE_API_TOKEN='your_token_here'")
    sys.exit(1)

try:
    api = Api(api_token)
    base = api.base(base_id)
    print(f"✅ Connected to Airtable base: {base_id}")
    AIRTABLE_CONNECTED = True
except Exception as e:
    print(f"❌ Failed to connect to Airtable: {e}")
    AIRTABLE_CONNECTED = False
    api = None
    base = None

# HTML Template - Working Dashboard
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Working Airtable Dashboard</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f8f9fa;
        }
        .header { 
            background: white; padding: 20px; border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        .header h1 { color: #333; margin: 0 0 10px 0; }
        .status { 
            padding: 10px 15px; border-radius: 6px; margin: 10px 0;
            font-weight: 500;
        }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .nav { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
        .nav button { 
            padding: 12px 20px; background: #007bff; color: white; 
            border: none; border-radius: 6px; cursor: pointer; font-size: 14px;
            transition: all 0.2s;
        }
        .nav button:hover { background: #0056b3; transform: translateY(-2px); }
        .nav button.active { background: #28a745; }
        .content { 
            background: white; padding: 20px; border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-height: 400px;
        }
        .loading { 
            text-align: center; padding: 40px; color: #666;
            font-size: 16px;
        }
        .loading::before {
            content: '⏳ ';
            animation: spin 2s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; position: sticky; top: 0; }
        .record-row { cursor: pointer; transition: background-color 0.2s; }
        .record-row:hover { background: #f8f9fa; }
        .btn { 
            padding: 8px 16px; margin: 5px; border: none; border-radius: 4px;
            cursor: pointer; font-size: 14px; transition: all 0.2s;
        }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn:hover { opacity: 0.8; transform: translateY(-1px); }
        .form-group { margin: 15px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;
            font-size: 14px;
        }
        .modal { 
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5); z-index: 1000;
        }
        .modal-content {
            background: white; margin: 5% auto; padding: 20px; width: 90%;
            max-width: 600px; border-radius: 8px; max-height: 80vh; overflow-y: auto;
        }
        .close { 
            float: right; font-size: 28px; font-weight: bold; cursor: pointer;
            color: #aaa; line-height: 1;
        }
        .close:hover { color: #333; }
        .stats { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px; margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 20px; border-radius: 8px; text-align: center;
        }
        .stat-number { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Working Airtable Dashboard</h1>
        <div class="status {{ 'success' if connected else 'error' }}">
            {{ '✅ Connected to Airtable' if connected else '❌ Not connected to Airtable' }}
            | Base: {{ base_id }} | Server: {{ server_time }}
        </div>
    </div>

    {% if connected %}
    <div class="stats" id="stats"></div>
    
    <nav class="nav" id="table-nav">
        <div class="loading">Loading tables...</div>
    </nav>

    <div class="content">
        <div id="main-content" class="loading">
            Select a table to view records
        </div>
    </div>

    <!-- Modal for editing records -->
    <div id="edit-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2 id="modal-title">Edit Record</h2>
            <form id="edit-form">
                <div id="form-fields"></div>
                <button type="submit" class="btn btn-success">Save Changes</button>
                <button type="button" class="btn" onclick="closeModal()">Cancel</button>
            </form>
        </div>
    </div>

    <script>
        let currentTable = null;
        let tables = [];
        let records = [];

        // Initialize dashboard
        async function init() {
            console.log('🚀 Initializing dashboard...');
            await loadTables();
        }

        // Load all tables
        async function loadTables() {
            try {
                console.log('📋 Loading tables...');
                const response = await fetch('/api/tables');
                const data = await response.json();
                
                if (data.tables) {
                    tables = data.tables;
                    displayTables(tables);
                    displayStats(data.total);
                } else {
                    document.getElementById('table-nav').innerHTML = 
                        '<div class="status error">Failed to load tables</div>';
                }
            } catch (error) {
                console.error('Error loading tables:', error);
                document.getElementById('table-nav').innerHTML = 
                    '<div class="status error">Network error loading tables</div>';
            }
        }

        // Display tables as navigation buttons
        function displayTables(tables) {
            const nav = document.getElementById('table-nav');
            if (tables.length === 0) {
                nav.innerHTML = '<div class="status error">No tables found</div>';
                return;
            }
            
            nav.innerHTML = tables.map(table => 
                `<button onclick="loadTable('${table}')" id="btn-${table}">
                    📋 ${table}
                </button>`
            ).join('');
        }

        // Display statistics
        function displayStats(total) {
            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${total}</div>
                    <div class="stat-label">Total Tables</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="record-count">-</div>
                    <div class="stat-label">Records</div>
                </div>
            `;
        }

        // Load records for specific table
        async function loadTable(tableName) {
            currentTable = tableName;
            console.log(`📊 Loading table: ${tableName}`);
            
            // Update navigation
            document.querySelectorAll('.nav button').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`btn-${tableName}`).classList.add('active');
            
            // Show loading
            document.getElementById('main-content').innerHTML = 
                '<div class="loading">Loading records...</div>';
            
            try {
                const response = await fetch(`/api/table/${encodeURIComponent(tableName)}/records`);
                const data = await response.json();
                
                if (data.records) {
                    records = data.records;
                    displayRecords(records, tableName);
                    document.getElementById('record-count').textContent = records.length;
                } else {
                    document.getElementById('main-content').innerHTML = 
                        `<div class="status error">Failed to load records: ${data.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                console.error('Error loading records:', error);
                document.getElementById('main-content').innerHTML = 
                    '<div class="status error">Network error loading records</div>';
            }
        }

        // Display records in table
        function displayRecords(records, tableName) {
            const content = document.getElementById('main-content');
            
            if (records.length === 0) {
                content.innerHTML = `<div class="status error">No records found in ${tableName}</div>`;
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
            
            let html = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h2>📊 ${tableName} (${records.length} records)</h2>
                    <button class="btn btn-success" onclick="showAddForm()">➕ Add Record</button>
                </div>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Actions</th>
                                <th>ID</th>
                                ${fieldNames.map(field => `<th>${field}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            records.forEach(record => {
                html += `<tr class="record-row">
                    <td>
                        <button class="btn btn-primary" onclick="editRecord('${record.id}')">✏️</button>
                        <button class="btn btn-danger" onclick="deleteRecord('${record.id}')">🗑️</button>
                    </td>
                    <td><small>${record.id}</small></td>
                    ${fieldNames.map(field => {
                        const value = record.fields && record.fields[field];
                        let displayValue = '';
                        if (value !== null && value !== undefined) {
                            if (typeof value === 'object') {
                                displayValue = JSON.stringify(value);
                            } else {
                                displayValue = String(value);
                            }
                        }
                        return `<td>${displayValue}</td>`;
                    }).join('')}
                </tr>`;
            });
            
            html += '</tbody></table></div>';
            content.innerHTML = html;
        }

        // Edit record
        function editRecord(recordId) {
            const record = records.find(r => r.id === recordId);
            if (!record) return;
            
            document.getElementById('modal-title').textContent = `Edit Record: ${recordId}`;
            
            let formHTML = `<input type="hidden" id="record-id" value="${recordId}">`;
            
            if (record.fields) {
                Object.entries(record.fields).forEach(([field, value]) => {
                    let inputValue = value;
                    if (typeof value === 'object') {
                        inputValue = JSON.stringify(value);
                    }
                    
                    formHTML += `
                        <div class="form-group">
                            <label for="field-${field}">${field}</label>
                            <input type="text" id="field-${field}" name="${field}" 
                                   value="${inputValue || ''}" placeholder="Enter ${field}">
                        </div>
                    `;
                });
            }
            
            document.getElementById('form-fields').innerHTML = formHTML;
            document.getElementById('edit-modal').style.display = 'block';
        }

        // Show add form
        function showAddForm() {
            if (records.length === 0) return;
            
            document.getElementById('modal-title').textContent = `Add New Record to ${currentTable}`;
            document.getElementById('record-id').value = '';
            
            // Get fields from first record
            const sampleRecord = records[0];
            let formHTML = '<input type="hidden" id="record-id" value="">';
            
            if (sampleRecord.fields) {
                Object.keys(sampleRecord.fields).forEach(field => {
                    formHTML += `
                        <div class="form-group">
                            <label for="field-${field}">${field}</label>
                            <input type="text" id="field-${field}" name="${field}" 
                                   placeholder="Enter ${field}">
                        </div>
                    `;
                });
            }
            
            document.getElementById('form-fields').innerHTML = formHTML;
            document.getElementById('edit-modal').style.display = 'block';
        }

        // Close modal
        function closeModal() {
            document.getElementById('edit-modal').style.display = 'none';
        }

        // Save record
        document.getElementById('edit-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const recordId = document.getElementById('record-id').value;
            const formData = new FormData(e.target);
            
            const fields = {};
            for (let [key, value] of formData.entries()) {
                if (key !== 'record-id' && value.trim()) {
                    // Try to parse JSON for complex fields
                    try {
                        fields[key] = JSON.parse(value);
                    } catch {
                        fields[key] = value;
                    }
                }
            }
            
            try {
                let response;
                if (recordId) {
                    // Update existing record
                    response = await fetch(`/api/table/${currentTable}/record/${recordId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ fields })
                    });
                } else {
                    // Create new record
                    response = await fetch(`/api/table/${currentTable}/record`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ fields })
                    });
                }
                
                const result = await response.json();
                
                if (result.success) {
                    closeModal();
                    loadTable(currentTable); // Reload table
                    alert(recordId ? 'Record updated successfully!' : 'Record created successfully!');
                } else {
                    alert('Error: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error saving record:', error);
                alert('Network error saving record');
            }
        });

        // Delete record
        async function deleteRecord(recordId) {
            if (!confirm('Are you sure you want to delete this record?')) return;
            
            try {
                const response = await fetch(`/api/table/${currentTable}/record/${recordId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    loadTable(currentTable); // Reload table
                    alert('Record deleted successfully!');
                } else {
                    alert('Error deleting record: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error deleting record:', error);
                alert('Network error deleting record');
            }
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', init);
    </script>
    {% else %}
    <div class="content">
        <div class="status error">
            <h2>🔐 Airtable Not Connected</h2>
            <p>Please configure your Airtable API token:</p>
            <pre>$env:AIRTABLE_API_TOKEN="your_token_here"</pre>
            <p>Then restart the server.</p>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(HTML_TEMPLATE, 
                                connected=AIRTABLE_CONNECTED,
                                base_id=base_id,
                                server_time=datetime.now().strftime("%H:%M:%S"))

@app.route('/api/tables')
def get_tables():
    """Get all available tables"""
    if not AIRTABLE_CONNECTED:
        return jsonify({'error': 'Airtable not connected'}), 500
    
    try:
        # Pre-defined table names (since Airtable API doesn't provide table listing)
        table_names = [
            "Projects", "Invoices", "Equipment", "Employees", 
            "Time Tracking", "Materials", "Contracts", 
            "Payments", "Vendors", "Tasks", "Clients"
        ]
        
        return jsonify({
            'tables': table_names,
            'total': len(table_names),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>/records')
def get_records(table_name):
    """Get records from a specific table"""
    if not AIRTABLE_CONNECTED:
        return jsonify({'error': 'Airtable not connected'}), 500
    
    try:
        table = base.table(table_name)
        records = table.all()
        
        return jsonify({
            'records': records,
            'count': len(records),
            'table': table_name,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>/record', methods=['POST'])
def create_record(table_name):
    """Create a new record"""
    if not AIRTABLE_CONNECTED:
        return jsonify({'error': 'Airtable not connected'}), 500
    
    try:
        data = request.get_json()
        if not data or 'fields' not in data:
            return jsonify({'error': 'Missing fields data'}), 400
        
        table = base.table(table_name)
        record = table.create(data['fields'])
        
        return jsonify({
            'success': True,
            'record': record,
            'message': f'Record created in {table_name}'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/table/<table_name>/record/<record_id>', methods=['PUT'])
def update_record(table_name, record_id):
    """Update an existing record"""
    if not AIRTABLE_CONNECTED:
        return jsonify({'error': 'Airtable not connected'}), 500
    
    try:
        data = request.get_json()
        if not data or 'fields' not in data:
            return jsonify({'error': 'Missing fields data'}), 400
        
        table = base.table(table_name)
        record = table.update(record_id, data['fields'])
        
        return jsonify({
            'success': True,
            'record': record,
            'message': f'Record {record_id} updated in {table_name}'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/table/<table_name>/record/<record_id>', methods=['DELETE'])
def delete_record(table_name, record_id):
    """Delete a record"""
    if not AIRTABLE_CONNECTED:
        return jsonify({'error': 'Airtable not connected'}), 500
    
    try:
        table = base.table(table_name)
        table.delete(record_id)
        
        return jsonify({
            'success': True,
            'message': f'Record {record_id} deleted from {table_name}'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 WORKING AIRTABLE DASHBOARD")
    print("="*50)
    print(f"📊 Base ID: {base_id}")
    print(f"🔗 URL: http://localhost:5000")
    print(f"✅ SSL Bypass: Enabled")
    print(f"📡 Connection: {'✅ Connected' if AIRTABLE_CONNECTED else '❌ Not Connected'}")
    print("="*50)
    
    if not AIRTABLE_CONNECTED:
        print("⚠️  Set your API token: $env:AIRTABLE_API_TOKEN='your_token'")
        print("🔄 Then restart the server")
    
    try:
        app.run(host='localhost', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")