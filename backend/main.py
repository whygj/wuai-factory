import io
import json
import os
from datetime import date
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, init_db
from init_data import init_data
from auth import (
    create_access_token, get_current_user,
    get_current_role, check_write_permission, ROLE_LABELS,
)
from models import User
import crud
import schemas
import sms

app = FastAPI(title="五爱食品工厂管理系统", version="3.0.0")

# 允许的前端来源：默认同源部署（nginx 反代），跨域调用时用环境变量覆盖
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "https://wuai.agentmj.vip").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    init_data()


# ==================== Auth ====================

@app.post("/api/auth/send-code")
def send_code(req: schemas.SendCodeRequest):
    if not req.phone or len(req.phone) != 11:
        raise HTTPException(status_code=400, detail="请输入正确的手机号")
    result = sms.send_verify_code(req.phone)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["msg"])
    return {"msg": result["msg"]}


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    # 先查用户状态（不消费验证码），未注册用户走注册流程时验证码仍有效
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未注册")

    if user.status == "pending":
        raise HTTPException(status_code=403, detail="账号待审核，请等待管理员通过")
    if user.status == "rejected":
        raise HTTPException(status_code=403, detail="账号未通过审核，请联系管理员")
    if user.status == "disabled":
        raise HTTPException(status_code=403, detail="账号已停用，请联系管理员")

    v = sms.verify_code(req.phone, req.code)
    if not v["ok"]:
        raise HTTPException(status_code=401, detail=v["msg"])

    roles = json.loads(user.roles)
    current_role = roles[0] if roles else "clerk"
    token = create_access_token({
        "user_id": user.id,
        "sub": user.phone,
        "current_role": current_role,
    })

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=24 * 60 * 60,
    )

    return {
        "access_token": token,
        "roles": roles,
        "display_name": user.display_name or user.phone,
    }


@app.post("/api/auth/register")
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    v = sms.verify_code(req.phone, req.code)
    if not v["ok"]:
        raise HTTPException(status_code=401, detail=v["msg"])

    existing = db.query(User).filter(User.phone == req.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="该手机号已注册")

    if req.role not in ("boss", "clerk", "leader"):
        raise HTTPException(status_code=400, detail="无效的角色")

    user = crud.register_user(db, req.phone, req.display_name, req.role)
    return {
        "msg": "注册成功，请等待管理员审核",
        "status": "pending",
        "user_id": user.id,
    }


@app.get("/api/auth/roles")
def get_roles(current_user: User = Depends(get_current_user)):
    roles = json.loads(current_user.roles)
    return {"roles": roles, "labels": {r: ROLE_LABELS.get(r, r) for r in roles}}


@app.post("/api/auth/select-role", response_model=schemas.TokenResponse)
def select_role(
    req: schemas.RoleSelectRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    roles = json.loads(current_user.roles)
    if req.role not in roles:
        raise HTTPException(status_code=403, detail="您没有该角色")
    token = create_access_token({
        "user_id": current_user.id,
        "sub": current_user.phone,
        "current_role": req.role,
    })

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=24 * 60 * 60,
    )

    return {
        "access_token": token,
        "roles": roles,
        "display_name": current_user.display_name or current_user.phone,
    }


@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    roles = json.loads(current_user.roles)
    return {
        "id": current_user.id,
        "phone": current_user.phone,
        "display_name": current_user.display_name,
        "roles": roles,
        "status": current_user.status,
    }


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


# ==================== User Management ====================

@app.get("/api/users/pending")
def get_pending_users(current_user: User = Depends(get_current_user), current_role: str = Depends(get_current_role), db: Session = Depends(get_db)):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="无权限")
    users = crud.get_pending_users(db)
    result = []
    for u in users:
        result.append({
            "id": u.id, "phone": u.phone, "display_name": u.display_name,
            "roles": json.loads(u.roles), "status": u.status, "created_at": u.created_at,
        })
    return result


