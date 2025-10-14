#!/usr/bin/env python3
"""
Airtable Dashboard with Sidebar Navigation - Edit Records Interface
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from flask import Flask, jsonify, request, render_template_string
except ImportError:
    print("Flask is not installed. Installing now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    from flask import Flask, jsonify, request, render_template_string

from pyairtable import AirtableClient
from pyairtable.utils import setup_logging

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Setup logging
setup_logging("INFO")

# Initialize Airtable client
try:
    client = AirtableClient()
    AIRTABLE_CONNECTED = True
    print(f"✅ Connected to Airtable: {client}")
except ValueError as e:
    AIRTABLE_CONNECTED = False
    print(f"⚠️  Airtable not configured: {e}")
    client = None

# Server start time
SERVER_START_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# HTML Template with Sidebar
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Airtable Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .container {
            display: flex;
            min-height: 100vh;
        }
        
        /* Sidebar Styles */
        .sidebar {
            width: 280px;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            z-index: 100;
        }
        .sidebar-header {
            padding: 30px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .sidebar-header h3 {
            font-size: 1.3em;
            margin-bottom: 5px;
        }
        .sidebar-header p {
            font-size: 0.85em;
            opacity: 0.8;
        }
        .sidebar-menu {
            list-style: none;
            padding: 10px 0;
        }
        .sidebar-menu li {
            padding: 0;
            margin: 0;
        }
        .sidebar-menu button {
            width: 100%;
            text-align: left;
            padding: 15px 20px;
            background: transparent;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 0.95em;
            border-left: 4px solid transparent;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .sidebar-menu button:hover {
            background: rgba(255,255,255,0.1);
            border-left-color: white;
        }
        .sidebar-menu button.active {
            background: rgba(255,255,255,0.2);
            border-left-color: white;
            font-weight: bold;
        }
        .table-badge {
            margin-left: auto;
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75em;
        }
        
        /* Main Content Styles */
        .main-content {
            flex: 1;
            margin-left: 280px;
            background: white;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 40px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2em; margin-bottom: 5px; }
        .header p { font-size: 1em; opacity: 0.9; margin-bottom: 20px; }
        
        /* Tabs */
        .tabs-container {
            display: flex;
            gap: 5px;
            overflow-x: auto;
            padding: 0;
        }
        .tab {
            background: rgba(255,255,255,0.1);
            color: white;
            border: none;
            padding: 12px 20px;
            cursor: pointer;
            font-size: 0.9em;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            transition: all 0.2s;
            white-space: nowrap;
            border-bottom: 3px solid transparent;
        }
        .tab:hover {
            background: rgba(255,255,255,0.2);
        }
        .tab.active {
            background: white;
            color: #667eea;
            font-weight: bold;
            border-bottom-color: #667eea;
        }
        
        .content { padding: 30px 40px; min-height: calc(100vh - 200px); }
        
        /* Table Styles */
        .table-info {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .table-info h2 {
            color: #333;
            margin-bottom: 15px;
        }
        .table-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat-box {
            background: white;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        .stat-box .number {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-box .label {
            font-size: 0.9em;
            color: #666;
        }
        
        /* Records Container */
        .records-container {
            display: grid;
            gap: 20px;
        }
        .record-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .record-card h4 {
            color: #667eea;
            margin-bottom: 15px;
        }
        .record-field {
            padding: 10px;
            margin-bottom: 8px;
            background: #f5f5f5;
            border-radius: 4px;
        }
        .field-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .field-value {
            color: #666;
        }
        
        /* Buttons */
        .action-btn {
            background: #4caf50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .action-btn:hover { background: #45a049; }
        .action-btn.secondary { background: #2196f3; }
        .action-btn.secondary:hover { background: #1976d2; }
        .action-btn.danger { background: #f44336; }
        .action-btn.danger:hover { background: #da190b; }
        
        /* Form Styles */
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        /* Loading & Messages */
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1.1em;
        }
        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #c62828;
            margin-bottom: 20px;
        }
        .success-message {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #2e7d32;
            margin-bottom: 20px;
        }
        
        .footer {
            background: #f5f5f5;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <h3>📋 Tables</h3>
                <p id="tableCount">Loading...</p>
            </div>
            <ul class="sidebar-menu" id="sidebarMenu">
                <li><div class="loading">Loading tables...</div></li>
            </ul>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="header">
                <h1>🚀 Airtable Client Server</h1>
                <p>Modern REST API for Airtable Operations</p>
                
                <!-- Tabs -->
                <div class="tabs-container" id="tabsContainer">
                    <div class="loading" style="padding: 10px; color: white; opacity: 0.7;">Loading tables...</div>
                </div>
            </div>

            <div class="content">
                <div id="mainContent">
                    <div class="loading">
                        ⏳ Select a table from the sidebar or tabs to get started...
                    </div>
                </div>
            </div>

            <div class="footer">
                <p>Airtable Dashboard v3.2.0 | Server started: {{ server_start_time }}</p>
            </div>
        </div>
    </div>

    <script>
        let currentTable = null;
        let allTables = [];

        // Load tables on page load
        document.addEventListener('DOMContentLoaded', () => {
            loadSidebar();
        });

        async function loadSidebar() {
            const sidebar = document.getElementById('sidebarMenu');
            const tableCount = document.getElementById('tableCount');
            const tabsContainer = document.getElementById('tabsContainer');
            
            try {
                const response = await fetch('/api/tables');
                const data = await response.json();

                if (data.error) {
                    sidebar.innerHTML = `<li><div class="error-message" style="margin: 20px;">❌ ${data.error}</div></li>`;
                    tabsContainer.innerHTML = `<div style="color: white; opacity: 0.7; padding: 10px;">Error loading tables</div>`;
                    return;
                }

                allTables = data.tables;
                tableCount.textContent = `${data.table_count} tables available`;

                // Populate sidebar
                let sidebarHtml = '';
                for (const table of data.tables) {
                    sidebarHtml += `
                        <li>
                            <button onclick="loadTable('${table.name}', '${table.id}')" data-table="${table.name}">
                                📋 ${table.name}
                                <span class="table-badge">${table.fields.length}</span>
                            </button>
                        </li>
                    `;
                }
                sidebar.innerHTML = sidebarHtml;

                // Populate tabs
                let tabsHtml = '';
                for (const table of data.tables) {
                    tabsHtml += `
                        <button class="tab" onclick="loadTable('${table.name}', '${table.id}')" data-tab="${table.name}">
                            ${table.name}
                        </button>
                    `;
                }
                tabsContainer.innerHTML = tabsHtml;

            } catch (error) {
                sidebar.innerHTML = `<li><div class="error-message" style="margin: 20px;">❌ ${error.message}</div></li>`;
                tabsContainer.innerHTML = `<div style="color: white; opacity: 0.7; padding: 10px;">Error: ${error.message}</div>`;
            }
        }

        async function loadTable(tableName, tableId) {
            currentTable = tableName;
            
            // Update active state in sidebar
            document.querySelectorAll('.sidebar-menu button').forEach(btn => {
                btn.classList.remove('active');
            });
            const sidebarBtn = document.querySelector(`.sidebar-menu button[data-table="${tableName}"]`);
            if (sidebarBtn) sidebarBtn.classList.add('active');
            
            // Update active state in tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            const activeTab = document.querySelector(`.tab[data-tab="${tableName}"]`);
            if (activeTab) {
                activeTab.classList.add('active');
                // Scroll tab into view
                activeTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
            
            // Load table info and records
            const container = document.getElementById('mainContent');
            container.innerHTML = '<div class="loading">⏳ Loading records...</div>';

            try {
                const table = allTables.find(t => t.name === tableName);
                const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records?max_records=50`);
                const data = await response.json();

                if (data.error) {
                    container.innerHTML = `<div class="error-message">❌ ${data.error}</div>`;
                    return;
                }

                // Filter editable fields
                const editableFields = table.fields.filter(f => 
                    !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
                );

                let html = `
                    <div class="table-info">
                        <h2>📋 ${tableName}</h2>
                        ${table.description ? `<p style="color: #666; margin-bottom: 15px;">${table.description}</p>` : ''}
                        <div class="table-stats">
                            <div class="stat-box">
                                <div class="number">${data.count}</div>
                                <div class="label">Records</div>
                            </div>
                            <div class="stat-box">
                                <div class="number">${table.fields.length}</div>
                                <div class="label">Total Fields</div>
                            </div>
                            <div class="stat-box">
                                <div class="number">${editableFields.length}</div>
                                <div class="label">Editable Fields</div>
                            </div>
                            <div class="stat-box">
                                <div class="number">${table.views.length}</div>
                                <div class="label">Views</div>
                            </div>
                        </div>
                        <div style="margin-top: 20px;">
                            <button class="action-btn" onclick="showAddRecordForm('${tableName}', ${JSON.stringify(editableFields)})">
                                ➕ Add New Record
                            </button>
                        </div>
                    </div>
                `;

                if (data.records.length === 0) {
                    html += '<p style="text-align: center; color: #666; padding: 40px;">No records found. Click "Add New Record" to create one.</p>';
                } else {
                    html += '<div class="records-container">';
                    for (const record of data.records) {
                        html += `
                            <div class="record-card">
                                <h4>🔖 ${record.id}</h4>
                                <div style="margin-bottom: 15px;">
                        `;
                        
                        for (const [fieldName, fieldValue] of Object.entries(record.fields)) {
                            html += `
                                <div class="record-field">
                                    <div class="field-name">${fieldName}</div>
                                    <div class="field-value">${JSON.stringify(fieldValue)}</div>
                                </div>
                            `;
                        }
                        
                        html += `
                                </div>
                                <button class="action-btn" onclick="showEditRecordForm('${tableName}', '${record.id}', ${JSON.stringify(record.fields).replace(/'/g, "&#39;")})">
                                    ✏️ Edit
                                </button>
                                <button class="action-btn danger" onclick="deleteRecord('${tableName}', '${record.id}')">
                                    🗑️ Delete
                                </button>
                            </div>
                        `;
                    }
                    html += '</div>';
                }

                container.innerHTML = html;

            } catch (error) {
                container.innerHTML = `<div class="error-message">❌ ${error.message}</div>`;
            }
        }

        function showAddRecordForm(tableName, fields) {
            const container = document.getElementById('mainContent');
            
            let html = `
                <div class="table-info">
                    <h2>➕ Add New Record to ${tableName}</h2>
                    <button class="action-btn secondary" onclick="loadTable('${tableName}')">← Back to Records</button>
                </div>
                <form id="addRecordForm" onsubmit="addRecord(event, '${tableName}')">
            `;

            for (const field of fields) {
                html += `
                    <div class="form-group">
                        <label>${field.name} <span style="color: #999; font-weight: normal;">(${field.type})</span></label>
                `;
                
                if (field.type === 'multilineText') {
                    html += `<textarea name="${field.name}"></textarea>`;
                } else if (field.type === 'checkbox') {
                    html += `<input type="checkbox" name="${field.name}" value="true">`;
                } else if (field.type === 'number' || field.type === 'currency' || field.type === 'percent' || field.type === 'rating') {
                    html += `<input type="number" name="${field.name}">`;
                } else if (field.type === 'date') {
                    html += `<input type="date" name="${field.name}">`;
                } else if (field.type === 'dateTime') {
                    html += `<input type="datetime-local" name="${field.name}">`;
                } else {
                    html += `<input type="text" name="${field.name}">`;
                }
                
                html += `</div>`;
            }

            html += `
                    <button type="submit" class="action-btn">💾 Save Record</button>
                    <button type="button" class="action-btn secondary" onclick="loadTable('${tableName}')">Cancel</button>
                </form>
            `;

            container.innerHTML = html;
        }

        async function addRecord(event, tableName) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const fields = {};
            
            for (const [key, value] of formData.entries()) {
                if (value) {
                    fields[key] = value;
                }
            }

            try {
                const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ fields })
                });

                const data = await response.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert('✅ Record created successfully!');
                    loadTable(tableName);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }

        function showEditRecordForm(tableName, recordId, currentFields) {
            const table = allTables.find(t => t.name === tableName);
            const editableFields = table.fields.filter(f => 
                !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
            );

            const container = document.getElementById('mainContent');
            
            let html = `
                <div class="table-info">
                    <h2>✏️ Edit Record in ${tableName}</h2>
                    <p style="color: #666;">Record ID: ${recordId}</p>
                    <button class="action-btn secondary" onclick="loadTable('${tableName}')">← Back to Records</button>
                </div>
                <form id="editRecordForm" onsubmit="updateRecord(event, '${tableName}', '${recordId}')">
            `;

            for (const field of editableFields) {
                const currentValue = currentFields[field.name] || '';
                
                html += `
                    <div class="form-group">
                        <label>${field.name} <span style="color: #999; font-weight: normal;">(${field.type})</span></label>
                `;
                
                if (field.type === 'multilineText') {
                    html += `<textarea name="${field.name}">${currentValue}</textarea>`;
                } else if (field.type === 'checkbox') {
                    html += `<input type="checkbox" name="${field.name}" value="true" ${currentValue ? 'checked' : ''}>`;
                } else if (field.type === 'number' || field.type === 'currency' || field.type === 'percent' || field.type === 'rating') {
                    html += `<input type="number" name="${field.name}" value="${currentValue}">`;
                } else if (field.type === 'date') {
                    html += `<input type="date" name="${field.name}" value="${currentValue}">`;
                } else if (field.type === 'dateTime') {
                    html += `<input type="datetime-local" name="${field.name}" value="${currentValue}">`;
                } else {
                    html += `<input type="text" name="${field.name}" value="${currentValue}">`;
                }
                
                html += `</div>`;
            }

            html += `
                    <button type="submit" class="action-btn">💾 Update Record</button>
                    <button type="button" class="action-btn secondary" onclick="loadTable('${tableName}')">Cancel</button>
                </form>
            `;

            container.innerHTML = html;
        }

        async function updateRecord(event, tableName, recordId) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const fields = {};
            
            for (const [key, value] of formData.entries()) {
                fields[key] = value;
            }

            try {
                const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records/${recordId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ fields })
                });

                const data = await response.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert('✅ Record updated successfully!');
                    loadTable(tableName);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }

        async function deleteRecord(tableName, recordId) {
            if (!confirm('Are you sure you want to delete this record? This cannot be undone.')) {
                return;
            }

            try {
                const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records/${recordId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert('✅ Record deleted successfully!');
                    loadTable(tableName);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Main dashboard page"""
    return render_template_string(HTML_TEMPLATE, 
                                 connected=AIRTABLE_CONNECTED, 
                                 server_start_time=SERVER_START_TIME)

