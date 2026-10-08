# Empirical Resilience Evaluation of Multi-Region Cloud Architectures under Orchestration Chaos Injections

> **Milestone 3**: Deployment to Local K3s / Kubernetes Environment  
> *Note: This milestone establishes single-cluster Kubernetes orchestration, manifests, persistent storage, health probes, and ingress routing. Multi-cluster federation, Istio service mesh, Chaos Mesh, JMeter, Prometheus, Grafana, and multi-region chaos experiments will be implemented in subsequent milestones.*

---

## 1. Project Overview

This project serves as the empirical testbed for evaluating the resilience and fault tolerance of multi-region cloud architectures subjected to orchestration-layer chaos injections.

**Milestone 2** transitions the local microservices application into a fully containerized, production-aligned Docker Compose testbed. All services run as isolated containers within a private bridge network (`ecommerce-net`), resolving each other strictly via Docker DNS service names rather than `localhost`.

### Key Milestone 2 Capabilities
- **Complete Docker Compose Stack**: Single-command startup (`docker compose up --build`).
- **Containerized Frontend**: Multi-stage production build (Node.js build stage + Nginx Alpine runtime) serving static assets and reverse-proxying API calls to the Gateway.
- **Service Name DNS Networking**: Inter-service communication uses Docker service names (`product-service`, `order-service`, `payment-service`, `postgres`, `gateway`).
- **Zero Localhost Coupling**: Backend-to-backend communication contains zero hardcoded localhost dependencies; all URLs and database credentials are environment-driven.
- **Persistent Database Storage**: PostgreSQL runs as an Alpine container with a named volume (`postgres_data`) and automatic initialization/seeding.
- **Deterministic Health Checks**: Healthchecks are configured across all services with `depends_on` conditions (`service_healthy`) ensuring race-condition-free startup ordering.

---

## 2. Container Architecture & Networking

```text
Host Browser / Client (http://localhost:5173 or http://localhost:8000)
                              │
       ┌──────────────────────┴──────────────────────┐
       │ (Port 5173)                                 │ (Port 8000)
       ▼                                             ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│      ecommerce-frontend      │              │      ecommerce-gateway       │
│      (Nginx Alpine: 80)      │              │       (FastAPI: 8000)        │
│  - Static React UI           │              │  - Observability & Logging   │
│  - Reverse Proxy:            │              │  - Error Normalization       │
│    /api/  ──► gateway:8000   │─────────────►│  - Request ID Tracing        │
│    /health ─► gateway:8000   │              │  - Reverse Proxy / Router    │
└──────────────────────────────┘              └──────┬───────┬───────┬───────┘
                                                     │       │       │
                     ┌───────────────────────────────┘       │       └───────────────────────────────┐
                     │ http://product-service:8001           │ http://order-service:8002             │ http://payment-service:8003
                     ▼                                       ▼                                       ▼
       ┌──────────────────────────────┐       ┌──────────────────────────────┐       ┌──────────────────────────────┐
       │  ecommerce-product-service   │       │   ecommerce-order-service    │       │  ecommerce-payment-service   │
       │       (FastAPI: 8001)        │◄──────│       (FastAPI: 8002)        │◄──────│       (FastAPI: 8003)        │
       │  - Catalog Management        │  REST │  - Order Placement Logic     │ PATCH │  - Payment Simulation        │
       │  - Product Lookup & Stock    │       │  - Product Price/Stock Sync  │ Order │  - Status Callback Sync      │
       └──────────────┬───────────────┘       └──────────────┬───────────────┘ Status└──────────────┬───────────────┘
                      │                                      │                                      │
                      │ postgresql://postgres@postgres:5432  │ postgresql://postgres@postgres:5432  │ postgresql://postgres@postgres:5432
                      └──────────────────────────────┐       │       ┌──────────────────────────────┘
                                                     ▼       ▼       ▼
                                      ┌──────────────────────────────────────────────┐
                                      │              ecommerce-postgres              │
                                      │             (Postgres 16 Alpine)             │
                                      │  - Database: ecommerce                       │
                                      │  - Persistent Volume: postgres_data          │
                                      │  - DDL Init & Seed: docker-entrypoint-initdb │
                                      └──────────────────────────────────────────────┘
                                          All containers on Docker network:
                                                   ecommerce-net
```

