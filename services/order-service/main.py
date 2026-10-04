import logging
import uuid
import time
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import List
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config import SERVICE_NAME, PORT, PRODUCT_SERVICE_URL
from database import engine, Base, get_db
from models import Order
from schemas import OrderCreate, OrderResponse, OrderStatusUpdate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger(SERVICE_NAME)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {SERVICE_NAME} on port {PORT}")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Order service database tables initialized.")
    except Exception as e:
        logger.warning(f"Database initialization warning on startup: {e}")
    yield
    logger.info(f"Shutting down {SERVICE_NAME}")

app = FastAPI(
    title="Order Service",
    description="Microservice responsible for order placement, stock verification, and order management",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = req_id
    start_time = time.time()
    
    logger.info(f"[{req_id}] INCOMING {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        logger.info(f"[{req_id}] COMPLETED {request.method} {request.url.path} - Status {response.status_code} ({duration_ms}ms)")
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[{req_id}] ERROR {request.method} {request.url.path} ({duration_ms}ms): {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error in order service", "request_id": req_id},
            headers={"X-Request-ID": req_id}
        )

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "product_service_url": PRODUCT_SERVICE_URL
    }

@app.get("/orders", response_model=List[OrderResponse], tags=["Orders"])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.id.desc()).all()

@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return order

@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_order(order_in: OrderCreate, request: Request, db: Session = Depends(get_db)):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.info(f"[{req_id}] Processing order for product_id={order_in.product_id}, qty={order_in.quantity}")

    # 1. Communicate with Product Service to verify product and fetch price
    product_url = f"{PRODUCT_SERVICE_URL.rstrip('/')}/products/{order_in.product_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(product_url, headers={"X-Request-ID": req_id})
    except httpx.RequestError as exc:
        logger.error(f"[{req_id}] Failed to connect to Product Service at {product_url}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Product Service unavailable: {str(exc)}"
        )

    if resp.status_code == 404:
        logger.warning(f"[{req_id}] Product with ID {order_in.product_id} was not found in Product Service")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {order_in.product_id} does not exist"
        )
    elif resp.status_code != 200:
        logger.error(f"[{req_id}] Product Service returned error status {resp.status_code}: {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Product Service returned error: {resp.text}"
        )

    product_data = resp.json()
    product_price = Decimal(str(product_data["price"]))
    product_stock = int(product_data.get("stock", 0))

    # 2. Check stock availability
    if product_stock < order_in.quantity:
        logger.warning(f"[{req_id}] Insufficient stock for product {order_in.product_id}. Available: {product_stock}, Requested: {order_in.quantity}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock for product. Available: {product_stock}, Requested: {order_in.quantity}"
        )

    # 3. Calculate total amount
    total_amount = round(product_price * order_in.quantity, 2)

    # 4. Save order in PostgreSQL
    order = Order(
        user_id=order_in.user_id,
        product_id=order_in.product_id,
        quantity=order_in.quantity,
        total_amount=total_amount,
        status="PENDING"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    logger.info(f"[{req_id}] Successfully created Order #{order.id} with total amount ${total_amount} (status={order.status})")
    return order

@app.patch("/orders/{order_id}/status", response_model=OrderResponse, tags=["Orders"])
def update_order_status(order_id: int, status_update: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    order.status = status_update.status.upper()
    db.commit()
    db.refresh(order)
    logger.info(f"Order #{order_id} status updated to {order.status}")
    return order

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
