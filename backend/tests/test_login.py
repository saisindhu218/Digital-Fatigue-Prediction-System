import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_registration():
    """Test user registration"""
    print("\n📝 Testing Registration...")
    
    # Generate unique email
    import uuid
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    
    user_data = {
        "email": email,
        "full_name": "Test User",
        "password": "password123"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=user_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        print(f"✅ Registration successful: {email}")
        print(f"   Response: {response.json()}")
        return email, "password123"
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None

def test_login_json(email, password):
    """Test login with JSON"""
    print("\n🔐 Testing Login with JSON...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login-json",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print(f"✅ Login successful!")
        print(f"   Access Token: {response.json()['access_token'][:20]}...")
        return response.json()
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_login_generic(email, password):
    """Test login with generic JSON"""
    print("\n🔐 Testing Login with Generic JSON...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print(f"✅ Login successful!")
        print(f"   Access Token: {response.json()['access_token'][:20]}...")
        return response.json()
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_debug():
    """Test debug endpoint"""
    print("\n🔍 Testing Debug Endpoint...")
    
    response = requests.get(f"{BASE_URL}/auth/debug")
    
    if response.status_code == 200:
        print(f"✅ Debug endpoint working!")
        print(f"   Database connected: {response.json().get('database_connected')}")
        print(f"   Total users: {response.json().get('total_users')}")
        print(f"   Test user exists: {response.json().get('test_user_exists')}")
        return response.json()
    else:
        print(f"❌ Debug endpoint failed: {response.status_code}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 AUTHENTICATION TEST SUITE")
    print("=" * 60)
    
    # Test debug endpoint first
    test_debug()
    
    # Test registration and login
    email, password = test_registration()
    
    if email and password:
        # Test both login methods
        test_login_json(email, password)
        test_login_generic(email, password)
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)