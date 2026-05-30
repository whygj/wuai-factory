from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, init_db
from init_data import init_data
from auth import authenticate_user, create_access_token, get_current_user
from models import User
import crud
import schemas

app = FastAPI(title="五爱食品工厂管理系统", version="1.0.0")

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
    user = authenticate_user(db, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token}


@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


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
    db: Session = Depends(get_db),
):
    if current_user.role == "leader":
        raise HTTPException(status_code=403, detail="无权限")
    return crud.create_material(db, data)


@app.put("/api/materials/{material_id}", response_model=schemas.MaterialResponse)
def update_material(
    material_id: int,
    data: schemas.MaterialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "leader":
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
    db: Session = Depends(get_db),
):
    if current_user.role not in ("clerk",):
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
    db: Session = Depends(get_db),
):
    if current_user.role == "leader":
        raise HTTPException(status_code=403, detail="无权限")
    return crud.create_product(db, data)


@app.put("/api/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    data: schemas.ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "leader":
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
    db: Session = Depends(get_db),
):
    if current_user.role not in ("clerk", "leader"):
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
    db: Session = Depends(get_db),
):
    if current_user.role not in ("clerk",):
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
    db: Session = Depends(get_db),
):
    if current_user.role not in ("clerk", "boss"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        record = crud.update_shipment_status(db, record_id, data, current_user.username)
        return {
            "id": record.id, "status": record.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
