from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OrderItemIngredientIn(BaseModel):
    ingredient_id: int
    ingredient_name: str
    included: bool = True


class OrderItemOptionIn(BaseModel):
    option_id: int
    option_name: str
    group_name: str


class OrderItemIn(BaseModel):
    menu_item_id: int
    menu_item_name: str
    ingredients: list[OrderItemIngredientIn] = []
    options: list[OrderItemOptionIn] = []


class OrderIn(BaseModel):
    customer_name: str
    items: list[OrderItemIn]


class OrderItemIngredientOut(BaseModel):
    ingredient_id: int
    ingredient_name: str
    included: bool
    model_config = {"from_attributes": True}


class OrderItemOptionOut(BaseModel):
    option_id: int
    option_name: str
    group_name: str
    model_config = {"from_attributes": True}


class OrderItemOut(BaseModel):
    id: int
    menu_item_id: int
    menu_item_name: str
    ingredients: list[OrderItemIngredientOut] = []
    options: list[OrderItemOptionOut] = []
    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    public_id: str
    order_number: str
    customer_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = []
    queue_position: Optional[int] = None
    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str


class PrinterRegistration(BaseModel):
    mac_address: str


class PrinterClaim(BaseModel):
    claim_code: str
    name: str


class PrinterRename(BaseModel):
    name: str


class PrinterDeviceOut(BaseModel):
    id: int
    mac_address: str
    claim_code: str
    name: Optional[str]
    kitchen_id: Optional[str]
    registered_at: datetime
    claimed_at: Optional[datetime]
    last_seen_at: Optional[datetime]
    model_config = {"from_attributes": True}


class PrinterRegisterResponse(BaseModel):
    claim_code: str
    claimed: bool
    kitchen_id: Optional[str]
