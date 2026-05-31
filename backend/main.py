import json
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, init_db
from init_data import init_data
from auth import (
    authenticate_user, create_access_token, get_current_user,
    get_current_role, check_write_permission, ROLE_LABELS,
)
from models import User
import crud
import schemas

app = FastAPI(title="五爱食品工厂管理系统", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    init_data()


# ==================== Auth ====================

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.phone, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    roles = json.loads(user.roles)
    current_role = roles[0] if roles else "clerk"
    token = create_access_token({
        "user_id": user.id,
        "sub": user.phone,
        "role": user.role,
        "current_role": current_role,
    })
    return {
        "access_token": token,
        "roles": roles,
        "display_name": user.display_name or user.username,
    }


@app.get("/api/auth/roles")
def get_roles(current_user: User = Depends(get_current_user)):
    roles = json.loads(current_user.roles)
    return {"roles": roles, "labels": {r: ROLE_LABELS.get(r, r) for r in roles}}


@app.post("/api/auth/select-role", response_model=schemas.TokenResponse)
def select_role(
    req: schemas.RoleSelectRequest,
    current_user: User = Depends(get_current_user),
):
    roles = json.loads(current_user.roles)
    if req.role not in roles:
        raise HTTPException(status_code=403, detail="您没有该角色")
    token = create_access_token({
        "user_id": current_user.id,
        "sub": current_user.phone,
        "role": current_user.role,
        "current_role": req.role,
    })
    return {
        "access_token": token,
        "roles": roles,
        "display_name": current_user.display_name or current_user.username,
    }


@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    roles = json.loads(current_user.roles)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "phone": current_user.phone,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "roles": roles,
    }


# ==================== Dashboard ====================

@app.get("/api/dashboard/overview")
def dashboard_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_dashboard_overview(db)


# ==================== Materials ====================

@app.get("/api/materials")
def list_materials(
    search: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_materials(db, search=search, page=page, page_size=page_size)


@app.post("/api/materials", response_model=schemas.MaterialResponse)
def create_material(
    data: schemas.MaterialCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "inbound"):
        raise HTTPException(status_code=403, detail="无权限")
    return crud.create_material(db, data)


@app.put("/api/materials/{material_id}", response_model=schemas.MaterialResponse)
def update_material(
    material_id: int,
    data: schemas.MaterialUpdate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "inbound"):
        raise HTTPException(status_code=403, detail="无权限")
    material = crud.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="原料不存在")
    return crud.update_material(db, material, data)


@app.post("/api/materials/{material_id}/inbound", response_model=schemas.MaterialResponse)
def inbound_material(
    material_id: int,
    data: schemas.InboundRequest,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "inbound"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        return crud.inbound_material(db, material_id, data, current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/materials/transactions")
def list_transactions(
    material_id: int = Query(0),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_transactions(db, material_id=material_id, page=page, page_size=page_size)


# ==================== Products ====================

@app.get("/api/products")
def list_products(
    search: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_products(db, search=search, page=page, page_size=page_size)


@app.post("/api/products", response_model=schemas.ProductResponse)
def create_product(
    data: schemas.ProductCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "production"):
        raise HTTPException(status_code=403, detail="无权限")
    return crud.create_product(db, data)


@app.put("/api/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    data: schemas.ProductUpdate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "production"):
        raise HTTPException(status_code=403, detail="无权限")
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return crud.update_product(db, product, data)


# ==================== Production ====================

@app.get("/api/production")
def list_production(
    start_date: str = Query(""),
    end_date: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_production_records(db, start_date=start_date, end_date=end_date, page=page, page_size=page_size)


@app.post("/api/production")
def create_production(
    data: schemas.ProductionCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "production"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        record = crud.create_production(db, data, current_user.username)
        return crud.get_production_record(db, record.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/production/{record_id}")
def get_production(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = crud.get_production_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


# ==================== Shipments ====================

@app.get("/api/shipments")
def list_shipments(
    status: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_shipments(db, status=status, page=page, page_size=page_size)


@app.post("/api/shipments")
def create_shipment(
    data: schemas.ShipmentCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "shipment"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        record = crud.create_shipment(db, data, current_user.username)
        db.refresh(record)
        return {
            "id": record.id, "date": record.date,
            "customer_name": record.customer_name,
            "product_id": record.product_id,
            "quantity": record.quantity, "unit": record.unit,
            "unit_price": record.unit_price, "total_amount": record.total_amount,
            "status": record.status, "operator": record.operator,
            "notes": record.notes, "created_at": record.created_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/shipments/{record_id}/status")
def update_shipment_status(
    record_id: int,
    data: schemas.ShipmentStatusUpdate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "shipment"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        record = crud.update_shipment_status(db, record_id, data, current_user.username)
        return {
            "id": record.id, "status": record.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Customers ====================

@app.get("/api/customers")
def list_customers(
    search: str = Query(""),
    type: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_customers(db, search=search, type=type, page=page, page_size=page_size)


@app.post("/api/customers", response_model=schemas.CustomerResponse)
def create_customer(
    data: schemas.CustomerCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "customer"):
        raise HTTPException(status_code=403, detail="无权限")
    return crud.create_customer(db, data)


@app.put("/api/customers/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(
    customer_id: int,
    data: schemas.CustomerUpdate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "customer"):
        raise HTTPException(status_code=403, detail="无权限")
    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return crud.update_customer(db, customer, data)


@app.delete("/api/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="仅老板可删除客户")
    if not crud.delete_customer(db, customer_id):
        raise HTTPException(status_code=404, detail="客户不存在")
    return {"ok": True}


@app.get("/api/customers/{customer_id}/summary")
def customer_summary(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    summary = crud.get_customer_summary(db, customer_id)
    if not summary:
        raise HTTPException(status_code=404, detail="客户不存在")
    return summary


# ==================== Suppliers ====================

@app.get("/api/suppliers")
def list_suppliers(
    search: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_suppliers(db, search=search, page=page, page_size=page_size)


@app.post("/api/suppliers", response_model=schemas.SupplierResponse)
def create_supplier(
    data: schemas.SupplierCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "supplier"):
        raise HTTPException(status_code=403, detail="无权限")
    return crud.create_supplier(db, data)


@app.put("/api/suppliers/{supplier_id}", response_model=schemas.SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: schemas.SupplierUpdate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "supplier"):
        raise HTTPException(status_code=403, detail="无权限")
    supplier = crud.get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return crud.update_supplier(db, supplier, data)


@app.delete("/api/suppliers/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="仅老板可删除供应商")
    if not crud.delete_supplier(db, supplier_id):
        raise HTTPException(status_code=404, detail="供应商不存在")
    return {"ok": True}


# ==================== Stats ====================

@app.get("/api/stats/material-distribution")
def material_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_material_distribution(db)


@app.get("/api/stats/product-ranking")
def product_ranking(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_product_ranking(db)


@app.get("/api/stats/production-trend")
def production_trend(
    days: int = Query(7),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_production_trend(db, days=days)
