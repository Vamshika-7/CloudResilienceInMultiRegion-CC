from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

class PaymentRequest(BaseModel):
    order_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)
    simulate_failure: Optional[bool] = False

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    status: str
    payment_method: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
