import json
from datetime import date, timedelta
from utils import now_cn
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import (
    User, RawMaterial, Product, InventoryTransaction, ProductTransaction,
    ProductionRecord, ShipmentRecord, OperationLog,
    Customer, Supplier, SalesOrder, PurchaseOrder,
    LabRecord, MaterialBatch, BatchUsage, PurchasePayment, ReturnRecord, Bom,
)
from schemas import (
    MaterialCreate, MaterialUpdate, InboundRequest, StockAdjustRequest,
    ProductCreate, ProductUpdate,
    ProductionCreate, MaterialUsage,
    ShipmentCreate, ShipmentStatusUpdate,
    CustomerCreate, CustomerUpdate,
    SupplierCreate, SupplierUpdate,
    SalesOrderCreate, SalesOrderStatusUpdate, PaymentRequest,
    PurchaseOrderCreate, PurchaseStatusUpdate,
    LabRecordCreate, LabRecordUpdate,
    PurchasePaymentRequest, ReturnCreateRequest,
    BomSaveRequest, BomPreviewRequest,
)


def log_operation(db: Session, user_name: str, action: str, table_name: str, record_id: int, detail: str = ""):
    log = OperationLog(
        user_name=user_name, action=action, table_name=table_name,
        record_id=record_id, detail=detail,
    )
    db.add(log)


