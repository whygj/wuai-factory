import json
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import (
    User, RawMaterial, Product, InventoryTransaction,
    ProductionRecord, ShipmentRecord, OperationLog,
    Customer, Supplier,
)
from schemas import (
    MaterialCreate, MaterialUpdate, InboundRequest,
    ProductCreate, ProductUpdate,
    ProductionCreate, MaterialUsage,
    ShipmentCreate, ShipmentStatusUpdate,
    CustomerCreate, CustomerUpdate,
    SupplierCreate, SupplierUpdate,
)


def log_operation(db: Session, user_name: str, action: str, table_name: str, record_id: int, detail: str = ""):
    log = OperationLog(
        user_name=user_name, action=action, table_name=table_name,
        record_id=record_id, detail=detail,
    )
    db.add(log)


# ==================== Materials ====================

def get_materials(db: Session, search: str = "", page: int = 1, page_size: int = 50):
    query = db.query(RawMaterial)
    if search:
        query = query.filter(RawMaterial.name.contains(search))
    total = query.count()
    items = query.order_by(RawMaterial.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


def get_material(db: Session, material_id: int) -> Optional[RawMaterial]:
    return db.query(RawMaterial).filter(RawMaterial.id == material_id).first()


def create_material(db: Session, data: MaterialCreate) -> RawMaterial:
    material = RawMaterial(**data.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def update_material(db: Session, material: RawMaterial, data: MaterialUpdate) -> RawMaterial:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(material, key, value)
    material.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(material)
    return material


def inbound_material(db: Session, material_id: int, data: InboundRequest, operator: str) -> RawMaterial:
    material = db.query(RawMaterial).filter(RawMaterial.id == material_id).with_for_update().first()
    if not material:
        raise ValueError("原料不存在")

    material.current_stock += data.quantity
    material.updated_at = datetime.utcnow()

    transaction = InventoryTransaction(
        transaction_type="in",
        raw_material_id=material_id,
        quantity=data.quantity,
        unit=data.unit or material.unit,
        source="purchase",
        related_id=0,
        operator=operator,
        notes=data.notes,
    )
    db.add(transaction)
    log_operation(db, operator, "原料入库", "raw_materials", material_id, f"{material.name} +{data.quantity}{data.unit or material.unit}")
    db.commit()
    db.refresh(material)
    return material


def get_transactions(db: Session, material_id: int = 0, page: int = 1, page_size: int = 50):
    query = db.query(InventoryTransaction)
    if material_id:
        query = query.filter(InventoryTransaction.raw_material_id == material_id)
    total = query.count()
    items = query.order_by(InventoryTransaction.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for t in items:
        d = {
            "id": t.id, "transaction_type": t.transaction_type,
            "raw_material_id": t.raw_material_id, "quantity": t.quantity,
            "unit": t.unit, "source": t.source, "related_id": t.related_id,
            "operator": t.operator, "notes": t.notes, "created_at": t.created_at,
            "material_name": t.material.name if t.material else "",
        }
        result.append(d)
    return {"total": total, "items": result}


# ==================== Products ====================

def get_products(db: Session, search: str = "", page: int = 1, page_size: int = 50):
    query = db.query(Product)
    if search:
        query = query.filter(Product.name.contains(search))
    total = query.count()
    items = query.order_by(Product.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, data: ProductUpdate) -> Product:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product


# ==================== Production ====================

def create_production(db: Session, data: ProductionCreate, operator: str) -> ProductionRecord:
    product = db.query(Product).filter(Product.id == data.product_id).with_for_update().first()
    if not product:
        raise ValueError("产品不存在")

    materials_used = data.raw_materials_used or []
    materials_json = json.dumps([m.model_dump() for m in materials_used], ensure_ascii=False)

    for usage in materials_used:
        material = db.query(RawMaterial).filter(RawMaterial.id == usage.material_id).with_for_update().first()
        if not material:
            raise ValueError(f"原料ID {usage.material_id} 不存在")
        if material.current_stock < usage.quantity:
            raise ValueError(f"原料 {material.name} 库存不足（当前: {material.current_stock}，需要: {usage.quantity}）")
        material.current_stock -= usage.quantity
        material.updated_at = datetime.utcnow()

        transaction = InventoryTransaction(
            transaction_type="out",
            raw_material_id=usage.material_id,
            quantity=usage.quantity,
            unit=usage.unit or material.unit,
            source="production",
            related_id=0,
            operator=operator,
            notes="生产消耗",
        )
        db.add(transaction)

    product.current_stock += data.quantity
    product.updated_at = datetime.utcnow()

    record = ProductionRecord(
        date=data.date,
        product_id=data.product_id,
        quantity=data.quantity,
        unit=data.unit or product.unit,
        sugar_degree=data.sugar_degree,
        raw_materials_used=materials_json,
        operator=operator,
        notes=data.notes,
    )
    db.add(record)
    db.flush()

    db.query(InventoryTransaction).filter(
        InventoryTransaction.source == "production",
        InventoryTransaction.related_id == 0,
        InventoryTransaction.operator == operator,
    ).update({"related_id": record.id})

    log_operation(db, operator, "生产登记", "production_records", record.id, f"生产 {product.name} {data.quantity}{data.unit or product.unit}")
    db.commit()
    db.refresh(record)
    return record


def get_production_records(db: Session, start_date: str = "", end_date: str = "", page: int = 1, page_size: int = 50):
    query = db.query(ProductionRecord)
    if start_date:
        query = query.filter(ProductionRecord.date >= start_date)
    if end_date:
        query = query.filter(ProductionRecord.date <= end_date)
    total = query.count()
    items = query.order_by(ProductionRecord.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for r in items:
        d = {
            "id": r.id, "date": r.date, "product_id": r.product_id,
            "product_name": r.product.name if r.product else "",
            "quantity": r.quantity, "unit": r.unit,
            "sugar_degree": r.sugar_degree, "raw_materials_used": r.raw_materials_used,
            "operator": r.operator, "notes": r.notes, "created_at": r.created_at,
        }
        result.append(d)
    return {"total": total, "items": result}


def get_production_record(db: Session, record_id: int):
    r = db.query(ProductionRecord).filter(ProductionRecord.id == record_id).first()
    if not r:
        return None
    return {
        "id": r.id, "date": r.date, "product_id": r.product_id,
        "product_name": r.product.name if r.product else "",
        "quantity": r.quantity, "unit": r.unit,
        "sugar_degree": r.sugar_degree, "raw_materials_used": r.raw_materials_used,
        "operator": r.operator, "notes": r.notes, "created_at": r.created_at,
    }


# ==================== Shipments ====================

def create_shipment(db: Session, data: ShipmentCreate, operator: str) -> ShipmentRecord:
    product = db.query(Product).filter(Product.id == data.product_id).with_for_update().first()
    if not product:
        raise ValueError("产品不存在")
    if product.current_stock < data.quantity:
        raise ValueError(f"产品 {product.name} 库存不足（当前: {product.current_stock}，需要: {data.quantity}）")

    product.current_stock -= data.quantity
    product.updated_at = datetime.utcnow()

    total_amount = data.quantity * data.unit_price if data.unit_price else 0

    record = ShipmentRecord(
        date=data.date,
        customer_name=data.customer_name,
        product_id=data.product_id,
        quantity=data.quantity,
        unit=data.unit or product.unit,
        unit_price=data.unit_price,
        total_amount=total_amount,
        status="待发货",
        operator=operator,
        notes=data.notes,
    )
    db.add(record)
    db.flush()
    log_operation(db, operator, "发货登记", "shipment_records", record.id, f"发货 {product.name} {data.quantity}{data.unit or product.unit} 给 {data.customer_name}")
    db.commit()
    db.refresh(record)
    return record


def get_shipments(db: Session, status: str = "", page: int = 1, page_size: int = 50):
    query = db.query(ShipmentRecord)
    if status:
        query = query.filter(ShipmentRecord.status == status)
    total = query.count()
    items = query.order_by(ShipmentRecord.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for s in items:
        d = {
            "id": s.id, "date": s.date, "customer_name": s.customer_name,
            "product_id": s.product_id, "product_name": s.product.name if s.product else "",
            "quantity": s.quantity, "unit": s.unit,
            "unit_price": s.unit_price, "total_amount": s.total_amount,
            "status": s.status, "operator": s.operator,
            "notes": s.notes, "created_at": s.created_at,
        }
        result.append(d)
    return {"total": total, "items": result}


def update_shipment_status(db: Session, record_id: int, data: ShipmentStatusUpdate, operator: str) -> ShipmentRecord:
    record = db.query(ShipmentRecord).filter(ShipmentRecord.id == record_id).first()
    if not record:
        raise ValueError("发货记录不存在")
    if data.status not in ("待发货", "已发货", "已签收"):
        raise ValueError("无效状态")
    record.status = data.status
    log_operation(db, operator, f"发货状态更新为{data.status}", "shipment_records", record_id)
    db.commit()
    db.refresh(record)
    return record


# ==================== Customers ====================

def get_customers(db: Session, search: str = "", type: str = "", page: int = 1, page_size: int = 50):
    query = db.query(Customer)
    if search:
        query = query.filter(
            (Customer.name.contains(search)) |
            (Customer.contact.contains(search)) |
            (Customer.phone.contains(search))
        )
    if type:
        query = query.filter(Customer.type == type)
    total = query.count()
    items = query.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    return db.query(Customer).filter(Customer.id == customer_id).first()


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer: Customer, data: CustomerUpdate) -> Customer:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int) -> bool:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return False
    db.delete(customer)
    db.commit()
    return True


def get_customer_summary(db: Session, customer_id: int):
    customer = get_customer(db, customer_id)
    if not customer:
        return None
    return {
        "customer": customer,
        "total_orders": 0,
        "total_amount": 0,
        "last_order_date": None,
    }


# ==================== Suppliers ====================

def get_suppliers(db: Session, search: str = "", page: int = 1, page_size: int = 50):
    query = db.query(Supplier)
    if search:
        query = query.filter(
            (Supplier.name.contains(search)) |
            (Supplier.contact.contains(search)) |
            (Supplier.phone.contains(search))
        )
    total = query.count()
    items = query.order_by(Supplier.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


def get_supplier(db: Session, supplier_id: int) -> Optional[Supplier]:
    return db.query(Supplier).filter(Supplier.id == supplier_id).first()


def create_supplier(db: Session, data: SupplierCreate) -> Supplier:
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def update_supplier(db: Session, supplier: Supplier, data: SupplierUpdate) -> Supplier:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)
    supplier.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(supplier)
    return supplier


def delete_supplier(db: Session, supplier_id: int) -> bool:
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        return False
    db.delete(supplier)
    db.commit()
    return True


# ==================== Dashboard ====================

def get_dashboard_overview(db: Session):
    material_count = db.query(func.count(RawMaterial.id)).scalar()
    product_count = db.query(func.count(Product.id)).scalar()

    today = date.today()
    today_production = db.query(func.coalesce(func.sum(ProductionRecord.quantity), 0)).filter(
        ProductionRecord.date == today
    ).scalar()

    pending_shipments = db.query(func.count(ShipmentRecord.id)).filter(
        ShipmentRecord.status == "待发货"
    ).scalar()

    alerts = db.query(RawMaterial).filter(
        RawMaterial.current_stock <= RawMaterial.safety_stock,
        RawMaterial.safety_stock > 0,
    ).all()
    alert_list = [{"id": a.id, "name": a.name, "current_stock": a.current_stock, "safety_stock": a.safety_stock, "unit": a.unit} for a in alerts]

    return {
        "material_count": material_count,
        "product_count": product_count,
        "today_production": today_production,
        "pending_shipments": pending_shipments,
        "alerts": alert_list,
    }


# ==================== Stats ====================

def get_material_distribution(db: Session):
    results = db.query(RawMaterial.name, RawMaterial.current_stock).filter(
        RawMaterial.current_stock > 0
    ).all()
    return [{"name": r[0], "value": r[1]} for r in results]


def get_product_ranking(db: Session):
    results = db.query(Product.name, Product.current_stock).filter(
        Product.current_stock > 0
    ).order_by(Product.current_stock.desc()).limit(10).all()
    return [{"name": r[0], "value": r[1]} for r in results]


def get_production_trend(db: Session, days: int = 7):
    start = date.today() - timedelta(days=days - 1)
    results = db.query(
        ProductionRecord.date,
        func.coalesce(func.sum(ProductionRecord.quantity), 0),
    ).filter(
        ProductionRecord.date >= start,
    ).group_by(ProductionRecord.date).all()

    date_map = {r[0]: r[1] for r in results}
    trend = []
    for i in range(days):
        d = start + timedelta(days=i)
        trend.append({"date": d.strftime("%Y-%m-%d"), "quantity": date_map.get(d, 0)})
    return trend