### Docker Service DNS Resolution Table

| Communicating Pair | Source Container | Destination Target | Protocol / Port | Configuration Variable |
|---|---|---|---|---|
| Frontend → Gateway | `frontend` | `http://gateway:8000` | HTTP / 8000 | Nginx `proxy_pass` |
| Gateway → Product Service | `gateway` | `http://product-service:8001` | HTTP / 8001 | `PRODUCT_SERVICE_URL` |
| Gateway → Order Service | `gateway` | `http://order-service:8002` | HTTP / 8002 | `ORDER_SERVICE_URL` |
| Gateway → Payment Service | `gateway` | `http://payment-service:8003` | HTTP / 8003 | `PAYMENT_SERVICE_URL` |
| Order Service → Product Service | `order-service` | `http://product-service:8001` | HTTP / 8001 | `PRODUCT_SERVICE_URL` |
| Payment Service → Order Service | `payment-service` | `http://order-service:8002` | HTTP / 8002 | `ORDER_SERVICE_URL` |
| Product Service → PostgreSQL | `product-service` | `postgres:5432` | TCP / 5432 | `DB_HOST` / `DATABASE_URL` |
| Order Service → PostgreSQL | `order-service` | `postgres:5432` | TCP / 5432 | `DB_HOST` / `DATABASE_URL` |
| Payment Service → PostgreSQL | `payment-service` | `postgres:5432` | TCP / 5432 | `DB_HOST` / `DATABASE_URL` |

---

## 3. Technology Stack

- **Containerization**: Docker, Docker Compose (Compose Spec v3.8)
- **Base Images**:
  - Backend Services & Gateway: `python:3.11-slim`
  - Frontend Build: `node:20-alpine`
  - Frontend Web Server: `nginx:alpine`
  - Database: `postgres:16-alpine`
- **Frontend**: React 18, Vite 5, JavaScript (ES modules), Native CSS
- **Backend Services**: Python 3.11+, FastAPI, Uvicorn, HTTPX, SQLAlchemy 2.0, Psycopg
- **Testing**: Pytest, FastAPI TestClient

---

## 4. Folder Structure

```text
CC/
├── .dockerignore                 # Root Docker ignore rules (pycache, env, venv, git)
├── .env                          # Local environment variables
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore file
├── docker-compose.yml            # Docker Compose multi-service definition
├── README.md                     # Project documentation
│
├── database/
│   ├── init/
│   │   └── init.sql              # PostgreSQL DDL table schemas (mounted into Postgres)
│   ├── seed/
│   │   └── seed.sql              # Seed SQL script for sample catalog
│   └── init_db.py                # Standalone SQLAlchemy migration & seeding script
│
├── gateway/
│   ├── config.py                 # Gateway environment configuration
│   ├── main.py                   # FastAPI API Gateway with proxy routing & CORS
│   ├── requirements.txt          # Gateway Python dependencies
│   ├── Dockerfile                # Python 3.11-slim container definition
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
│   │   ├── Dockerfile            # Python 3.11-slim container definition
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
│   │   ├── Dockerfile            # Python 3.11-slim container definition
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
│       ├── Dockerfile            # Python 3.11-slim container definition
│       └── tests/
│           ├── __init__.py
│           └── test_payment.py   # Payment service tests
│
├── frontend/
│   ├── .dockerignore             # Frontend Docker ignore (node_modules, dist)
│   ├── Dockerfile                # Multi-stage Dockerfile (Node build + Nginx runtime)
│   ├── nginx.conf                # Nginx reverse-proxy routing /api/ and /health to gateway
│   ├── package.json              # NPM dependencies and scripts
│   ├── vite.config.js            # Vite configuration with local proxy
│   ├── index.html                # HTML document entry
│   └── src/
│       ├── main.jsx              # React mounting script
│       ├── App.jsx               # Stateful e-commerce UI
│       ├── index.css             # Styling
│       ├── api/
│       │   └── client.js         # Deployment-independent relative API client
│       └── components/
│           ├── Products.jsx      # Catalog list component
│           ├── Orders.jsx        # Order creation and list component
│           ├── PaymentModal.jsx  # Payment modal with chaos failure toggle
│           └── OrderDetailsModal.jsx # Single-order inspector modal
│
└── scripts/
    ├── verify_docker_compose.py  # Automated Compose spec and networking validator
    ├── run_tests.ps1             # Pytest test suites runner across all services
    ├── setup_postgres.ps1        # Standalone local PostgreSQL setup script
    ├── start_all.ps1             # Standalone local microservices starter script
    └── stop_all.ps1              # Standalone local microservices stopper script
```

