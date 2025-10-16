#!/usr/bin/env python3
"""
Simple test server to display Airtable tables
"""

import os
from flask import Flask
from dotenv import load_dotenv
from pyairtable import Api

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# Initialize Flask
app = Flask(__name__)

@app.route('/')
def index():
    """Show all tables in the Airtable base"""
    try:
        # Connect to Airtable
        api = Api(AIRTABLE_TOKEN)
        base = api.base(AIRTABLE_BASE_ID)
        schema = base.schema()
        
        # Generate HTML for the tables
        tables_html = ""
        for table in schema.tables:
            try:
                table_obj = base.table(table.name)
                records = table_obj.all()
                record_count = len(records)
            except Exception as e:
                record_count = f"Error: {str(e)}"
                
            tables_html += f"""
            <div class="table">
                <h3>{table.name}</h3>
                <p><strong>Records:</strong> {record_count}</p>
                <p><strong>ID:</strong> {table.id}</p>
            </div>
            """
        
        # Return the complete HTML page
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Airtable Tables</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #4285f4; }}
                .tables {{ display: flex; flex-wrap: wrap; gap: 15px; }}
                .table {{ 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    border-radius: 8px;
                    width: 250px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .table:hover {{ background-color: #f8f8f8; }}
            </style>
        </head>
        <body>
            <h1>Airtable Tables</h1>
            <p>Base ID: {AIRTABLE_BASE_ID}</p>
            <p>Found {len(schema.tables)} tables:</p>
            
            <div class="tables">
                {tables_html}
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .error {{ color: #d32f2f; }}
            </style>
        </head>
        <body>
            <h1>Error</h1>
            <div class="error">
                <p>{str(e)}</p>
            </div>
        </body>
        </html>
        """

if __name__ == '__main__':
    print("[*] Starting test server...")
    print(f"[*] Using Airtable base: {AIRTABLE_BASE_ID}")
    print(f"[*] Token configured: {AIRTABLE_TOKEN is not None}")
    if AIRTABLE_TOKEN:
        print(f"[*] Token starts with: {AIRTABLE_TOKEN[:10]}...")
    
    app.run(host='0.0.0.0', port=8080, debug=True)