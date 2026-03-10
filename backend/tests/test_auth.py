"""
Authentication tests
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_register_success():
    """Test successful user registration"""
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == "test@example.com"

def test_register_duplicate_email():
    """Test registration with duplicate email"""
    # First registration
    client.post("/api/v1/auth/register", json={
        "email": "duplicate@example.com",
        "full_name": "Test User",
        "password": "password123"
    })
    
    # Second registration with same email
    response = client.post("/api/v1/auth/register", json={
        "email": "duplicate@example.com",
        "full_name": "Another User",
        "password": "password456"
    })
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_success():
    """Test successful login"""
    # First register
    client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "full_name": "Login User",
        "password": "password123"
    })
    
    # Then login
    response = client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]