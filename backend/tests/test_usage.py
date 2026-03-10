"""
Usage data endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app
from datetime import datetime

client = TestClient(app)

def test_receive_laptop_usage():
    """Test receiving laptop usage data"""
    usage_data = {
        "device_id": "laptop_test_001",
        "user_id": "test_user_001",
        "timestamp": datetime.now().isoformat(),
        "session_id": "session_001",
        "active_app": "VS Code",
        "usage_duration": 60.5,
        "session_length": 120.0,
        "idle_time": 10.0,
        "time_of_day": "morning",
        "keystrokes": 500,
        "mouse_clicks": 200
    }
    
    response = client.post("/api/v1/usage/laptop", json=usage_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "record_id" in data
    assert data["message"] == "Laptop usage data received"

def test_receive_mobile_usage():
    """Test receiving mobile usage data"""
    usage_data = {
        "device_id": "mobile_test_001",
        "user_id": "test_user_001",
        "timestamp": datetime.now().isoformat(),
        "session_id": "mobile_session_001",
        "app_name": "WhatsApp",
        "screen_time": 30.5,
        "category": "Social",
        "notifications_received": 15
    }
    
    response = client.post("/api/v1/usage/mobile", json=usage_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "record_id" in data
    assert data["message"] == "Mobile usage data received"

def test_get_recent_usage():
    """Test getting recent usage data"""
    response = client.get("/api/v1/usage/user/test_user_001/recent?hours=24")
    
    assert response.status_code == 200
    data = response.json()
    assert "laptop_usage" in data
    assert "mobile_usage" in data
    assert "totals" in data
    assert isinstance(data["laptop_usage"], list)
    assert isinstance(data["mobile_usage"], list)