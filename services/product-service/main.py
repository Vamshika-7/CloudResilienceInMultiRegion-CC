import logging
import uuid
import time
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config import SERVICE_NAME, PORT, DATABASE_URL
from database import engine, Base, get_db, SessionLocal
from models import Product
from schemas import ProductResponse, ProductCreate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger(SERVICE_NAME)

SAMPLE_PRODUCTS = [
    {
        "name": "Cloud Ultra Laptop 15",
        "description": "High-performance 16-core laptop optimized for distributed systems engineers and developers.",
        "price": 1299.99,
        "stock": 25,
    },
    {
        "name": "Noise-Canceling Wireless Headphones",
        "description": "Active noise cancellation with 40-hour battery life and spatial audio support.",
        "price": 199.50,
        "stock": 50,
    },
    {
        "name": "Mechanical Tactile Keyboard",
        "description": "Custom RGB backlit keyboard with hot-swappable switches and PBT keycaps.",
        "price": 89.99,
        "stock": 75,
    },
    {
        "name": "4K HDR Professional Monitor",
        "description": "27-inch IPS panel with 99% sRGB color gamut and 90W USB-C power delivery.",
        "price": 399.00,
        "stock": 30,
    },
    {
        "name": "Ergonomic Precision Mouse",
        "description": "Wireless dual-mode connectivity with customizable DPI and thumb scroll wheel.",
        "price": 49.99,
        "stock": 100,
    },
    {
        "name": "USB-C Dual 4K Docking Station",
        "description": "Thunderbolt-compatible dock with dual HDMI, Gigabit Ethernet, and 100W PD.",
        "price": 129.00,
        "stock": 40,
    },
]

def init_tables_and_seed():
    try:
        logger.info("Initializing Product database tables...")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            count = db.query(Product).count()
            if count == 0:
                logger.info("Seeding initial products...")
                for item in SAMPLE_PRODUCTS:
                    prod = Product(**item)
                    db.add(prod)
                db.commit()
                logger.info(f"Seeded {len(SAMPLE_PRODUCTS)} products.")
            else:
                logger.info(f"Found {count} existing products in database.")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not connect to database at startup: {e}. Will retry on requests.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {SERVICE_NAME} on port {PORT}")
    init_tables_and_seed()
    yield
    logger.info(f"Shutting down {SERVICE_NAME}")

app = FastAPI(
    title="Product Service",
    description="Microservice responsible for managing catalog products and stock",
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
            content={"detail": "Internal server error in product service", "request_id": req_id},
            headers={"X-Request-ID": req_id}
        )

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "database": "connected"
    }

@app.get("/products", response_model=List[ProductResponse], tags=["Products"])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.id.asc()).all()
    return products

@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return product

@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(**product_in.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    logger.info(f"Created new product '{new_product.name}' with ID {new_product.id}")
    return new_product

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
