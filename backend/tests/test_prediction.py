"""
Prediction endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app
from unittest.mock import patch

client = TestClient(app)

def test_predict_with_valid_data():
    """Test prediction with valid data"""
    with patch('src.services.ml_service.ml_service.load_models'):
        with patch('src.services.ml_service.ml_service.predict_fatigue') as mock_predict:
            mock_predict.return_value = (65.5, "Medium")
            
            response = client.post("/api/v1/prediction/predict", json={
                "user_id": "test_user_001",
                "timestamp": "2024-01-01T10:00:00Z",
                "features": {}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "fatigue_score" in data
            assert "fatigue_level" in data
            assert data["fatigue_level"] == "Medium"

def test_predict_without_data():
    """Test prediction when no usage data exists"""
    response = client.post("/api/v1/prediction/predict", json={
        "user_id": "nonexistent_user",
        "timestamp": "2024-01-01T10:00:00Z",
        "features": {}
    })
    
    # Should return 404 when no data found
    assert response.status_code == 404
    assert "No recent usage data" in response.json()["detail"]

def test_prediction_history():
    """Test getting prediction history"""
    response = client.get("/api/v1/prediction/user/test_user_001/history?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "predictions" in data
    assert isinstance(data["predictions"], list)