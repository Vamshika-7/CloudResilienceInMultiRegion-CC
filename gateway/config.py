import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("GATEWAY_PORT", 8000))

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001").rstrip('/')
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002").rstrip('/')
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003").rstrip('/')
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ecommerce")
