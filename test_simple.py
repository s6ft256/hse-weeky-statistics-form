#!/usr/bin/env python3
"""
Simple test server to verify basic functionality
"""

import os
import ssl
import urllib3
import requests
from flask import Flask
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable SSL warnings and verification
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

# Configuration
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

print("[*] Starting Simple Test Server...")
print(f"[*] Token: {AIRTABLE_TOKEN[:10] if AIRTABLE_TOKEN else 'None'}...")
print(f"[*] Base ID: {AIRTABLE_BASE_ID}")

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Test Server</title>
    </head>
    <body>
        <h1>Simple Test Server is Working!</h1>
        <p>Server is running successfully on port 8080</p>
        <p><a href="/test">Test Airtable Connection</a></p>
    </body>
    </html>
    """

@app.route('/test')
def test_airtable():
    try:
        if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
            return f"""
            <h1>Configuration Error</h1>
            <p>Token: {'Set' if AIRTABLE_TOKEN else 'Missing'}</p>
            <p>Base ID: {'Set' if AIRTABLE_BASE_ID else 'Missing'}</p>
            """
        
        api = Api(AIRTABLE_TOKEN)
        base = api.base(AIRTABLE_BASE_ID)
        schema = base.schema()
        tables = schema.tables
        
        table_list = "<ul>"
        for table in tables:
            table_list += f"<li>{table.name} (ID: {table.id})</li>"
        table_list += "</ul>"
        
        return f"""
        <h1>Airtable Connection Test</h1>
        <p>✅ Successfully connected to Airtable!</p>
        <p>Found {len(tables)} tables:</p>
        {table_list}
        <p><a href="/">Back to Home</a></p>
        """
    except Exception as e:
        return f"""
        <h1>Airtable Connection Failed</h1>
        <p>❌ Error: {str(e)}</p>
        <p><a href="/">Back to Home</a></p>
        """

if __name__ == '__main__':
    print("[*] Server starting on http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)