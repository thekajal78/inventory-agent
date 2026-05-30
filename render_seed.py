import os
os.environ['DB_URL'] = 'postgresql://inventory_db_901g_user:7ij87DOgz2rRcTX8c0ktDCFiy2thzo1x@dpg-d8c1vd9o3t8c73au2n40-a.oregon-postgres.render.com/inventory_db_901g'

from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
from datetime import datetime

engine = create_engine(os.environ['DB_URL'])

df = pd.read_csv('data/train.csv/train.csv')
df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True)

product_sales = df.groupby(['Product ID', 'Product Name', 'Category', 'Sub-Category']).agg(
    total_qty=('Sales', 'count'), total_sales=('Sales', 'sum')
).reset_index()

top_products = product_sales.nlargest(150, 'total_qty').reset_index(drop=True)
print(f'Selected {len(top_products)} products')

product_id_map = {}
with engine.begin() as conn:
    conn.execute(text('DELETE FROM sales_history WHERE 1=1'))
    conn.execute(text('DELETE FROM stock_levels WHERE 1=1'))
    conn.execute(text('DELETE FROM products WHERE 1=1'))
    for i, row in top_products.iterrows():
        sku = f'SS-{str(i+1).zfill(4)}'
        result = conn.execute(text("""
            INSERT INTO products (sku, name, category, unit_cost, reorder_threshold, reorder_qty)
            VALUES (:sku, :name, :cat, :cost, :thresh, :rqty) RETURNING id
        """), {
            'sku': sku, 'name': row['Product Name'][:100], 'cat': row['Sub-Category'],
            'cost': round(row['total_sales']/max(row['total_qty'],1), 2),
            'thresh': max(10, int(row['total_qty']*0.1)),
            'rqty': max(20, int(row['total_qty']*0.2))
        })
        product_id_map[row['Product ID']] = result.fetchone()[0]

print(f'Inserted {len(product_id_map)} products')

sales_rows = []
for orig, new in product_id_map.items():
    for _, s in df[df['Product ID']==orig].iterrows():
        sales_rows.append({
            'product_id': new, 'qty_sold': max(1, int(abs(s['Sales'])/50)+1),
            'sale_date': s['Order Date'].date(), 'price': round(float(s['Sales']), 2),
            'channel': 'retail', 'promo_flag': False
        })

with engine.begin() as conn:
    for i in range(0, len(sales_rows), 500):
        conn.execute(text("""
            INSERT INTO sales_history (product_id, qty_sold, sale_date, price, channel, promo_flag)
            VALUES (:product_id, :qty_sold, :sale_date, :price, :channel, :promo_flag)
        """), sales_rows[i:i+500])
    print(f'Inserted {len(sales_rows)} sales rows')

    for orig, new in product_id_map.items():
        qty = np.random.randint(5, 30)
        conn.execute(text('INSERT INTO stock_levels (product_id, quantity, updated_at) VALUES (:pid, :qty, :now)'),
            {'pid': new, 'qty': int(qty), 'now': datetime.utcnow()})

    conn.execute(text('DELETE FROM suppliers WHERE 1=1'))
    conn.execute(text("""
        INSERT INTO suppliers (name, email, lead_time_days, reliability, cost_per_unit, min_order_qty, payment_terms)
        VALUES
        ('OfficeMax Supply Co', 'orders@officemax.com', 2, 0.96, 45.00, 50, 'Net-30'),
        ('Global Furniture Ltd', 'supply@globalfurniture.com', 7, 0.85, 120.00, 20, 'Net-60'),
        ('TechDirect Express', 'orders@techdirect.com', 1, 0.92, 85.00, 25, 'Net-15')
    """))
    print('Suppliers inserted!')

print('Done! Render database seeded successfully.')