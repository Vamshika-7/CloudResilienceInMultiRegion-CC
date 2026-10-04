# Empirical Resilience Evaluation of Multi-Region Cloud Architectures under Orchestration Chaos Injections

> **Milestone 1**: Working Local E-Commerce Microservices Application Testbed  
> *Note: This milestone establishes the baseline microservices application locally. Kubernetes, K3s, Istio, Chaos Mesh, JMeter, Prometheus, Grafana, AWS, and multi-region deployment will be implemented in later milestones.*

---

## 1. Project Overview

This project serves as the empirical testbed for evaluating the resilience and fault tolerance of multi-region cloud architectures subjected to orchestration-layer chaos injections. 

**Milestone 1** focuses strictly on building a clean, reliable, and observable e-commerce microservices application locally. The application features independent services that communicate exclusively via REST/HTTP and persist transactional state in PostgreSQL. The design avoids tight coupling and hardcoded addresses to allow containerization (Docker) and deployment across dual K3s clusters in subsequent milestones.

---

## 2. Architecture

```text
               +----------------------------------+
               |     React Frontend (Vite)        |
               |       http://localhost:5173      |
               +-----------------+----------------+
                                 |
                                 | REST / HTTP
                                 v
               +----------------------------------+
               |      FastAPI API Gateway         |
               |       http://localhost:8000      |
               +--------+--------+--------+-------+
                        |        |        |
         +--------------+        |        +---------------+
         | /api/products         | /api/orders            | /api/payments
         v                       v                        v
+------------------+    +------------------+    +------------------+
| Product Service  |    |  Order Service   |    | Payment Service  |
|  Port 8001       |    |   Port 8002      |    |   Port 8003      |
+--------+---------+    +---+---------+----+    +---------+--------+
         |                  |         |                   |
         |                  |         +--- sync status ---+
         |                  |              (PATCH status)
         |                  |
         +------------------+-----------------------------+
                                     |
                                     v
                       +---------------------------+
                       |    PostgreSQL Database    |
                       |    localhost:5432         |
                       |    (DB: ecommerce)        |
                       +---------------------------+
```

### Key Architectural Characteristics
- **De-coupled Microservices**: Each service runs as an independent FastAPI process with its own data models and routing.
- **Unified API Gateway**: The frontend communicates solely with the API Gateway on port 8000. The Gateway handles request proxying, request tracing (`X-Request-ID`), error standardisation, and CORS.
- **Service-to-Service HTTP Communication**: When an order is placed, the Order Service directly calls the Product Service (`GET /products/{id}`) to verify stock availability and retrieve the authoritative unit price.
- **Simulated Payment Processing**: The Payment Service simulates transactions and records payment events (`SUCCESS` or `FAILED`), then notifies the Order Service to update the order status.
- **Observability**: Every service provides a `/health` endpoint, emits structured logs, and generates or propagates request tracking IDs.

---

## 3. Technology Stack

- **Frontend**: React 18, Vite 5, JavaScript (ES modules), Native CSS
- **Backend**: Python 3.11+ / 3.14+, FastAPI, Uvicorn, Starlette
- **HTTP Client**: HTTPX (async client for inter-service communication)
- **Database**: PostgreSQL 16 (Relational DB engine)
- **ORM & Drivers**: SQLAlchemy 2.0, `psycopg` (v3), `psycopg2-binary`
- **Validation**: Pydantic v2
- **Testing**: Pytest, FastAPI TestClient

---

## 4. Folder Structure

