import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")
import os
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import text
from api.db import engine

TOP_N_PRODUCTS = 150
CSV_PATH = "data/train.csv" if os.path.exists("data/train.csv") else "data/train.csv/train.csv"

def load_superstore():
    print("Loading Superstore dataset...")

    df = pd.read_csv(CSV_PATH)
    print(f"Total rows: {len(df)}")

    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True)

    product_sales = df.groupby(['Product ID', 'Product Name', 'Category', 'Sub-Category']).agg(
        total_qty=('Sales', 'count'),
        total_sales=('Sales', 'sum')
    ).reset_index()

    top_products = product_sales.nlargest(TOP_N_PRODUCTS, 'total_qty').reset_index(drop=True)
    print(f"Selected {len(top_products)} products")

    print("Clearing existing data...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM agent_decisions WHERE 1=1"))
        conn.execute(text("""
            DO $$ BEGIN
                IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'purchase_orders') THEN
                    DELETE FROM purchase_orders;
                END IF;
            END $$;
        """))
        conn.execute(text("DELETE FROM stock_movements WHERE 1=1"))
        conn.execute(text("DELETE FROM sales_history WHERE 1=1"))
        conn.execute(text("DELETE FROM stock_levels WHERE 1=1"))
        conn.execute(text("DELETE FROM products WHERE 1=1"))

    print("Inserting products...")
    product_id_map = {}

    with engine.begin() as conn:
        for i, row in top_products.iterrows():
            sku = f"SS-{str(i+1).zfill(4)}"
            name = row['Product Name'][:100]
            category = row['Sub-Category']
            unit_cost = round(row['total_sales'] / max(row['total_qty'], 1), 2)
            reorder_threshold = max(10, int(row['total_qty'] * 0.1))
            reorder_qty = max(20, int(row['total_qty'] * 0.2))

            result = conn.execute(text("""
                INSERT INTO products (sku, name, category, unit_cost, reorder_threshold, reorder_qty)
                VALUES (:sku, :name, :category, :unit_cost, :threshold, :reorder_qty)
                RETURNING id
            """), {
                "sku": sku, "name": name, "category": category,
                "unit_cost": unit_cost, "threshold": reorder_threshold,
                "reorder_qty": reorder_qty
            })
            new_id = result.fetchone()[0]
            product_id_map[row['Product ID']] = new_id

    print(f" Inserted {len(product_id_map)} products")

    print("Inserting sales history...")
    sales_rows = []

    for orig_pid, new_pid in product_id_map.items():
        prod_sales = df[df['Product ID'] == orig_pid].copy()
        for _, sale in prod_sales.iterrows():
            qty = max(1, int(abs(sale['Sales']) / 50) + 1)
            sales_rows.append({
                "product_id": new_pid,
                "qty_sold": qty,
                "sale_date": sale['Order Date'].date(),
                "price": round(float(sale['Sales']), 2),
                "channel": "retail",
                "promo_flag": False
            })

    batch_size = 500
    total = len(sales_rows)
    with engine.begin() as conn:
        for i in range(0, total, batch_size):
            batch = sales_rows[i:i+batch_size]
            conn.execute(text("""
                INSERT INTO sales_history (product_id, qty_sold, sale_date, price, channel, promo_flag)
                VALUES (:product_id, :qty_sold, :sale_date, :price, :channel, :promo_flag)
            """), batch)
            print(f"  Inserted {min(i+batch_size, total)}/{total} sales rows...")

    print(f" Inserted {total} sales rows")

    print("Inserting stock levels...")
    with engine.begin() as conn:
        for orig_pid, new_pid in product_id_map.items():
            prod_df = df[df['Product ID'] == orig_pid]
            avg_monthly = len(prod_df) * 2
            current_stock = np.random.randint(
                max(5, int(avg_monthly * 0.1)),
                max(20, int(avg_monthly * 0.8))
            )
            conn.execute(text("""
                INSERT INTO stock_levels (product_id, quantity, updated_at)
                VALUES (:pid, :qty, :now)
            """), {"pid": new_pid, "qty": int(current_stock), "now": datetime.utcnow()})

    print(f" Stock levels inserted")

    print("Inserting suppliers...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM suppliers WHERE 1=1"))
        conn.execute(text("""
            INSERT INTO suppliers (name, email, lead_time_days, reliability, cost_per_unit, min_order_qty, payment_terms)
            VALUES
            ('OfficeMax Supply Co', 'orders@officemax.com', 2, 0.96, 45.00, 50, 'Net-30'),
            ('Global Furniture Ltd', 'supply@globalfurniture.com', 7, 0.85, 120.00, 20, 'Net-60'),
            ('TechDirect Express', 'orders@techdirect.com', 1, 0.92, 85.00, 25, 'Net-15')
        """))

    print(" Suppliers inserted")
    print("\n Superstore dataset loaded successfully!")
    print(f"   Products: {len(product_id_map)}")
    print(f"   Sales rows: {total}")
    print(f"   Suppliers: 3")

if __name__ == "__main__":
    load_superstore()