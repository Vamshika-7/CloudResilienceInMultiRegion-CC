import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add service directory to sys.path
service_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(service_dir))

from main import app
from database import Base, get_db
from models import Payment
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, poolclass=StaticPool, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        p = Payment(order_id=1, amount=99.99, status="SUCCESS", payment_method="SIMULATED_CARD")
        db.add(p)
        db.commit()
        db.refresh(p)
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
    assert data["service"] == "payment-service"

@patch("httpx.AsyncClient.patch")
def test_process_payment_success(mock_patch, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_patch.return_value = mock_resp

    payload = {
        "order_id": 10,
        "amount": 150.00,
        "simulate_failure": False
    }
    response = client.post("/payments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == 10
    assert float(data["amount"]) == 150.00
    assert data["status"] == "SUCCESS"
    assert data["id"] is not None

@patch("httpx.AsyncClient.patch")
def test_process_payment_simulated_failure(mock_patch, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_patch.return_value = mock_resp

    payload = {
        "order_id": 10,
        "amount": 150.00,
        "simulate_failure": True
    }
    response = client.post("/payments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == 10
    assert data["status"] == "FAILED"

def test_process_payment_invalid_amount(client):
    payload = {
        "order_id": 10,
        "amount": -5.00
    }
    response = client.post("/payments", json=payload)
    assert response.status_code == 422  # validation error from pydantic (amount > 0)

def test_get_payment_success(client):
    response = client.get("/payments/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["order_id"] == 1
    assert data["status"] == "SUCCESS"

def test_get_payment_not_found(client):
    response = client.get("/payments/999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
