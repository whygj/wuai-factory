import json
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import (
    User, RawMaterial, Product, InventoryTransaction,
    ProductionRecord, ShipmentRecord, OperationLog,
    Customer, Supplier, SalesOrder, PurchaseOrder,
    LabRecord,
)
from schemas import (
    MaterialCreate, MaterialUpdate, InboundRequest,
    ProductCreate, ProductUpdate,
    ProductionCreate, MaterialUsage,
    ShipmentCreate, ShipmentStatusUpdate,
    CustomerCreate, CustomerUpdate,
    SupplierCreate, SupplierUpdate,
    SalesOrderCreate, SalesOrderStatusUpdate, PaymentRequest,
    PurchaseOrderCreate, PurchaseStatusUpdate,
    LabRecordCreate, LabRecordUpdate,
)


def log_operation(db: Session, user_name: str, action: str, table_name: str, record_id: int, detail: str = ""):
    log = OperationLog(
        user_name=user_name, action=action, table_name=table_name,
        record_id=record_id, detail=detail,
    )
    db.add(log)


def get_operation_logs(db: Session, table_name: str = "", start_date: str = "", end_date: str = "", page: int = 1, page_size: int = 50):
    query = db.query(OperationLog)
    if table_name:
        query = query.filter(OperationLog.table_name == table_name)
    if start_date:
        query = query.filter(OperationLog.created_at >= start_date)
    if end_date:
        query = query.filter(OperationLog.created_at <= end_date)
    total = query.count()
    items = query.order_by(OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


# ==================== Users ====================

def register_user(db: Session, phone: str, display_name: str, role: str) -> User:
    user = User(
        phone=phone,
        display_name=display_name,
        roles=json.dumps([role], ensure_ascii=False),
        status="pending",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def approve_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    user.status = "approved"
    db.commit()
    db.refresh(user)
    return user


def reject_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    user.status = "rejected"
    db.commit()
    db.refresh(user)
    return user


def get_pending_users(db: Session):
    return db.query(User).filter(User.status == "pending").order_by(User.id.desc()).all()


def get_all_users(db: Session):
    return db.query(User).order_by(User.id.desc()).all()


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
    try:
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
    except Exception as e:
        db.rollback()
        raise


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
    try:
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
    except Exception as e:
        db.rollback()
        raise


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


# ==================== Sales Orders ====================

def _generate_order_no(db: Session, prefix: str, today: date) -> str:
    date_str = today.strftime("%Y%m%d")
    pattern = f"{prefix}-{date_str}-%"
    count = db.query(func.count(SalesOrder.id if prefix == "SO" else PurchaseOrder.id)).filter(
        (SalesOrder.order_no.like(pattern) if prefix == "SO" else PurchaseOrder.order_no.like(pattern))
    ).scalar()
    return f"{prefix}-{date_str}-{count + 1:03d}"


def create_sales_order(db: Session, data: SalesOrderCreate, operator: str) -> SalesOrder:
    items_data = []
    total = 0
    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise ValueError(f"产品ID {item.product_id} 不存在")
        subtotal = item.quantity * item.unit_price
        total += subtotal
        items_data.append({
            "product_id": item.product_id,
            "product_name": product.name,
            "quantity": item.quantity,
            "unit": product.unit,
            "unit_price": item.unit_price,
            "subtotal": subtotal,
        })

    order_no = _generate_order_no(db, "SO", data.date)
    order = SalesOrder(
        order_no=order_no,
        date=data.date,
        customer_id=data.customer_id,
        items=json.dumps(items_data, ensure_ascii=False),
        total_amount=total,
        status="待发货",
        payment_status="未付款",
        paid_amount=0,
        operator=operator,
        notes=data.notes,
    )
    db.add(order)
    db.flush()
    log_operation(db, operator, "创建销售订单", "sales_orders", order.id, f"订单号 {order_no}，金额 {total}")
    db.commit()
    db.refresh(order)
    return order


def get_sales_orders(db: Session, customer_id: int = 0, status: str = "", start_date: str = "", end_date: str = "", page: int = 1, page_size: int = 50):
    query = db.query(SalesOrder)
    if customer_id:
        query = query.filter(SalesOrder.customer_id == customer_id)
    if status:
        query = query.filter(SalesOrder.status == status)
    if start_date:
        query = query.filter(SalesOrder.date >= start_date)
    if end_date:
        query = query.filter(SalesOrder.date <= end_date)
    total = query.count()
    items = query.order_by(SalesOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for o in items:
        d = {
            "id": o.id, "order_no": o.order_no, "date": o.date,
            "customer_id": o.customer_id,
            "customer_name": o.customer.name if o.customer else "",
            "items": o.items, "total_amount": o.total_amount,
            "status": o.status, "payment_status": o.payment_status,
            "paid_amount": o.paid_amount, "operator": o.operator,
            "notes": o.notes, "created_at": o.created_at,
        }
        result.append(d)
    return {"total": total, "items": result}


def get_sales_order(db: Session, order_id: int):
    o = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not o:
        return None
    return {
        "id": o.id, "order_no": o.order_no, "date": o.date,
        "customer_id": o.customer_id,
        "customer_name": o.customer.name if o.customer else "",
        "items": o.items, "total_amount": o.total_amount,
        "status": o.status, "payment_status": o.payment_status,
        "paid_amount": o.paid_amount, "operator": o.operator,
        "notes": o.notes, "created_at": o.created_at,
    }


def update_sales_order_status(db: Session, order_id: int, data: SalesOrderStatusUpdate, operator: str) -> SalesOrder:
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise ValueError("订单不存在")
    if data.status not in ("待发货", "部分发货", "已发货", "已签收", "已取消"):
        raise ValueError("无效状态")
    order.status = data.status
    log_operation(db, operator, f"销售订单状态更新为{data.status}", "sales_orders", order_id)
    db.commit()
    db.refresh(order)
    return order


def ship_sales_order(db: Session, order_id: int, operator: str) -> SalesOrder:
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).with_for_update().first()
    if not order:
        raise ValueError("订单不存在")
    if order.status == "已发货":
        raise ValueError("订单已发货")
    if order.status == "已取消":
        raise ValueError("订单已取消")

    items = json.loads(order.items) if order.items else []
    for item in items:
        product = db.query(Product).filter(Product.id == item["product_id"]).with_for_update().first()
        if not product:
            raise ValueError(f"产品 {item.get('product_name', item['product_id'])} 不存在")
        if product.current_stock < item["quantity"]:
            raise ValueError(f"产品 {product.name} 库存不足（当前: {product.current_stock}，需要: {item['quantity']}）")
        product.current_stock -= item["quantity"]
        product.updated_at = datetime.utcnow()

    order.status = "已发货"
    log_operation(db, operator, "销售订单发货", "sales_orders", order_id, f"订单号 {order.order_no}，扣减 {len(items)} 种产品库存")
    db.commit()
    db.refresh(order)
    return order


def record_payment(db: Session, order_id: int, data: PaymentRequest, operator: str) -> SalesOrder:
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise ValueError("订单不存在")
    order.paid_amount += data.paid_amount
    if order.paid_amount >= order.total_amount:
        order.payment_status = "已付款"
        order.paid_amount = order.total_amount
    else:
        order.payment_status = "部分付款"
    log_operation(db, operator, "登记回款", "sales_orders", order_id, f"回款 {data.paid_amount}，累计 {order.paid_amount}")
    db.commit()
    db.refresh(order)
    return order


def get_sales_stats(db: Session):
    today = date.today()
    month_start = today.replace(day=1)

    month_total = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.date >= month_start,
        SalesOrder.status != "已取消",
    ).scalar()

    month_count = db.query(func.count(SalesOrder.id)).filter(
        SalesOrder.date >= month_start,
        SalesOrder.status != "已取消",
    ).scalar()

    by_customer = db.query(
        Customer.name,
        func.coalesce(func.sum(SalesOrder.total_amount), 0),
    ).join(SalesOrder, SalesOrder.customer_id == Customer.id).filter(
        SalesOrder.date >= month_start,
        SalesOrder.status != "已取消",
    ).group_by(Customer.id).order_by(func.sum(SalesOrder.total_amount).desc()).limit(5).all()

    by_product_data = []
    orders = db.query(SalesOrder).filter(
        SalesOrder.date >= month_start,
        SalesOrder.status != "已取消",
    ).all()
    product_totals = {}
    for o in orders:
        items = json.loads(o.items) if o.items else []
        for item in items:
            name = item.get("product_name", str(item["product_id"]))
            product_totals[name] = product_totals.get(name, 0) + item.get("subtotal", 0)
    sorted_products = sorted(product_totals.items(), key=lambda x: x[1], reverse=True)[:5]
    by_product_data = [{"name": p[0], "amount": p[1]} for p in sorted_products]

    return {
        "month_total": month_total,
        "month_count": month_count,
        "by_customer": [{"name": r[0], "amount": r[1]} for r in by_customer],
        "by_product": by_product_data,
    }


# ==================== Purchase Orders ====================

def _generate_purchase_no(db: Session, today: date) -> str:
    date_str = today.strftime("%Y%m%d")
    pattern = f"PO-{date_str}-%"
    count = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.order_no.like(pattern)
    ).scalar()
    return f"PO-{date_str}-{count + 1:03d}"