@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get all tables with their schemas"""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 500
    
    try:
        base_id = os.getenv('AIRTABLE_BASE_ID')
        base = client.base(base_id)
        schema = base.schema()
        
        tables_info = []
        for table in schema.tables:
            tables_info.append({
                "id": table.id,
                "name": table.name,
                "description": table.description,
                "fields": [{"id": f.id, "name": f.name, "type": f.type} for f in table.fields],
                "views": [{"id": v.id, "name": v.name, "type": v.type} for v in table.views]
            })
        
        return jsonify({
            "base_id": base_id,
            "table_count": len(tables_info),
            "tables": tables_info
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tables/<table_name>/records', methods=['GET', 'POST'])
def handle_records(table_name):
    """Get or create records in a table"""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 500
    
    try:
        base_id = os.getenv('AIRTABLE_BASE_ID')
        table = client.table(base_id, table_name)
        
        if request.method == 'GET':
            max_records = request.args.get('max_records', 100, type=int)
            records = table.all(max_records=max_records)
            return jsonify({
                "table": table_name,
                "count": len(records),
                "records": records
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            fields = data.get('fields', {})
            record = table.create(fields)
            return jsonify({
                "success": True,
                "record": record
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tables/<table_name>/records/<record_id>', methods=['GET', 'PATCH', 'DELETE'])
def handle_single_record(table_name, record_id):
    """Get, update, or delete a specific record"""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 500
    
    try:
        base_id = os.getenv('AIRTABLE_BASE_ID')
        table = client.table(base_id, table_name)
        
        if request.method == 'GET':
            record = table.get(record_id)
            return jsonify(record)
        
        elif request.method == 'PATCH':
            data = request.get_json()
            fields = data.get('fields', {})
            record = table.update(record_id, fields)
            return jsonify({
                "success": True,
                "record": record
            })
        
        elif request.method == 'DELETE':
            table.delete(record_id)
            return jsonify({
                "success": True,
                "message": f"Record {record_id} deleted"
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Airtable Dashboard Server")
    print("="*60)
    print(f"📊 Server URL: http://localhost:5000")
    print(f"🔗 Airtable Connection: {'✅ Connected' if AIRTABLE_CONNECTED else '❌ Not Connected'}")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
