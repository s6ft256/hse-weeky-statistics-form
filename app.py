#!/usr/bin/env python3
"""
Production Airtable Dashboard for Render Deployment
"""

import os
from flask import Flask, render_template_string, request, jsonify
from pyairtable import Api
from dotenv import load_dotenv

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
    <title>Airtable Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
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
            padding: 40px;
        }
        .form-section {
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #007bff;
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
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
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
        .table-selector {
            margin-bottom: 30px;
            text-align: center;
        }
        .table-btn {
            display: inline-block;
            margin: 10px;
            padding: 15px 25px;
            background: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
            font-weight: 600;
        }
        .table-btn:hover, .table-btn.active {
            background: #007bff;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,123,255,0.3);
        }
        @media (max-width: 768px) {
            .content { padding: 20px; }
            .form-section { padding: 20px; }
            .header h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Airtable Dashboard</h1>
            <p>Streamlined Data Management Interface</p>
        </div>
        <div class="content">
            <div class="table-selector" id="tableSelector">
                <!-- Table buttons will be populated by JavaScript -->
            </div>
            
            <div id="formContainer">
                <!-- Forms will be populated by JavaScript -->
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        </div>
    </div>

    <script>
        let currentTable = '';
        let tableSchemas = {};

        // Load tables on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadTables();
        });

        async function loadTables() {
            showLoading(true);
            try {
                const response = await fetch('/api/tables');
                const data = await response.json();
                
                if (data.success) {
                    tableSchemas = data.schemas;
                    displayTableButtons(data.tables);
                    if (data.tables.length > 0) {
                        loadTable(data.tables[0].id, data.tables[0].name);
                    }
                } else {
                    showMessage(data.error || 'Failed to load tables', 'error');
                }
            } catch (error) {
                console.error('Error loading tables:', error);
                showMessage('Failed to connect to server', 'error');
            } finally {
                showLoading(false);
            }
        }

        function displayTableButtons(tables) {
            const selector = document.getElementById('tableSelector');
            selector.innerHTML = tables.map(table => 
                `<a href="#" class="table-btn" onclick="loadTable('${table.id}', '${table.name}')">${table.name}</a>`
            ).join('');
        }

        async function loadTable(tableId, tableName) {
            currentTable = tableId;
            showLoading(true);
            
            // Update active button
            document.querySelectorAll('.table-btn').forEach(btn => btn.classList.remove('active'));
            event?.target?.classList.add('active');
            
            try {
                const response = await fetch(`/api/form/${tableId}`);
                const data = await response.json();
                
                if (data.success) {
                    displayForm(data.form, tableName);
                } else {
                    showMessage(data.error || 'Failed to load form', 'error');
                }
            } catch (error) {
                console.error('Error loading form:', error);
                showMessage('Failed to load form', 'error');
            } finally {
                showLoading(false);
            }
        }

        function displayForm(formHtml, tableName) {
            document.getElementById('formContainer').innerHTML = `
                <div class="form-section">
                    <h2>📝 Add New Record to ${tableName}</h2>
                    <form onsubmit="submitForm(event)" id="dataForm">
                        ${formHtml}
                        <button type="submit" class="btn">💾 Save Record</button>
                    </form>
                    <div id="message"></div>
                </div>
            `;
        }

        async function submitForm(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const data = {};
            
            // Convert FormData to object, handling multiple values for the same key
            for (let [key, value] = formData.entries()) {
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
            messageDiv.className = type;
            messageDiv.textContent = message;
            messageDiv.style.display = 'block';
            
            // Auto-hide success messages
            if (type === 'success') {
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 5000);
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
    field_id = f"field_{field_name.replace(' ', '_').replace('(', '').replace(')', '')}"
    
    # Special handling for Training table - convert select fields to text
    is_training_table = 'training' in table_name.lower() and 'competency' in table_name.lower()
    if is_training_table and field_type == 'select':
        field_type = 'text'
    
    html_parts = [f'<div class="form-group">']
    html_parts.append(f'<label for="{field_id}">{field_name}</label>')
    
    if field_type == 'textarea':
        html_parts.append(f'<textarea id="{field_id}" name="{field_name}" rows="4"></textarea>')
    elif field_type == 'select' and not is_training_table:
        options = field.get('options', {}).get('choices', [])
        html_parts.append(f'<select id="{field_id}" name="{field_name}">')
        html_parts.append('<option value="">-- Select an option --</option>')
        for option in options:
            option_name = option.get('name', str(option))
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
                        'options': getattr(field, 'options', None)
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