def create_purchase_order(db: Session, data: PurchaseOrderCreate, operator: str) -> PurchaseOrder:
    items_data = []
    total = 0
    for item in data.items:
        material = db.query(RawMaterial).filter(RawMaterial.id == item.material_id).first()
        if not material:
            raise ValueError(f"原料ID {item.material_id} 不存在")
        subtotal = item.quantity * item.unit_price
        total += subtotal
        items_data.append({
            "material_id": item.material_id,
            "material_name": material.name,
            "unit": material.unit,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": subtotal,
        })

    order_no = _generate_purchase_no(db, data.date)
    order = PurchaseOrder(
        order_no=order_no,
        date=data.date,
        supplier_id=data.supplier_id,
        items=json.dumps(items_data, ensure_ascii=False),
        total_amount=total,
        status="待到货",
        operator=operator,
        notes=data.notes,
    )
    db.add(order)
    db.flush()
    log_operation(db, operator, "创建采购单", "purchase_orders", order.id, f"采购单号 {order_no}，金额 {total}")
    db.commit()
    db.refresh(order)
    return order


def get_purchase_orders(db: Session, supplier_id: int = 0, status: str = "", start_date: str = "", end_date: str = "", page: int = 1, page_size: int = 50):
    query = db.query(PurchaseOrder)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if start_date:
        query = query.filter(PurchaseOrder.date >= start_date)
    if end_date:
        query = query.filter(PurchaseOrder.date <= end_date)
    total = query.count()
    items = query.order_by(PurchaseOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for o in items:
        d = {
            "id": o.id, "order_no": o.order_no, "date": o.date,
            "supplier_id": o.supplier_id,
            "supplier_name": o.supplier.name if o.supplier else "",
            "items": o.items, "total_amount": o.total_amount,
            "status": o.status, "operator": o.operator,
            "notes": o.notes, "created_at": o.created_at,
        }
        result.append(d)
    return {"total": total, "items": result}


def get_purchase_order(db: Session, order_id: int):
    o = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not o:
        return None
    return {
        "id": o.id, "order_no": o.order_no, "date": o.date,
        "supplier_id": o.supplier_id,
        "supplier_name": o.supplier.name if o.supplier else "",
        "items": o.items, "total_amount": o.total_amount,
        "status": o.status, "operator": o.operator,
        "notes": o.notes, "created_at": o.created_at,
    }


def update_purchase_status(db: Session, order_id: int, data: PurchaseStatusUpdate, operator: str) -> PurchaseOrder:
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise ValueError("采购单不存在")
    if data.status not in ("待到货", "已到货", "已入库", "已取消"):
        raise ValueError("无效状态")
    order.status = data.status
    log_operation(db, operator, f"采购单状态更新为{data.status}", "purchase_orders", order_id)
    db.commit()
    db.refresh(order)
    return order


def confirm_inbound(db: Session, order_id: int, operator: str) -> PurchaseOrder:
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise ValueError("采购单不存在")
    if order.status == "已入库":
        raise ValueError("采购单已入库")
    if order.status == "已取消":
        raise ValueError("采购单已取消")

    items = json.loads(order.items) if order.items else []
    for item in items:
        material = db.query(RawMaterial).filter(RawMaterial.id == item["material_id"]).with_for_update().first()
        if not material:
            raise ValueError(f"原料 {item.get('material_name', item['material_id'])} 不存在")
        material.current_stock += item["quantity"]
        material.updated_at = datetime.utcnow()

        transaction = InventoryTransaction(
            transaction_type="in",
            raw_material_id=item["material_id"],
            quantity=item["quantity"],
            unit=item.get("unit", ""),
            source="purchase",
            related_id=order_id,
            operator=operator,
            notes=f"采购入库 {order.order_no}",
        )
        db.add(transaction)

    order.status = "已入库"
    log_operation(db, operator, "采购入库", "purchase_orders", order_id, f"采购单号 {order.order_no}，入库 {len(items)} 种原料")
    db.commit()
    db.refresh(order)
    return order


# ==================== Receivables ====================

def get_receivables(db: Session, page: int = 1, page_size: int = 50):
    query = db.query(SalesOrder).filter(
        SalesOrder.payment_status != "已付款",
        SalesOrder.status != "已取消",
    )
    total = query.count()
    items = query.order_by(SalesOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for o in items:
        result.append({
            "id": o.id, "order_no": o.order_no, "date": o.date,
            "customer_id": o.customer_id,
            "customer_name": o.customer.name if o.customer else "",
            "total_amount": o.total_amount,
            "paid_amount": o.paid_amount,
            "unpaid_amount": o.total_amount - o.paid_amount,
            "payment_status": o.payment_status,
            "status": o.status,
            "created_at": o.created_at,
        })
    return {"total": total, "items": result}


def get_overdue_receivables(db: Session, page: int = 1, page_size: int = 50):
    cutoff = date.today() - timedelta(days=30)
    query = db.query(SalesOrder).filter(
        SalesOrder.payment_status != "已付款",
        SalesOrder.status != "已取消",
        SalesOrder.date < cutoff,
    )
    total = query.count()
    items = query.order_by(SalesOrder.date.asc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for o in items:
        overdue_days = (date.today() - o.date).days
        result.append({
            "id": o.id, "order_no": o.order_no, "date": o.date,
            "customer_id": o.customer_id,
            "customer_name": o.customer.name if o.customer else "",
            "total_amount": o.total_amount,
            "paid_amount": o.paid_amount,
            "unpaid_amount": o.total_amount - o.paid_amount,
            "payment_status": o.payment_status,
            "overdue_days": overdue_days,
            "created_at": o.created_at,
        })
    return {"total": total, "items": result}


def get_receivables_summary(db: Session):
    results = db.query(
        Customer.name,
        func.coalesce(func.sum(SalesOrder.total_amount), 0),
        func.coalesce(func.sum(SalesOrder.paid_amount), 0),
    ).join(SalesOrder, SalesOrder.customer_id == Customer.id).filter(
        SalesOrder.payment_status != "已付款",
        SalesOrder.status != "已取消",
    ).group_by(Customer.id).all()
    return [{"customer_name": r[0], "total_amount": r[1], "paid_amount": r[2], "unpaid_amount": r[1] - r[2]} for r in results]


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


# ==================== Role-based Dashboards ====================

def get_boss_dashboard(db: Session):
    today = date.today()
    month_start = today.replace(day=1)

    month_sales = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.date >= month_start,
        SalesOrder.status != "已取消",
    ).scalar()

    receivables = db.query(func.coalesce(func.sum(SalesOrder.total_amount - SalesOrder.paid_amount), 0)).filter(
        SalesOrder.payment_status != "已付款",
        SalesOrder.status != "已取消",
    ).scalar()

    alert_count = db.query(func.count(RawMaterial.id)).filter(
        RawMaterial.current_stock <= RawMaterial.safety_stock,
        RawMaterial.safety_stock > 0,
    ).scalar()

    today_prod = db.query(func.coalesce(func.sum(ProductionRecord.quantity), 0)).filter(
        ProductionRecord.date == today
    ).scalar()

    customer_top5 = db.query(
        Customer.name, func.sum(SalesOrder.total_amount).label('amount')
    ).join(SalesOrder).filter(
        SalesOrder.date >= month_start,
        SalesOrder.status != "已取消",
    ).group_by(Customer.id).order_by(func.sum(SalesOrder.total_amount).desc()).limit(5).all()

    alerts = db.query(RawMaterial).filter(
        RawMaterial.current_stock <= RawMaterial.safety_stock,
        RawMaterial.safety_stock > 0,
    ).all()

    trend_start = today - timedelta(days=29)
    sales_trend = db.query(
        SalesOrder.date, func.coalesce(func.sum(SalesOrder.total_amount), 0)
    ).filter(
        SalesOrder.date >= trend_start,
        SalesOrder.status != "已取消",
    ).group_by(SalesOrder.date).all()

    activities = []

    for po in db.query(PurchaseOrder).filter(PurchaseOrder.date == today).all():
        activities.append({"time": po.created_at.strftime("%H:%M") if po.created_at else "", "type": "采购入库", "desc": f"采购单 {po.order_no}", "icon": "📦"})
    for pr in db.query(ProductionRecord).filter(ProductionRecord.date == today).all():
        pname = pr.product.name if pr.product else ""
        activities.append({"time": pr.created_at.strftime("%H:%M") if pr.created_at else "", "type": "生产", "desc": f"生产 {pname} {pr.quantity}{pr.unit or ''}", "icon": "🏭"})
    for so in db.query(SalesOrder).filter(SalesOrder.date == today).all():
        cname = so.customer.name if so.customer else ""
        status_text = so.status
        activities.append({"time": so.created_at.strftime("%H:%M") if so.created_at else "", "type": "销售", "desc": f"订单 {so.order_no} → {cname} [{status_text}]", "icon": "🚚"})

    activities.sort(key=lambda x: x["time"], reverse=True)

    return {
        "month_sales": month_sales,
        "receivables": receivables,
        "alert_count": alert_count,
        "today_production": today_prod,
        "customer_top5": [{"name": r[0], "amount": r[1]} for r in customer_top5],
        "alerts": [{"id": a.id, "name": a.name, "current": a.current_stock, "safety": a.safety_stock, "unit": a.unit} for a in alerts],
        "sales_trend": [{"date": r[0].strftime("%Y-%m-%d") if hasattr(r[0], 'strftime') else str(r[0]), "amount": r[1]} for r in sales_trend],
        "today_activities": activities,
    }


def get_clerk_dashboard(db: Session):
    today = date.today()

    pending_ship = db.query(func.count(SalesOrder.id)).filter(SalesOrder.status == "待发货").scalar()
    pending_inbound = db.query(func.count(PurchaseOrder.id)).filter(PurchaseOrder.status == "待到货").scalar()
    alerts = db.query(RawMaterial).filter(
        RawMaterial.current_stock <= RawMaterial.safety_stock,
        RawMaterial.safety_stock > 0,
    ).all()
    today_sales = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.date == today,
        SalesOrder.status != "已取消",
    ).scalar()

    return {
        "pending_shipments": pending_ship,
        "pending_inbound": pending_inbound,
        "alerts": [{"id": a.id, "name": a.name, "current": a.current_stock, "safety": a.safety_stock, "unit": a.unit} for a in alerts],
        "today_sales": today_sales,
    }


def get_leader_dashboard(db: Session):
    today = date.today()

    today_records = db.query(ProductionRecord).filter(ProductionRecord.date == today).all()
    today_quantity = sum(r.quantity for r in today_records)

    trend = get_production_trend(db, days=7)

    low_materials = db.query(RawMaterial).filter(
        RawMaterial.safety_stock > 0
    ).order_by((RawMaterial.current_stock / RawMaterial.safety_stock).asc()).limit(10).all()

    return {
        "today_quantity": today_quantity,
        "today_records": len(today_records),
        "trend": trend,
        "material_status": [{"name": m.name, "current": m.current_stock, "safety": m.safety_stock, "unit": m.unit, "ratio": round(m.current_stock / m.safety_stock, 2) if m.safety_stock > 0 else 0} for m in low_materials],
    }


# ==================== Lab Records ====================

def get_lab_records(db: Session, result: str = "", start_date: str = "", end_date: str = "", page: int = 1, page_size: int = 50):
    query = db.query(LabRecord)
    if result:
        query = query.filter(LabRecord.result == result)
    if start_date:
        query = query.filter(LabRecord.date >= start_date)
    if end_date:
        query = query.filter(LabRecord.date <= end_date)
    total = query.count()
    items = query.order_by(LabRecord.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


def get_lab_record(db: Session, record_id: int) -> Optional[LabRecord]:
    return db.query(LabRecord).filter(LabRecord.id == record_id).first()


def create_lab_record(db: Session, data: LabRecordCreate, operator: str) -> LabRecord:
    record = LabRecord(
        date=data.date,
        name=data.name,
        recipe=data.recipe,
        process_params=data.process_params,
        result=data.result or "待测",
        score=data.score,
        notes=data.notes,
        operator=operator,
    )
    db.add(record)
    db.flush()
    log_operation(db, operator, "新建试验记录", "lab_records", record.id, f"试验 {data.name}")
    db.commit()
    db.refresh(record)
    return record


def update_lab_record(db: Session, record: LabRecord, data: LabRecordUpdate) -> LabRecord:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


# ==================== Reports ====================

def get_sales_report(db: Session, start_date: str = "", end_date: str = ""):
    today = date.today()
    if not start_date:
        start_date = (today.replace(day=1)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")

    total_amount = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.date >= start_date,
        SalesOrder.date <= end_date,
        SalesOrder.status != "已取消",
    ).scalar()
    total_orders = db.query(func.count(SalesOrder.id)).filter(
        SalesOrder.date >= start_date,
        SalesOrder.date <= end_date,
        SalesOrder.status != "已取消",
    ).scalar()

    by_customer = db.query(
        Customer.name,
        func.coalesce(func.sum(SalesOrder.total_amount), 0),
        func.count(SalesOrder.id),
    ).join(SalesOrder, SalesOrder.customer_id == Customer.id).filter(
        SalesOrder.date >= start_date,
        SalesOrder.date <= end_date,
        SalesOrder.status != "已取消",
    ).group_by(Customer.id).order_by(func.sum(SalesOrder.total_amount).desc()).all()

    orders = db.query(SalesOrder).filter(
        SalesOrder.date >= start_date,
        SalesOrder.date <= end_date,
        SalesOrder.status != "已取消",
    ).all()
    product_totals = {}
    for o in orders:
        items = json.loads(o.items) if o.items else []
        for item in items:
            name = item.get("product_name", str(item["product_id"]))
            product_totals[name] = product_totals.get(name, 0) + item.get("subtotal", 0)
    sorted_products = sorted(product_totals.items(), key=lambda x: x[1], reverse=True)

    daily = db.query(
        SalesOrder.date,
        func.coalesce(func.sum(SalesOrder.total_amount), 0),
    ).filter(
        SalesOrder.date >= start_date,
        SalesOrder.date <= end_date,
        SalesOrder.status != "已取消",
    ).group_by(SalesOrder.date).order_by(SalesOrder.date).all()

    return {
        "total_amount": total_amount,
        "total_orders": total_orders,
        "start_date": start_date,
        "end_date": end_date,
        "by_customer": [{"name": r[0], "amount": r[1], "count": r[2]} for r in by_customer],
        "by_product": [{"name": p[0], "amount": p[1]} for p in sorted_products],
        "daily": [{"date": r[0].strftime("%Y-%m-%d") if hasattr(r[0], 'strftime') else str(r[0]), "amount": r[1]} for r in daily],
    }


def get_production_report(db: Session, days: int = 30):
    start = date.today() - timedelta(days=days - 1)

    total_qty = db.query(func.coalesce(func.sum(ProductionRecord.quantity), 0)).filter(
        ProductionRecord.date >= start
    ).scalar()
    total_records = db.query(func.count(ProductionRecord.id)).filter(
        ProductionRecord.date >= start
    ).scalar()

    by_product = db.query(
        Product.name,
        func.coalesce(func.sum(ProductionRecord.quantity), 0),
        func.count(ProductionRecord.id),
    ).join(ProductionRecord, ProductionRecord.product_id == Product.id).filter(
        ProductionRecord.date >= start
    ).group_by(Product.id).order_by(func.sum(ProductionRecord.quantity).desc()).all()

    daily = db.query(
        ProductionRecord.date,
        func.coalesce(func.sum(ProductionRecord.quantity), 0),
    ).filter(
        ProductionRecord.date >= start
    ).group_by(ProductionRecord.date).order_by(ProductionRecord.date).all()

    date_map = {r[0]: r[1] for r in daily}
    daily_filled = []
    for i in range(days):
        d = start + timedelta(days=i)
        daily_filled.append({"date": d.strftime("%Y-%m-%d"), "quantity": date_map.get(d, 0)})

    return {
        "total_quantity": total_qty,
        "total_records": total_records,
        "days": days,
        "by_product": [{"name": r[0], "quantity": r[1], "count": r[2]} for r in by_product],
        "daily": daily_filled,
    }


def get_inventory_report(db: Session):
    materials = db.query(RawMaterial).order_by(RawMaterial.name).all()
    products = db.query(Product).order_by(Product.name).all()

    alert_materials = [{"id": m.id, "name": m.name, "current": m.current_stock, "safety": m.safety_stock, "unit": m.unit, "category": m.category} for m in materials if m.safety_stock > 0 and m.current_stock <= m.safety_stock]

    return {
        "materials": [{"id": m.id, "name": m.name, "category": m.category, "current": m.current_stock, "unit": m.unit, "safety": m.safety_stock, "price": m.purchase_price, "value": m.current_stock * (m.purchase_price or 0)} for m in materials],
        "products": [{"id": p.id, "name": p.name, "category": p.category, "spec": p.spec, "current": p.current_stock, "unit": p.unit} for p in products],
        "alert_materials": alert_materials,
        "material_count": len(materials),
        "product_count": len(products),
        "alert_count": len(alert_materials),
        "total_material_value": sum(m.current_stock * (m.purchase_price or 0) for m in materials),
    }


def get_boss_dashboard_extended(db: Session):
    today = date.today()
    month_start = today.replace(day=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # 本月销售额
    month_sales = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.date >= month_start,
        SalesOrder.status != "已取消",
    ).scalar()

    # 上月销售额
    last_month_sales = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.date >= last_month_start,
        SalesOrder.date < month_start,
        SalesOrder.status != "已取消",
    ).scalar()

    # 今日销售额
    today_sales = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.date == today,
        SalesOrder.status != "已取消",
    ).scalar()

    # 应收款
    receivables_total = db.query(func.coalesce(func.sum(SalesOrder.total_amount - SalesOrder.paid_amount), 0)).filter(
        SalesOrder.payment_status != "已付款",
        SalesOrder.status != "已取消",
    ).scalar()

    # 逾期应收款（超过30天未付）
    overdue_date = today - timedelta(days=30)
    receivables_overdue = db.query(func.coalesce(func.sum(SalesOrder.total_amount - SalesOrder.paid_amount), 0)).filter(
        SalesOrder.payment_status != "已付款",
        SalesOrder.status != "已取消",
        SalesOrder.date < overdue_date,
    ).scalar()

    # 库存预警
    alert_count = db.query(func.count(RawMaterial.id)).filter(
        RawMaterial.current_stock <= RawMaterial.safety_stock,
        RawMaterial.safety_stock > 0,
    ).scalar()

    alerts = db.query(RawMaterial).filter(
        RawMaterial.current_stock <= RawMaterial.safety_stock,
        RawMaterial.safety_stock > 0,
    ).all()

    # 待审核用户
    pending_users = db.query(func.count(User.id)).filter(User.status == "pending").scalar()

    # 待发货订单数
    shipments_pending = db.query(func.count(SalesOrder.id)).filter(SalesOrder.status == "待发货").scalar()

    # 今日产量
    today_production = db.query(func.coalesce(func.sum(ProductionRecord.quantity), 0)).filter(
        ProductionRecord.date == today
    ).scalar()

    # 客户活跃度TOP5（最近30天交易次数）
    active30 = today - timedelta(days=30)
    customers_active = db.query(
        Customer.name, func.count(SalesOrder.id).label('order_count')
    ).join(SalesOrder).filter(
        SalesOrder.date >= active30,
        SalesOrder.status != "已取消",
    ).group_by(Customer.id).order_by(func.count(SalesOrder.id).desc()).limit(5).all()

    # 产品销量TOP5（本月）
    products_top5_rows = []
    try:
        orders = db.query(SalesOrder).filter(
            SalesOrder.date >= month_start,
            SalesOrder.status != "已取消",
        ).all()
        product_sales = {}
        for o in orders:
            items = json.loads(o.items) if o.items else []
            for it in items:
                name = it.get("product_name", "")
                qty = it.get("quantity", 0)
                product_sales[name] = product_sales.get(name, 0) + qty
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
        products_top5_rows = sorted_products
    except Exception:
        pass

    # 销售趋势（近30天）
    trend_start = today - timedelta(days=29)
    sales_trend = db.query(
        SalesOrder.date, func.coalesce(func.sum(SalesOrder.total_amount), 0)
    ).filter(
        SalesOrder.date >= trend_start,
        SalesOrder.status != "已取消",
    ).group_by(SalesOrder.date).all()

    # 客户TOP5（本月消费金额）
    customer_top5 = db.query(
        Customer.name, func.sum(SalesOrder.total_amount).label('amount')
    ).join(SalesOrder).filter(
        SalesOrder.date >= month_start,
        SalesOrder.status != "已取消",
    ).group_by(Customer.id).order_by(func.sum(SalesOrder.total_amount).desc()).limit(5).all()

    # 今日动态
    activities = []
    for po in db.query(PurchaseOrder).filter(PurchaseOrder.date == today).all():
        activities.append({"time": po.created_at.strftime("%H:%M") if po.created_at else "", "type": "采购入库", "desc": f"采购单 {po.order_no}", "icon": "📦"})
    for pr in db.query(ProductionRecord).filter(ProductionRecord.date == today).all():
        pname = pr.product.name if pr.product else ""
        activities.append({"time": pr.created_at.strftime("%H:%M") if pr.created_at else "", "type": "生产", "desc": f"生产 {pname} {pr.quantity}{pr.unit or ''}", "icon": "🏭"})
    for so in db.query(SalesOrder).filter(SalesOrder.date == today).all():
        cname = so.customer.name if so.customer else ""
        activities.append({"time": so.created_at.strftime("%H:%M") if so.created_at else "", "type": "销售", "desc": f"订单 {so.order_no} → {cname} [{so.status}]", "icon": "🚚"})
    activities.sort(key=lambda x: x["time"], reverse=True)

    # 环比变化
    month_change = 0
    if last_month_sales > 0:
        month_change = round((month_sales - last_month_sales) / last_month_sales * 100, 1)

    return {
        "month_sales": month_sales,
        "last_month_sales": last_month_sales,
        "month_change": month_change,
        "today_sales": today_sales,
        "receivables_total": receivables_total,
        "receivables_overdue": receivables_overdue,
        "alert_count": alert_count,
        "alerts": [{"id": a.id, "name": a.name, "current": a.current_stock, "safety": a.safety_stock, "unit": a.unit} for a in alerts],
        "pending_users": pending_users,
        "shipments_pending": shipments_pending,
        "today_production": today_production,
        "customers_active": [{"name": r[0], "count": r[1]} for r in customers_active],
        "products_top5": [{"name": r[0], "quantity": r[1]} for r in products_top5_rows],
        "customer_top5": [{"name": r[0], "amount": r[1]} for r in customer_top5],
        "sales_trend": [{"date": r[0].strftime("%Y-%m-%d") if hasattr(r[0], 'strftime') else str(r[0]), "amount": r[1]} for r in sales_trend],
        "today_activities": activities,
    }


