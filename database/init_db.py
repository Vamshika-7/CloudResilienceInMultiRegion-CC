import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, Numeric, DateTime, ForeignKey, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DatabaseInit")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ecommerce")

DEFAULT_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

Base = declarative_base()

class ProductModel(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class OrderModel(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class PaymentModel(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False)
    payment_method = Column(String(50), default="SIMULATED_CARD")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

INITIAL_PRODUCTS = [
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

def init_db(engine=None):
    if engine is None:
        logger.info(f"Connecting to database at {DATABASE_URL}")
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    logger.info("Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created / verified successfully.")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        count = db.query(ProductModel).count()
        if count == 0:
            logger.info("Products table is empty. Seeding initial products...")
            for p_data in INITIAL_PRODUCTS:
                product = ProductModel(**p_data)
                db.add(product)
            db.commit()
            logger.info(f"Successfully seeded {len(INITIAL_PRODUCTS)} products.")
        else:
            logger.info(f"Products table already contains {count} products. Skipping seed.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        init_db()
        logger.info("Database initialization and seed complete!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
