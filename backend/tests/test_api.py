import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)

def test_api_health():
    """Test that the application healthcheck returns 200 OK"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"

def test_missing_auth_header():
    """Test that protected endpoints reject requests without a JWT Bearer token"""
    response = client.get("/api/v1/resume/history")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_invalid_upload_format():
    """Test that the upload endpoint strictly rejects non-pdf/docx mock files"""
    # Create dummy token payload and mock users_db entry
    from services.auth import create_access_token, users_db
    test_email = "test@example.com"
    users_db[test_email] = {"email": test_email, "hashed_password": "mock"}
    token = create_access_token({"sub": test_email})
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = {
        "file": ("image.png", b"dummy_content", "image/png")
    }
    
    response = client.post("/api/v1/resume/upload", headers=headers, files=files)
    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF and DOCX files are supported"}

if __name__ == "__main__":
    print("Running tests...")
    test_api_health()
    print("Health check passed!")
    test_missing_auth_header()
    print("Auth header check passed!")
    test_invalid_upload_format()
    print("Invalid upload format check passed!")
    print("All tests passed!")
