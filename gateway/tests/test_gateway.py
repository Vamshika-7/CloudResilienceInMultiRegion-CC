import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

gateway_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(gateway_dir))

from main import app

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@patch("httpx.AsyncClient.get")
def test_gateway_health(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "api-gateway"
    assert "downstream_services" in data

@patch("httpx.AsyncClient.request")
def test_proxy_products_route(mock_request, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'[{"id": 1, "name": "Laptop", "price": 999.0, "stock": 10}]'
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_request.return_value = mock_resp

    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Laptop"
    assert "X-Request-ID" in response.headers

@patch("httpx.AsyncClient.request")
def test_proxy_create_order_route(mock_request, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.content = b'{"id": 1, "user_id": "u1", "product_id": 1, "quantity": 2, "total_amount": 199.98, "status": "PENDING"}'
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_request.return_value = mock_resp

    payload = {"user_id": "u1", "product_id": 1, "quantity": 2}
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["status"] == "PENDING"

@patch("httpx.AsyncClient.request")
def test_proxy_create_payment_route(mock_request, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"id": 1, "order_id": 1, "amount": 199.98, "status": "SUCCESS", "payment_method": "SIMULATED_CARD"}'
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_request.return_value = mock_resp

    payload = {"order_id": 1, "amount": 199.98}
    response = client.post("/api/payments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