@app.get("/api/users")
def get_all_users(current_user: User = Depends(get_current_user), current_role: str = Depends(get_current_role), db: Session = Depends(get_db)):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="无权限")
    users = crud.get_all_users(db)
    result = []
    for u in users:
        result.append({
            "id": u.id, "phone": u.phone, "display_name": u.display_name,
            "roles": json.loads(u.roles), "status": u.status, "created_at": u.created_at,
        })
    return result


@app.post("/api/users/{user_id}/approve")
def approve_user(user_id: int, current_user: User = Depends(get_current_user), current_role: str = Depends(get_current_role), db: Session = Depends(get_db)):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="无权限")
    try:
        user = crud.approve_user(db, user_id, current_user.display_name or current_user.phone)
        return {"ok": True, "id": user.id, "status": user.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/users/{user_id}/reject")
def reject_user(user_id: int, current_user: User = Depends(get_current_user), current_role: str = Depends(get_current_role), db: Session = Depends(get_db)):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="无权限")
    try:
        user = crud.reject_user(db, user_id, current_user.display_name or current_user.phone)
        return {"ok": True, "id": user.id, "status": user.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/api/users/{user_id}")
def update_user(
    user_id: int,
    data: schemas.UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="无权限")
    try:
        user = crud.update_user(db, user_id, data, current_user.display_name or current_user.phone)
        return {
            "ok": True, "id": user.id, "phone": user.phone,
            "display_name": user.display_name, "roles": json.loads(user.roles), "status": user.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/operation-logs")
def list_operation_logs(
    table_name: str = Query(""),
    user_name: str = Query(""),
    start_date: str = Query(""),
    end_date: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="无权限")
    return crud.get_operation_logs(db, table_name=table_name, user_name=user_name,
                                   start_date=start_date, end_date=end_date,
                                   page=page, page_size=page_size)


@app.get("/api/operation-logs/filters")
def operation_log_filters(
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="无权限")
    return crud.get_operation_log_filters(db)


# ==================== Dashboard ====================

@app.get("/api/dashboard/overview")
def dashboard_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_dashboard_overview(db)


@app.get("/api/dashboard/boss")
def boss_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_boss_dashboard(db)


@app.get("/api/dashboard/clerk")
def clerk_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_clerk_dashboard(db)


@app.get("/api/dashboard/leader")
def leader_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_leader_dashboard(db)


@app.get("/api/dashboard/boss-extended")
def boss_dashboard_extended(current_user: User = Depends(get_current_user), current_role: str = Depends(get_current_role), db: Session = Depends(get_db)):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="无权限")
    return crud.get_boss_dashboard_extended(db)


@app.get("/api/quick-search")
def quick_search_api(
    keyword: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.quick_search(db, keyword)


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
    return crud.create_material(db, data, current_user.display_name or current_user.phone)


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
    return crud.update_material(db, material, data, current_user.display_name or current_user.phone)


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
        return crud.inbound_material(db, material_id, data, current_user.display_name or current_user.phone)
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


@app.post("/api/materials/{material_id}/adjust")
def adjust_material(
    material_id: int,
    data: schemas.StockAdjustRequest,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    # 盘点是改账动作，必须过老板的手（与回款登记同款防御）
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="仅老板可盘点调整")
    try:
        return crud.adjust_material_stock(db, material_id, data, current_user.display_name or current_user.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/products/{product_id}/adjust")
def adjust_product(
    product_id: int,
    data: schemas.StockAdjustRequest,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="仅老板可盘点调整")
    try:
        return crud.adjust_product_stock(db, product_id, data, current_user.display_name or current_user.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    return crud.create_product(db, data, current_user.display_name or current_user.phone)


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
    return crud.update_product(db, product, data, current_user.display_name or current_user.phone)


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
        record = crud.create_production(db, data, current_user.display_name or current_user.phone)
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
        record = crud.create_shipment(db, data, current_user.display_name or current_user.phone)
        db.refresh(record)
        return {
            "id": record.id, "date": record.date,
            "customer_name": record.customer_name,
            "customer_id": record.customer_id,
            "product_id": record.product_id,
            "quantity": record.quantity, "unit": record.unit,
            "unit_price": record.unit_price, "total_amount": record.total_amount,
            "sales_order_id": record.sales_order_id,
            "order_no": record.sales_order.order_no if record.sales_order else None,
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
        record = crud.update_shipment_status(db, record_id, data, current_user.display_name or current_user.phone)
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
    return crud.create_customer(db, data, current_user.display_name or current_user.phone)


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
    return crud.update_customer(db, customer, data, current_user.display_name or current_user.phone)


@app.delete("/api/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="仅老板可删除客户")
    try:
        if not crud.delete_customer(db, customer_id):
            raise HTTPException(status_code=404, detail="客户不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    return crud.create_supplier(db, data, current_user.display_name or current_user.phone)


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
    return crud.update_supplier(db, supplier, data, current_user.display_name or current_user.phone)


@app.delete("/api/suppliers/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="仅老板可删除供应商")
    try:
        if not crud.delete_supplier(db, supplier_id):
            raise HTTPException(status_code=404, detail="供应商不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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


# ==================== Sales Orders ====================

@app.get("/api/sales-orders")
def list_sales_orders(
    customer_id: int = Query(0),
    status: str = Query(""),
    start_date: str = Query(""),
    end_date: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_sales_orders(db, customer_id=customer_id, status=status,
                                 start_date=start_date, end_date=end_date,
                                 page=page, page_size=page_size)


@app.post("/api/sales-orders")
def create_sales_order(
    data: schemas.SalesOrderCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "sales"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        order = crud.create_sales_order(db, data, current_user.display_name or current_user.phone)
        return crud.get_sales_order(db, order.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sales-orders/stats")
def sales_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_sales_stats(db)


@app.get("/api/sales-orders/{order_id}")
def get_sales_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = crud.get_sales_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@app.get("/api/sales-orders/{order_id}/shipment-progress")
def get_order_shipment_progress(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_order_shipment_progress(db, order_id)


@app.put("/api/sales-orders/{order_id}/status")
def update_sales_order_status(
    order_id: int,
    data: schemas.SalesOrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "sales"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        order = crud.update_sales_order_status(db, order_id, data, current_user.display_name or current_user.phone)
        return {"id": order.id, "status": order.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/sales-orders/{order_id}/payment")
def record_payment(
    order_id: int,
    data: schemas.PaymentRequest,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    # 需求权限矩阵：登记回款仅老板（内勤/班长均不可）
    if current_role != "boss":
        raise HTTPException(status_code=403, detail="仅老板可登记回款")
    try:
        order = crud.record_payment(db, order_id, data, current_user.display_name or current_user.phone)
        return {"id": order.id, "payment_status": order.payment_status, "paid_amount": order.paid_amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Purchase Orders ====================

@app.get("/api/purchases")
def list_purchases(
    supplier_id: int = Query(0),
    status: str = Query(""),
    start_date: str = Query(""),
    end_date: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_purchase_orders(db, supplier_id=supplier_id, status=status,
                                    start_date=start_date, end_date=end_date,
                                    page=page, page_size=page_size)


@app.post("/api/purchases")
def create_purchase(
    data: schemas.PurchaseOrderCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "purchase"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        order = crud.create_purchase_order(db, data, current_user.display_name or current_user.phone)
        return crud.get_purchase_order(db, order.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/purchases/{order_id}")
def get_purchase_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = crud.get_purchase_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="采购单不存在")
    return order


@app.put("/api/purchases/{order_id}/status")
def update_purchase_status(
    order_id: int,
    data: schemas.PurchaseStatusUpdate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "purchase"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        order = crud.update_purchase_status(db, order_id, data, current_user.display_name or current_user.phone)
        return {"id": order.id, "status": order.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/purchases/{order_id}/inbound")
def confirm_purchase_inbound(
    order_id: int,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "purchase"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        order = crud.confirm_inbound(db, order_id, current_user.display_name or current_user.phone)
        return {"id": order.id, "status": order.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Receivables ====================

@app.get("/api/receivables")
def list_receivables(
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_receivables(db, page=page, page_size=page_size)


@app.get("/api/receivables/overdue")
def list_overdue_receivables(
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_overdue_receivables(db, page=page, page_size=page_size)


@app.get("/api/receivables/summary")
def receivables_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_receivables_summary(db)


# ==================== Lab Records ====================

@app.get("/api/lab")
def list_lab_records(
    result: str = Query(""),
    start_date: str = Query(""),
    end_date: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_lab_records(db, result=result, start_date=start_date, end_date=end_date, page=page, page_size=page_size)


@app.post("/api/lab", response_model=schemas.LabRecordResponse)
def create_lab_record(
    data: schemas.LabRecordCreate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "lab"):
        raise HTTPException(status_code=403, detail="无权限")
    return crud.create_lab_record(db, data, current_user.display_name or current_user.phone)


@app.put("/api/lab/{record_id}", response_model=schemas.LabRecordResponse)
def update_lab_record(
    record_id: int,
    data: schemas.LabRecordUpdate,
    current_user: User = Depends(get_current_user),
    current_role: str = Depends(get_current_role),
    db: Session = Depends(get_db),
):
    if not check_write_permission(current_role, "lab"):
        raise HTTPException(status_code=403, detail="无权限")
    record = crud.get_lab_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return crud.update_lab_record(db, record, data, current_user.display_name or current_user.phone)


# ==================== Reports ====================

@app.get("/api/reports/sales")
def sales_report(
    start_date: str = Query(""),
    end_date: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_sales_report(db, start_date=start_date, end_date=end_date)


@app.get("/api/reports/production")
def production_report(
    days: int = Query(30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_production_report(db, days=days)


@app.get("/api/reports/inventory")
def inventory_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_inventory_report(db)


# ==================== Batches (v3.1) ====================

@app.get("/api/batches")
def list_batches(
    material_id: int = Query(0),
    status: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_material_batches(db, material_id=material_id, status=status, page=page, page_size=page_size)


@app.get("/api/batches/expiring")
def expiring_batches(
    days: int = Query(30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_expiring_batches(db, days=days)


@app.get("/api/batches/preview-usage")
def preview_usage(
    material_id: int = Query(...),
    quantity: float = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生产页FEFO预览：只读提示「将消耗 B1(50)→B2(30)」"""
    return crud.preview_production_batches(db, material_id, quantity)


@app.get("/api/batches/{batch_id}/trace-forward")
def batch_trace_forward(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = crud.trace_batch_forward(db, batch_id)
    if not result:
        raise HTTPException(status_code=404, detail="批次不存在")
    return result


@app.get("/api/production/{record_id}/trace-backward")
def production_trace_backward(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = crud.trace_production_backward(db, record_id)
    if not result:
        raise HTTPException(status_code=404, detail="生产记录不存在")
    return result


# ==================== Export (Excel) ====================

from urllib.parse import quote
from fastapi.responses import StreamingResponse
import export_excel


def _xlsx_response(content: bytes, filename: str) -> StreamingResponse:
    # RFC 5987：中文文件名 URL 编码，防各浏览器乱码
    encoded = quote(filename)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
            "Content-Length": str(len(content)),
        },
    )


@app.get("/api/export/sales")
def export_sales(
    start_date: str = Query(""),
    end_date: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today().strftime("%Y%m%d")
    return _xlsx_response(export_excel.export_sales(db, start_date, end_date), f"销售明细_{today}.xlsx")


@app.get("/api/export/purchases")
def export_purchases(
    start_date: str = Query(""),
    end_date: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today().strftime("%Y%m%d")
    return _xlsx_response(export_excel.export_purchases(db, start_date, end_date), f"采购明细_{today}.xlsx")


@app.get("/api/export/inventory")
def export_inventory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today().strftime("%Y%m%d")
    return _xlsx_response(export_excel.export_inventory(db), f"库存快照_{today}.xlsx")


@app.get("/api/export/receivables")
def export_receivables(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today().strftime("%Y%m%d")
    return _xlsx_response(export_excel.export_receivables(db), f"应收账款_{today}.xlsx")


@app.get("/api/export/production")
def export_production(
    start_date: str = Query(""),
    end_date: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today().strftime("%Y%m%d")
    return _xlsx_response(export_excel.export_production(db, start_date, end_date), f"生产记录_{today}.xlsx")
