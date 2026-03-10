"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from src.app import app
from src.database import db
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def test_client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Setup test database"""
    # Connect to test database
    test_db_client = AsyncIOMotorClient("mongodb://localhost:27017")
    test_db = test_db_client["fatigue_prediction_test"]
    
    # Store original database reference
    original_db = db.db
    
    # Replace with test database
    db.db = test_db
    
    yield
    
    # Cleanup - drop test database
    await test_db_client.drop_database("fatigue_prediction_test")
    
    # Restore original database
    db.db = original_db

@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    }

@pytest.fixture
def sample_laptop_usage():
    """Sample laptop usage data for tests"""
    from datetime import datetime
    return {
        "device_id": "test_laptop_001",
        "user_id": "test_user_001",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test_session_001",
        "active_app": "Test App",
        "usage_duration": 60.0,
        "session_length": 120.0,
        "idle_time": 10.0,
        "time_of_day": "morning",
        "keystrokes": 100,
        "mouse_clicks": 50
    }

@pytest.fixture
def sample_mobile_usage():
    """Sample mobile usage data for tests"""
    from datetime import datetime
    return {
        "device_id": "test_mobile_001",
        "user_id": "test_user_001",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test_mobile_session_001",
        "app_name": "Test Mobile App",
        "screen_time": 30.0,
        "category": "Test",
        "notifications_received": 5
    }