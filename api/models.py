from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from api.db import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    unit_cost = Column(Numeric(10,2))
    reorder_qty = Column(Integer)
    reorder_threshold = Column(Integer)
    stock_level = relationship("StockLevel", back_populates="product", uselist=False)
    stock_movements = relationship("StockMovement", back_populates="product")

class StockLevel(Base):
    __tablename__ = "stock_levels"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="stock_level")

class StockMovement(Base):
    __tablename__ = "stock_movements"
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    delta = Column(Integer)
    reason = Column(Text)
    reference = Column(Text)
    occurred_at = Column(DateTime, default=datetime.utcnow, primary_key=True)
    product = relationship("Product", back_populates="stock_movements")

class SalesHistory(Base):
    __tablename__ = "sales_history"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    qty_sold = Column(Integer)
    sale_date = Column(DateTime)
    price = Column(Numeric(10,2))
    channel = Column(String(50))
    promo_flag = Column(Boolean, default=False)

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    lead_time_days = Column(Integer)
    reliability = Column(Numeric(3,2))
    cost_per_unit = Column(Numeric(10,2))
    min_order_qty = Column(Integer)
    payment_terms = Column(String(50))

class AgentDecision(Base):
    __tablename__ = "agent_decisions"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    trigger_stock = Column(Integer)
    forecast_demand = Column(Numeric(10,2))
    selected_supplier = Column(String(100))
    recommended_qty = Column(Integer)
    confidence = Column(Numeric(4,2))
    po_id = Column(String(100))
    auto_executed = Column(Boolean, default=False)
    decision_json = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)