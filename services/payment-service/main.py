import logging
import uuid
import time
from contextlib import asynccontextmanager
from typing import List
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config import SERVICE_NAME, PORT, ORDER_SERVICE_URL
from database import engine, Base, get_db
from models import Payment
from schemas import PaymentRequest, PaymentResponse

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
        logger.info("Payment service database tables initialized.")
    except Exception as e:
        logger.warning(f"Database initialization warning on startup: {e}")
    yield
    logger.info(f"Shutting down {SERVICE_NAME}")

app = FastAPI(
    title="Payment Service",
    description="Microservice responsible for processing and recording order payments",
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
            content={"detail": "Internal server error in payment service", "request_id": req_id},
            headers={"X-Request-ID": req_id}
        )

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": SERVICE_NAME
    }

@app.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_200_OK, tags=["Payments"])
async def process_payment(payment_in: PaymentRequest, request: Request, db: Session = Depends(get_db)):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.info(f"[{req_id}] Processing payment for order_id={payment_in.order_id}, amount=${payment_in.amount}")

    # Validate amount
    if payment_in.amount <= 0:
        logger.warning(f"[{req_id}] Invalid payment amount: ${payment_in.amount}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero"
        )

    # Simulated payment processing logic
    payment_status = "FAILED" if payment_in.simulate_failure else "SUCCESS"

    # Persist payment record
    payment = Payment(
        order_id=payment_in.order_id,
        amount=payment_in.amount,
        status=payment_status,
        payment_method="SIMULATED_CARD"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    logger.info(f"[{req_id}] Payment #{payment.id} recorded with status: {payment_status}")

    # Notify Order Service of payment result (if reachable)
    if ORDER_SERVICE_URL:
        order_status_url = f"{ORDER_SERVICE_URL.rstrip('/')}/orders/{payment_in.order_id}/status"
        target_status = "PAID" if payment_status == "SUCCESS" else "FAILED"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.patch(
                    order_status_url,
                    json={"status": target_status},
                    headers={"X-Request-ID": req_id}
                )
            logger.info(f"[{req_id}] Updated Order #{payment_in.order_id} status to '{target_status}'")
        except Exception as e:
            logger.warning(f"[{req_id}] Could not update order status at {order_status_url}: {e}")

    return payment

@app.get("/payments/{payment_id}", response_model=PaymentResponse, tags=["Payments"])
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found"
        )
    return payment

@app.get("/payments/order/{order_id}", response_model=List[PaymentResponse], tags=["Payments"])
def get_payments_for_order(order_id: int, db: Session = Depends(get_db)):
    return db.query(Payment).filter(Payment.order_id == order_id).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
