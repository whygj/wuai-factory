from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# Auth
class LoginRequest(BaseModel):
    phone: str
    password: str


class LoginUsernameRequest(BaseModel):
    username: str
    password: str


class RoleSelectRequest(BaseModel):
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    roles: List[str] = []
    display_name: str = ""


class UserResponse(BaseModel):
    id: int
    username: str
    phone: str
    display_name: Optional[str] = None
    role: str
    roles: List[str] = []

    class Config:
        from_attributes = True


# Raw Material
class MaterialCreate(BaseModel):
    name: str
    category: Optional[str] = None
    unit: Optional[str] = None
    safety_stock: Optional[float] = 0
    supplier: Optional[str] = None
    supplier_id: Optional[int] = None
    purchase_price: Optional[float] = 0
    notes: Optional[str] = None


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    safety_stock: Optional[float] = None
    supplier: Optional[str] = None
    supplier_id: Optional[int] = None
    purchase_price: Optional[float] = None
    notes: Optional[str] = None


class MaterialResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    unit: Optional[str] = None
    current_stock: float
    safety_stock: float
    supplier: Optional[str] = None
    supplier_id: Optional[int] = None
    purchase_price: Optional[float] = 0
    notes: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InboundRequest(BaseModel):
    quantity: float
    unit: Optional[str] = None
    supplier: Optional[str] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    transaction_type: str
    raw_material_id: int
    quantity: float
    unit: Optional[str] = None
    source: Optional[str] = None
    related_id: Optional[int] = 0
    operator: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    material_name: Optional[str] = None

    class Config:
        from_attributes = True


# Product
class ProductCreate(BaseModel):
    name: str
    category: Optional[str] = None
    unit: Optional[str] = None
    spec: Optional[str] = None
    notes: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    spec: Optional[str] = None
    notes: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    unit: Optional[str] = None
    spec: Optional[str] = None
    current_stock: float
    notes: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Production
class MaterialUsage(BaseModel):
    material_id: int
    quantity: float
    unit: Optional[str] = None


class ProductionCreate(BaseModel):
    date: date
    product_id: int
    quantity: float
    unit: Optional[str] = None
    sugar_degree: Optional[float] = None
    raw_materials_used: Optional[List[MaterialUsage]] = None
    notes: Optional[str] = None


class ProductionResponse(BaseModel):
    id: int
    date: date
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    sugar_degree: Optional[float] = None
    raw_materials_used: Optional[str] = None
    operator: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Shipment
class ShipmentCreate(BaseModel):
    date: date
    customer_name: str
    product_id: int
    quantity: float
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    notes: Optional[str] = None


class ShipmentStatusUpdate(BaseModel):
    status: str


class ShipmentResponse(BaseModel):
    id: int
    date: date
    customer_name: Optional[str] = None
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None
    status: str
    operator: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Customer
class CustomerCreate(BaseModel):
    name: str
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None
    level: Optional[str] = "普通"
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None
    level: Optional[str] = None
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    id: int
    name: str
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None
    level: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Supplier
class SupplierCreate(BaseModel):
    name: str
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Dashboard
class DashboardOverview(BaseModel):
    material_count: int
    product_count: int
    today_production: float
    pending_shipments: int
    alerts: List[dict]


# Stats
class MaterialDistribution(BaseModel):
    name: str
    value: float


class ProductRanking(BaseModel):
    name: str
    value: float


class ProductionTrend(BaseModel):
    date: str
    quantity: float
