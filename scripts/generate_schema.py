import os
import sys
import json
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

def generate_openapi_spec():
    """Generate OpenAPI JSON schema"""
    print("Generating OpenAPI specification...")
    
    openapi_schema = app.openapi()
    
    with open('openapi.json', 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("Successfully generated openapi.json")

if __name__ == "__main__":
    generate_openapi_spec()
