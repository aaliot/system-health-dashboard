import os
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "UP"}

def test_version(client):
    response = client.get('/version')
    assert response.status_code == 200
    assert response.get_json() == {"version": "1.0.1"}

def test_environment(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    response = client.get('/environment')
    assert response.status_code == 200
    assert response.get_json() == {"environment": "testing"}