def quick_search(db: Session, keyword: str):
    results = {"customers": [], "orders": [], "products": [], "suppliers": []}
    if not keyword or len(keyword) < 1:
        return results

    like = f"%{keyword}%"

    customers = db.query(Customer).filter(
        (Customer.name.ilike(like)) | (Customer.phone.ilike(like)) | (Customer.contact.ilike(like))
    ).limit(10).all()
    results["customers"] = [{"id": c.id, "name": c.name, "phone": c.phone, "type": c.type} for c in customers]

    orders = db.query(SalesOrder).filter(
        (SalesOrder.order_no.ilike(like))
    ).limit(10).all()
    results["orders"] = [{"id": o.id, "order_no": o.order_no, "customer_name": o.customer.name if o.customer else "", "total_amount": o.total_amount, "status": o.status, "date": str(o.date)} for o in orders]

    products = db.query(Product).filter(
        (Product.name.ilike(like)) | (Product.category.ilike(like))
    ).limit(10).all()
    results["products"] = [{"id": p.id, "name": p.name, "category": p.category, "stock": p.current_stock, "unit": p.unit} for p in products]

    suppliers = db.query(Supplier).filter(
        (Supplier.name.ilike(like)) | (Supplier.phone.ilike(like)) | (Supplier.contact.ilike(like))
    ).limit(10).all()
    results["suppliers"] = [{"id": s.id, "name": s.name, "phone": s.phone, "category": s.category} for s in suppliers]

    return results
