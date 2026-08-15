from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, ForeignKey, REAL, UniqueConstraint
from sqlalchemy.orm import relationship
from utils import now_cn
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(Text, unique=True, nullable=False)
    display_name = Column(Text)
    roles = Column(Text, nullable=False, default='["clerk"]')
    status = Column(Text, default="approved")
    created_at = Column(DateTime, default=now_cn)


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    category = Column(Text)
    unit = Column(Text)
    current_stock = Column(REAL, default=0)
    safety_stock = Column(REAL, default=0)
    supplier = Column(Text)
    supplier_id = Column(Integer, nullable=True)
    purchase_price = Column(REAL, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)
    updated_at = Column(DateTime, default=now_cn, onupdate=now_cn)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    category = Column(Text)
    unit = Column(Text)
    spec = Column(Text)
    current_stock = Column(REAL, default=0)
    # v3.1: 产品批次号前缀规则（产品批次=生产记录本身，不建产品批次表）
    production_batch_no_prefix = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)
    updated_at = Column(DateTime, default=now_cn, onupdate=now_cn)


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(Text, nullable=False)
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    unit = Column(Text)
    source = Column(Text)
    related_id = Column(Integer, default=0)
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)

    material = relationship("RawMaterial")


class ProductTransaction(Base):
    """产品库存流水（v3.0.7 新增）：盘点调整等直接作用于产品库存的变动留痕。
    注意：inventory_transactions.raw_material_id 是非空外键，产品侧变动无法复用——
    生产入库/发货扣减产品库存属于业务单据自身的留痕，不在此表。"""
    __tablename__ = "product_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(Text, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    unit = Column(Text)
    source = Column(Text)
    related_id = Column(Integer, default=0)
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)

    product = relationship("Product")


class ProductionRecord(Base):
    __tablename__ = "production_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    unit = Column(Text)
    sugar_degree = Column(REAL)
    raw_materials_used = Column(Text)
    # v3.3 成本快照：登记时算好写死，报表读快照不回算（批次价/配方后变历史不漂移）
    material_cost = Column(REAL)  # 该次生产原料成本（实际消耗法；None=登记时算不出）
    bom_snapshot = Column(Text)   # 本次生产提交的用量快照JSON（含手改/替代）
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)

    product = relationship("Product")


class Bom(Base):
    """产品配方（v3.3）：基准批量语义——每 base_quantity base_unit 用 material_quantity material_unit。
    一个产品一份配方，一料一行；改配方=整体替换（先删后插），历史靠 production_records.bom_snapshot 留底。"""
    __tablename__ = "boms"
    __table_args__ = (UniqueConstraint("product_id", "material_id", name="uq_bom_product_material"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    base_quantity = Column(REAL, nullable=False)
    base_unit = Column(Text, nullable=False)
    material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    material_quantity = Column(REAL, nullable=False)
    material_unit = Column(Text, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)
    updated_at = Column(DateTime, default=now_cn, onupdate=now_cn)


class ShipmentRecord(Base):
    __tablename__ = "shipment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    customer_name = Column(Text)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    unit = Column(Text)
    unit_price = Column(REAL)
    total_amount = Column(REAL)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=True)
    status = Column(Text, default="待发货")
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)

    product = relationship("Product")
    sales_order = relationship("SalesOrder")
    customer_rel = relationship("Customer")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(Text)
    action = Column(Text)
    table_name = Column(Text)
    record_id = Column(Integer)
    detail = Column(Text)
    created_at = Column(DateTime, default=now_cn)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    contact = Column(Text)
    phone = Column(Text)
    address = Column(Text)
    type = Column(Text)
    level = Column(Text, default="普通")
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)
    updated_at = Column(DateTime, default=now_cn, onupdate=now_cn)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    contact = Column(Text)
    phone = Column(Text)
    address = Column(Text)
    category = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)
    updated_at = Column(DateTime, default=now_cn, onupdate=now_cn)


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(Text, unique=True)
    date = Column(Date, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    items = Column(Text)
    total_amount = Column(REAL, default=0)
    status = Column(Text, default="待发货")
    payment_status = Column(Text, default="未付款")
    paid_amount = Column(REAL, default=0)
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)

    customer = relationship("Customer")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(Text, unique=True)
    date = Column(Date, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    items = Column(Text)
    total_amount = Column(REAL, default=0)
    # v3.2: 供应商付款（与 sales_orders 对称）
    paid_amount = Column(REAL, default=0)
    payment_status = Column(Text, default="未付款")
    status = Column(Text, default="待到货")
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)

    supplier = relationship("Supplier")


