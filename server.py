#!/usr/bin/env python3
"""
Working Airtable Dashboard - Updated with Modern UI Structure
Based on the successful working dashboard design
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
    AIRTABLE_CONNECTED = False
    api = None
    base = None
else:
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


# HTML Template for the home page
HOME_TEMPLATE = """
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
        .stat-label { font-size: 0.9em; opacity: 0.9;
        }
        .endpoint {
            background: #f5f5f5;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .endpoint h3 { color: #667eea; margin-bottom: 10px; }
        .method {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.85em;
            margin-right: 10px;
        }
        .get { background: #4caf50; color: white; }
        .post { background: #2196f3; color: white; }
        .put { background: #ff9800; color: white; }
        .delete { background: #f44336; color: white; }
        .url { font-family: 'Courier New', monospace; color: #333; }
        .description { color: #666; margin-top: 10px; line-height: 1.6; }
        .example {
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }
        .footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
        .test-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
            font-size: 1em;
        }
        .test-button:hover { background: #5568d3; }
        .test-button:disabled { background: #ccc; cursor: not-allowed; }
        .tables-container {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .table-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .table-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .table-card h4 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.15em;
        }
        .table-details summary {
            transition: color 0.2s;
        }
        .table-details summary:hover {
            color: #5568d3;
        }
        .table-details[open] summary {
            margin-bottom: 10px;
        }
        .table-meta {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .fields-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .field-tag {
            background: #e3f2fd;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            border-left: 3px solid #2196f3;
        }
        .field-name { font-weight: bold; color: #1976d2; }
        .field-type { color: #666; font-style: italic; }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #c62828;
        }
        .table-actions {
            margin-top: 15px;
        }
        .action-btn {
            background: #4caf50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
            font-size: 0.9em;
        }
        .action-btn:hover { background: #45a049; }
        .action-btn.secondary { background: #2196f3; }
        .action-btn.secondary:hover { background: #1976d2; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Airtable Client Server</h1>
            <p>Modern REST API for Airtable Operations</p>
        </div>

        <div class="content">
            {% if connected %}
            <div class="section">
                <h2>� Your Airtable Dashboard</h2>
                <p class="description" style="margin-bottom: 20px;">
                    Loading your tables and data from Airtable...
                </p>
                <div id="tablesContainer">
                    <div class="loading">⏳ Loading tables from your Airtable base...</div>
                </div>
            </div>
            {% endif %}
        </div>

        <div class="footer">
            <p>Modernized Airtable Client v3.2.0 | Running on Flask</p>
            <p>Server started: {{ server_start_time }}</p>
        </div>
    </div>

    <script>
        function testEndpoint(url) {
            window.open(url, '_blank');
        }
        
        function toggleAllDetails(expand) {
            const details = document.querySelectorAll('.table-details');
            details.forEach(detail => {
                detail.open = expand;
            });
        }

        async function loadTables() {
            const container = document.getElementById('tablesContainer');
            container.innerHTML = '<div class="loading">⏳ Loading tables from Airtable...</div>';

            try {
                const response = await fetch('/api/tables');
                const data = await response.json();

                if (data.error) {
                    container.innerHTML = `<div class="error-message">❌ ${data.error}</div>`;
                    return;
                }

                if (data.tables.length === 0) {
                    container.innerHTML = '<p class="description">No tables found in this base.</p>';
                    return;
                }

                // Calculate statistics
                const totalFields = data.tables.reduce((sum, t) => sum + t.fields.length, 0);
                const totalViews = data.tables.reduce((sum, t) => sum + t.views.length, 0);

                let html = '<div class="tables-container">';
                
                // Dashboard stats
                html += `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2.5em; font-weight: bold;">${data.table_count}</div>
                            <div style="opacity: 0.9;">Tables</div>
                        </div>
                        <div style="background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2.5em; font-weight: bold;">${totalFields}</div>
                            <div style="opacity: 0.9;">Total Fields</div>
                        </div>
                        <div style="background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2.5em; font-weight: bold;">${totalViews}</div>
                            <div style="opacity: 0.9;">Total Views</div>
                        </div>
                        <div style="background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 1.2em; font-weight: bold; padding: 10px 0;">${data.base_id}</div>
                            <div style="opacity: 0.9;">Base ID</div>
                        </div>
                    </div>
                `;

                html += `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                        <h3 style="color: #667eea; margin: 0;">📋 All Tables (${data.table_count})</h3>
                        <div>
                            <button class="action-btn secondary" onclick="toggleAllDetails(true)" style="margin-right: 10px;">
                                📂 Expand All
                            </button>
                            <button class="action-btn secondary" onclick="toggleAllDetails(false)">
                                📁 Collapse All
                            </button>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px;">
                `;

                for (const table of data.tables) {
                    const editableFields = table.fields.filter(f => 
                        !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
                    );
                    
                    html += `
                        <div class="table-card" style="position: relative; height: fit-content;">
                            <div style="position: absolute; top: 15px; right: 15px; display: flex; gap: 5px;">
                                <span style="background: #667eea; color: white; padding: 4px 10px; border-radius: 15px; font-size: 0.75em;">
                                    ${table.fields.length} fields
                                </span>
                                <span style="background: #2196f3; color: white; padding: 4px 10px; border-radius: 15px; font-size: 0.75em;">
                                    ${editableFields.length} editable
                                </span>
                            </div>
                            <h4 style="margin-bottom: 10px; padding-right: 180px;">📋 ${table.name}</h4>
                            <div class="table-meta" style="font-size: 0.85em; margin-bottom: 15px;">
                                ${table.description ? `<div style="color: #666; margin-bottom: 8px;">${table.description}</div>` : ''}
                                <div style="color: #999;">ID: <code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-size: 0.85em;">${table.id}</code></div>
                                ${table.views.length > 0 ? `<div style="color: #999; margin-top: 5px;">Views: ${table.views.length}</div>` : ''}
                            </div>
                            
                            <details class="table-details" style="margin-bottom: 15px;">
                                <summary style="cursor: pointer; font-weight: bold; color: #667eea; padding: 8px; background: #f8f9fa; border-radius: 4px; user-select: none;">
                                    🔍 Fields (${table.fields.length})
                                </summary>
                                <div style="margin-top: 10px; max-height: 300px; overflow-y: auto;">
                                    ${table.fields.map(field => {
                                        const isEditable = editableFields.some(f => f.id === field.id);
                                        return `
                                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #eee;">
                                                <div>
                                                    <div style="font-weight: 500; color: #333;">${field.name}</div>
                                                    <div style="font-size: 0.8em; color: #999;">${field.type}</div>
                                                </div>
                                                <div style="font-size: 0.75em; padding: 2px 8px; border-radius: 10px; ${isEditable ? 'background: #e8f5e9; color: #2e7d32;' : 'background: #fff3e0; color: #e65100;'}">
                                                    ${isEditable ? '✓ Editable' : '🔒 Read-only'}
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            </details>

                            <div style="display: flex; flex-direction: column; gap: 8px;">
                                <button class="action-btn" onclick="viewRecords('${table.name}')" style="width: 100%;">
                                    📊 View Records
                                </button>
                                <button class="action-btn" onclick="showAddRecordForm('${table.name}', ${JSON.stringify(table.fields)})" style="width: 100%;">
                                    ➕ Add Record
                                </button>
                            </div>
                        </div>
                    `;
                }
                
                html += `</div>`; // Close grid

                html += '</div>';
                container.innerHTML = html;

            } catch (error) {
                container.innerHTML = `<div class="error-message">❌ Error loading tables: ${error.message}</div>`;
            }
        }

        async function viewRecords(tableName) {
            const container = document.getElementById('tablesContainer');
            container.innerHTML = `<div class="loading">⏳ Loading records from ${tableName}...</div>`;

            try {
                const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records?max_records=10`);
                const data = await response.json();

                if (data.error) {
                    container.innerHTML = `<div class="error-message">❌ ${data.error}</div>`;
                    return;
                }

                let html = '<div class="tables-container">';
                html += `
                    <div style="margin-bottom: 20px;">
                        <button class="action-btn" onclick="loadTables()">← Back to Tables</button>
                    </div>
                    <h3>Records from: ${data.table} (showing ${data.count} records)</h3>
                `;

                if (data.records.length === 0) {
                    html += '<p class="description">No records found in this table.</p>';
                } else {
                    for (const record of data.records) {
                        html += `
                            <div class="table-card">
                                <h4>🔖 Record ID: ${record.id}</h4>
                                <div class="table-meta">
                                    <strong>Created:</strong> ${record.createdTime || 'N/A'}
                                </div>
                                <details open style="margin-top: 10px;">
                                    <summary style="cursor: pointer; font-weight: bold; color: #667eea;">
                                        📝 Fields
                                    </summary>
                                    <pre style="background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; margin-top: 10px;">${JSON.stringify(record.fields, null, 2)}</pre>
                                </details>
                                <div class="table-actions">
                                    <button class="action-btn" onclick="showEditRecordForm('${data.table}', '${record.id}', ${JSON.stringify(record.fields).replace(/'/g, "&#39;")})">
                                        ✏️ Edit Record
                                    </button>
                                    <button class="action-btn secondary" onclick="deleteRecord('${data.table}', '${record.id}')">
                                        🗑️ Delete Record
                                    </button>
                                </div>
                            </div>
                        `;
                    }
                }

                html += '</div>';
                container.innerHTML = html;

            } catch (error) {
                container.innerHTML = `<div class="error-message">❌ Error loading records: ${error.message}</div>`;
            }
        }

        function showAddRecordForm(tableName, fields) {
            const container = document.getElementById('tablesContainer');
            
            // Filter to only allow editable field types
            const editableFields = fields.filter(f => 
                !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
            );

            let html = '<div class="tables-container">';
            html += `
                <div style="margin-bottom: 20px;">
                    <button class="action-btn" onclick="loadTables()">← Back to Tables</button>
                </div>
                <div class="table-card">
                    <h3>➕ Add New Record to: ${tableName}</h3>
                    <p class="description" style="color: #666; margin-bottom: 20px;">
                        ⚠️ Note: You can add/edit field values, but cannot modify the table structure itself.
                    </p>
                    <form id="addRecordForm" onsubmit="submitNewRecord(event, '${tableName}')">
            `;

            for (const field of editableFields) {
                html += `
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; font-weight: bold; margin-bottom: 5px; color: #333;">
                            ${field.name} <span style="color: #999; font-size: 0.9em;">(${field.type})</span>
                        </label>
                        ${getFieldInput(field)}
                    </div>
                `;
            }

            html += `
                        <div style="margin-top: 20px; display: flex; gap: 10px;">
                            <button type="submit" class="action-btn">💾 Save Record</button>
                            <button type="button" class="action-btn secondary" onclick="loadTables()">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>`;
            
            container.innerHTML = html;
        }

        function showEditRecordForm(tableName, recordId, currentFields) {
            const container = document.getElementById('tablesContainer');

            let html = '<div class="tables-container">';
            html += `
                <div style="margin-bottom: 20px;">
                    <button class="action-btn" onclick="viewRecords('${tableName}')">← Back to Records</button>
                </div>
                <div class="table-card">
                    <h3>✏️ Edit Record: ${recordId}</h3>
                    <p class="description" style="color: #666; margin-bottom: 20px;">
                        ⚠️ Note: You can edit field values, but cannot modify the table structure itself.
                    </p>
                    <form id="editRecordForm" onsubmit="submitEditRecord(event, '${tableName}', '${recordId}')">
            `;

            for (const [fieldName, fieldValue] of Object.entries(currentFields)) {
                const valueStr = JSON.stringify(fieldValue);
                html += `
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; font-weight: bold; margin-bottom: 5px; color: #333;">
                            ${fieldName}
                        </label>
                        <textarea 
                            name="${fieldName}" 
                            style="width: 100%; min-height: 60px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace;"
                        >${typeof fieldValue === 'object' ? JSON.stringify(fieldValue, null, 2) : fieldValue}</textarea>
                    </div>
                `;
            }

            html += `
                        <div style="margin-top: 20px; display: flex; gap: 10px;">
                            <button type="submit" class="action-btn">💾 Update Record</button>
                            <button type="button" class="action-btn secondary" onclick="viewRecords('${tableName}')">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>`;
            
            container.innerHTML = html;
        }

        function getFieldInput(field) {
            const fieldName = field.name.replace(/"/g, '&quot;');
            
            switch(field.type) {
                case 'multilineText':
                    return `<textarea name="${fieldName}" style="width: 100%; min-height: 80px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"></textarea>`;
                case 'checkbox':
                    return `<input type="checkbox" name="${fieldName}" style="width: 20px; height: 20px;">`;
                case 'number':
                case 'currency':
                case 'percent':
                case 'duration':
                    return `<input type="number" name="${fieldName}" step="any" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">`;
                case 'date':
                    return `<input type="date" name="${fieldName}" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">`;
                case 'dateTime':
                    return `<input type="datetime-local" name="${fieldName}" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">`;
                case 'email':
                    return `<input type="email" name="${fieldName}" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">`;
                case 'url':
                    return `<input type="url" name="${fieldName}" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">`;
                case 'phoneNumber':
                    return `<input type="tel" name="${fieldName}" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">`;
                case 'rating':
                    return `<input type="number" name="${fieldName}" min="0" max="10" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">`;
                default:
                    return `<input type="text" name="${fieldName}" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">`;
            }
        }

        async function submitNewRecord(event, tableName) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = {};

            for (const [key, value] of formData.entries()) {
                if (value !== '') {
                    // Try to parse as JSON for complex fields
                    try {
                        data[key] = JSON.parse(value);
                    } catch {
                        // Handle checkbox
                        if (form.elements[key].type === 'checkbox') {
                            data[key] = form.elements[key].checked;
                        } else {
                            data[key] = value;
                        }
                    }
                }
            }

            try {
                const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                
                if (response.ok) {
                    alert('✅ Record created successfully!');
                    viewRecords(tableName);
                } else {
                    alert(`❌ Error: ${result.error || 'Unknown error'}`);
                }
            } catch (error) {
                alert(`❌ Error creating record: ${error.message}`);
            }
        }

        async function submitEditRecord(event, tableName, recordId) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = {};

            for (const [key, value] of formData.entries()) {
                if (value !== '') {
                    // Try to parse as JSON for complex fields
                    try {
                        data[key] = JSON.parse(value);
                    } catch {
                        data[key] = value;
                    }
                }
            }

            try {
                const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records/${recordId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                
                if (response.ok) {
                    alert('✅ Record updated successfully!');
                    viewRecords(tableName);
                } else {
                    alert(`❌ Error: ${result.error || 'Unknown error'}`);
                }
            } catch (error) {
                alert(`❌ Error updating record: ${error.message}`);
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

                const result = await response.json();
                
                if (response.ok) {
                    alert('✅ Record deleted successfully!');
                    viewRecords(tableName);
                } else {
                    alert(`❌ Error: ${result.error || 'Unknown error'}`);
                }
            } catch (error) {
                alert(`❌ Error deleting record: ${error.message}`);
            }
        }

        // Auto-load tables on page load
        window.addEventListener('DOMContentLoaded', function() {
            console.log('Page loaded, attempting to load tables...');
            loadTables();
        });
    </script>
</body>
</html>
"""

SERVER_START_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route('/')
def home():
    """Home page with API documentation."""
    return render_template_string(
        HOME_TEMPLATE,
        connected=AIRTABLE_CONNECTED,
        server_start_time=SERVER_START_TIME
    )


@app.route('/api/status')
def status():
    """Get server and Airtable connection status."""
    return jsonify({
        "status": "running",
        "airtable_connected": AIRTABLE_CONNECTED,
        "server_start_time": SERVER_START_TIME,
        "base_id": client.base_id if AIRTABLE_CONNECTED else None,
        "permissions": {
            "can_view_tables": True,
            "can_view_records": True,
            "can_create_records": True,
            "can_update_records": True,
            "can_delete_records": True,
            "can_create_tables": False,
            "can_modify_table_structure": False,
            "can_delete_tables": False
        },
        "endpoints": [
            "GET /",
            "GET /api/status",
            "GET /api/tables",
            "GET /api/tables/<table_name>/records",
            "GET /api/tables/<table_name>/records/<record_id>",
            "POST /api/tables/<table_name>/records",
            "PUT /api/tables/<table_name>/records/<record_id>",
            "DELETE /api/tables/<table_name>/records/<record_id>",
        ]
    })


@app.route('/api/tables')
def list_tables():
    """Get list of all tables in the base with their schemas."""
    if not AIRTABLE_CONNECTED:
        return jsonify({
            "error": "Airtable not configured",
            "demo_tables": ["Users", "Tasks", "Projects"]
        }), 503
    
    try:
        # Try to get schema first (requires schema.bases:read permission)
        try:
            base = client._api.base(client.base_id)
            schema = base.schema()
            
            tables_info = []
            for table in schema.tables:
                table_info = {
                    "id": table.id,
                    "name": table.name,
                    "description": table.description,
                    "primary_field_id": table.primary_field_id,
                    "fields": [
                        {
                            "id": field.id,
                            "name": field.name,
                            "type": field.type,
                            "description": field.description if hasattr(field, 'description') else None
                        }
                        for field in table.fields
                    ],
                    "views": [
                        {
                            "id": view.id,
                            "name": view.name,
                            "type": view.type
                        }
                        for view in table.views
                    ] if table.views else []
                }
                tables_info.append(table_info)
            
            return jsonify({
                "base_id": client.base_id,
                "table_count": len(tables_info),
                "tables": tables_info
            })
        except Exception as schema_error:
            # If schema API fails, log the full error and provide helpful message
            import traceback
            error_trace = traceback.format_exc()
            print(f"Schema API Error: {error_trace}")
            
            return jsonify({
                "error": "Unable to fetch table schemas - token needs 'schema.bases:read' permission",
                "base_id": client.base_id,
                "api_error": str(schema_error),
                "help": "To see your tables, update your Airtable Personal Access Token with schema.bases:read scope",
                "steps": [
                    "1. Go to https://airtable.com/create/tokens",
                    "2. Edit your token",
                    "3. Add 'schema.bases:read' scope",
                    "4. Add your base to the token's access list",
                    "5. Restart the server"
                ]
            }), 403
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in /api/tables: {error_details}")
        return jsonify({
            "error": f"Failed to fetch tables: {str(e)}",
            "details": error_details
        }), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tables/<table_name>/records', methods=['GET'])
def get_records(table_name: str):
    """Get all records from a table with support for large datasets."""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 503
    
    try:
        # Get query parameters
        filters = request.args.get('filters')
        fields = request.args.get('fields')
        max_records = request.args.get('max_records', type=int)
        
        # If max_records is not specified, fetch ALL records (no limit)
        # Otherwise use the specified limit
        if max_records is None:
            max_records = None  # This tells get_records to fetch all records via pagination
        
        # Parse fields if provided
        fields_list = fields.split(',') if fields else None
        
        # Fetch records (with automatic pagination for large datasets)
        records = client.get_records(
            table_name,
            filters=filters,
            fields=fields_list,
            max_records=max_records
        )
        
        return jsonify({
            "table": table_name,
            "count": len(records),
            "records": records,
            "note": "Fetched all available records" if max_records is None else f"Limited to {max_records} records"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tables/<table_name>/records/<record_id>', methods=['GET'])
def get_record(table_name: str, record_id: str):
    """Get a single record by ID."""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 503
    
    try:
        record = client.get_record(table_name, record_id)
        return jsonify(record)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tables/<table_name>/records', methods=['POST'])
def create_record(table_name: str):
    """Create a new record."""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        record = client.create_record(table_name, data)
        return jsonify(record), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tables/<table_name>/records/<record_id>', methods=['PUT'])
def update_record(table_name: str, record_id: str):
    """Update a record."""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        replace = request.args.get('replace', 'false').lower() == 'true'
        
        record = client.update_record(table_name, record_id, data, replace=replace)
        return jsonify(record)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tables/<table_name>/records/<record_id>', methods=['DELETE'])
def delete_record(table_name: str, record_id: str):
    """Delete a record."""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 503
    
    try:
        result = client.delete_record(table_name, record_id)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🚀 Airtable Client Development Server")
    print("="*60)
    print(f"\n  Status: {'✅ Connected to Airtable' if AIRTABLE_CONNECTED else '⚠️  Demo Mode (Configure credentials)'}")
    print(f"\n  Server URL: http://localhost:5000")
    print(f"  API Status: http://localhost:5000/api/status")
    print(f"\n  Press Ctrl+C to stop the server")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
