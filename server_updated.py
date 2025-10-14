#!/usr/bin/env python3
"""
Airtable Dashboard with Working UI Structure - Updated server.py
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

# HTML Template - Enterprise Product Roadmap Style UI
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Roadmapping - Airtable Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #333;
            line-height: 1.5;
        }
        
        /* Layout Structure */
        .dashboard-container {
            display: flex;
            min-height: 100vh;
        }
        
        /* Sidebar - Teal Theme */
        .sidebar {
            width: 240px;
            background: linear-gradient(180deg, #20b2aa 0%, #008b8b 100%);
            color: white;
            padding: 0;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            z-index: 100;
        }
        
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .sidebar-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .sidebar-subtitle {
            font-size: 14px;
            opacity: 0.8;
        }
        
        .sidebar-nav {
            padding: 10px 0;
        }
        
        .nav-section {
            margin-bottom: 8px;
        }
        
        .nav-section-title {
            padding: 8px 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.7;
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 20px;
            color: white;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }
        
        .nav-item:hover {
            background: rgba(255,255,255,0.1);
            border-left-color: rgba(255,255,255,0.5);
        }
        
        .nav-item.active {
            background: rgba(255,255,255,0.15);
            border-left-color: white;
            font-weight: 500;
        }
        
        .nav-icon {
            width: 16px;
            height: 16px;
            opacity: 0.8;
        }
        
        /* Main Content Area */
        .main-content {
            flex: 1;
            margin-left: 240px;
            display: flex;
            flex-direction: column;
        }
        
        /* Top Header */
        .top-header {
            background: white;
            padding: 16px 24px;
            border-bottom: 1px solid #e9ecef;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .header-top {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: #6c757d;
        }
        
        .connection-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .connection-status.connected {
            background: #d4f6d4;
            color: #0f6937;
        }
        
        .connection-status.disconnected {
            background: #fdeaea;
            color: #dc2626;
        }
        
        /* Content Header */
        .content-header {
            background: white;
            padding: 20px 24px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .content-title-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .content-title {
            font-size: 24px;
            font-weight: 600;
            color: #333;
        }
        
        .header-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .btn {
            padding: 8px 16px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
            color: #333;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .btn:hover {
            background: #f8f9fa;
            border-color: #adb5bd;
        }
        
        .btn-primary {
            background: #007bff;
            color: white;
            border-color: #007bff;
        }
        
        .btn-primary:hover {
            background: #0056b3;
            border-color: #0056b3;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
            border-color: #28a745;
        }
        
        .btn-success:hover {
            background: #1e7e34;
        }
        
        /* Filter Bar */
        .filter-bar {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .filter-select {
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            font-size: 14px;
            min-width: 120px;
        }
        
        /* Main Content */
        .content-body {
            flex: 1;
            padding: 0;
            background: #f8f9fa;
        }
        
        .table-container {
            background: white;
            margin: 0;
            border-radius: 0;
        }
        
        /* Data Table */
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th {
            background: #f8f9fa;
            padding: 12px 16px;
            text-align: left;
            font-weight: 500;
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #e9ecef;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .data-table td {
            padding: 16px;
            border-bottom: 1px solid #f1f3f4;
            vertical-align: middle;
        }
        
        .data-table tr:hover {
            background: #f8f9fa;
        }
        
        /* Status Badges */
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            text-transform: capitalize;
        }
        
        .status-complete {
            background: #d4f6d4;
            color: #0f6937;
        }
        
        .status-progress {
            background: #cff4fc;
            color: #0c5460;
        }
        
        .status-not-started {
            background: #f8f9fa;
            color: #6c757d;
            border: 1px solid #e9ecef;
        }
        
        .status-at-risk {
            background: #fff3cd;
            color: #664d03;
        }
        
        .status-off-track {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-on-track {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        /* Action Buttons */
        .action-btn {
            padding: 4px 8px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-right: 4px;
            transition: all 0.2s;
        }
        
        .action-btn-edit {
            background: #e3f2fd;
            color: #1976d2;
        }
        
        .action-btn-delete {
            background: #ffebee;
            color: #d32f2f;
        }
        
        .action-btn:hover {
            opacity: 0.8;
            transform: translateY(-1px);
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        
        .modal-dialog {
            background: white;
            margin: 50px auto;
            border-radius: 8px;
            max-width: 600px;
            max-height: calc(100vh - 100px);
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0,0,0,0.25);
        }
        
        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-title {
            font-size: 18px;
            font-weight: 600;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #6c757d;
        }
        
        .modal-body {
            padding: 24px;
            max-height: 60vh;
            overflow-y: auto;
        }
        
        .modal-footer {
            padding: 16px 24px;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }
        
        /* Form Styles */
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            color: #333;
        }
        
        .form-control {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
        }
        
        /* Loading States */
        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s;
            }
            
            .sidebar.open {
                transform: translateX(0);
            }
            
            .main-content {
                margin-left: 0;
            }
            
            .filter-bar {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Sidebar Navigation -->
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">
                    � Product Roadmapping
                </div>
                <div class="sidebar-subtitle">Airtable Dashboard</div>
            </div>
            
            <nav class="sidebar-nav">
                <div class="nav-section">
                    <div class="nav-section-title">Getting Started</div>
                    <div class="nav-item" onclick="showDashboard()">
                        <span class="nav-icon">📊</span>
                        Dashboard
                    </div>
                </div>
                
                <div class="nav-section">
                    <div class="nav-section-title">Tables</div>
                    <div class="nav-item active" onclick="showAllTables()">
                        <span class="nav-icon">📋</span>
                        All Tables
                    </div>
                    <div id="table-nav-items">
                        <!-- Dynamic table items will be inserted here -->
                    </div>
                </div>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Top Header -->
            <div class="top-header">
                <div class="header-top">
                    <div class="breadcrumb">
                        <span>Airtable</span>
                        <span>></span>
                        <span id="current-breadcrumb">All Tables</span>
                    </div>
                    <div class="connection-status {{ 'connected' if connected else 'disconnected' }}">
                        {{ '✅ Connected' if connected else '❌ Disconnected' }}
                    </div>
                </div>
            </div>

            {% if connected %}
            <!-- Content Header -->
            <div class="content-header">
                <div class="content-title-row">
                    <h1 class="content-title" id="page-title">All Tables</h1>
                    <div class="header-actions">
                        <button class="btn" onclick="refreshData()">
                            🔄 Refresh
                        </button>
                        <button class="btn btn-success" onclick="showAddForm()" id="add-btn" style="display: none;">
                            ➕ Add Record
                        </button>
                    </div>
                </div>
                
                <div class="filter-bar" id="filter-bar" style="display: none;">
                    <div class="filter-group">
                        <label>Status</label>
                        <select class="filter-select" id="status-filter">
                            <option value="">All Status</option>
                            <option value="complete">Complete</option>
                            <option value="in-progress">In Progress</option>
                            <option value="not-started">Not Started</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Sort</label>
                        <select class="filter-select" id="sort-filter">
                            <option value="name">Name</option>
                            <option value="date">Date</option>
                            <option value="status">Status</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Content Body -->
            <div class="content-body">
                <div class="table-container">
                    <div id="main-content" class="loading">
                        <div class="spinner"></div>
                        Loading dashboard...
                    </div>
                </div>
            </div>
            {% else %}
            <div class="content-header">
                <div class="content-title-row">
                    <h1 class="content-title">Connection Required</h1>
                </div>
            </div>
            <div class="content-body" style="padding: 40px;">
                <div style="text-align: center; color: #6c757d;">
                    <h2>🔐 Airtable Not Connected</h2>
                    <p>Please configure your Airtable API token:</p>
                    <pre style="background: #f8f9fa; padding: 16px; border-radius: 4px; margin: 20px 0;">$env:AIRTABLE_API_TOKEN="your_token_here"</pre>
                    <p>Then restart the server.</p>
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <!-- Modal for editing records -->
    <div id="edit-modal" class="modal">
        <div class="modal-dialog">
            <div class="modal-header">
                <h3 class="modal-title" id="modal-title">Edit Record</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <form id="edit-form">
                <div class="modal-body">
                    <div id="form-fields"></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-success">Save Changes</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let currentTable = null;
        let tables = [];
        let records = [];
        let filteredRecords = [];

        // Initialize dashboard
        async function init() {
            console.log('🚀 Initializing Product Roadmap Dashboard...');
            await loadTables();
            showAllTables();
        }

        // Load all tables
        async function loadTables() {
            try {
                console.log('📋 Loading tables...');
                const response = await fetch('/api/tables');
                const data = await response.json();
                
                if (data.tables) {
                    tables = data.tables;
                    displayTablesInSidebar(tables);
                } else {
                    showError('Failed to load tables');
                }
            } catch (error) {
                console.error('Error loading tables:', error);
                showError('Network error loading tables');
            }
        }

        // Display tables in sidebar navigation
        function displayTablesInSidebar(tables) {
            const navItems = document.getElementById('table-nav-items');
            if (tables.length === 0) {
                navItems.innerHTML = '<div style="padding: 12px 20px; color: rgba(255,255,255,0.7);">No tables found</div>';
                return;
            }
            
            navItems.innerHTML = tables.map(table => 
                `<div class="nav-item" onclick="loadTable('${table}')" id="nav-${table}">
                    <span class="nav-icon">�</span>
                    ${table}
                </div>`
            ).join('');
        }

        // Show dashboard overview
        function showDashboard() {
            document.getElementById('page-title').textContent = 'Dashboard';
            document.getElementById('current-breadcrumb').textContent = 'Dashboard';
            document.getElementById('filter-bar').style.display = 'none';
            document.getElementById('add-btn').style.display = 'none';
            
            // Update active nav item
            updateActiveNav('dashboard');
            
            // Show dashboard content
            const content = document.getElementById('main-content');
            content.innerHTML = `
                <div style="padding: 40px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 32px;">
                        <div style="background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="margin-bottom: 16px; color: #20b2aa;">📊 Total Tables</h3>
                            <div style="font-size: 2.5em; font-weight: bold; color: #333;">${tables.length}</div>
                        </div>
                        <div style="background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="margin-bottom: 16px; color: #20b2aa;">📋 Active Projects</h3>
                            <div style="font-size: 2.5em; font-weight: bold; color: #333;">-</div>
                        </div>
                    </div>
                    
                    <div style="background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3 style="margin-bottom: 16px;">Available Tables</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
                            ${tables.map(table => `
                                <div style="border: 1px solid #e9ecef; border-radius: 6px; padding: 16px; cursor: pointer; transition: all 0.2s;" 
                                     onclick="loadTable('${table}')" 
                                     onmouseover="this.style.background='#f8f9fa'"
                                     onmouseout="this.style.background='white'">
                                    <div style="font-weight: 500; margin-bottom: 8px;">📊 ${table}</div>
                                    <div style="color: #6c757d; font-size: 14px;">Click to view records</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }

        // Show all tables view
        function showAllTables() {
            showDashboard(); // For now, show dashboard instead of a separate all tables view
        }

        // Load records for specific table
        async function loadTable(tableName) {
            currentTable = tableName;
            console.log(`📊 Loading table: ${tableName}`);
            
            // Update UI
            document.getElementById('page-title').textContent = tableName;
            document.getElementById('current-breadcrumb').textContent = tableName;
            document.getElementById('filter-bar').style.display = 'flex';
            document.getElementById('add-btn').style.display = 'block';
            
            // Update active nav item
            updateActiveNav(tableName);
            
            // Show loading
            document.getElementById('main-content').innerHTML = 
                '<div class="loading"><div class="spinner"></div>Loading records...</div>';
            
            try {
                const response = await fetch(`/api/table/${encodeURIComponent(tableName)}/records`);
                const data = await response.json();
                
                if (data.records) {
                    records = data.records;
                    filteredRecords = [...records];
                    displayRecordsTable(filteredRecords, tableName);
                } else {
                    showError(`Failed to load records: ${data.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error loading records:', error);
                showError('Network error loading records');
            }
        }

        // Update active navigation item
        function updateActiveNav(itemName) {
            // Remove active from all nav items
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            
            // Add active to current item
            if (itemName === 'dashboard') {
                document.querySelector('.nav-item[onclick="showDashboard()"]').classList.add('active');
            } else {
                const navItem = document.getElementById(`nav-${itemName}`);
                if (navItem) navItem.classList.add('active');
            }
        }

        // Display records in professional table format
        function displayRecordsTable(records, tableName) {
            const content = document.getElementById('main-content');
            
            if (records.length === 0) {
                content.innerHTML = `
                    <div style="padding: 60px; text-align: center; color: #6c757d;">
                        <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
                        <h3>No records found</h3>
                        <p>There are no records in ${tableName} yet.</p>
                        <button class="btn btn-success" onclick="showAddForm()" style="margin-top: 20px;">
                            ➕ Add First Record
                        </button>
                    </div>
                `;
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
                <table class="data-table">
                    <thead>
                        <tr>
                            <th style="width: 120px;">Actions</th>
                            <th style="width: 100px;">ID</th>
                            ${fieldNames.map(field => `<th>${field}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            records.forEach((record, index) => {
                html += `<tr>
                    <td>
                        <button class="action-btn action-btn-edit" onclick="editRecord('${record.id}')" title="Edit">
                            ✏️
                        </button>
                        <button class="action-btn action-btn-delete" onclick="deleteRecord('${record.id}')" title="Delete">
                            🗑️
                        </button>
                    </td>
                    <td>
                        <div style="font-family: monospace; font-size: 11px; color: #6c757d;">
                            ${record.id.substring(0, 8)}...
                        </div>
                    </td>
                    ${fieldNames.map(field => {
                        const value = record.fields && record.fields[field];
                        let displayValue = '';
                        let cellClass = '';
                        
                        if (value !== null && value !== undefined) {
                            if (typeof value === 'object') {
                                displayValue = JSON.stringify(value);
                            } else {
                                displayValue = String(value);
                            }
                        }
                        
                        // Check if this looks like a status field
                        if (field.toLowerCase().includes('status') || field.toLowerCase().includes('state')) {
                            const status = displayValue.toLowerCase().replace(/\\s+/g, '-');
                            cellClass = getStatusClass(status);
                            displayValue = `<span class="status-badge ${cellClass}">${displayValue}</span>`;
                        } else if (field.toLowerCase().includes('date')) {
                            // Format dates nicely
                            try {
                                const date = new Date(displayValue);
                                if (!isNaN(date.getTime())) {
                                    displayValue = date.toLocaleDateString();
                                }
                            } catch (e) {
                                // Keep original value if date parsing fails
                            }
                        }
                        
                        return `<td>${displayValue}</td>`;
                    }).join('')}
                </tr>`;
            });
            
            html += `
                    </tbody>
                </table>
                <div style="padding: 16px; background: #f8f9fa; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px;">
                    Showing ${records.length} record${records.length !== 1 ? 's' : ''} in ${tableName}
                </div>
            `;
            
            content.innerHTML = html;
        }

        // Get appropriate status class for badge styling
        function getStatusClass(status) {
            const statusMap = {
                'complete': 'status-complete',
                'completed': 'status-complete',
                'done': 'status-complete',
                'finished': 'status-complete',
                'in-progress': 'status-progress',
                'in progress': 'status-progress',
                'active': 'status-progress',
                'working': 'status-progress',
                'not-started': 'status-not-started',
                'not started': 'status-not-started',
                'pending': 'status-not-started',
                'todo': 'status-not-started',
                'at-risk': 'status-at-risk',
                'at risk': 'status-at-risk',
                'warning': 'status-at-risk',
                'off-track': 'status-off-track',
                'off track': 'status-off-track',
                'blocked': 'status-off-track',
                'on-track': 'status-on-track',
                'on track': 'status-on-track',
                'healthy': 'status-on-track'
            };
            
            return statusMap[status] || 'status-not-started';
        }

        // Refresh data
        function refreshData() {
            if (currentTable) {
                loadTable(currentTable);
            } else {
                loadTables();
                showDashboard();
            }
        }

        // Show error message
        function showError(message) {
            document.getElementById('main-content').innerHTML = `
                <div style="padding: 60px; text-align: center; color: #dc3545;">
                    <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                    <h3>Error</h3>
                    <p>${message}</p>
                    <button class="btn btn-primary" onclick="refreshData()" style="margin-top: 20px;">
                        🔄 Try Again
                    </button>
                </div>
            `;
        }

        // Edit record
        function editRecord(recordId) {
            const record = records.find(r => r.id === recordId);
            if (!record) return;
            
            document.getElementById('modal-title').textContent = `Edit Record`;
            
            let formHTML = `<input type="hidden" id="record-id" value="${recordId}">`;
            
            if (record.fields) {
                Object.entries(record.fields).forEach(([field, value]) => {
                    let inputValue = value;
                    if (typeof value === 'object') {
                        inputValue = JSON.stringify(value);
                    }
                    
                    // Determine input type based on field name or value
                    let inputType = 'text';
                    let inputElement = '';
                    
                    if (field.toLowerCase().includes('date')) {
                        inputType = 'date';
                        try {
                            const date = new Date(inputValue);
                            if (!isNaN(date.getTime())) {
                                inputValue = date.toISOString().split('T')[0];
                            }
                        } catch (e) {}
                    } else if (field.toLowerCase().includes('status') || field.toLowerCase().includes('state')) {
                        // Create select dropdown for status fields
                        inputElement = `
                            <select class="form-control" id="field-${field}" name="${field}">
                                <option value="">Select ${field}</option>
                                <option value="Not Started" ${inputValue === 'Not Started' ? 'selected' : ''}>Not Started</option>
                                <option value="In Progress" ${inputValue === 'In Progress' ? 'selected' : ''}>In Progress</option>
                                <option value="Complete" ${inputValue === 'Complete' ? 'selected' : ''}>Complete</option>
                                <option value="On Track" ${inputValue === 'On Track' ? 'selected' : ''}>On Track</option>
                                <option value="At Risk" ${inputValue === 'At Risk' ? 'selected' : ''}>At Risk</option>
                                <option value="Off Track" ${inputValue === 'Off Track' ? 'selected' : ''}>Off Track</option>
                            </select>
                        `;
                    } else if (field.toLowerCase().includes('description') || field.toLowerCase().includes('notes')) {
                        inputElement = `
                            <textarea class="form-control" id="field-${field}" name="${field}" 
                                      rows="3" placeholder="Enter ${field}">${inputValue || ''}</textarea>
                        `;
                    }
                    
                    if (!inputElement) {
                        inputElement = `
                            <input type="${inputType}" class="form-control" id="field-${field}" name="${field}" 
                                   value="${inputValue || ''}" placeholder="Enter ${field}">
                        `;
                    }
                    
                    formHTML += `
                        <div class="form-group">
                            <label class="form-label" for="field-${field}">${field}</label>
                            ${inputElement}
                        </div>
                    `;
                });
            }
            
            document.getElementById('form-fields').innerHTML = formHTML;
            document.getElementById('edit-modal').style.display = 'block';
        }

        // Show add form
        function showAddForm() {
            if (!currentTable) return;
            
            document.getElementById('modal-title').textContent = `Add New Record to ${currentTable}`;
            
            let formHTML = '<input type="hidden" id="record-id" value="">';
            
            // Get fields from first record or create default fields
            if (records.length > 0 && records[0].fields) {
                Object.keys(records[0].fields).forEach(field => {
                    let inputElement = '';
                    
                    if (field.toLowerCase().includes('date')) {
                        inputElement = `
                            <input type="date" class="form-control" id="field-${field}" name="${field}">
                        `;
                    } else if (field.toLowerCase().includes('status') || field.toLowerCase().includes('state')) {
                        inputElement = `
                            <select class="form-control" id="field-${field}" name="${field}">
                                <option value="">Select ${field}</option>
                                <option value="Not Started">Not Started</option>
                                <option value="In Progress">In Progress</option>
                                <option value="Complete">Complete</option>
                                <option value="On Track">On Track</option>
                                <option value="At Risk">At Risk</option>
                                <option value="Off Track">Off Track</option>
                            </select>
                        `;
                    } else if (field.toLowerCase().includes('description') || field.toLowerCase().includes('notes')) {
                        inputElement = `
                            <textarea class="form-control" id="field-${field}" name="${field}" 
                                      rows="3" placeholder="Enter ${field}"></textarea>
                        `;
                    } else {
                        inputElement = `
                            <input type="text" class="form-control" id="field-${field}" name="${field}" 
                                   placeholder="Enter ${field}">
                        `;
                    }
                    
                    formHTML += `
                        <div class="form-group">
                            <label class="form-label" for="field-${field}">${field}</label>
                            ${inputElement}
                        </div>
                    `;
                });
            } else {
                // Default form for empty tables
                formHTML += `
                    <div class="form-group">
                        <label class="form-label" for="field-name">Name</label>
                        <input type="text" class="form-control" id="field-name" name="Name" placeholder="Enter name">
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="field-status">Status</label>
                        <select class="form-control" id="field-status" name="Status">
                            <option value="">Select Status</option>
                            <option value="Not Started">Not Started</option>
                            <option value="In Progress">In Progress</option>
                            <option value="Complete">Complete</option>
                        </select>
                    </div>
                `;
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
            
            // Show loading state
            const submitBtn = e.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Saving...';
            submitBtn.disabled = true;
            
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
                    showNotification(recordId ? 'Record updated successfully!' : 'Record created successfully!', 'success');
                } else {
                    showNotification('Error: ' + (result.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                console.error('Error saving record:', error);
                showNotification('Network error saving record', 'error');
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });

        // Delete record with confirmation
        async function deleteRecord(recordId) {
            if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) return;
            
            try {
                const response = await fetch(`/api/table/${currentTable}/record/${recordId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    loadTable(currentTable); // Reload table
                    showNotification('Record deleted successfully!', 'success');
                } else {
                    showNotification('Error deleting record: ' + (result.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                console.error('Error deleting record:', error);
                showNotification('Network error deleting record', 'error');
            }
        }

        // Show notification (simple implementation)
        function showNotification(message, type = 'info') {
            // For now, use alert. In a real app, you'd use a toast notification system
            if (type === 'success') {
                alert('✅ ' + message);
            } else if (type === 'error') {
                alert('❌ ' + message);
            } else {
                alert('ℹ️ ' + message);
            }
        }

        // Filter and sort functionality
        document.getElementById('status-filter').addEventListener('change', function() {
            applyFilters();
        });

        document.getElementById('sort-filter').addEventListener('change', function() {
            applyFilters();
        });

        function applyFilters() {
            if (!records.length) return;

            let filtered = [...records];
            
            // Apply status filter
            const statusFilter = document.getElementById('status-filter').value;
            if (statusFilter) {
                filtered = filtered.filter(record => {
                    const fields = record.fields || {};
                    for (const [key, value] of Object.entries(fields)) {
                        if (key.toLowerCase().includes('status') && 
                            String(value).toLowerCase().includes(statusFilter.toLowerCase())) {
                            return true;
                        }
                    }
                    return false;
                });
            }
            
            // Apply sorting
            const sortBy = document.getElementById('sort-filter').value;
            if (sortBy === 'name') {
                filtered.sort((a, b) => {
                    const aName = Object.values(a.fields || {})[0] || '';
                    const bName = Object.values(b.fields || {})[0] || '';
                    return String(aName).localeCompare(String(bName));
                });
            } else if (sortBy === 'date') {
                filtered.sort((a, b) => {
                    // Find date fields and sort by them
                    const aDate = findDateValue(a.fields || {});
                    const bDate = findDateValue(b.fields || {});
                    return new Date(bDate) - new Date(aDate);
                });
            }
            
            filteredRecords = filtered;
            displayRecordsTable(filteredRecords, currentTable);
        }

        function findDateValue(fields) {
            for (const [key, value] of Object.entries(fields)) {
                if (key.toLowerCase().includes('date') && value) {
                    return value;
                }
            }
            return new Date().toISOString();
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
    return render_template_string(HOME_TEMPLATE, 
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