from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, ForeignKey, REAL
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, unique=True)
    phone = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    display_name = Column(Text)
    role = Column(Text, nullable=False, default="clerk")
    roles = Column(Text, nullable=False, default='["clerk"]')
    created_at = Column(DateTime, default=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    category = Column(Text)
    unit = Column(Text)
    spec = Column(Text)
    current_stock = Column(REAL, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("RawMaterial")


class ProductionRecord(Base):
    __tablename__ = "production_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    unit = Column(Text)
    sugar_degree = Column(REAL)
    raw_materials_used = Column(Text)
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")


class ShipmentRecord(Base):
    __tablename__ = "shipment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    customer_name = Column(Text)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    unit = Column(Text)
    unit_price = Column(REAL)
    total_amount = Column(REAL)
    status = Column(Text, default="待发货")
    operator = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(Text)
    action = Column(Text)
    table_name = Column(Text)
    record_id = Column(Integer)
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    contact = Column(Text)
    phone = Column(Text)
    address = Column(Text)
    category = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