---

## 5. Running with Docker Compose (Recommended)

### Step 1: Validate Compose Specification
Run the automated Docker Compose validation script:
```bash
python scripts/verify_docker_compose.py
```
Or with the Docker CLI:
```bash
docker compose config
```

### Step 2: Build and Start Stack
Build and launch all 6 containerized services in detached mode:
```bash
docker compose up --build -d
```
Or run in the foreground to monitor live container logs:
```bash
docker compose up --build
```

### Step 3: Verify Container Health
Check container statuses and healthchecks:
```bash
docker compose ps
```
Expected output:
```text
NAME                        STATUS                    PORTS
ecommerce-postgres          Up (healthy)              0.0.0.0:5432->5432/tcp
ecommerce-product-service   Up (healthy)              0.0.0.0:8001->8001/tcp
ecommerce-order-service     Up (healthy)              0.0.0.0:8002->8002/tcp
ecommerce-payment-service   Up (healthy)              0.0.0.0:8003->8003/tcp
ecommerce-gateway           Up (healthy)              0.0.0.0:8000->8000/tcp
ecommerce-frontend          Up (healthy)              0.0.0.0:5173->80/tcp
```

### Step 4: Access Applications
- **React Frontend**: [http://localhost:5173](http://localhost:5173)
- **API Gateway**: [http://localhost:8000](http://localhost:8000)
- **API Gateway Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Product Service Swagger**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Order Service Swagger**: [http://localhost:8002/docs](http://localhost:8002/docs)
- **Payment Service Swagger**: [http://localhost:8003/docs](http://localhost:8003/docs)

### Step 5: Stop the Docker Stack
To gracefully stop all containers:
```bash
docker compose down
```
To stop all containers and remove the persistent PostgreSQL volume:
```bash
docker compose down -v
```

---

## 6. End-to-End API Verification

Execute these verification commands against the running stack:

### 1. Gateway Health Check (Checks All Downstreams)
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

### 2. Retrieve Product Catalog
```bash
curl -X GET http://localhost:8000/api/products
```

### 3. Retrieve Single Product
```bash
curl -X GET http://localhost:8000/api/products/1
```

### 4. Create an Order
```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": "docker_tester", "product_id": 1, "quantity": 1}'
```
**Response**:
```json
{
  "id": 1,
  "user_id": "docker_tester",
  "product_id": 1,
  "quantity": 1,
  "total_amount": 1299.99,
  "status": "PENDING",
  "created_at": "..."
}
```

### 5. Lookup Order by ID
```bash
curl -X GET http://localhost:8000/api/orders/1
```

### 6. Process Payment for Order
```bash
curl -X POST http://localhost:8000/api/payments \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1, "amount": 1299.99}'
```
**Response**:
```json
{
  "id": 1,
  "order_id": 1,
  "amount": 1299.99,
  "status": "SUCCESS",
  "payment_method": "SIMULATED_CARD",
  "created_at": "..."
}
```

### 7. Verify Order Status Updated to PAID
```bash
curl -X GET http://localhost:8000/api/orders/1
```
The status reflects `PAID` via the inter-service callback from Payment Service to Order Service.

### 8. Verify Frontend Gateway Proxy
```bash
curl -X GET http://localhost:5173/api/products
curl -X GET http://localhost:5173/health
```
Both endpoints respond identically through the Nginx reverse-proxy on port 5173.

---

## 7. Running Backend Unit & Integration Tests

The test suite covers unit and integration tests across all microservices and the API Gateway (23 total tests).

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1
```

Or run pytest per service:
```bash
python -m pytest services/product-service/tests -v
python -m pytest services/order-service/tests -v
python -m pytest services/payment-service/tests -v
python -m pytest gateway/tests -v
```

All 23 tests execute in an isolated environment with in-memory SQLite / mock client fixtures and require no running background containers.

---

## 8. Docker Healthcheck Specifications

| Container | Healthcheck Test Command | Interval | Timeout | Retries | Start Period |
|---|---|---|---|---|---|
| `postgres` | `pg_isready -U postgres -d ecommerce` | 5s | 5s | 5 | 5s |
| `product-service` | `urllib.request.urlopen('http://localhost:8001/health')` | 5s | 5s | 5 | 5s |
| `order-service` | `urllib.request.urlopen('http://localhost:8002/health')` | 5s | 5s | 5 | 5s |
| `payment-service` | `urllib.request.urlopen('http://localhost:8003/health')` | 5s | 5s | 5 | 5s |
| `gateway` | `urllib.request.urlopen('http://localhost:8000/health')` | 5s | 5s | 5 | 10s |
| `frontend` | `wget -q --spider http://localhost:80/` | 5s | 5s | 5 | 5s |

### Startup Dependency Ordering
```text
postgres (healthy)
   ├──► product-service (healthy)
   │       └──► order-service (healthy)
   │               └──► payment-service (healthy)
   │                       └──► gateway (healthy)
   │                               └──► frontend (healthy)
```

---

## 9. Kubernetes (K3s) Architecture & Deployment (Milestone 3)

Milestone 3 deploys the complete e-commerce testbed to a local K3s cluster (`ecommerce`), using declarative Kubernetes manifests located in the `k8s/` directory.

### Kubernetes Architecture

```text
Browser / Client (http://localhost:5173 or http://localhost:8000)
                              │
        ┌─────────────────────┴─────────────────────┐
        │ Port 5173                                 │ Port 8000
        ▼                                           ▼
┌─────────────────────────────┐           ┌─────────────────────────────┐
│   Ingress (ecommerce-ingress)│           │   Service: gateway          │
│   (Traefik / Port 80)       │           │   (Type: LoadBalancer 8000) │
└──────────────┬──────────────┘           └──────────────┬──────────────┘
               │                                         │
               ▼                                         ▼
┌─────────────────────────────┐           ┌─────────────────────────────┐
│   Service: frontend         │           │   Deployment: gateway       │
│   (Type: ClusterIP 80)      │           │   (cc-gateway:latest)       │
│   Deployment: frontend      │           └──────┬───────┬───────┬──────┘
│   (Nginx reverse proxy)     │                  │       │       │
│   - /      ──► Static UI    │                  │       │       │
│   - /api/  ──► gateway:8000 ├──────────────────┘       │       │
│   - /health──► gateway:8000 │                          │       │
└─────────────────────────────┘                          │       │
                                                         │       │
               ┌─────────────────────────────────────────┘       │       └─────────────────────────┐
               │ http://product-service:8001                     │ http://order-service:8002       │ http://payment-service:8003
               ▼                                                 ▼                                 ▼
┌─────────────────────────────┐                   ┌─────────────────────────────┐   ┌─────────────────────────────┐
│  Service: product-service   │                   │   Service: order-service    │   │  Service: payment-service   │
│  (Type: ClusterIP 8001)     │                   │   (Type: ClusterIP 8002)    │   │  (Type: ClusterIP 8003)     │
│  Deployment: product-service│◄──────────────────┤   Deployment: order-service │◄──┤  Deployment: payment-service│
│  (cc-product-service:latest)│       REST        │   (cc-order-service:latest) │   │  (cc-payment-service:latest)│
└──────────────┬──────────────┘                   └──────────────┬──────────────┘   └──────────────┬──────────────┘
               │                                                 │                                 │
               │ postgresql://postgres@postgres:5432             │                                 │
               └─────────────────────────────────────────┐       │       ┌─────────────────────────┘
                                                         ▼       ▼       ▼
                                          ┌─────────────────────────────────────────────┐
                                          │              Service: postgres              │
                                          │            (ClusterIP Port 5432)            │
                                          │            Deployment: postgres             │
                                          │            (postgres:16-alpine)             │
                                          │  - PersistentVolumeClaim: postgres-pvc      │
                                          │  - ConfigMap: postgres-init-scripts         │
                                          └─────────────────────────────────────────────┘
                                                All resources in namespace: ecommerce
```

### Kubernetes Manifests Structure (`k8s/`)

- `k8s/00-namespace.yaml`: Defines dedicated `ecommerce` namespace.
- `k8s/01-configmap-secret.yaml`:
  - `Secret: ecommerce-secrets`: Database credentials and connection string (`DB_USER`, `DB_PASSWORD`, `DATABASE_URL`).
  - `ConfigMap: ecommerce-config`: Service hostnames, ports, and inter-service URLs using Kubernetes Service DNS.
  - `ConfigMap: postgres-init-scripts`: DDL schema (`01-init.sql`) and sample catalog (`02-seed.sql`).
- `k8s/02-postgres.yaml`: `PersistentVolumeClaim: postgres-pvc` (1Gi backed by K3s `local-path` storage), PostgreSQL Deployment, and Service (`postgres:5432`).
- `k8s/03-product-service.yaml`: Deployment and ClusterIP Service (`product-service:8001`) with HTTP `/health` probes.
- `k8s/04-order-service.yaml`: Deployment and ClusterIP Service (`order-service:8002`) with HTTP `/health` probes.
- `k8s/05-payment-service.yaml`: Deployment and ClusterIP Service (`payment-service:8003`) with HTTP `/health` probes.
- `k8s/06-gateway.yaml`: Deployment and LoadBalancer Service (`gateway:8000`) exposing host port 8000 with HTTP `/health` probes.
- `k8s/07-frontend.yaml`: Deployment and ClusterIP Service (`frontend:80`) with HTTP liveness/readiness probes.
- `k8s/08-ingress.yaml`: Ingress resource (`ecommerce-ingress`) routing external traffic on port 80 (mapped to host 5173) to `frontend:80`.

### Deploying to K3s

#### Step 1: Apply All Manifests
```bash
kubectl apply -f k8s/
```

#### Step 2: Verify Pod and Service Status
```bash
kubectl get pods,svc,pvc,ingress -n ecommerce -o wide
```
All 6 pods will transition to `Running` (1/1) and pass readiness probes.

#### Step 3: Run Manifest Validation Script
```bash
python scripts/verify_k8s.py
```

#### Step 4: Run End-to-End Test Suite
```bash
python scripts/verify_k8s_e2e.py
```
This script exercises:
1. API Gateway `/health` check verifying downstream connectivity.
2. Frontend static bundle delivery via Ingress on port 5173.
3. Frontend reverse proxy `/health` and `/api/products` routing.
4. Order placement (`POST /api/orders`) and persistence in PostgreSQL.
5. Order lookup (`GET /api/orders/{id}`).
6. Successful payment processing (`POST /api/payments`) and order state transition to `PAID`.
7. Simulated chaos payment failure (`simulate_failure: true`) and order state transition to `FAILED`.

---

## 10. Future Milestones Roadmap

- **Milestone 4**: Multi-region service mesh configuration using Istio (traffic routing, failover, virtual services).
- **Milestone 5**: Chaos engineering testbed deployment using Chaos Mesh (pod failure, network latency, partition).
- **Milestone 6**: Distributed performance profiling & benchmark generation using Apache JMeter.
- **Milestone 7**: Telemetry and metrics aggregation using Prometheus & Grafana dashboards.
- **Milestone 8**: Empirical data analysis, resilience metric calculations, and research publication write-up.