class PurchasePayment(Base):
    """供应商付款流水（v3.2）：只作废不物理删（与盘点流水同一哲学）"""
    __tablename__ = "purchase_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    amount = Column(REAL, nullable=False)
    date = Column(Date, nullable=False)
    method = Column(Text)  # 转账/现金/承兑，自由文本
    status = Column(Text, default="有效")  # 有效/已作废
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)


class LabRecord(Base):
    __tablename__ = "lab_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    name = Column(Text)
    recipe = Column(Text)
    process_params = Column(Text)
    result = Column(Text)
    score = Column(REAL)
    notes = Column(Text)
    operator = Column(Text)
    created_at = Column(DateTime, default=now_cn)


class UsageLog(Base):
    """领用记录台账（v3.4）：生产登记事务内自动写入，N种料=N行，回滚一起消失。
    material_name/category 刻意冗余——台账监管语义是"当时发生了什么"，
    主档改名后历史不漂移（与 v3.3 material_cost 快照同一哲学）。只读，无编辑/删除。"""
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)  # 生产日期（非提交时间）
    material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    material_name = Column(Text, nullable=False)
    category = Column(Text)
    quantity = Column(REAL, nullable=False)
    unit = Column(Text)
    stock_after = Column(REAL)  # 领用后库存余量（监管看点）
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(Text)  # 用途："生产 草莓果酱 300盒"
    production_quantity = Column(REAL)
    production_id = Column(Integer, ForeignKey("production_records.id"))
    source = Column(Text, default="production")  # production / lab
    related_id = Column(Integer)  # lab时=lab_records.id
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)


class MaterialBatch(Base):
    """原料批次（v3.1）：采购入库时可选创建，生产按FEFO消耗。
    未填批次的入库不建记录——历史"未分批"库存走兼容层。"""
    __tablename__ = "material_batches"
    __table_args__ = (UniqueConstraint("material_id", "batch_no", name="uq_batch_material_no"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    batch_no = Column(Text, nullable=False)
    quantity_in = Column(REAL, nullable=False)
    quantity_remaining = Column(REAL, nullable=False)
    unit_price = Column(REAL)  # 本批进价，v3.2 成本核算（移动加权）直接用
    production_date = Column(Date)  # 供应商标签上的生产日期
    expiry_date = Column(Date)  # 保质期到，空=不管理
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    status = Column(Text, default="在库")  # 在库/耗尽/报废
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)

    material = relationship("RawMaterial")
    supplier = relationship("Supplier")


class BatchUsage(Base):
    """批次消耗明细（v3.1）：一次生产消耗N个批次=N行。
    设计依据：多批次消耗单字段外键装不下（CC提醒），用关联表。"""
    __tablename__ = "batch_usages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    production_id = Column(Integer, ForeignKey("production_records.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("material_batches.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    created_at = Column(DateTime, default=now_cn)

    batch = relationship("MaterialBatch")


class ReturnRecord(Base):
    """销售退货（v3.2 预埋，本版只建表不建路由）：退回入库/报废退回两路径"""
    __tablename__ = "return_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    unit_price = Column(REAL)
    total_amount = Column(REAL)
    return_type = Column(Text, nullable=False)  # 退回入库 / 报废退回
    product_batch_ref = Column(Text)  # 退回的是哪个生产批次（文本引用，轻量）
    status = Column(Text, default="有效")  # 有效/已作废
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_cn)

    product = relationship("Product")
