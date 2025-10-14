#!/usr/bin/env python3
"""
Modernized Airtable Dashboard Application
Enterprise-grade architecture with modular components
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from flask import Flask, jsonify, request, render_template, url_for
except ImportError:
    print("Flask is not installed. Installing now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    from flask import Flask, jsonify, request, render_template, url_for

from pyairtable import AirtableClient
from pyairtable.utils import setup_logging

# Application Configuration
class Config:
    """Application configuration"""
    DEBUG = True
    JSON_SORT_KEYS = False
    MAX_RECORDS_DEFAULT = 50
    CACHE_TIMEOUT = 300  # 5 minutes
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Application Factory
def create_app(config_class=DevelopmentConfig):
    """Create Flask application with configuration"""
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    app.config.from_object(config_class)
    
    # Setup logging
    setup_logging("INFO")
    
    return app

# Initialize Flask app
app = create_app()

# Initialize Airtable client
try:
    client = AirtableClient()
    AIRTABLE_CONNECTED = True
    print(f"✅ Connected to Airtable: {client}")
except ValueError as e:
    AIRTABLE_CONNECTED = False
    print(f"⚠️  Airtable not configured: {e}")
    client = None

# Server metadata
SERVER_START_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Utility Functions
def get_table_schema(table_name: str) -> Optional[Dict]:
    """Get table schema information"""
    if not AIRTABLE_CONNECTED:
        return None
    
    try:
        base_id = os.getenv('AIRTABLE_BASE_ID')
        base = client.base(base_id)
        schema = base.schema()
        
        for table in schema.tables:
            if table.name == table_name:
                return {
                    "id": table.id,
                    "name": table.name,
                    "description": table.description,
                    "fields": [{"id": f.id, "name": f.name, "type": f.type} for f in table.fields],
                    "views": [{"id": v.id, "name": v.name, "type": v.type} for v in table.views]
                }
        return None
    except Exception:
        return None

def validate_record_fields(fields: Dict, table_name: str) -> Dict:
    """Validate and clean record fields"""
    schema = get_table_schema(table_name)
    if not schema:
        return fields
    
    # Get editable field names
    editable_fields = {
        f['name'] for f in schema['fields'] 
        if f['type'] not in ['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber']
    }
    
    # Filter to only editable fields
    return {k: v for k, v in fields.items() if k in editable_fields and v}

# Routes
@app.route('/')
def home():
    """Main dashboard page"""
    return render_template('index.html', 
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
            "tables": tables_info,
            "timestamp": datetime.now().isoformat()
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
            max_records = request.args.get('max_records', app.config['MAX_RECORDS_DEFAULT'], type=int)
            view = request.args.get('view')
            sort = request.args.getlist('sort')
            
            # Build query parameters
            kwargs = {'max_records': max_records}
            if view:
                kwargs['view'] = view
            if sort:
                kwargs['sort'] = sort
            
            records = table.all(**kwargs)
            
            return jsonify({
                "table": table_name,
                "count": len(records),
                "records": records,
                "timestamp": datetime.now().isoformat()
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'fields' not in data:
                return jsonify({"error": "Missing 'fields' in request body"}), 400
            
            # Validate and clean fields
            fields = validate_record_fields(data['fields'], table_name)
            if not fields:
                return jsonify({"error": "No valid fields provided"}), 400
            
            record = table.create(fields)
            return jsonify({
                "success": True,
                "record": record,
                "message": "Record created successfully"
            }), 201
    
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
            return jsonify({
                "record": record,
                "timestamp": datetime.now().isoformat()
            })
        
        elif request.method == 'PATCH':
            data = request.get_json()
            if not data or 'fields' not in data:
                return jsonify({"error": "Missing 'fields' in request body"}), 400
            
            # Validate and clean fields
            fields = validate_record_fields(data['fields'], table_name)
            if not fields:
                return jsonify({"error": "No valid fields provided"}), 400
            
            record = table.update(record_id, fields)
            return jsonify({
                "success": True,
                "record": record,
                "message": "Record updated successfully"
            })
        
        elif request.method == 'DELETE':
            table.delete(record_id)
            return jsonify({
                "success": True,
                "message": f"Record {record_id} deleted successfully"
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tables/<table_name>/schema', methods=['GET'])
def get_table_schema_route(table_name):
    """Get schema information for a specific table"""
    if not AIRTABLE_CONNECTED:
        return jsonify({"error": "Airtable not configured"}), 500
    
    schema = get_table_schema(table_name)
    if not schema:
        return jsonify({"error": f"Table '{table_name}' not found"}), 404
    
    return jsonify({
        "schema": schema,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "airtable_connected": AIRTABLE_CONNECTED,
        "server_start_time": SERVER_START_TIME,
        "timestamp": datetime.now().isoformat()
    })

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

# Development Server
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Starting Modernized Airtable Dashboard Server")
    print("="*70)
    print(f"📊 Server URL: http://localhost:5000")
    print(f"🔗 Airtable Connection: {'✅ Connected' if AIRTABLE_CONNECTED else '❌ Not Connected'}")
    print(f"🎯 Environment: {'Development' if app.config['DEBUG'] else 'Production'}")
    if AIRTABLE_CONNECTED:
        base_id = os.getenv('AIRTABLE_BASE_ID')
        print(f"📋 Base ID: {base_id}")
    print("="*70)
    print("🎨 Features:")
    print("   • Modern UI with responsive design")
    print("   • Component-based JavaScript architecture") 
    print("   • Intelligent caching and performance optimization")
    print("   • Full CRUD operations with validation")
    print("   • Real-time updates and auto-refresh")
    print("   • Keyboard shortcuts (Ctrl+R: Refresh, Ctrl+N: New Record)")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)