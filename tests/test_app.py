import json
import os
import pytest
from prometheus_client import REGISTRY
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

def sample(endpoint):
    return REGISTRY.get_sample_value(
        'http_requests_total',
        {'method': 'GET', 'endpoint': endpoint, 'status': '200'},
    ) or 0


def test_metrics_counter_increases(client):
    before = sample('/health')
    client.get('/health')
    assert sample('/health') == before + 1
    assert client.get('/metrics').status_code == 200


def test_simulate_error_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv('ENABLE_FAULT_INJECTION', raising=False)
    assert client.get('/simulate-error').status_code == 404


def test_simulate_error_enabled(client, monkeypatch):
    monkeypatch.setenv('ENABLE_FAULT_INJECTION', 'true')
    assert client.get('/simulate-error').status_code == 500


def test_request_logged_as_json(client, capsys):
    client.get('/health')
    entry = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    for field in ('timestamp', 'level', 'message', 'endpoint', 'method', 'status', 'environment'):
        assert field in entry