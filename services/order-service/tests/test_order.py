import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import httpx

# Add service directory to sys.path
service_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(service_dir))

from main import app
from database import Base, get_db
from models import Order
from sqlalchemy.pool import StaticPool

# Isolated in-memory database
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, poolclass=StaticPool, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        order = Order(user_id="user_123", product_id=1, quantity=2, total_amount=199.98, status="PENDING")
        db.add(order)
        db.commit()
        db.refresh(order)
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "order-service"

def test_get_order_success(client):
    response = client.get("/orders/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["user_id"] == "user_123"
    assert float(data["total_amount"]) == 199.98
    assert data["status"] == "PENDING"

def test_get_order_not_found(client):
    response = client.get("/orders/999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

@patch("httpx.AsyncClient.get")
def test_create_order_success(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 1,
        "name": "Test Laptop",
        "price": "99.99",
        "stock": 10
    }
    mock_get.return_value = mock_resp

    payload = {
        "user_id": "test_user",
        "product_id": 1,
        "quantity": 3
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "test_user"
    assert data["product_id"] == 1
    assert data["quantity"] == 3
    assert float(data["total_amount"]) == 299.97
    assert data["status"] == "PENDING"

@patch("httpx.AsyncClient.get")
def test_create_order_product_not_found(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    payload = {
        "user_id": "test_user",
        "product_id": 9999,
        "quantity": 1
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"].lower()

@patch("httpx.AsyncClient.get")
def test_create_order_insufficient_stock(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 1,
        "name": "Test Laptop",
        "price": "100.00",
        "stock": 2
    }
    mock_get.return_value = mock_resp

    payload = {
        "user_id": "test_user",
        "product_id": 1,
        "quantity": 5
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    assert "insufficient stock" in response.json()["detail"].lower()

def test_create_order_invalid_quantity(client):
    payload = {
        "user_id": "test_user",
        "product_id": 1,
        "quantity": 0  # Invalid
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 422

def test_update_order_status(client):
    response = client.patch("/orders/1/status", json={"status": "PAID"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PAID"
