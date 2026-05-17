import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from api.db import engine, Base
from api.models import Product, StockLevel, Supplier, SalesHistory
import random
from datetime import datetime, timedelta

# Create all tables
Base.metadata.create_all(bind=engine)

db = Session(engine)

# Clear existing data
db.query(SalesHistory).delete()
db.query(StockLevel).delete()
db.query(Product).delete()
db.query(Supplier).delete()
db.commit()

# Create 20 products
categories = ["electronics", "clothing", "food", "furniture", "sports"]
products = []
for i in range(1, 21):
    p = Product(
        sku=f"SKU-{i:04d}",
        name=f"Product {i}",
        category=random.choice(categories),
        unit_cost=round(random.uniform(10, 500), 2),
        reorder_qty=random.randint(50, 200),
        reorder_threshold=random.randint(10, 50)
    )
    db.add(p)
    products.append(p)

db.commit()

# Create stock levels
for p in products:
    sl = StockLevel(
        product_id=p.id,
        quantity=random.randint(5, 100)
    )
    db.add(sl)

db.commit()

# Create 3 suppliers
suppliers_data = [
    {"name": "TechParts Ltd", "email": "tech@parts.com", "lead_time_days": 2,
     "reliability": 0.96, "cost_per_unit": 280, "min_order_qty": 50, "payment_terms": "Net-30"},
    {"name": "GlobalGoods", "email": "info@globalgoods.com", "lead_time_days": 7,
     "reliability": 0.85, "cost_per_unit": 200, "min_order_qty": 100, "payment_terms": "Net-60"},
    {"name": "FastShip Co", "email": "orders@fastship.com", "lead_time_days": 1,
     "reliability": 0.92, "cost_per_unit": 320, "min_order_qty": 25, "payment_terms": "Net-15"},
]

for s in suppliers_data:
    supplier = Supplier(**s)
    db.add(supplier)

db.commit()

# Create 730 days of sales history
print("Creating sales history...")
start_date = datetime.now() - timedelta(days=730)

for day in range(730):
    current_date = start_date + timedelta(days=day)
    month = current_date.month
    is_weekend = current_date.weekday() >= 5

    for p in products:
        base_qty = random.randint(5, 20)

        # Seasonality
        if month in [11, 12]:
            base_qty = int(base_qty * 1.5)
        elif month in [1, 2]:
            base_qty = int(base_qty * 0.7)

        if is_weekend:
            base_qty = int(base_qty * 1.2)

        sale = SalesHistory(
            product_id=p.id,
            qty_sold=base_qty,
            sale_date=current_date,
            price=float(p.unit_cost) * random.uniform(1.2, 1.8),
            channel=random.choice(["online", "store", "wholesale"]),
            promo_flag=random.random() < 0.1
        )
        db.add(sale)

    if day % 100 == 0:
        db.commit()
        print(f"Day {day}/730 done...")

db.commit()
print("✅ Seed complete! 14600 sales rows created.")
db.close()