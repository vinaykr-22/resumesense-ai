import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_flow():
    print("1. Testing Registration Endpoint (/api/v1/auth/register)...")
    res = client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com", 
        "password": "password123"
    })
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}\n")
    
    print("2. Testing Login Endpoint (/api/v1/auth/login)...")
    res = client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com", 
        "password": "password123"
    })
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}\n")
    
    token = res.json().get("access_token")
    if token:
        print(f"3. Received JWT Token successfully: {token[:15]}...{token[-10:]}")
        print("You can verify standard Bearer token behavior using this token.")
        
        # Testing user retrieval directly (as a bonus check)
        from services.auth import get_current_user
        try:
            email = get_current_user(token)
            print(f"4. Token successfully decoded to user: {email}")
            print("\nSuccess! JWT authentication flow works perfectly.")
        except Exception as e:
            print(f"Failed to decode token as user: {e}")
            
    else:
        print("Failed to get token.")

if __name__ == "__main__":
    test_flow()
