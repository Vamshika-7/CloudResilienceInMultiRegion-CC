from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

class OrderCreate(BaseModel):
    user_id: str = Field(default="user_demo", min_length=1, max_length=100)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

class OrderStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)

class OrderResponse(BaseModel):
    id: int
    user_id: str
    product_id: int
    quantity: int
    total_amount: Decimal
    status: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
