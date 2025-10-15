#!/usr/bin/env python3
"""
Production Airtable Dashboard for Render Deployment
"""

import os
import ssl
import urllib3
import requests
from flask import Flask, render_template_string, request, jsonify
from pyairtable import Api
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration - Use environment variables
AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
    print("❌ ERROR: Missing environment variables!")
    print(f"AIRTABLE_TOKEN: {'✅ Set' if AIRTABLE_TOKEN else '❌ Missing'}")
    print(f"AIRTABLE_BASE_ID: {'✅ Set' if AIRTABLE_BASE_ID else '❌ Missing'}")
    print("Please add these in your Render Environment settings.")
    raise ValueError("Missing required environment variables: AIRTABLE_TOKEN and AIRTABLE_BASE_ID")

# Initialize Airtable API
api = Api(AIRTABLE_TOKEN)
base = api.base(AIRTABLE_BASE_ID)

# Dashboard HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HSE Statistics Report - Trojan Construction Group</title>
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --container-bg: white;
            --text-color: #2c3e50;
            --section-bg: #f8f9fa;
            --border-color: #e9ecef;
            --input-bg: white;
        }
        [data-theme="dark"] {
            --bg-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            --container-bg: #34495e;
            --text-color: #ecf0f1;
            --section-bg: #2c3e50;
            --border-color: #34495e;
            --input-bg: #2c3e50;
        }
        
        /* Dark theme for Airtable-style interface */
        [data-theme="dark"] .tab-navigation {
            background: #2c3e50;
            border-bottom-color: #34495e;
        }
        
        [data-theme="dark"] .tab-item {
            color: #bdc3c7;
        }
        
        [data-theme="dark"] .tab-item:hover {
            color: #ecf0f1;
            background: #34495e;
        }
        
        [data-theme="dark"] .tab-item.active {
            color: #3498db;
            background: #2c3e50;
            border-bottom-color: #3498db;
        }
        
        [data-theme="dark"] .grid-toolbar {
            background: #2c3e50;
            border-bottom-color: #34495e;
            color: #ecf0f1;
        }
        
        [data-theme="dark"] .toolbar-btn {
            background: #34495e;
            border-color: #2c3e50;
            color: #bdc3c7;
        }
        
        [data-theme="dark"] .toolbar-btn:hover {
            background: #2c3e50;
            border-color: #34495e;
        }
        
        [data-theme="dark"] .airtable-grid {
            background: #2c3e50;
        }
        
        [data-theme="dark"] .airtable-grid th {
            background: #34495e;
            border-color: #2c3e50;
            color: #ecf0f1;
        }
        
        [data-theme="dark"] .airtable-grid td {
            border-color: #2c3e50;
            color: #bdc3c7;
        }
        
        [data-theme="dark"] .airtable-grid td:first-child {
            background: #34495e;
        }
        
        [data-theme="dark"] .airtable-grid tbody tr:hover {
            background: #34495e;
        }
        
        [data-theme="dark"] .container {
            background: #2c3e50;
        }
        
        [data-theme="dark"] .top-nav {
            background: #2c3e50;
            border-bottom-color: #34495e;
        }
        
        [data-theme="dark"] .workspace-name {
            color: #ecf0f1;
        }
        
        [data-theme="dark"] .nav-item {
            color: #bdc3c7;
        }
        
        [data-theme="dark"] .nav-item:hover {
            color: #ecf0f1;
        }
        
        [data-theme="dark"] .nav-btn:hover {
            background: #34495e;
        }
        
        [data-theme="dark"] .table-footer {
            background: #2c3e50;
            border-top-color: #34495e;
        }
        
        [data-theme="dark"] .add-record-btn {
            color: #bdc3c7;
        }
        
        [data-theme="dark"] .add-record-btn:hover {
            background: #34495e;
            color: #ecf0f1;
        }
        
        [data-theme="dark"] .add-icon {
            background: #34495e;
        }
        
        [data-theme="dark"] .content {
            background: #2c3e50;
        }
        
        [data-theme="dark"] .add-field-btn {
            background: #34495e;
            border-color: #2c3e50;
            color: #bdc3c7;
        }
        
        [data-theme="dark"] .add-field-btn:hover {
            background: #2c3e50;
            border-color: #34495e;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: var(--bg-gradient);
            min-height: 100vh;
            transition: all 0.3s ease;
        }
        .container {
            max-width: 100%;
            margin: 0;
            background: white;
            color: var(--text-color);
            min-height: 100vh;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        /* Top navigation */
        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            height: 56px;
            background: white;
            border-bottom: 1px solid #e6e6e6;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .nav-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .workspace-icon {
            width: 32px;
            height: 32px;
            background: #2d7ff9;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
        }
        
        .workspace-info {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .workspace-name {
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }
        
        .workspace-dropdown {
            color: #999;
            cursor: pointer;
        }
        
        .main-nav {
            display: flex;
            gap: 32px;
        }
        
        .nav-item {
            text-decoration: none;
            color: #666;
            font-size: 14px;
            font-weight: 500;
            padding: 8px 0;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
        }
        
        .nav-item:hover {
            color: #333;
        }
        
        .nav-item.active {
            color: #2d7ff9;
            border-bottom-color: #2d7ff9;
        }
        
        .nav-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .nav-btn {
            background: none;
            border: none;
            color: #666;
            cursor: pointer;
            padding: 6px;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        
        .nav-btn:hover {
            background: #f5f5f5;
        }
        
        .trial-info {
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .content {
            padding: 0;
            background: #fafafa;
            min-height: calc(100vh - 56px);
        }
        .form-section {
            margin-bottom: 40px;
            padding: 30px;
            background: var(--section-bg);
            border-radius: 10px;
            border-left: 5px solid #007bff;
            transition: all 0.3s ease;
        }
        .form-section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #34495e;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-size: 16px;
            background: var(--input-bg);
            color: var(--text-color);
            transition: all 0.3s ease;
            box-sizing: border-box;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.25);
        }
        .btn {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,123,255,0.3);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        /* Airtable-style tab navigation */
        .tab-navigation {
            display: flex;
            border-bottom: 1px solid #e6e6e6;
            background: #fafafa;
            padding: 0 16px;
            overflow-x: auto;
            white-space: nowrap;
        }
        .tab-item {
            display: inline-flex;
            align-items: center;
            padding: 12px 16px;
            text-decoration: none;
            color: #666;
            font-size: 14px;
            font-weight: 500;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            cursor: pointer;
            user-select: none;
        }
        .tab-item:hover {
            color: #333;
            background: #f0f0f0;
        }
        .tab-item.active {
            color: #2d7ff9;
            border-bottom-color: #2d7ff9;
            background: white;
        }
        .tab-item .tab-icon {
            margin-right: 6px;
            font-size: 12px;
        }
        
        /* Main content area */
        .main-content {
            background: white;
            min-height: 600px;
        }
        
        /* Grid toolbar */
        .grid-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            border-bottom: 1px solid #e6e6e6;
            background: #fafafa;
        }
        .view-controls {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 500;
            color: #333;
        }
        .grid-icon {
            font-size: 16px;
            color: #666;
        }
        .dropdown-arrow {
            color: #999;
            margin-left: 4px;
        }
        .toolbar-actions {
            display: flex;
            gap: 8px;
        }
        .toolbar-btn {
            background: white;
            border: 1px solid #ddd;
            color: #666;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .toolbar-btn:hover {
            background: #f5f5f5;
            border-color: #ccc;
        }
        
        /* Airtable-style grid table */
        .airtable-grid {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 14px;
            background: white;
        }
        .airtable-grid th {
            background: #f7f7f7;
            border-right: 1px solid #e6e6e6;
            border-bottom: 1px solid #e6e6e6;
            padding: 12px 8px;
            text-align: left;
            font-weight: 500;
            color: #333;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .airtable-grid th:first-child {
            border-left: 1px solid #e6e6e6;
            width: 40px;
            text-align: center;
        }
        .airtable-grid td {
            border-right: 1px solid #e6e6e6;
            border-bottom: 1px solid #e6e6e6;
            padding: 12px 8px;
            vertical-align: top;
            max-width: 200px;
            word-wrap: break-word;
        }
        .airtable-grid td:first-child {
            border-left: 1px solid #e6e6e6;
            text-align: center;
            font-weight: 500;
            color: #666;
            background: #fafafa;
        }
        .airtable-grid tbody tr:hover {
            background: #f8f9ff;
        }
        .record-number {
            color: #999;
            font-size: 12px;
        }
        .cell-content {
            word-break: break-word;
            line-height: 1.4;
        }
        
        /* Table footer */
        .table-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: white;
            border-top: 1px solid #e6e6e6;
        }
        
        .add-record-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            background: none;
            border: none;
            color: #666;
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.2s ease;
        }
        
        .add-record-btn:hover {
            background: #f5f5f5;
            color: #333;
        }
        
        .add-icon {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            background: #e6e6e6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: bold;
        }
        
        .record-count-info {
            font-size: 13px;
            color: #999;
        }
        
        /* Add field button */
        .add-field-btn {
            width: 24px;
            height: 24px;
            border-radius: 4px;
            background: #f5f5f5;
            border: 1px solid #e6e6e6;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 14px;
            color: #666;
            transition: all 0.2s ease;
        }
        
        .add-field-btn:hover {
            background: #eeeeee;
            border-color: #ddd;
        }
            font-weight: 600;
            font-size: 14px;
            white-space: nowrap;
            min-width: 120px;
            text-align: center;
            border: 2px solid transparent;
        }
        .table-btn:hover, .table-btn.active {
            background: #007bff;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,123,255,0.3);
        }
        .theme-btn, .about-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
            padding: 10px 15px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
            backdrop-filter: blur(10px);
        }
        .theme-btn:hover, .about-btn:hover {
            background: rgba(255,255,255,0.3);
            border-color: rgba(255,255,255,0.5);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .about-btn.active {
            background: rgba(255,255,255,0.4);
            border-color: rgba(255,255,255,0.6);
        }
        .records-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .record-card {
            background: var(--container-bg);
            border: 2px solid var(--border-color);
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .record-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .record-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }
        .record-id {
            font-family: monospace;
            background: #007bff;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        .record-time {
            color: #6c757d;
            font-size: 12px;
        }
        .field-display {
            margin-bottom: 8px;
            padding: 4px 0;
            font-size: 14px;
        }
        .field-display strong {
            color: var(--text-color);
            margin-right: 8px;
        }
        .records-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding: 15px 20px;
            background: var(--section-bg);
            border-radius: 8px;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .records-count {
            color: #28a745;
            font-size: 16px;
        }
        .refresh-btn {
            background: #17a2b8;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        .refresh-btn:hover {
            background: #138496;
            transform: scale(1.05);
        }
        .record-footer {
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #6c757d;
        }
        .field-value {
            word-wrap: break-word;
            color: var(--text-color);
        }
        .no-fields {
            color: #6c757d;
            font-style: italic;
            text-align: center;
            padding: 10px;
        }
        .no-records, .error-records {
            text-align: center;
            padding: 40px 20px;
            background: var(--section-bg);
            border-radius: 10px;
            color: var(--text-color);
        }
        .no-records-icon, .error-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .no-records h3, .error-records h3 {
            margin: 10px 0;
            color: var(--text-color);
        }
        .loading-records {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-color);
        }
        .loading-records .spinner {
            margin: 0 auto 15px auto;
        }
        /* Definitions table special styling */
        .definition-card {
            background: var(--container-bg);
            border: 2px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 15px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }

        .definition-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .definition-term {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #007bff;
        }

        .term-number {
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            flex-shrink: 0;
        }

        .term-title {
            margin: 0;
            color: var(--text-color);
            font-size: 18px;
            font-weight: 600;
        }

        .definition-content {
            padding-left: 42px;
        }

        .definition-text {
            margin: 0;
            color: var(--text-color);
            line-height: 1.6;
            font-size: 16px;
            opacity: 0.9;
        }

        @media (max-width: 768px) {
            .content { padding: 10px; }
            .form-section { padding: 15px; }
            .header h1 { font-size: 2em; }
            .records-grid { grid-template-columns: 1fr; }
            .definition-content { padding-left: 20px; }
            .term-title { font-size: 16px; }
            .tab-navigation { padding: 0 8px; }
            .tab-item { padding: 10px 12px; font-size: 13px; }
            .grid-toolbar { padding: 8px 12px; flex-direction: column; gap: 10px; }
            .toolbar-actions { justify-content: center; }
            .airtable-grid { font-size: 13px; }
            .airtable-grid th, .airtable-grid td { padding: 8px 4px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Airtable-style top navigation -->
        <div class="top-nav">
            <div class="nav-left">
                <div class="workspace-icon">🏗️</div>
                <div class="workspace-info">
                    <span class="workspace-name">HSE Statistics</span>
                    <span class="workspace-dropdown">⌄</span>
                </div>
            </div>
            <div class="nav-center">
                <nav class="main-nav">
                    <a href="#" class="nav-item active">Data</a>
                    <a href="#" class="nav-item">Automations</a>
                    <a href="#" class="nav-item">Interfaces</a>
                    <a href="#" class="nav-item">Forms</a>
                </nav>
            </div>
            <div class="nav-right">
                <button onclick="toggleTheme()" class="nav-btn" title="Toggle Theme">🌓</button>
                <button onclick="showAbout()" class="nav-btn" title="About">📚</button>
                <div class="trial-info">Trial: 13</div>
            </div>
        </div>
        <div class="content">
            <!-- Airtable-style tab navigation -->
            <div class="tab-navigation" id="tabNavigation">
                <!-- Table tabs will be populated by JavaScript -->
            </div>
            
            <!-- Main content area -->
            <div class="main-content">
                <!-- Grid view container -->
                <div id="gridViewContainer" style="display: none;">
                    <div class="grid-toolbar">
                        <div class="view-controls">
                            <span class="grid-icon">⚏</span>
                            <span class="view-name">Grid view</span>
                            <span class="dropdown-arrow">⌄</span>
                        </div>
                        <div class="toolbar-actions">
                            <button class="toolbar-btn" title="Hide fields">👁️ Hide fields</button>
                            <button class="toolbar-btn" title="Filter">🔍 Filter</button>
                            <button class="toolbar-btn" title="Group">📊 Group</button>
                            <button class="toolbar-btn" title="Sort">↕️ Sort</button>
                            <button class="toolbar-btn refresh-btn" onclick="refreshCurrentTable()" title="Refresh">🔄</button>
                        </div>
                    </div>
                    <div id="gridTable">
                        <!-- Grid table will be populated here -->
                    </div>
                </div>
                
                <!-- Form container (hidden by default) -->
                <div id="formContainer" style="display: none;">
                    <!-- Forms will be populated by JavaScript -->
                </div>
            </div>
            
            <div id="aboutContainer" style="display: none;">
                <div class="form-section">
                    <h2>📚 About HSE Statistics Report</h2>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                        <h3>🏗️ Trojan Construction Group HSE Management</h3>
                        <p>A comprehensive Health, Safety & Environment statistics reporting system built with Python API client library for Airtable, providing wrappers around Airtable's REST API to simplify CRUD operations, filtering and pagination.</p>
                        
                        <h3>📜 License</h3>
                        <p>MIT license, permissive for both open and proprietary use.</p>
                        
                        <h3>✨ HSE Features</h3>
                        <ul>
                            <li>🏗️ Health, Safety & Environment data management</li>
                            <li>📊 Training & Competency Register tracking</li>
                            <li>📝 Dynamic form generation for HSE records</li>
                            <li>🔍 Smart field validation for safety compliance</li>
                            <li>💾 Streamlined incident and training reporting</li>
                            <li>🎯 Specialized training table optimizations</li>
                            <li>🔒 Secure data handling for sensitive HSE information</li>
                        </ul>
                        
                        <h3>🛠️ Built With</h3>
                        <ul>
                            <li>Python Flask - Web framework</li>
                            <li>pyairtable - Airtable API client</li>
                            <li>Gunicorn - WSGI HTTP Server</li>
                            <li>Modern HTML5/CSS3/JavaScript</li>
                        </ul>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #e3f2fd; border-radius: 6px;">
                            <strong>🌐 Repository:</strong> <a href="https://github.com/s6ft256/airtablepy3" target="_blank" style="color: #1976d2; text-decoration: none;">github.com/s6ft256/airtablepy3</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        </div>
    </div>

    <script>
        let currentTable = null;
        let currentTableName = null;
        let tableSchemas = {};

        // Load tables and theme on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadTheme();
            loadTables();
        });

        async function loadTables() {
            showLoading(true);
            try {
                console.log('Fetching tables from /api/tables...');
                const response = await fetch('/api/tables');
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('Tables data received:', data);
                
                if (data.success) {
                    tableSchemas = data.schemas;
                    displayTableButtons(data.tables);
                    if (data.tables.length > 0) {
                        loadTable(data.tables[0].id, data.tables[0].name);
                    }
                } else {
                    console.error('API returned error:', data.error);
                    showMessage(data.error || 'Failed to load tables', 'error');
                }
            } catch (error) {
                console.error('Error loading tables:', error);
                const errorMessage = error.message || 'Unknown error occurred';
                showMessage(`Failed to connect to Airtable: ${errorMessage}`, 'error');
                
                // Show additional help for SSL errors
                if (errorMessage.includes('SSL') || errorMessage.includes('certificate')) {
                    showMessage('SSL Certificate issue detected. Please check environment variables.', 'error');
                }
            } finally {
                showLoading(false);
            }
        }

        function displayTableButtons(tables) {
            const tabNavigation = document.getElementById('tabNavigation');
            
            // Define the preferred order based on your Airtable structure
            const tableOrder = [
                'Definitions',
                'Project Information', 
                'MAIN REGISTER',
                'Incident Tracker',
                'Injury Details',
                'Induction Register',
                'Training & competency Register',
                'Observation Register',
                'NCR Tracker'
            ];
            
            // Sort tables according to preferred order
            const sortedTables = tables.sort((a, b) => {
                const aIndex = tableOrder.findIndex(name => 
                    a.name.toLowerCase().includes(name.toLowerCase()) || 
                    name.toLowerCase().includes(a.name.toLowerCase())
                );
                const bIndex = tableOrder.findIndex(name => 
                    b.name.toLowerCase().includes(name.toLowerCase()) || 
                    name.toLowerCase().includes(b.name.toLowerCase())
                );
                
                if (aIndex === -1 && bIndex === -1) return a.name.localeCompare(b.name);
                if (aIndex === -1) return 1;
                if (bIndex === -1) return -1;
                return aIndex - bIndex;
            });
            
            const tabItems = sortedTables.map((table, index) => {
                const escapedId = table.id.replace(/'/g, "\\'");
                const escapedName = table.name.replace(/'/g, "\\'");
                
                // Determine display name (numbered like in Airtable)
                let displayName = table.name;
                let tabNumber = '';
                
                // Add numbering based on position
                if (index === 0) tabNumber = '';
                else tabNumber = `${index + 1}.`;
                
                const activeClass = index === 0 ? 'active' : '';
                
                return `<div class="tab-item ${activeClass}" onclick="switchToTable('${escapedId}', '${escapedName}', this)">
                    ${tabNumber}${displayName}
                </div>`;
            }).join('');
            
            tabNavigation.innerHTML = tabItems;
            
            // Load the first table by default
            if (sortedTables.length > 0) {
                loadGridTable(sortedTables[0].id, sortedTables[0].name);
            }
        }

        function switchToTable(tableId, tableName, tabElement) {
            // Update active tab
            document.querySelectorAll('.tab-item').forEach(tab => tab.classList.remove('active'));
            tabElement.classList.add('active');
            
            // Load the grid table
            loadGridTable(tableId, tableName);
        }
        
        function refreshCurrentTable() {
            if (currentTable && currentTableName) {
                loadGridTable(currentTable, currentTableName);
            }
        }
        
        async function loadGridTable(tableId, tableName) {
            currentTable = tableId;
            currentTableName = tableName;
            
            // Show grid view, hide form view
            document.getElementById('gridViewContainer').style.display = 'block';
            document.getElementById('formContainer').style.display = 'none';
            
            // Load records and display in grid format
            try {
                const response = await fetch('/load_table_records', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        table_id: tableId,
                        table_name: tableName
                    })
                });
                
                const data = await response.json();
                console.log('Records data received:', data);
                
                if (data.success && data.records && data.records.length > 0) {
                    displayGridTable(data.records, tableName);
                } else {
                    document.getElementById('gridTable').innerHTML = `
                        <div style="text-align: center; padding: 40px; color: #666;">
                            <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
                            <h3>No records found</h3>
                            <p>This table appears to be empty or there was an error loading the data.</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading grid table:', error);
                document.getElementById('gridTable').innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #d32f2f;">
                        <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                        <h3>Error loading table</h3>
                        <p>There was an error loading the table data. Please try again.</p>
                    </div>
                `;
            }
        }
        
        function displayGridTable(records, tableName) {
            const gridContainer = document.getElementById('gridTable');
            
            if (!records || records.length === 0) {
                gridContainer.innerHTML = '<div style="padding: 20px; text-align: center;">No records found</div>';
                return;
            }
            
            // Get all field names from the records
            const allFields = new Set();
            records.forEach(record => {
                Object.keys(record.fields || {}).forEach(field => allFields.add(field));
            });
            const fieldNames = Array.from(allFields);
            
            // Special handling for Definitions table
            const isDefinitionsTable = fieldNames.includes('Term') && fieldNames.includes('Definitions');
            
            let tableHTML = '';
            
            if (isDefinitionsTable) {
                // Use Term and Definitions columns specifically
                tableHTML = `
                    <table class="airtable-grid">
                        <thead>
                            <tr>
                                <th></th>
                                <th>� Term</th>
                                <th>📝 Definitions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${records.map((record, index) => `
                                <tr>
                                    <td class="record-number">${index + 1}</td>
                                    <td><div class="cell-content">${record.fields.Term || ''}</div></td>
                                    <td><div class="cell-content">${record.fields.Definitions || ''}</div></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else if (tableName.toLowerCase().includes('project')) {
                // Special handling for Project Information table to match exact structure from screenshot
                const projectStructure = [
                    'Project Stakeholder',
                    'Project Code', 
                    'Project Name:',
                    'Partner Name (if any):',
                    'Client:',
                    'Consultant:',
                    'Project Time line',
                    'Project starting date:',
                    'Project Progress %',
                    'Project Duration (days):',
                    'Elapsed time (days):',
                    'Time to completion (days):',
                    'Project Key Personnel',
                    'Sr. Project Manager:',
                    'HSE Manager:',
                    'Project Manager:'
                ];
                
                tableHTML = `
                    <table class="airtable-grid">
                        <thead>
                            <tr>
                                <th></th>
                                <th>📋 PROJECT INFORMATION</th>
                                <th>📄 Field 1</th>
                                <th style="width: 40px;">
                                    <div class="add-field-btn" title="Add field">+</div>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            ${records.map((record, index) => {
                                // Map record fields to the project structure
                                const recordFields = Object.entries(record.fields || {});
                                const fieldName = recordFields[0] ? recordFields[0][0] : (projectStructure[index] || `Field ${index + 1}`);
                                const fieldValue = recordFields[0] ? recordFields[0][1] : '';
                                
                                return `
                                    <tr>
                                        <td class="record-number">${index + 1}</td>
                                        <td><div class="cell-content">${fieldName}</div></td>
                                        <td><div class="cell-content">${fieldValue}</div></td>
                                        <td></td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                // Standard grid layout for other tables with proper column structure
                const maxColumns = Math.min(fieldNames.length, 3); // Limit to 3 data columns for better display
                const displayFields = fieldNames.slice(0, maxColumns);
                
                tableHTML = `
                    <table class="airtable-grid">
                        <thead>
                            <tr>
                                <th></th>
                                ${displayFields.map((field, index) => {
                                    if (index === 0) return `<th>📋 ${field.toUpperCase()}</th>`;
                                    return `<th>📄 Field ${index + 1}</th>`;
                                }).join('')}
                                <th style="width: 40px;">
                                    <div class="add-field-btn" title="Add field">+</div>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            ${records.map((record, index) => `
                                <tr>
                                    <td class="record-number">${index + 1}</td>
                                    ${displayFields.map((field, fieldIndex) => `
                                        <td><div class="cell-content">${fieldIndex === 0 ? field : (record.fields[field] || '')}</div></td>
                                    `).join('')}
                                    <td></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
            
            // Add the table footer with add button and record count
            const footerHTML = `
                <div class="table-footer">
                    <button class="add-record-btn" onclick="showAddForm()">
                        <span class="add-icon">+</span>
                        <span>Add...</span>
                    </button>
                    <div class="record-count-info">
                        ${records.length} record${records.length !== 1 ? 's' : ''}
                    </div>
                </div>
            `;
            
            gridContainer.innerHTML = tableHTML + footerHTML;
        }

        async function loadTable(tableId, tableName) {
            // This function now switches to grid view
            loadGridTable(tableId, tableName);
        }

        function showAddForm() {
            // Switch to form view
            document.getElementById('gridViewContainer').style.display = 'none';
            document.getElementById('formContainer').style.display = 'block';
            
            // Load the form for the current table
            if (currentTable && currentTableName) {
                loadTableOld(currentTable, currentTableName);
            }
        }

        // Keep the original loadTable function for backward compatibility
        async function loadTableOld(tableId, tableName) {
            currentTable = tableId;
            showLoading(true);
            
            console.log(`Loading table: ${tableName} (${tableId})`);
            
            // Update active button states
            document.querySelectorAll('.table-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.about-btn').forEach(btn => btn.classList.remove('active'));
            if (window.event && window.event.target) {
                window.event.target.classList.add('active');
            }
            
            // Hide about section
            document.getElementById('aboutContainer').style.display = 'none';
            
            try {
                // Load both form and records
                const formResponse = await fetch(`/api/form/${tableId}`);
                const formData = await formResponse.json();
                
                if (formData.success) {
                    displayForm(formData.form, tableName);
                    // Records will be loaded automatically by displayForm function
                } else {
                    showMessage(formData.error || 'Failed to load table', 'error');
                }
            } catch (error) {
                console.error('Error loading table:', error);
                showMessage(`Failed to load table: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }

        function displayForm(formHtml, tableName) {
            // Hide about section and show form
            document.getElementById('aboutContainer').style.display = 'none';
            document.getElementById('formContainer').style.display = 'block';
            
            document.getElementById('formContainer').innerHTML = `
                <div class="form-section">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h2>📊 ${tableName} Management</h2>
                        <button onclick="toggleView()" class="btn" id="viewToggleBtn" style="background: #28a745;">📝 Add New Record</button>
                    </div>
                    
                    <div id="message" style="display: none;"></div>
                    
                    <!-- Records Display Section -->
                    <div id="recordsSection">
                        <h3>📋 Existing Records</h3>
                        <div id="recordsContainer">
                            <div class="loading-records">Loading records...</div>
                        </div>
                    </div>
                    
                    <!-- Add New Record Form -->
                    <div id="formSection" style="display: none;">
                        <h3>➕ Add New Record</h3>
                        <form onsubmit="submitForm(event)" id="dataForm">
                            ${formHtml}
                            <div style="margin-top: 20px;">
                                <button type="submit" class="btn">💾 Save Record</button>
                                <button type="button" onclick="toggleView()" class="btn" style="background: #6c757d; margin-left: 10px;">📋 View Records</button>
                            </div>
                        </form>
                    </div>
                </div>
            `;
            
            // Load existing records
            loadTableRecords(currentTable);
        }

        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }
        
        function loadTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
        }

        function showAbout() {
            // Update active button states
            document.querySelectorAll('.table-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.about-btn').forEach(btn => btn.classList.add('active'));
            
            // Hide form and show about section
            document.getElementById('formContainer').style.display = 'none';
            document.getElementById('aboutContainer').style.display = 'block';
        }

        async function loadTableRecords(tableId) {
            const recordsContainer = document.getElementById('recordsContainer');
            
            // Show loading state
            recordsContainer.innerHTML = `
                <div class="loading-records">
                    <div class="spinner"></div>
                    <p>Loading records from Airtable...</p>
                </div>
            `;
            
            try {
                console.log(`Loading records for table: ${tableId}`);
                const response = await fetch(`/api/records/${tableId}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('Records data received:', data);
                
                // Check if this is the Definitions table for special formatting
                const isDefinitionsTable = data.records && data.records.length > 0 && 
                    data.records.some(record => {
                        console.log('Checking record fields:', Object.keys(record.fields));
                        return record.fields.hasOwnProperty('Term') && record.fields.hasOwnProperty('Definitions');
                    });
                console.log('Is Definitions table:', isDefinitionsTable, 'Table name:', data.table_name);
                
                if (data.success && data.records && data.records.length > 0) {
                    let recordsHtml;
                    
                    if (isDefinitionsTable) {
                        // Special formatting for Definitions table
                        recordsHtml = data.records.map((record, index) => {
                            const term = record.fields.Term || `Term ${index + 1}`;
                            const definition = record.fields.Definitions || 'No definition available';
                            
                            return `
                                <div class="definition-card">
                                    <div class="definition-term">
                                        <span class="term-number">${index + 1}</span>
                                        <h3 class="term-title">${term}</h3>
                                    </div>
                                    <div class="definition-content">
                                        <p class="definition-text">${definition}</p>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    } else {
                        // Standard formatting for other tables
                        recordsHtml = data.records.map((record, index) => {
                            const fieldsHtml = Object.entries(record.fields).map(([key, value]) => {
                                if (value !== null && value !== undefined && value !== '') {
                                    // Truncate long values
                                    const displayValue = String(value).length > 100 ? 
                                        String(value).substring(0, 100) + '...' : String(value);
                                    return `<div class="field-display">
                                        <strong>${key}:</strong> 
                                        <span class="field-value">${displayValue}</span>
                                    </div>`;
                                }
                                return '';
                            }).filter(html => html).join('');
                            
                            const createdDate = record.created_time ? 
                                new Date(record.created_time).toLocaleDateString() : 
                                'Unknown';
                            
                            return `
                                <div class="record-card" data-record-id="${record.id}">
                                    <div class="record-header">
                                        <span class="record-id">Record #${index + 1}</span>
                                        <span class="record-time">📅 ${createdDate}</span>
                                    </div>
                                    <div class="record-fields">
                                        ${fieldsHtml || '<div class="no-fields">No data available</div>'}
                                    </div>
                                    <div class="record-footer">
                                        <small class="full-id">ID: ${record.id}</small>
                                        <small class="field-count">${record.field_count || 0} fields</small>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    }
                    
                    recordsContainer.innerHTML = `
                        <div class="records-header">
                            <span class="records-count">📊 ${data.count} records loaded from Airtable</span>
                            <button onclick="loadTableRecords('${tableId}')" class="refresh-btn" title="Refresh Records">🔄</button>
                        </div>
                        <div class="records-grid">${recordsHtml}</div>
                    `;
                } else if (data.success && data.records && data.records.length === 0) {
                    recordsContainer.innerHTML = `
                        <div class="no-records">
                            <div class="no-records-icon">📭</div>
                            <h3>No Records Found</h3>
                            <p>This table appears to be empty.</p>
                            <p>Click <strong>"Add New Record"</strong> to create the first entry.</p>
                            <button onclick="toggleView()" class="btn" style="margin-top: 15px;">📝 Add First Record</button>
                        </div>
                    `;
                } else {
                    throw new Error(data.error || 'Failed to load records');
                }
            } catch (error) {
                console.error('Error loading records:', error);
                recordsContainer.innerHTML = `
                    <div class="error-records">
                        <div class="error-icon">❌</div>
                        <h3>Failed to Load Records</h3>
                        <p><strong>Error:</strong> ${error.message}</p>
                        <p>Please check your Airtable connection and try again.</p>
                        <button onclick="loadTableRecords('${tableId}')" class="btn" style="margin-top: 15px;">🔄 Retry</button>
                    </div>
                `;
            }
        }
        
        function toggleView() {
            const recordsSection = document.getElementById('recordsSection');
            const formSection = document.getElementById('formSection');
            const toggleBtn = document.getElementById('viewToggleBtn');
            
            if (formSection.style.display === 'none') {
                // Show form, hide records
                recordsSection.style.display = 'none';
                formSection.style.display = 'block';
                toggleBtn.textContent = '📋 View Records';
                toggleBtn.style.background = '#17a2b8';
            } else {
                // Show records, hide form
                recordsSection.style.display = 'block';
                formSection.style.display = 'none';
                toggleBtn.textContent = '📝 Add New Record';
                toggleBtn.style.background = '#28a745';
            }
        }

        async function submitForm(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const data = {};
            
            // Convert FormData to object, handling multiple values for the same key
            for (let [key, value] of formData.entries()) {
                if (data[key]) {
                    if (!Array.isArray(data[key])) {
                        data[key] = [data[key]];
                    }
                    data[key].push(value);
                } else {
                    data[key] = value;
                }
            }
            
            showLoading(true);
            try {
                const response = await fetch(`/api/submit/${currentTable}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage('✅ Record saved successfully!', 'success');
                    document.getElementById('dataForm').reset();
                    
                    // Refresh records after successful submission
                    setTimeout(() => {
                        toggleView(); // Switch back to records view
                        loadTableRecords(currentTable); // Reload records
                    }, 1500);
                } else {
                    showMessage(`❌ Error: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('Error submitting form:', error);
                showMessage('❌ Failed to save record', 'error');
            } finally {
                showLoading(false);
            }
        }

        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }

        function showMessage(message, type) {
            const messageDiv = document.getElementById('message');
            if (messageDiv) {
                messageDiv.className = type;
                messageDiv.textContent = message;
                messageDiv.style.display = 'block';
                
                // Auto-hide success messages
                if (type === 'success') {
                    setTimeout(() => {
                        messageDiv.style.display = 'none';
                    }, 5000);
                }
            } else {
                // Fallback: show alert if message div not found
                alert(`${type.toUpperCase()}: ${message}`);
                console.error('Message div not found, using alert fallback');
            }
        }
    </script>
</body>
</html>
"""

def get_field_type(field):
    """Determine the appropriate input type for a field"""
    field_type = field.get('type', 'singleLineText')
    
    type_mapping = {
        'singleLineText': 'text',
        'email': 'email',
        'url': 'url',
        'multilineText': 'textarea',
        'number': 'number',
        'currency': 'number',
        'percent': 'number',
        'date': 'date',
        'dateTime': 'datetime-local',
        'phoneNumber': 'tel',
        'singleSelect': 'select',
        'multipleSelects': 'select',
        'checkbox': 'checkbox',
        'rating': 'number',
        'richText': 'textarea'
    }
    
    return type_mapping.get(field_type, 'text')

def serialize_field_options(options):
    """Safely serialize field options to JSON-compatible format"""
    if options is None:
        return None
    
    try:
        # Handle different types of options objects
        if hasattr(options, '__dict__'):
            # Convert object to dict
            result = {}
            for key, value in options.__dict__.items():
                if not key.startswith('_'):  # Skip private attributes
                    try:
                        # Try to serialize the value
                        import json
                        json.dumps(value)  # Test if it's serializable
                        result[key] = value
                    except (TypeError, ValueError):
                        # If not serializable, convert to string
                        result[key] = str(value)
            return result
        elif isinstance(options, dict):
            return options
        else:
            return str(options)
    except Exception:
        return None

def should_exclude_field(field):
    """Check if field should be excluded from forms"""
    field_type = field.get('type', '')
    field_name = field.get('name', '').lower()
    
    # Exclude computed fields
    computed_types = [
        'formula', 'rollup', 'lookup', 'count', 'createdTime', 
        'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'
    ]
    
    if field_type in computed_types:
        return True
        
    # Exclude auto-generated fields
    auto_fields = ['record id', 'id', 'created time', 'modified time']
    if any(auto in field_name for auto in auto_fields):
        return True
        
    return False

def generate_field_html(field, table_name):
    """Generate HTML for a form field"""
    if should_exclude_field(field):
        return ""
    
    field_name = field['name']
    field_type = get_field_type(field)
    field_id = f"field_{field_name.replace(' ', '_').replace('(', '').replace(')', '').replace('&', '')}"
    
    # Special handling for Training table - convert select fields to text
    is_training_table = 'training' in table_name.lower() and 'competency' in table_name.lower()
    if is_training_table and field_type == 'select':
        field_type = 'text'
    
    html_parts = [f'<div class="form-group">']
    html_parts.append(f'<label for="{field_id}">{field_name}</label>')
    
    if field_type == 'textarea':
        html_parts.append(f'<textarea id="{field_id}" name="{field_name}" rows="4"></textarea>')
    elif field_type == 'select' and not is_training_table:
        # Handle serialized options safely
        options = []
        field_options = field.get('options', {})
        if isinstance(field_options, dict):
            choices = field_options.get('choices', [])
            if isinstance(choices, list):
                options = choices
        
        html_parts.append(f'<select id="{field_id}" name="{field_name}">')
        html_parts.append('<option value="">-- Select an option --</option>')
        for option in options:
            if isinstance(option, dict):
                option_name = option.get('name', str(option))
            else:
                option_name = str(option)
            html_parts.append(f'<option value="{option_name}">{option_name}</option>')
        html_parts.append('</select>')
    elif field_type == 'checkbox':
        html_parts.append(f'<input type="checkbox" id="{field_id}" name="{field_name}" value="true">')
    elif field_type == 'number':
        step = '0.01' if field.get('type') in ['currency', 'percent'] else '1'
        html_parts.append(f'<input type="number" id="{field_id}" name="{field_name}" step="{step}">')
    else:
        html_parts.append(f'<input type="{field_type}" id="{field_id}" name="{field_name}">')
    
    html_parts.append('</div>')
    return ''.join(html_parts)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/test')
def test_connection():
    """Simple test endpoint"""
    return jsonify({
        'success': True,
        'message': 'API is working!',
        'token_set': bool(AIRTABLE_TOKEN),
        'base_id_set': bool(AIRTABLE_BASE_ID)
    })

@app.route('/api/tables')
def get_tables():
    """Get list of all tables and their schemas"""
    try:
        tables = []
        schemas = {}
        
        for table in base.schema().tables:
            table_info = {
                'id': table.id,
                'name': table.name
            }
            tables.append(table_info)
            
            # Store schema for form generation
            schemas[table.id] = {
                'name': table.name,
                'fields': [
                    {
                        'name': field.name,
                        'type': field.type,
                        'options': serialize_field_options(getattr(field, 'options', None))
                    }
                    for field in table.fields
                ]
            }
        
        return jsonify({
            'success': True,
            'tables': tables,
            'schemas': schemas
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/form/<table_id>')
def get_form(table_id):
    """Generate form HTML for a specific table"""
    try:
        table = base.table(table_id)
        schema = base.schema().table(table_id)
        
        form_html = []
        for field in schema.fields:
            field_dict = {
                'name': field.name,
                'type': field.type,
                'options': getattr(field, 'options', None)
            }
            field_html = generate_field_html(field_dict, schema.name)
            if field_html:
                form_html.append(field_html)
        
        return jsonify({
            'success': True,
            'form': ''.join(form_html)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/records/<table_id>')
def get_records(table_id):
    """Get existing records from the specified table"""
    try:
        table = base.table(table_id)
        
        # Get records with limit to avoid overwhelming the interface
        records = table.all(max_records=100)
        
        # Format records for display
        formatted_records = []
        for record in records:
            # Clean and format fields
            clean_fields = {}
            for key, value in record['fields'].items():
                if value is not None and str(value).strip():
                    # Handle different field types
                    if isinstance(value, list):
                        clean_fields[key] = ', '.join(str(v) for v in value)
                    elif isinstance(value, dict):
                        clean_fields[key] = str(value)
                    else:
                        clean_fields[key] = str(value)
            
            formatted_record = {
                'id': record['id'],
                'fields': clean_fields,
                'created_time': record.get('createdTime', ''),
                'field_count': len(clean_fields)
            }
            formatted_records.append(formatted_record)
        
        return jsonify({
            'success': True,
            'records': formatted_records,
            'count': len(formatted_records),
            'table_id': table_id
        })
    except Exception as e:
        print(f"Error fetching records from table {table_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Failed to load records: {str(e)}",
            'table_id': table_id
        })

@app.route('/api/submit/<table_id>', methods=['POST'])
def submit_record(table_id):
    """Submit a new record to the specified table"""
    try:
        data = request.get_json()
        table = base.table(table_id)
        
        # Clean the data - remove empty values and handle special cases
        clean_data = {}
        for key, value in data.items():
            if value and str(value).strip():
                # Handle checkbox fields
                if value == 'true':
                    clean_data[key] = True
                elif value == 'false':
                    clean_data[key] = False
                else:
                    clean_data[key] = value
        
        if not clean_data:
            raise ValueError("No valid data provided")
        
        # Create the record
        record = table.create(clean_data)
        
        return jsonify({
            'success': True,
            'record_id': record['id'],
            'message': 'Record created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)