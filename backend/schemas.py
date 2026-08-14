from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
import re


# Auth
class SendCodeRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v):
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class LoginRequest(BaseModel):
    phone: str
    code: str

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v):
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class RegisterRequest(BaseModel):
    phone: str
    code: str
    display_name: str
    role: str

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v):
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class RoleSelectRequest(BaseModel):
    role: str


class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    roles: Optional[List[str]] = None
    status: Optional[str] = None

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v):
        if v is not None:
            if not v:
                raise ValueError("角色不能为空")
            for r in v:
                if r not in ("boss", "clerk", "leader"):
                    raise ValueError(f"无效角色: {r}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ("approved", "disabled", "pending", "rejected"):
            raise ValueError("无效状态")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    roles: List[str] = []
    display_name: str = ""


class UserResponse(BaseModel):
    id: int
    phone: str
    display_name: Optional[str] = None
    roles: List[str] = []
    status: str = "approved"

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
    quantity: float = Field(gt=0, description="入库数量必须大于0")
    unit: Optional[str] = None
    supplier: Optional[str] = None
    notes: Optional[str] = None


class StockAdjustRequest(BaseModel):
    """库存盘点调整：actual_stock为实盘数，reason必填留痕"""
    actual_stock: float = Field(ge=0, description="实际清点数量，不能为负")
    reason: str = Field(min_length=2, description="盘点原因必填（差异留痕）")


# Purchase Item 批次信息（v3.1）：全可选——不填走"未分批"兼容层
class PurchaseItemBatchInfo(BaseModel):
    batch_no: Optional[str] = None      # 留空自动生成 YYYYMMDD-序号
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None  # 空=不管理保质期


class PurchaseItem(BaseModel):
    material_id: int
    quantity: float = Field(gt=0, description="采购数量必须大于0")
    unit_price: float = Field(default=0, ge=0, description="单价不能为负")
    batch_no: Optional[str] = None
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None


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
    quantity: float = Field(gt=0, description="耗料数量必须大于0")
    unit: Optional[str] = None


class ProductionCreate(BaseModel):
    date: date
    product_id: int
    quantity: float = Field(gt=0, description="生产数量必须大于0")
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
    customer_id: Optional[int] = None
    product_id: int
    quantity: float = Field(gt=0, description="发货数量必须大于0")
    unit: Optional[str] = None
    unit_price: Optional[float] = Field(default=None, ge=0, description="单价不能为负")
    sales_order_id: Optional[int] = None
    notes: Optional[str] = None


class ShipmentStatusUpdate(BaseModel):
    status: str


class ShipmentResponse(BaseModel):
    id: int
    date: date
    customer_name: Optional[str] = None
    customer_id: Optional[int] = None
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None
    sales_order_id: Optional[int] = None
    order_no: Optional[str] = None
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


# Sales Order
class OrderItem(BaseModel):
    product_id: int
    quantity: float = Field(gt=0, description="数量必须大于0")
    unit_price: float = Field(default=0, ge=0, description="单价不能为负")


class SalesOrderCreate(BaseModel):
    date: date
    customer_id: int
    items: List[OrderItem]
    notes: Optional[str] = None


class SalesOrderStatusUpdate(BaseModel):
    status: str


class PaymentRequest(BaseModel):
    paid_amount: float = Field(gt=0, description="回款金额必须大于0")


class SalesOrderResponse(BaseModel):
    id: int
    order_no: Optional[str] = None
    date: date
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    items: Optional[str] = None
    total_amount: float = 0
    status: str = "待发货"
    payment_status: str = "未付款"
    paid_amount: float = 0
    operator: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Purchase Order
class PurchaseOrderCreate(BaseModel):
    date: date
    supplier_id: int
    items: List[PurchaseItem]
    notes: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id: int
    order_no: Optional[str] = None
    date: date
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    items: Optional[str] = None
    total_amount: float = 0
    status: str = "待到货"
    operator: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PurchaseStatusUpdate(BaseModel):
    status: str


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


# Lab Record
class LabRecordCreate(BaseModel):
    date: date
    name: str
    recipe: Optional[str] = None
    process_params: Optional[str] = None
    result: Optional[str] = None
    score: Optional[float] = None
    notes: Optional[str] = None


class LabRecordUpdate(BaseModel):
    name: Optional[str] = None
    recipe: Optional[str] = None
    process_params: Optional[str] = None
    result: Optional[str] = None
    score: Optional[float] = None
    notes: Optional[str] = None


class LabRecordResponse(BaseModel):
    id: int
    date: date
    name: Optional[str] = None
    recipe: Optional[str] = None
    process_params: Optional[str] = None
    result: Optional[str] = None
    score: Optional[float] = None
    notes: Optional[str] = None
    operator: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
