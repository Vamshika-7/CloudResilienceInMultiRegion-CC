import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add service directory to sys.path
service_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(service_dir))

from main import app
from database import Base, get_db
from models import Product
from sqlalchemy.pool import StaticPool

# Create isolated test database
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, poolclass=StaticPool, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        # Seed a test product
        p = Product(name="Test Gadget", description="A test gadget", price=49.99, stock=10)
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
    assert data["service"] == "product-service"

def test_list_products(client):
    response = client.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) >= 1
    assert products[0]["name"] == "Test Gadget"

def test_get_product_success(client):
    response = client.get("/products/1")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == 1
    assert product["name"] == "Test Gadget"
    assert float(product["price"]) == 49.99

def test_get_product_not_found(client):
    response = client.get("/products/9999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_create_product(client):
    payload = {
        "name": "New Gaming Mouse",
        "description": "Ergonomic gaming mouse",
        "price": 29.99,
        "stock": 15
    }
    response = client.post("/products", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "New Gaming Mouse"
    assert created["id"] is not None