```text
CC/
├── .env                          # Local environment variables
├── .env.example                  # Template of environment variables
├── .gitignore                    # Git ignore file for Python, Node, and PG artifacts
├── docker-compose.yml            # Docker Compose specification (Milestone 2 ready)
├── README.md                     # Project documentation
│
├── database/
│   ├── init/
│   │   └── init.sql              # PostgreSQL DDL table schemas
│   ├── seed/
│   │   └── seed.sql              # Seed SQL script for sample catalog
│   └── init_db.py                # Automated SQLAlchemy migration & seeding script
│
├── gateway/
│   ├── config.py                 # Gateway environment configuration
│   ├── main.py                   # FastAPI API Gateway with proxy routing & CORS
│   ├── requirements.txt          # Gateway Python dependencies
│   ├── Dockerfile                # Docker container build definition
│   └── tests/
│       ├── __init__.py
│       └── test_gateway.py       # Gateway unit and routing tests
│
├── services/
│   ├── product-service/
│   │   ├── config.py             # Product service configuration
│   │   ├── database.py           # DB engine and session factory
│   │   ├── models.py             # SQLAlchemy models for products
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   ├── main.py               # FastAPI product catalog application
│   │   ├── requirements.txt      # Product service dependencies
│   │   ├── Dockerfile            # Container build definition
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_product.py   # Product service tests
│   │
│   ├── order-service/
│   │   ├── config.py             # Order service configuration
│   │   ├── database.py           # DB engine and session factory
│   │   ├── models.py             # SQLAlchemy models for orders
│   │   ├── schemas.py            # Pydantic schemas for orders
│   │   ├── main.py               # FastAPI order placement & stock validation
│   │   ├── requirements.txt      # Order service dependencies
│   │   ├── Dockerfile            # Container build definition
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_order.py     # Order service tests
│   │
│   └── payment-service/
│       ├── config.py             # Payment service configuration
│       ├── database.py           # DB engine and session factory
│       ├── models.py             # SQLAlchemy models for payments
│       ├── schemas.py            # Pydantic schemas for payments
│       ├── main.py               # FastAPI payment simulation & status sync
│       ├── requirements.txt      # Payment service dependencies
│       ├── Dockerfile            # Container build definition
│       └── tests/
│           ├── __init__.py
│           └── test_payment.py   # Payment service tests
│
├── frontend/
│   ├── package.json              # NPM dependencies and scripts
│   ├── vite.config.js            # Vite configuration
│   ├── index.html                # HTML document entry
│   └── src/
│       ├── main.jsx              # React mounting script
│       ├── App.jsx               # Main stateful application UI
│       ├── index.css             # UI styling
│       ├── api.js                # API Gateway client module
│       └── components/
│           ├── Products.jsx      # Product catalog list
│           ├── Orders.jsx        # Order creation form and orders table
│           ├── PaymentModal.jsx  # Payment processing and chaos simulation modal
│           └── OrderDetailsModal.jsx # Detailed single-order inspector
│
└── scripts/
    ├── setup_postgres.ps1        # Automated portable PostgreSQL downloader & initializer
    ├── stop_postgres.ps1         # Gracefully stop PostgreSQL server
    ├── start_all.ps1             # Start all microservices, gateway, and frontend
    ├── stop_all.ps1              # Stop all running microservices and gateway
    └── run_tests.ps1             # Run pytest test suites across all services
```

---

## 5. Prerequisites

Before running the application, make sure you have:
1. **Python**: 3.11 or newer (Python 3.14 verified)
2. **Node.js**: v18 or newer (Node v24 with npm 11 verified)
3. **PowerShell** (on Windows) or Bash (on Linux/macOS)
4. **Internet connection** for initial package retrieval

---

## 6. PostgreSQL Setup

Database configuration is completely driven by environment variables. No credentials are hardcoded.

### Automated Setup (Zero Admin Rights Needed)
The repository includes `scripts/setup_postgres.ps1`. If PostgreSQL is not installed on your Windows machine, this script automatically downloads portable PostgreSQL 16 binaries to `~/.pgsql`, initializes a data cluster with user `postgres`, creates database `ecommerce`, and starts the database on port `5432`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_postgres.ps1
```

### Manual or Existing PostgreSQL Setup
If you already have PostgreSQL running:
1. Create a database named `ecommerce`:
   ```sql
   CREATE DATABASE ecommerce;
   ```
2. Initialize tables and seed products:
   ```bash
   python database/init_db.py
   ```
   *(Or execute `database/init/init.sql` followed by `database/seed/seed.sql` using `psql`)*

---

## 7. Backend Setup

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux / macOS:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r services/product-service/requirements.txt
   pip install psycopg[binary]
   ```

3. Ensure your `.env` file exists:
   ```bash
   cp .env.example .env
   ```

---

## 8. Frontend Setup

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Build or verify the frontend bundle:
   ```bash
   npm run build
   ```

---

## 9. Environment Variables

All services load configurations from environment variables or `.env`.

| Variable | Default Value | Description |
|---|---|---|
| `DB_HOST` | `localhost` | PostgreSQL server host |
| `DB_PORT` | `5432` | PostgreSQL server port |
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `DB_NAME` | `ecommerce` | PostgreSQL database name |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/ecommerce` | Full SQLAlchemy connection string |
| `GATEWAY_PORT` | `8000` | Port for API Gateway |
| `PRODUCT_SERVICE_PORT` | `8001` | Port for Product Service |
| `ORDER_SERVICE_PORT` | `8002` | Port for Order Service |
| `PAYMENT_SERVICE_PORT` | `8003` | Port for Payment Service |
| `PRODUCT_SERVICE_URL` | `http://localhost:8001` | Product Service base URL (used by Gateway & Order Service) |
| `ORDER_SERVICE_URL` | `http://localhost:8002` | Order Service base URL (used by Gateway & Payment Service) |
| `PAYMENT_SERVICE_URL` | `http://localhost:8003` | Payment Service base URL (used by Gateway) |
| `VITE_API_GATEWAY_URL` | `http://localhost:8000/api` | API Gateway endpoint accessed by Frontend |

---

## 10. How to Run Each Service

### Option A: Run All Services Together (One Command)
Run the PowerShell orchestrator:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1
```
To stop all services:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_all.ps1
```

### Option B: Run Services Individually

1. **Start PostgreSQL**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\setup_postgres.ps1
   ```

2. **Start Product Service (Terminal 1)**:
   ```bash
   cd services/product-service
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

3. **Start Order Service (Terminal 2)**:
   ```bash
   cd services/order-service
   uvicorn main:app --host 0.0.0.0 --port 8002 --reload
   ```

