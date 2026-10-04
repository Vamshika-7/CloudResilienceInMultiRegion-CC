import logging
import uuid
import time
from typing import Optional, Any
import httpx
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import PORT, PRODUCT_SERVICE_URL, ORDER_SERVICE_URL, PAYMENT_SERVICE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [api-gateway] %(message)s"
)
logger = logging.getLogger("api-gateway")

app = FastAPI(
    title="API Gateway",
    description="Lightweight routing gateway for E-Commerce microservices architecture",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = req_id
    start_time = time.time()
    
    logger.info(f"[{req_id}] INCOMING {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        logger.info(f"[{req_id}] COMPLETED {request.method} {request.url.path} -> Status {response.status_code} ({duration_ms}ms)")
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[{req_id}] FAILED {request.method} {request.url.path} ({duration_ms}ms): {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "API Gateway internal error", "request_id": req_id},
            headers={"X-Request-ID": req_id}
        )

async def proxy_request(
    service_base_url: str,
    target_path: str,
    request: Request,
    timeout: float = 8.0
) -> Response:
    """Forward incoming HTTP request to designated microservice and stream back response."""
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    target_url = f"{service_base_url}{target_path}"
    
    # Filter and propagate headers
    forward_headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in ["host", "content-length"]
    }
    forward_headers["X-Request-ID"] = req_id
    
    body = await request.body()
    query_params = dict(request.query_params)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=forward_headers,
                params=query_params,
                content=body
            )
            
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers={
                    "Content-Type": resp.headers.get("Content-Type", "application/json"),
                    "X-Request-ID": req_id
                }
            )
    except httpx.ConnectError as err:
        logger.error(f"[{req_id}] Connection error reaching {target_url}: {err}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": f"Downstream service unavailable: {service_base_url}", "request_id": req_id},
            headers={"X-Request-ID": req_id}
        )
    except httpx.TimeoutException as err:
        logger.error(f"[{req_id}] Timeout connecting to {target_url}: {err}")
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"detail": f"Downstream service timed out: {service_base_url}", "request_id": req_id},
            headers={"X-Request-ID": req_id}
        )
    except Exception as err:
        logger.error(f"[{req_id}] Proxy error forwarding to {target_url}: {err}")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": f"Error proxying request: {str(err)}", "request_id": req_id},
            headers={"X-Request-ID": req_id}
        )

# Health endpoint (checks Gateway and downstreams)
@app.get("/health", tags=["Health"])
async def gateway_health():
    services_status = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in [
            ("product_service", PRODUCT_SERVICE_URL),
            ("order_service", ORDER_SERVICE_URL),
            ("payment_service", PAYMENT_SERVICE_URL)
        ]:
            try:
                r = await client.get(f"{url}/health")
                services_status[name] = "healthy" if r.status_code == 200 else f"unhealthy ({r.status_code})"
            except Exception:
                services_status[name] = "unreachable"

    overall_status = "healthy" if all(v == "healthy" for v in services_status.values()) else "degraded"
    return {
        "status": overall_status,
        "service": "api-gateway",
        "downstream_services": services_status
    }

# ----------------- Product Routes -----------------

@app.get("/api/products", tags=["Products"])
async def get_all_products(request: Request):
    return await proxy_request(PRODUCT_SERVICE_URL, "/products", request)

@app.get("/api/products/{product_id}", tags=["Products"])
async def get_product_by_id(product_id: int, request: Request):
    return await proxy_request(PRODUCT_SERVICE_URL, f"/products/{product_id}", request)

@app.post("/api/products", tags=["Products"])
async def create_product(request: Request):
    return await proxy_request(PRODUCT_SERVICE_URL, "/products", request)

# ----------------- Order Routes -----------------

@app.get("/api/orders", tags=["Orders"])
async def get_all_orders(request: Request):
    return await proxy_request(ORDER_SERVICE_URL, "/orders", request)

@app.post("/api/orders", tags=["Orders"])
async def create_order(request: Request):
    return await proxy_request(ORDER_SERVICE_URL, "/orders", request)

@app.get("/api/orders/{order_id}", tags=["Orders"])
async def get_order_by_id(order_id: int, request: Request):
    return await proxy_request(ORDER_SERVICE_URL, f"/orders/{order_id}", request)

@app.patch("/api/orders/{order_id}/status", tags=["Orders"])
async def update_order_status(order_id: int, request: Request):
    return await proxy_request(ORDER_SERVICE_URL, f"/orders/{order_id}/status", request)

# ----------------- Payment Routes -----------------

@app.post("/api/payments", tags=["Payments"])
async def create_payment(request: Request):
    return await proxy_request(PAYMENT_SERVICE_URL, "/payments", request)

@app.get("/api/payments/{payment_id}", tags=["Payments"])
async def get_payment_by_id(payment_id: int, request: Request):
    return await proxy_request(PAYMENT_SERVICE_URL, f"/payments/{payment_id}", request)

@app.get("/api/payments/order/{order_id}", tags=["Payments"])
async def get_payments_by_order_id(order_id: int, request: Request):
    return await proxy_request(PAYMENT_SERVICE_URL, f"/payments/order/{order_id}", request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