def get_operation_logs(db: Session, table_name: str = "", user_name: str = "", start_date: str = "", end_date: str = "", page: int = 1, page_size: int = 50):
    query = db.query(OperationLog)
    if table_name:
        query = query.filter(OperationLog.table_name == table_name)
    if user_name:
        query = query.filter(OperationLog.user_name.contains(user_name))
    if start_date:
        query = query.filter(OperationLog.created_at >= start_date)
    if end_date:
        # end_date 只给日期时含当天结束
        if len(end_date) == 10:
            end_date += " 23:59:59"
        query = query.filter(OperationLog.created_at <= end_date)
    total = query.count()
    items = query.order_by(OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


def get_operation_log_filters(db: Session):
    """日志筛选下拉选项：去重后的表名和操作人"""
    tables = [r[0] for r in db.query(OperationLog.table_name).distinct().all() if r[0]]
    users = [r[0] for r in db.query(OperationLog.user_name).distinct().all() if r[0]]
    return {"tables": tables, "users": users}


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


def approve_user(db: Session, user_id: int, operator: str = "") -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    user.status = "approved"
    log_operation(db, operator, "审核通过用户", "users", user_id, f"{user.display_name or user.phone}")
    db.commit()
    db.refresh(user)
    return user


def reject_user(db: Session, user_id: int, operator: str = "") -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    user.status = "rejected"
    log_operation(db, operator, "拒绝用户注册", "users", user_id, f"{user.display_name or user.phone}")
    db.commit()
    db.refresh(user)
    return user


def get_pending_users(db: Session):
    return db.query(User).filter(User.status == "pending").order_by(User.id.desc()).all()


def get_all_users(db: Session):
    return db.query(User).order_by(User.id.desc()).all()


def update_user(db: Session, user_id: int, data, operator: str = "") -> User:
    """boss 编辑用户：改姓名/角色/状态（停用即时生效——auth 校验 status）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    changes = []
    if data.display_name is not None and data.display_name != user.display_name:
        changes.append(f"姓名 {user.display_name or ''}->{data.display_name}")
        user.display_name = data.display_name
    if data.roles is not None and data.roles != json.loads(user.roles):
        # 防呆：不能移除最后一个 boss（否则没人能管理系统）
        old_roles = json.loads(user.roles)
        if "boss" in old_roles and "boss" not in data.roles:
            boss_count = sum(1 for u in db.query(User.roles).all() if "boss" in json.loads(u.roles))
            if boss_count <= 1:
                raise ValueError("系统至少需要保留一个老板角色")
        changes.append(f"角色 {old_roles}->{data.roles}")
        user.roles = json.dumps(data.roles, ensure_ascii=False)
    if data.status is not None and data.status != user.status:
        changes.append(f"状态 {user.status}->{data.status}")
        user.status = data.status
    if changes:
        log_operation(db, operator, "修改用户", "users", user_id, "；".join(changes))
    db.commit()
    db.refresh(user)
    return user


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


def create_material(db: Session, data: MaterialCreate, operator: str = "") -> RawMaterial:
    material = RawMaterial(**data.model_dump())
    db.add(material)
    db.flush()
    log_operation(db, operator, "新增原料", "raw_materials", material.id, f"{material.name}")
    db.commit()
    db.refresh(material)
    return material


def update_material(db: Session, material: RawMaterial, data: MaterialUpdate, operator: str = "") -> RawMaterial:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(material, key, value)
    material.updated_at = now_cn()
    log_operation(db, operator, "修改原料", "raw_materials", material.id, f"{material.name}")
    db.commit()
    db.refresh(material)
    return material


def inbound_material(db: Session, material_id: int, data: InboundRequest, operator: str) -> RawMaterial:
    material = db.query(RawMaterial).filter(RawMaterial.id == material_id).with_for_update().first()
    if not material:
        raise ValueError("原料不存在")

    material.current_stock += data.quantity
    material.updated_at = now_cn()

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


def adjust_material_stock(db: Session, material_id: int, data: StockAdjustRequest, operator: str) -> dict:
    """原料盘点调整（boss专属入口）：单事务改库存+写流水+操作日志，差异必须留痕"""
    try:
        material = db.query(RawMaterial).filter(RawMaterial.id == material_id).with_for_update().first()
        if not material:
            raise ValueError("原料不存在")
        old_stock = material.current_stock or 0
        diff = round(data.actual_stock - old_stock, 2)
        if diff == 0:
            raise ValueError("账实一致，无需调整")
        material.current_stock = data.actual_stock
        material.updated_at = now_cn()

        transaction = InventoryTransaction(
            transaction_type="盘点调整",
            raw_material_id=material_id,
            quantity=diff,
            unit=material.unit,
            source="adjust",
            related_id=0,
            operator=operator,
            notes=data.reason,
        )
        db.add(transaction)
        log_operation(db, operator, "盘点调整", "raw_materials", material_id,
                      f"{material.name} 账面{old_stock}→实际{data.actual_stock}，差异{diff:+g}：{data.reason}")
        db.commit()
        return {"old_stock": old_stock, "new_stock": data.actual_stock, "diff": diff}
    except Exception:
        db.rollback()
        raise


def adjust_product_stock(db: Session, product_id: int, data: StockAdjustRequest, operator: str) -> dict:
    """产品盘点调整（boss专属入口）：同原料，流水走 product_transactions"""
    try:
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise ValueError("产品不存在")
        old_stock = product.current_stock or 0
        diff = round(data.actual_stock - old_stock, 2)
        if diff == 0:
            raise ValueError("账实一致，无需调整")
        product.current_stock = data.actual_stock
        product.updated_at = now_cn()

        transaction = ProductTransaction(
            transaction_type="盘点调整",
            product_id=product_id,
            quantity=diff,
            unit=product.unit,
            source="adjust",
            related_id=0,
            operator=operator,
            notes=data.reason,
        )
        db.add(transaction)
        log_operation(db, operator, "盘点调整", "products", product_id,
                      f"{product.name} 账面{old_stock}→实际{data.actual_stock}，差异{diff:+g}：{data.reason}")
        db.commit()
        return {"old_stock": old_stock, "new_stock": data.actual_stock, "diff": diff}
    except Exception:
        db.rollback()
        raise


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


def create_product(db: Session, data: ProductCreate, operator: str = "") -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    db.flush()
    log_operation(db, operator, "新增产品", "products", product.id, f"{product.name}")
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, data: ProductUpdate, operator: str = "") -> Product:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    product.updated_at = now_cn()
    log_operation(db, operator, "修改产品", "products", product.id, f"{product.name}")
    db.commit()
    db.refresh(product)
    return product


# ==================== Production ====================

def _allocate_batches_fefo(db: Session, material_id: int, quantity: float) -> list:
    """FEFO 分配：先到期先出（无到期日的按入库先后排在有到期日的后面）。
    返回 [(batch, take), ...]；批次剩余量总和不足时返回的部分分配列表长度不变，
    由调用方决定是否接受（规格2.2：库存校验按总库存维度，批次仅尽力分配）。
    注意：批次余量是追溯参考值，不追求绝对精确（规格5节），缺批次覆盖不报错。"""
    batches = db.query(MaterialBatch).filter(
        MaterialBatch.material_id == material_id,
        MaterialBatch.status == "在库",
        MaterialBatch.quantity_remaining > 0,
    ).all()
    # 有到期日的按到期升序在前；无到期日的按创建先后垫底
    batches.sort(key=lambda b: (b.expiry_date is None, b.expiry_date or date.max, b.id))

    allocation = []
    remaining = quantity
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.quantity_remaining, remaining)
        allocation.append((batch, take))
        remaining -= take
    return allocation


def create_production(db: Session, data: ProductionCreate, operator: str) -> ProductionRecord:
    try:
        product = db.query(Product).filter(Product.id == data.product_id).with_for_update().first()
        if not product:
            raise ValueError("产品不存在")

        materials_used = data.raw_materials_used or []
        materials_json = json.dumps([m.model_dump() for m in materials_used], ensure_ascii=False)
        transactions = []
        batch_usages = []

        for usage in materials_used:
            material = db.query(RawMaterial).filter(RawMaterial.id == usage.material_id).with_for_update().first()
            if not material:
                raise ValueError(f"原料ID {usage.material_id} 不存在")
            if material.current_stock < usage.quantity:
                raise ValueError(f"原料 {material.name} 库存不足（当前: {material.current_stock}，需要: {usage.quantity}）")
            material.current_stock -= usage.quantity
            material.updated_at = now_cn()

            # v3.1 FEFO 扣批次：有在库批次则按到期先后扣并记 batch_usages；
            # 无批次记录（未分批兼容层）只扣总库存，追溯链断在"未分批"——可接受
            for batch, take in _allocate_batches_fefo(db, usage.material_id, usage.quantity):
                batch.quantity_remaining = round(batch.quantity_remaining - take, 4)
                if batch.quantity_remaining <= 0:
                    batch.status = "耗尽"
                batch_usages.append((batch, usage.material_id, take))

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
            transactions.append(transaction)

        product.current_stock += data.quantity
        product.updated_at = now_cn()

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

        # 直接对象赋值回填，不走批量 UPDATE（批量 UPDATE 的 filter 会误伤并发场景下
        # 同一操作员另一笔未回填的事务）
        for t in transactions:
            t.related_id = record.id

        # v3.1 批次消耗明细落表（一次生产跨N批次=N行）
        for batch, material_id, take in batch_usages:
            db.add(BatchUsage(
                production_id=record.id,
                batch_id=batch.id,
                material_id=material_id,
                quantity=take,
            ))

        # v3.3 成本快照：登记时算好写死，报表永远读快照（批次价/配方后变，历史不漂移）。
        # 口径=实际消耗法：Σ(batch_usages×批次进价) + 未分批部分×原料档案价；全算不出留 None。
        # 注意取值来源：batch_usages 记录的是实际扣减量（手改/替代后的量），不是配方量。
        cost = 0.0
        has_any_price = False
        batch_cost_by_material = {}
        for batch, material_id, take in batch_usages:
            price = batch.unit_price
            if price is None:
                mat = db.query(RawMaterial).filter(RawMaterial.id == material_id).first()
                price = mat.purchase_price if mat else None
            if price is not None:
                cost += take * price
                has_any_price = True
                batch_cost_by_material[material_id] = batch_cost_by_material.get(material_id, 0) + take
        # 未分批部分（总用量-批次覆盖量>0时回退档案价）
        for usage in materials_used:
            covered = batch_cost_by_material.get(usage.material_id, 0)
            uncovered = round(usage.quantity - covered, 4)
            if uncovered > 0.0001:
                mat = db.query(RawMaterial).filter(RawMaterial.id == usage.material_id).first()
                if mat and mat.purchase_price is not None:
                    cost += uncovered * mat.purchase_price
                    has_any_price = True

        record.material_cost = round(cost, 2) if has_any_price else None
        # bom_snapshot：提交时实际用量（含手改/替代），配方本身不快照
        record.bom_snapshot = materials_json

        log_operation(db, operator, "生产登记", "production_records", record.id,
                      f"生产 {product.name} {data.quantity}{data.unit or product.unit}"
                      + (f"，原料成本 {record.material_cost}" if record.material_cost is not None else ""))
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
            "material_cost": r.material_cost,
            "unit_cost": round(r.material_cost / r.quantity, 4) if r.material_cost is not None and r.quantity else None,
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
        "material_cost": r.material_cost,
        "unit_cost": round(r.material_cost / r.quantity, 4) if r.material_cost is not None and r.quantity else None,
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

        if data.sales_order_id:
            order = db.query(SalesOrder).filter(SalesOrder.id == data.sales_order_id).with_for_update().first()
            if not order:
                raise ValueError("销售订单不存在")
            if order.status in ("已取消",):
                raise ValueError("订单已取消，无法发货")
            order_items = json.loads(order.items) if order.items else []
            ordered_qty = 0
            for oi in order_items:
                if oi["product_id"] == data.product_id:
                    ordered_qty = oi["quantity"]
                    break
            if ordered_qty == 0:
                raise ValueError("该产品不在订单中")
            already_shipped = db.query(func.coalesce(func.sum(ShipmentRecord.quantity), 0)).filter(
                ShipmentRecord.sales_order_id == data.sales_order_id,
                ShipmentRecord.product_id == data.product_id,
            ).scalar()
            remaining = ordered_qty - already_shipped
            if data.quantity > remaining:
                raise ValueError(f"发货数量超过订单剩余量（订单量: {ordered_qty}，已发: {already_shipped}，剩余: {remaining}）")

        product.current_stock -= data.quantity
        product.updated_at = now_cn()

        total_amount = data.quantity * data.unit_price if data.unit_price else 0

        record = ShipmentRecord(
            date=data.date,
            customer_name=data.customer_name,
            customer_id=data.customer_id,
            product_id=data.product_id,
            quantity=data.quantity,
            unit=data.unit or product.unit,
            unit_price=data.unit_price,
            total_amount=total_amount,
            sales_order_id=data.sales_order_id,
            status="待发货",
            operator=operator,
            notes=data.notes,
        )
        db.add(record)
        db.flush()

        if data.sales_order_id:
            _update_order_shipment_status(db, data.sales_order_id)

        log_operation(db, operator, "发货登记", "shipment_records", record.id, f"发货 {product.name} {data.quantity}{data.unit or product.unit} 给 {data.customer_name}")
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise


def _update_order_shipment_status(db: Session, order_id: int):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        return
    order_items = json.loads(order.items) if order.items else []
    all_shipped = True
    for oi in order_items:
        shipped_qty = db.query(func.coalesce(func.sum(ShipmentRecord.quantity), 0)).filter(
            ShipmentRecord.sales_order_id == order_id,
            ShipmentRecord.product_id == oi["product_id"],
        ).scalar()
        if shipped_qty < oi["quantity"]:
            all_shipped = False
            break
    if all_shipped:
        order.status = "已发货"
    else:
        order.status = "部分发货"


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
            "customer_id": s.customer_id,
            "product_id": s.product_id, "product_name": s.product.name if s.product else "",
            "quantity": s.quantity, "unit": s.unit,
            "unit_price": s.unit_price, "total_amount": s.total_amount,
            "sales_order_id": s.sales_order_id,
            "order_no": s.sales_order.order_no if s.sales_order else None,
            "status": s.status, "operator": s.operator,
            "notes": s.notes, "created_at": s.created_at,
        }
        result.append(d)
    return {"total": total, "items": result}


# 发货记录合法状态迁移（只能向前推进）
SHIPMENT_TRANSITIONS = {
    "待发货": {"已发货", "已签收"},
    "已发货": {"已签收"},
    "已签收": set(),
}


def update_shipment_status(db: Session, record_id: int, data: ShipmentStatusUpdate, operator: str) -> ShipmentRecord:
    record = db.query(ShipmentRecord).filter(ShipmentRecord.id == record_id).first()
    if not record:
        raise ValueError("发货记录不存在")
    if data.status not in ("待发货", "已发货", "已签收"):
        raise ValueError("无效状态")
    if data.status == record.status:
        return record
    allowed = SHIPMENT_TRANSITIONS.get(record.status, set())
    if data.status not in allowed:
        raise ValueError(f"发货状态不能从「{record.status}」改为「{data.status}」")
    record.status = data.status
    log_operation(db, operator, f"发货状态更新为{data.status}", "shipment_records", record_id)

    if data.status == "已签收" and record.sales_order_id:
        order = db.query(SalesOrder).filter(SalesOrder.id == record.sales_order_id).first()
        if order:
            all_signed = not db.query(ShipmentRecord).filter(
                ShipmentRecord.sales_order_id == record.sales_order_id,
                ShipmentRecord.status != "已签收",
            ).first()
            if all_signed:
                order.status = "已签收"
                log_operation(db, operator, "销售订单已签收", "sales_orders", order.id)

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


def create_customer(db: Session, data: CustomerCreate, operator: str = "") -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.flush()
    log_operation(db, operator, "新增客户", "customers", customer.id, f"{customer.name}")
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer: Customer, data: CustomerUpdate, operator: str = "") -> Customer:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    customer.updated_at = now_cn()
    log_operation(db, operator, "修改客户", "customers", customer.id, f"{customer.name}")
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int) -> bool:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return False
    order_count = db.query(func.count(SalesOrder.id)).filter(SalesOrder.customer_id == customer_id).scalar()
    ship_count = db.query(func.count(ShipmentRecord.id)).filter(ShipmentRecord.customer_id == customer_id).scalar()
    if order_count > 0 or ship_count > 0:
        raise ValueError(f"该客户有 {order_count} 笔销售订单、{ship_count} 条发货记录，无法删除（历史数据需保留）")
    db.delete(customer)
    log_operation(db, "系统", "删除客户", "customers", customer_id, f"{customer.name}")
    db.commit()
    return True


def get_customer_summary(db: Session, customer_id: int):
    customer = get_customer(db, customer_id)
    if not customer:
        return None

    total_orders = db.query(func.count(SalesOrder.id)).filter(
        SalesOrder.customer_id == customer_id,
        SalesOrder.status != "已取消",
    ).scalar()

    total_amount = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.customer_id == customer_id,
        SalesOrder.status != "已取消",
    ).scalar()

    unpaid_amount = db.query(func.coalesce(func.sum(SalesOrder.total_amount - SalesOrder.paid_amount), 0)).filter(
        SalesOrder.customer_id == customer_id,
        SalesOrder.payment_status != "已付款",
        SalesOrder.status != "已取消",
    ).scalar()

    last_order = db.query(SalesOrder).filter(
        SalesOrder.customer_id == customer_id,
    ).order_by(SalesOrder.date.desc()).first()

    return {
        "customer": customer,
        "total_orders": total_orders,
        "total_amount": total_amount,
        "unpaid_amount": unpaid_amount,
        "last_order_date": str(last_order.date) if last_order else None,
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


def create_supplier(db: Session, data: SupplierCreate, operator: str = "") -> Supplier:
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    db.flush()
    log_operation(db, operator, "新增供应商", "suppliers", supplier.id, f"{supplier.name}")
    db.commit()
    db.refresh(supplier)
    return supplier


def update_supplier(db: Session, supplier: Supplier, data: SupplierUpdate, operator: str = "") -> Supplier:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)
    supplier.updated_at = now_cn()
    log_operation(db, operator, "修改供应商", "suppliers", supplier.id, f"{supplier.name}")
    db.commit()
    db.refresh(supplier)
    return supplier


def delete_supplier(db: Session, supplier_id: int) -> bool:
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        return False
    po_count = db.query(func.count(PurchaseOrder.id)).filter(PurchaseOrder.supplier_id == supplier_id).scalar()
    material_count = db.query(func.count(RawMaterial.id)).filter(RawMaterial.supplier_id == supplier_id).scalar()
    if po_count > 0 or material_count > 0:
        raise ValueError(f"该供应商有 {po_count} 笔采购单、{material_count} 种关联原料，无法删除（历史数据需保留）")
    db.delete(supplier)
    log_operation(db, "系统", "删除供应商", "suppliers", supplier_id, f"{supplier.name}")
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


def get_order_shipment_progress(db: Session, order_id: int):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        return None
    order_items = json.loads(order.items) if order.items else []
    progress = []
    for oi in order_items:
        shipped = db.query(func.coalesce(func.sum(ShipmentRecord.quantity), 0)).filter(
            ShipmentRecord.sales_order_id == order_id,
            ShipmentRecord.product_id == oi["product_id"],
        ).scalar()
        progress.append({
            "product_id": oi["product_id"],
            "product_name": oi.get("product_name", ""),
            "ordered_qty": oi["quantity"],
            "shipped_qty": shipped,
            "remaining_qty": oi["quantity"] - shipped,
            "unit": oi.get("unit", ""),
            "unit_price": oi.get("unit_price", 0),
        })
    shipments = db.query(ShipmentRecord).filter(
        ShipmentRecord.sales_order_id == order_id,
    ).order_by(ShipmentRecord.id.desc()).all()
    shipment_list = [{
        "id": s.id, "date": s.date, "product_id": s.product_id,
        "quantity": s.quantity, "status": s.status,
        "product_name": s.product.name if s.product else "",
    } for s in shipments]
    return {"progress": progress, "shipments": shipment_list}


# 销售订单合法状态迁移（终态不可逆，防"已签收改回待发货"再走一遍流程）
SALES_ORDER_TRANSITIONS = {
    "待发货": {"部分发货", "已发货", "已取消"},
    "部分发货": {"已发货", "已取消"},
    "已发货": {"已签收"},
    "已签收": set(),
    "已取消": set(),
}


def update_sales_order_status(db: Session, order_id: int, data: SalesOrderStatusUpdate, operator: str) -> SalesOrder:
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise ValueError("订单不存在")
    if data.status not in ("待发货", "部分发货", "已发货", "已签收", "已取消"):
        raise ValueError("无效状态")
    if data.status == order.status:
        return order
    allowed = SALES_ORDER_TRANSITIONS.get(order.status, set())
    if data.status not in allowed:
        raise ValueError(f"订单状态不能从「{order.status}」改为「{data.status}」")
    if data.status == "已取消":
        shipped = db.query(func.coalesce(func.sum(ShipmentRecord.quantity), 0)).filter(
            ShipmentRecord.sales_order_id == order_id,
        ).scalar()
        if shipped > 0:
            raise ValueError("该订单已有发货记录，不能取消（可联系负责人处理发货单）")
    order.status = data.status
    log_operation(db, operator, f"销售订单状态更新为{data.status}", "sales_orders", order_id)
    db.commit()
    db.refresh(order)
    return order


def record_payment(db: Session, order_id: int, data: PaymentRequest, operator: str) -> SalesOrder:
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise ValueError("订单不存在")
    if order.status == "已取消":
        raise ValueError("订单已取消，无法登记回款")
    unpaid = round(order.total_amount - order.paid_amount, 2)
    if unpaid <= 0:
        raise ValueError("该订单已全额付款")
    if data.paid_amount > unpaid:
        raise ValueError(f"回款金额超过未付余额（未付: {unpaid}）")
    order.paid_amount = round(order.paid_amount + data.paid_amount, 2)
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
            "batch_no": item.batch_no,
            "production_date": str(item.production_date) if item.production_date else None,
            "expiry_date": str(item.expiry_date) if item.expiry_date else None,
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
            "paid_amount": o.paid_amount or 0,
            "payment_status": o.payment_status or "未付款",
            "unpaid_amount": round((o.total_amount or 0) - (o.paid_amount or 0), 2),
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
        "paid_amount": o.paid_amount or 0,
        "payment_status": o.payment_status or "未付款",
        "unpaid_amount": round((o.total_amount or 0) - (o.paid_amount or 0), 2),
        "status": o.status, "operator": o.operator,
        "notes": o.notes, "created_at": o.created_at,
    }


# 采购单合法状态迁移（已入库是终态——库存已加，改回待到货可再次入库导致库存翻倍）
PURCHASE_TRANSITIONS = {
    "待到货": {"已到货", "已入库", "已取消"},
    "已到货": {"已入库", "已取消"},
    "已入库": set(),
    "已取消": set(),
}


def update_purchase_status(db: Session, order_id: int, data: PurchaseStatusUpdate, operator: str) -> PurchaseOrder:
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise ValueError("采购单不存在")
    if data.status not in ("待到货", "已到货", "已入库", "已取消"):
        raise ValueError("无效状态")
    if data.status == order.status:
        return order
    allowed = PURCHASE_TRANSITIONS.get(order.status, set())
    if data.status not in allowed:
        raise ValueError(f"采购单状态不能从「{order.status}」改为「{data.status}」")
    if data.status == "已入库":
        # 手动直接改"已入库"不经过入库事务会绕过库存增加，禁止；必须走 confirm_inbound
        raise ValueError("请使用「确认入库」按钮完成入库（会自动增加原料库存）")
    order.status = data.status
    log_operation(db, operator, f"采购单状态更新为{data.status}", "purchase_orders", order_id)
    db.commit()
    db.refresh(order)
    return order


def _parse_date_str(value):
    """items JSON 里的日期是字符串，Date 列要 date 对象；空/非法返回 None"""
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _generate_batch_no(db: Session, material_id: int, material_name: str) -> str:
    """默认批次号：原料名缩写YYYYMMDD-当日序号。与用户手输批次同走唯一约束，撞号报错让用户改。"""
    date_str = date.today().strftime("%Y%m%d")
    prefix = "".join(ch for ch in material_name if not ch.isdigit())[:6] or "B"
    pattern = f"{prefix}{date_str}-%"
    count = db.query(func.count(MaterialBatch.id)).filter(
        MaterialBatch.material_id == material_id,
        MaterialBatch.batch_no.like(pattern),
    ).scalar()
    return f"{prefix}{date_str}-{count + 1:02d}"


def confirm_inbound(db: Session, order_id: int, operator: str) -> PurchaseOrder:
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise ValueError("采购单不存在")
    if order.status == "已入库":
        raise ValueError("采购单已入库")
    if order.status == "已取消":
        raise ValueError("采购单已取消")

    items = json.loads(order.items) if order.items else []
    batches_created = 0
    for item in items:
        material = db.query(RawMaterial).filter(RawMaterial.id == item["material_id"]).with_for_update().first()
        if not material:
            raise ValueError(f"原料 {item.get('material_name', item['material_id'])} 不存在")
        material.current_stock += item["quantity"]
        material.updated_at = now_cn()

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

        # v3.1 批次：填了批次号/生产日期/保质期任一项才建批次记录；否则走"未分批"兼容层
        batch_no = (item.get("batch_no") or "").strip()
        production_date = _parse_date_str(item.get("production_date"))
        expiry_date = _parse_date_str(item.get("expiry_date"))
        if batch_no or production_date or expiry_date:
            if not batch_no:
                batch_no = _generate_batch_no(db, material.id, material.name)
            existing = db.query(MaterialBatch).filter(
                MaterialBatch.material_id == material.id,
                MaterialBatch.batch_no == batch_no,
            ).first()
            if existing:
                raise ValueError(f"原料 {material.name} 批次号 {batch_no} 已存在，请修改批次号")
            db.add(MaterialBatch(
                material_id=material.id,
                batch_no=batch_no,
                quantity_in=item["quantity"],
                quantity_remaining=item["quantity"],
                unit_price=item.get("unit_price"),
                production_date=production_date,
                expiry_date=expiry_date,
                supplier_id=order.supplier_id,
                status="在库",
                notes=f"采购入库 {order.order_no}",
            ))
            batches_created += 1

    order.status = "已入库"
    log_operation(db, operator, "采购入库", "purchase_orders", order_id,
                  f"采购单号 {order.order_no}，入库 {len(items)} 种原料" + (f"，建批次 {batches_created} 个" if batches_created else ""))
    db.commit()
    db.refresh(order)
    return order


# ==================== Receivables ====================

def get_receivables(db: Session, page: int = 1, page_size: int = 50):
    # v3.2: 全额回款后退货的订单（paid>total，负应收）也要出现在列表——老板要看到"应退款"。
    # 条件改为：未付清 或 已超付（total < paid）
    query = db.query(SalesOrder).filter(
        SalesOrder.status != "已取消",
        (SalesOrder.payment_status != "已付款") | (SalesOrder.total_amount < SalesOrder.paid_amount),
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


def update_lab_record(db: Session, record: LabRecord, data: LabRecordUpdate, operator: str = "") -> LabRecord:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    log_operation(db, operator, "修改试验记录", "lab_records", record.id, f"试验 {record.name} -> {record.result or '待测'}")
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


# ==================== Batches (v3.1) ====================

def get_material_batches(db: Session, material_id: int = 0, status: str = "", page: int = 1, page_size: int = 100):
    query = db.query(MaterialBatch)
    if material_id:
        query = query.filter(MaterialBatch.material_id == material_id)
    if status:
        query = query.filter(MaterialBatch.status == status)
    total = query.count()
    items = query.order_by(MaterialBatch.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for b in items:
        result.append({
            "id": b.id, "material_id": b.material_id,
            "material_name": b.material.name if b.material else "",
            "batch_no": b.batch_no,
            "quantity_in": b.quantity_in, "quantity_remaining": b.quantity_remaining,
            "unit": b.material.unit if b.material else "",
            "unit_price": b.unit_price,
            "production_date": str(b.production_date) if b.production_date else None,
            "expiry_date": str(b.expiry_date) if b.expiry_date else None,
            "supplier_name": b.supplier.name if b.supplier else "",
            "status": b.status, "notes": b.notes,
            "created_at": b.created_at,
        })
    return {"total": total, "items": result}


def get_expiring_batches(db: Session, days: int = 30):
    """临期批次：在库有余量且 expiry_date ≤ 今天+days，按剩余天数升序。
    无到期日的批次不参与（不管理保质期）。"""
    deadline = date.today() + timedelta(days=days)
    batches = db.query(MaterialBatch).filter(
        MaterialBatch.quantity_remaining > 0,
        MaterialBatch.status == "在库",
        MaterialBatch.expiry_date.isnot(None),
        MaterialBatch.expiry_date <= deadline,
    ).order_by(MaterialBatch.expiry_date.asc()).all()
    result = []
    for b in batches:
        remain_days = (b.expiry_date - date.today()).days
        result.append({
            "id": b.id, "material_id": b.material_id,
            "material_name": b.material.name if b.material else "",
            "batch_no": b.batch_no,
            "quantity_remaining": b.quantity_remaining,
            "unit": b.material.unit if b.material else "",
            "expiry_date": str(b.expiry_date),
            "remain_days": remain_days,
            "expired": remain_days < 0,
        })
    return result


def preview_production_batches(db: Session, material_id: int, quantity: float):
    """生产页FEFO预览：显示「将消耗 B1(50)→B2(30)」，班长不手选（规格2.2）"""
    allocation = _allocate_batches_fefo(db, material_id, quantity)
    return [{
        "batch_id": b.id, "batch_no": b.batch_no,
        "expiry_date": str(b.expiry_date) if b.expiry_date else None,
        "take": round(take, 4),
    } for b, take in allocation]


def trace_batch_forward(db: Session, batch_id: int):
    """反向追溯（原料批次→产品→客户）：批次→batch_usages→生产记录→该产品发往哪些客户"""
    batch = db.query(MaterialBatch).filter(MaterialBatch.id == batch_id).first()
    if not batch:
        return None
    usages = db.query(BatchUsage).filter(BatchUsage.batch_id == batch_id).order_by(BatchUsage.id).all()

    productions = []
    total_used = 0
    for u in usages:
        total_used += u.quantity
        pr = db.query(ProductionRecord).filter(ProductionRecord.id == u.production_id).first()
        if not pr:
            continue
        pname = pr.product.name if pr.product else ""
        # 该生产之后同产品的发货去向（按发货记录，含订单客户名）
        shipments = db.query(ShipmentRecord).filter(ShipmentRecord.product_id == pr.product_id).order_by(ShipmentRecord.id.desc()).limit(20).all()
        dests = []
        for s in shipments:
            dest = s.customer_name or (s.customer_rel.name if s.customer_rel and s.customer_rel.name else "")
            if dest and dest not in [d["customer"] for d in dests]:
                dests.append({"customer": dest, "date": str(s.date), "quantity": s.quantity, "order_no": s.sales_order.order_no if s.sales_order else None})
        productions.append({
            "production_id": pr.id, "date": str(pr.date),
            "product_id": pr.product_id, "product_name": pname,
            "quantity": pr.quantity, "unit": pr.unit,
            "sugar_degree": pr.sugar_degree, "operator": pr.operator,
            "used_in_this_production": u.quantity,
            "shipments": dests,
        })

    return {
        "batch": {
            "id": batch.id, "batch_no": batch.batch_no,
            "material_id": batch.material_id,
            "material_name": batch.material.name if batch.material else "",
            "quantity_in": batch.quantity_in,
            "quantity_remaining": batch.quantity_remaining,
            "unit": batch.material.unit if batch.material else "",
            "unit_price": batch.unit_price,
            "production_date": str(batch.production_date) if batch.production_date else None,
            "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
            "supplier_name": batch.supplier.name if batch.supplier else "",
            "status": batch.status,
        },
        "total_used": round(total_used, 4),
        "productions": productions,
    }


def trace_production_backward(db: Session, production_id: int):
    """正向追溯（生产记录→原料批次）：列全部消耗批次+供应商/生产日期/保质期"""
    pr = db.query(ProductionRecord).filter(ProductionRecord.id == production_id).first()
    if not pr:
        return None
    usages = db.query(BatchUsage).filter(BatchUsage.production_id == production_id).order_by(BatchUsage.id).all()

    batches = []
    for u in usages:
        b = u.batch
        if not b:
            continue
        batches.append({
            "batch_id": b.id, "batch_no": b.batch_no,
            "material_id": b.material_id,
            "material_name": b.material.name if b.material else "",
            "used_quantity": u.quantity,
            "unit": b.material.unit if b.material else "",
            "unit_price": b.unit_price,
            "production_date": str(b.production_date) if b.production_date else None,
            "expiry_date": str(b.expiry_date) if b.expiry_date else None,
            "supplier_name": b.supplier.name if b.supplier else "",
        })

    # 未分批的原料也列出（提示追溯链断点）
    unbatched = []
    material_names = {b["material_id"] for b in batches}
    used_list = json.loads(pr.raw_materials_used) if pr.raw_materials_used else []
    for m in used_list:
        if m.get("material_id") not in material_names:
            mat = db.query(RawMaterial).filter(RawMaterial.id == m.get("material_id")).first()
            unbatched.append({
                "material_id": m.get("material_id"),
                "material_name": mat.name if mat else str(m.get("material_id")),
                "used_quantity": m.get("quantity"),
                "unit": mat.unit if mat else "",
            })

    return {
        "production": {
            "id": pr.id, "date": str(pr.date),
            "product_id": pr.product_id,
            "product_name": pr.product.name if pr.product else "",
            "quantity": pr.quantity, "unit": pr.unit,
            "sugar_degree": pr.sugar_degree, "operator": pr.operator,
            "notes": pr.notes,
        },
        "batches": batches,
        "unbatched": unbatched,
    }


# ==================== Purchase Payments (v3.2) ====================

def _recalc_purchase_payment_status(order: PurchaseOrder):
    paid = order.paid_amount or 0
    total = order.total_amount or 0
    if paid <= 0:
        order.payment_status = "未付款"
    elif paid >= total:
        order.payment_status = "已付款"
    else:
        order.payment_status = "部分付款"


def record_purchase_payment(db: Session, order_id: int, data: PurchasePaymentRequest, operator: str) -> dict:
    """供应商付款登记（boss专属入口）：行锁+流水+状态重算，超额不拦（可先付后票/多退少补场景看流水对账）"""
    try:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).with_for_update().first()
        if not order:
            raise ValueError("采购单不存在")
        if order.status == "已取消":
            raise ValueError("采购单已取消，无法登记付款")
        order.paid_amount = round((order.paid_amount or 0) + data.amount, 2)
        _recalc_purchase_payment_status(order)

        payment = PurchasePayment(
            purchase_order_id=order_id,
            amount=data.amount,
            date=data.date,
            method=data.method,
            status="有效",
            operator=operator,
            notes=data.notes,
        )
        db.add(payment)
        db.flush()
        log_operation(db, operator, "登记付款", "purchase_orders", order_id,
                      f"采购单 {order.order_no} 付款 {data.amount}（{data.method or '未注明方式'}），累计已付 {order.paid_amount}")
        db.commit()
        return {"id": payment.id, "paid_amount": order.paid_amount, "payment_status": order.payment_status}
    except Exception:
        db.rollback()
        raise


def void_purchase_payment(db: Session, payment_id: int, operator: str) -> dict:
    """作废付款（boss专属）：逆向恢复 paid_amount、重算状态、流水只标已作废不物理删"""
    try:
        payment = db.query(PurchasePayment).filter(PurchasePayment.id == payment_id).first()
        if not payment:
            raise ValueError("付款流水不存在")
        if payment.status == "已作废":
            raise ValueError("该付款已作废")
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == payment.purchase_order_id).with_for_update().first()
        if not order:
            raise ValueError("采购单不存在")
        payment.status = "已作废"
        order.paid_amount = round((order.paid_amount or 0) - payment.amount, 2)
        if order.paid_amount < 0:
            order.paid_amount = 0
        _recalc_purchase_payment_status(order)
        log_operation(db, operator, "作废付款", "purchase_orders", order.id,
                      f"采购单 {order.order_no} 作废付款 {payment.amount}，已付恢复为 {order.paid_amount}")
        db.commit()
        return {"id": payment_id, "status": payment.status, "paid_amount": order.paid_amount,
                "payment_status": order.payment_status}
    except Exception:
        db.rollback()
        raise


def get_purchase_payments(db: Session, order_id: int):
    payments = db.query(PurchasePayment).filter(
        PurchasePayment.purchase_order_id == order_id,
    ).order_by(PurchasePayment.id.desc()).all()
    return [{
        "id": p.id, "purchase_order_id": p.purchase_order_id,
        "amount": p.amount, "date": str(p.date), "method": p.method or "",
        "status": p.status, "operator": p.operator or "", "notes": p.notes or "",
        "created_at": p.created_at,
    } for p in payments]


def get_payables_summary(db: Session):
    """应付款汇总：总应付=所有未取消采购单 total 之和；欠款=total-paid 之和（负数也计入）；
    本月已付=本月有效付款流水之和"""
    today = date.today()
    month_start = today.replace(day=1)

    orders = db.query(PurchaseOrder).filter(PurchaseOrder.status != "已取消").all()
    total_payable = sum(o.total_amount or 0 for o in orders)
    unpaid_total = sum((o.total_amount or 0) - (o.paid_amount or 0) for o in orders)

    month_paid = db.query(func.coalesce(func.sum(PurchasePayment.amount), 0)).filter(
        PurchasePayment.status == "有效",
        PurchasePayment.date >= month_start,
    ).scalar()

    return {
        "total_payable": round(total_payable, 2),
        "month_paid": round(month_paid, 2),
        "unpaid_total": round(unpaid_total, 2),
    }


def get_payable_orders(db: Session, supplier_id: int = 0, payment_status: str = "", page: int = 1, page_size: int = 50):
    """应付款明细：未付清的采购单（含负欠款=多付）"""
    query = db.query(PurchaseOrder).filter(PurchaseOrder.status != "已取消")
    if payment_status == "未付款":
        query = query.filter(PurchaseOrder.payment_status != "已付款")
    elif payment_status:
        query = query.filter(PurchaseOrder.payment_status == payment_status)
    else:
        query = query.filter(PurchaseOrder.payment_status != "已付款")
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    total = query.count()
    items = query.order_by(PurchaseOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for o in items:
        result.append({
            "id": o.id, "order_no": o.order_no, "date": str(o.date),
            "supplier_id": o.supplier_id,
            "supplier_name": o.supplier.name if o.supplier else "",
            "total_amount": o.total_amount or 0,
            "paid_amount": o.paid_amount or 0,
            "unpaid_amount": round((o.total_amount or 0) - (o.paid_amount or 0), 2),
            "payment_status": o.payment_status or "未付款",
            "status": o.status,
            "items": o.items,
            "created_at": o.created_at,
        })
    return {"total": total, "items": result}


# ==================== Sales Returns (v3.2) ====================

def _get_order_item_price(order: SalesOrder, product_id: int) -> Optional[float]:
    """订单行单价（退货默认价）"""
    items = json.loads(order.items) if order.items else []
    for it in items:
        if it.get("product_id") == product_id:
            return it.get("unit_price")
    return None


def create_return(db: Session, data: ReturnCreateRequest, operator: str) -> dict:
    """销售退货（clerk+boss入口）：方案A——订单 total 直接冲减+操作日志留痕；
    退回入库只加 current_stock 总量（不做可用区分，老李已知情）；报废不碰库存。
    防虚退：quantity 不得超过该订单该产品已发数量。"""
    try:
        if not data.sales_order_id:
            raise ValueError("退货必须关联销售订单")
        order = db.query(SalesOrder).filter(SalesOrder.id == data.sales_order_id).with_for_update().first()
        if not order:
            raise ValueError("销售订单不存在")
        if order.status == "已取消":
            raise ValueError("订单已取消，无法退货")

        product = db.query(Product).filter(Product.id == data.product_id).with_for_update().first()
        if not product:
            raise ValueError("产品不存在")

        # 防虚退：已发量校验（含已作废退货不减——作废退货视同没发生）
        already_shipped = db.query(func.coalesce(func.sum(ShipmentRecord.quantity), 0)).filter(
            ShipmentRecord.sales_order_id == data.sales_order_id,
            ShipmentRecord.product_id == data.product_id,
        ).scalar()
        already_returned = db.query(func.coalesce(func.sum(ReturnRecord.quantity), 0)).filter(
            ReturnRecord.sales_order_id == data.sales_order_id,
            ReturnRecord.product_id == data.product_id,
            ReturnRecord.status == "有效",
        ).scalar()
        returnable = already_shipped - already_returned
        if data.quantity > returnable:
            raise ValueError(f"退货数量超过可退量（已发: {already_shipped}，已退: {already_returned}，可退: {returnable}）")

        unit_price = data.unit_price if data.unit_price is not None else _get_order_item_price(order, data.product_id)
        amount = round(data.quantity * (unit_price or 0), 2)

        old_total = order.total_amount or 0
        order.total_amount = round(old_total - amount, 2)
        if order.total_amount < 0:
            order.total_amount = 0

        record = ReturnRecord(
            date=data.date,
            customer_id=data.customer_id if data.customer_id is not None else order.customer_id,
            sales_order_id=data.sales_order_id,
            product_id=data.product_id,
            quantity=data.quantity,
            unit_price=unit_price,
            total_amount=amount,
            return_type=data.return_type,
            product_batch_ref=data.product_batch_ref,
            status="有效",
            operator=operator,
            notes=data.notes,
        )
        db.add(record)

        if data.return_type == "退回入库":
            product.current_stock = round((product.current_stock or 0) + data.quantity, 2)
            product.updated_at = now_cn()
            db.add(ProductTransaction(
                transaction_type="退货入库",
                product_id=data.product_id,
                quantity=data.quantity,
                unit=product.unit,
                source="return",
                related_id=0,
                operator=operator,
                notes=f"退货 {order.order_no}",
            ))

        db.flush()
        log_operation(db, operator, "登记退货", "return_records", record.id,
                      f"{data.return_type} {product.name} ×{data.quantity}，订单 {order.order_no} 退货冲减：原额{old_total}→现额{order.total_amount}")
        db.commit()
        return {
            "id": record.id, "return_type": record.return_type,
            "total_amount": amount, "order_total": order.total_amount,
            "order_paid": order.paid_amount,
        }
    except Exception:
        db.rollback()
        raise


def void_return(db: Session, return_id: int, operator: str) -> dict:
    """作废退货（boss专属）：完全逆向——total加回、退回入库的减回、负向冲正流水、status=已作废"""
    try:
        record = db.query(ReturnRecord).filter(ReturnRecord.id == return_id).first()
        if not record:
            raise ValueError("退货记录不存在")
        if record.status == "已作废":
            raise ValueError("该退货已作废")

        order = db.query(SalesOrder).filter(SalesOrder.id == record.sales_order_id).with_for_update().first()
        if not order:
            raise ValueError("关联订单不存在")

        old_total = order.total_amount or 0
        order.total_amount = round(old_total + (record.total_amount or 0), 2)
        record.status = "已作废"

        if record.return_type == "退回入库":
            product = db.query(Product).filter(Product.id == record.product_id).with_for_update().first()
            if not product:
                raise ValueError("产品不存在")
            product.current_stock = round((product.current_stock or 0) - record.quantity, 2)
            product.updated_at = now_cn()
            db.add(ProductTransaction(
                transaction_type="退货作废冲正",
                product_id=record.product_id,
                quantity=-record.quantity,
                unit=product.unit,
                source="return-void",
                related_id=record.id,
                operator=operator,
                notes=f"作废退货冲正 {order.order_no}",
            ))

        log_operation(db, operator, "作废退货", "return_records", return_id,
                      f"订单 {order.order_no} 退货加回：原额{old_total}→现额{order.total_amount}")
        db.commit()
        return {"id": return_id, "status": record.status, "order_total": order.total_amount}
    except Exception:
        db.rollback()
        raise


def get_order_returns(db: Session, order_id: int):
    returns = db.query(ReturnRecord).filter(
        ReturnRecord.sales_order_id == order_id,
    ).order_by(ReturnRecord.id.desc()).all()
    return [{
        "id": r.id, "date": str(r.date),
        "customer_id": r.customer_id, "sales_order_id": r.sales_order_id,
        "product_id": r.product_id,
        "product_name": r.product.name if r.product else "",
        "quantity": r.quantity, "unit_price": r.unit_price,
        "total_amount": r.total_amount, "return_type": r.return_type,
        "product_batch_ref": r.product_batch_ref,
        "status": r.status, "operator": r.operator or "",
        "notes": r.notes or "", "created_at": r.created_at,
    } for r in returns]


# ==================== BOM (v3.3) ====================

def get_bom(db: Session, product_id: int):
    """查看配方（全角色）"""
    rows = db.query(Bom).filter(Bom.product_id == product_id).order_by(Bom.id).all()
    if not rows:
        return None
    materials = {m.id: m for m in db.query(RawMaterial).filter(RawMaterial.id.in_([r.material_id for r in rows])).all()}
    items = []
    total_cost = 0.0
    has_price = False
    for r in rows:
        mat = materials.get(r.material_id)
        price = mat.purchase_price if mat else None
        line_cost = r.material_quantity * price if price is not None else None
        if line_cost is not None:
            total_cost += line_cost
            has_price = True
        items.append({
            "material_id": r.material_id,
            "material_name": mat.name if mat else "",
            "material_quantity": r.material_quantity,
            "material_unit": r.material_unit or (mat.unit if mat else ""),
            "purchase_price": price,
            "line_cost": round(line_cost, 2) if line_cost is not None else None,
        })
    return {
        "product_id": product_id,
        "base_quantity": rows[0].base_quantity,
        "base_unit": rows[0].base_unit,
        "items": items,
        "base_cost": round(total_cost, 2) if has_price else None,
        "unit_cost": round(total_cost / rows[0].base_quantity, 4) if has_price and rows[0].base_quantity else None,
    }


def save_bom(db: Session, product_id: int, data: BomSaveRequest, operator: str = "") -> dict:
    """整体替换保存（先删后插，事务内）——一个产品一份配方，无版本，历史靠 bom_snapshot"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("产品不存在")
        for item in data.items:
            mat = db.query(RawMaterial).filter(RawMaterial.id == item.material_id).first()
            if not mat:
                raise ValueError(f"原料ID {item.material_id} 不存在")
        db.query(Bom).filter(Bom.product_id == product_id).delete()
        for item in data.items:
            mat = db.query(RawMaterial).filter(RawMaterial.id == item.material_id).first()
            db.add(Bom(
                product_id=product_id,
                base_quantity=data.base_quantity,
                base_unit=data.base_unit,
                material_id=item.material_id,
                material_quantity=item.material_quantity,
                material_unit=item.material_unit or mat.unit or "",
            ))
        log_operation(db, operator, "保存配方", "boms", product_id,
                      f"{product.name} 每{data.base_quantity}{data.base_unit}：{len(data.items)}种原料")
        db.commit()
        return get_bom(db, product_id)
    except Exception:
        db.rollback()
        raise


def preview_bom(db: Session, data: BomPreviewRequest):
    """纯计算无副作用：按基准批量等比换算产量用料 + 库存够否预检（事前预检，后端提交时照旧校验双保险）"""
    rows = db.query(Bom).filter(Bom.product_id == data.product_id).order_by(Bom.id).all()
    if not rows:
        return {"has_bom": False, "items": []}
    base_qty = rows[0].base_quantity
    ratio = data.quantity / base_qty
    materials = {m.id: m for m in db.query(RawMaterial).filter(RawMaterial.id.in_([r.material_id for r in rows])).all()}
    items = []
    for r in rows:
        mat = materials.get(r.material_id)
        need = round(r.material_quantity * ratio, 4)
        stock = mat.current_stock if mat else 0
        items.append({
            "material_id": r.material_id,
            "material_name": mat.name if mat else "",
            "needed_quantity": need,
            "material_unit": r.material_unit or (mat.unit if mat else ""),
            "current_stock": stock,
            "sufficient": stock >= need,
        })
    return {
        "has_bom": True,
        "base_quantity": base_qty,
        "base_unit": rows[0].base_unit,
        "quantity": data.quantity,
        "ratio": round(ratio, 4),
        "items": items,
    }


# ==================== Cost Reports (v3.3) ====================

def get_cost_report(db: Session, year: int = None, month: int = None):
    """生产成本页：当月生产次数/总产量/原料消耗总额（Σ快照）+ 明细 + 产品维度汇总"""
    today = date.today()
    y = year or today.year
    m = month or today.month
    month_start = date(y, m, 1)
    month_end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)

    records = db.query(ProductionRecord).filter(
        ProductionRecord.date >= month_start,
        ProductionRecord.date < month_end,
    ).order_by(ProductionRecord.date.desc(), ProductionRecord.id.desc()).all()

    total_cost = sum(r.material_cost or 0 for r in records)
    total_quantity = sum(r.quantity or 0 for r in records)
    uncosted = sum(1 for r in records if r.material_cost is None)

    details = [{
        "id": r.id, "date": str(r.date), "product_id": r.product_id,
        "product_name": r.product.name if r.product else "",
        "quantity": r.quantity, "unit": r.unit or "",
        "material_cost": r.material_cost,
        "unit_cost": round(r.material_cost / r.quantity, 4) if r.material_cost is not None and r.quantity else None,
        "operator": r.operator or "",
    } for r in records]

    by_product = {}
    for r in records:
        key = r.product.name if r.product else f"产品#{r.product_id}"
        agg = by_product.setdefault(key, {"product_name": key, "quantity": 0, "cost": 0, "count": 0})
        agg["quantity"] += r.quantity or 0
        agg["cost"] += r.material_cost or 0
        agg["count"] += 1
    by_product_list = sorted(by_product.values(), key=lambda x: x["cost"], reverse=True)

    return {
        "year": y, "month": m,
        "total_count": len(records),
        "total_quantity": round(total_quantity, 2),
        "total_cost": round(total_cost, 2),
        "uncosted_count": uncosted,
        "details": details,
        "by_product": by_product_list,
    }


def get_gross_margin(db: Session, year: int = None, month: int = None):
    """月度粗毛利：当月订单收入 − 当月生产原料消耗（快照Σ）。
    口径注：不含人工/水电/房租/包装；生产与销售存在时间错位（3月生产4月卖）。"""
    today = date.today()
    y = year or today.year
    m = month or today.month
    month_start = date(y, m, 1)
    month_end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)

    revenue = db.query(func.coalesce(func.sum(SalesOrder.total_amount), 0)).filter(
        SalesOrder.date >= month_start,
        SalesOrder.date < month_end,
        SalesOrder.status != "已取消",
    ).scalar()

    cost = db.query(func.coalesce(func.sum(ProductionRecord.material_cost), 0)).filter(
        ProductionRecord.date >= month_start,
        ProductionRecord.date < month_end,
    ).scalar()

    margin = (revenue or 0) - (cost or 0)
    margin_pct = round(margin / revenue * 100, 1) if revenue else None

    return {
        "year": y, "month": m,
        "revenue": round(revenue or 0, 2),
        "material_cost": round(cost or 0, 2),
        "gross_margin": round(margin, 2),
        "margin_pct": margin_pct,
    }
