from sqlalchemy import Column, Integer, Numeric, String, DateTime
from datetime import datetime, timezone
from database import Base

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False)
    payment_method = Column(String(50), default="SIMULATED_CARD")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