4. **Start Payment Service (Terminal 3)**:
   ```bash
   cd services/payment-service
   uvicorn main:app --host 0.0.0.0 --port 8003 --reload
   ```

5. **Start API Gateway (Terminal 4)**:
   ```bash
   cd gateway
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Start Frontend (Terminal 5)**:
   ```bash
   cd frontend
   npm run dev
   ```

The application UI is accessible at: **`http://localhost:5173`**

---

## 11. API Endpoints

### API Gateway (`http://localhost:8000`)
- `GET /health`: Overall system and downstream services health
- `GET /api/products`: Retrieve all products
- `GET /api/products/{id}`: Retrieve single product details
- `POST /api/orders`: Place a new order
- `GET /api/orders`: Retrieve list of all orders
- `GET /api/orders/{id}`: Retrieve order details by ID
- `POST /api/payments`: Process order payment
- `GET /api/payments/{id}`: Retrieve payment details
- `GET /api/payments/order/{id}`: Retrieve payment record for an order

### Individual Service Endpoints & Swagger Documentation
Each FastAPI service provides automatic Swagger/OpenAPI documentation:
- **API Gateway Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Product Service Swagger**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Order Service Swagger**: [http://localhost:8002/docs](http://localhost:8002/docs)
- **Payment Service Swagger**: [http://localhost:8003/docs](http://localhost:8003/docs)

---

## 12. Example Requests

### 1. Health Check
```bash
curl -X GET http://localhost:8000/health
```
**Response**:
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "downstream_services": {
    "product_service": "healthy",
    "order_service": "healthy",
    "payment_service": "healthy"
  }
}
```

### 2. Get Products Catalog
```bash
curl -X GET http://localhost:8000/api/products
```

### 3. Create an Order
```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_demo",
    "product_id": 1,
    "quantity": 2
  }'
```
**Response (201 Created)**:
```json
{
  "id": 1,
  "user_id": "user_demo",
  "product_id": 1,
  "quantity": 2,
  "total_amount": "2599.98",
  "status": "PENDING",
  "created_at": "2026-10-04T17:46:06.148651+05:30"
}
```

### 4. Process Payment (Success)
```bash
curl -X POST http://localhost:8000/api/payments \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "amount": 2599.98
  }'
```
**Response (200 OK)**:
```json
{
  "id": 1,
  "order_id": 1,
  "amount": "2599.98",
  "status": "SUCCESS",
  "payment_method": "SIMULATED_CARD",
  "created_at": "2026-10-04T17:46:43.258451+05:30"
}
```

### 5. Simulate Payment Failure (Chaos Testing)
```bash
curl -X POST http://localhost:8000/api/payments \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "amount": 2599.98,
    "simulate_failure": true
  }'
```
**Response (200 OK)**:
```json
{
  "id": 2,
  "order_id": 1,
  "amount": "2599.98",
  "status": "FAILED",
  "payment_method": "SIMULATED_CARD",
  "created_at": "2026-10-04T17:47:02.725448+05:30"
}
```

---

## 13. How to Run Tests

Run the test suite script to execute all unit and integration tests across services:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1
```

Or run tests for individual services directly:
```bash
# Product Service tests (5 tests)
python -m pytest services/product-service/tests -v

# Order Service tests (8 tests)
python -m pytest services/order-service/tests -v

# Payment Service tests (6 tests)
python -m pytest services/payment-service/tests -v

# API Gateway tests (4 tests)
python -m pytest gateway/tests -v
```

All 23 tests pass with isolated in-memory test databases and mock downstream service handlers.

---

## 14. Troubleshooting

1. **Port 5432 already in use**:
   - Check if an existing PostgreSQL instance is running: `pg_isready -p 5432`.
   - Update `DB_PORT` in `.env` if using a non-standard port.
2. **Cannot connect to database (`Connection refused` / `timeout`)**:
   - Verify PostgreSQL status using `& "$HOME\.pgsql\pgsql\bin\pg_isready.exe" -p 5432`.
   - Run `powershell -File .\scripts\setup_postgres.ps1` to ensure the local server is started.
3. **Product Service returns 404 on order creation**:
   - Verify that seed data was populated by running `python database/init_db.py`.
4. **CORS errors in browser**:
   - Ensure you are sending requests to the API Gateway (`http://localhost:8000/api`), not directly to microservice ports.
   - The Gateway has `CORSMiddleware` configured with `allow_origins=["*"]`.

---

## 15. Future Milestones

This repository is structured for subsequent research milestones:

- **Milestone 2**: Containerization with Docker & Multi-stage container optimization.
- **Milestone 3**: Orchestration deployment using K3s across two virtual clusters.
- **Milestone 4**: Multi-region service mesh configuration using Istio (traffic routing, failover, virtual services).
- **Milestone 5**: Chaos engineering testbed deployment using Chaos Mesh (pod failure, network latency, partition).
- **Milestone 6**: Distributed performance profiling & benchmark generation using Apache JMeter.
- **Milestone 7**: Telemetry and metrics aggregation using Prometheus & Grafana dashboards.
- **Milestone 8**: Empirical data analysis, resilience metric calculations, and research publication write-up.
