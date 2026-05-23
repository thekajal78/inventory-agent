import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

from datetime import datetime
from sqlalchemy import text
from api.db import engine

def raise_purchase_order(product_id, product_name, supplier_name, qty, unit_cost=0):
    try:
        po_ref = f"PO-{product_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        est_cost = qty * unit_cost if unit_cost else qty * 100

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO stock_movements (
                    product_id, delta, reason, reference, occurred_at
                ) VALUES (
                    :product_id, :delta, :reason, :reference, :occurred_at
                )
            """), {
                "product_id":  product_id,
                "delta":       qty,
                "reason":      f"Purchase Order raised — supplier: {supplier_name}",
                "reference":   po_ref,
                "occurred_at": datetime.utcnow()
            })

        print(f" PO raised: {po_ref} | {qty} units from {supplier_name} | Est cost: ₹{est_cost:,}")
        return po_ref

    except Exception as e:
        fallback = f"PENDING-{product_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        print(f" ERP failed, fallback ref: {fallback} | Error: {e}")
        return fallback