import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

from datetime import datetime, timedelta
from sqlalchemy import text
from api.db import engine

def raise_purchase_order(product_id, product_name, supplier_name,
                          qty, unit_cost=0, urgency="NORMAL",
                          confidence=0.0, reason=""):
    try:
        po_ref    = f"PO-{product_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        est_cost  = qty * unit_cost if unit_cost else qty * 100

        # Expected delivery based on urgency
        lead_days = 1 if urgency == "CRITICAL" else 3 if urgency == "WARNING" else 7
        expected  = datetime.utcnow() + timedelta(days=lead_days)

        with engine.begin() as conn:
            # Insert into purchase_orders table
            conn.execute(text("""
                INSERT INTO purchase_orders (
                    po_reference, product_id, product_name,
                    supplier_name, quantity, unit_cost, total_cost,
                    status, urgency, agent_confidence, agent_reason,
                    created_at, expected_delivery
                ) VALUES (
                    :po_ref, :product_id, :product_name,
                    :supplier_name, :qty, :unit_cost, :total_cost,
                    :status, :urgency, :confidence, :reason,
                    :created_at, :expected_delivery
                )
            """), {
                "po_ref":            po_ref,
                "product_id":        product_id,
                "product_name":      product_name,
                "supplier_name":     supplier_name,
                "qty":               qty,
                "unit_cost":         unit_cost if unit_cost else 100,
                "total_cost":        est_cost,
                "status":            "RAISED",
                "urgency":           urgency,
                "confidence":        confidence,
                "reason":            reason,
                "created_at":        datetime.utcnow(),
                "expected_delivery": expected
            })

            # Also log to stock_movements
            conn.execute(text("""
                INSERT INTO stock_movements (
                    product_id, delta, reason, reference, occurred_at
                ) VALUES (
                    :product_id, :delta, :reason, :reference, :occurred_at
                )
            """), {
                "product_id":  product_id,
                "delta":       qty,
                "reason":      f"PO raised — {supplier_name}",
                "reference":   po_ref,
                "occurred_at": datetime.utcnow()
            })

        print(f" PO raised: {po_ref}")
        print(f"   {qty} units from {supplier_name} | "
              f"Est cost: Rs {est_cost:,} | "
              f"Expected delivery: {expected.strftime('%d %b %Y')}")
        return po_ref

    except Exception as e:
        fallback = f"PENDING-{product_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        print(f" ERP failed, fallback ref: {fallback} | Error: {e}")
        return fallback

def get_all_pos():
    with engine.connect() as conn:
        import pandas as pd
        return pd.read_sql("""
            SELECT po_reference, product_name, supplier_name,
                   quantity, total_cost, status, urgency,
                   agent_confidence, created_at, expected_delivery
            FROM purchase_orders
            ORDER BY created_at DESC
        """, conn)

def approve_po(po_reference, approved_by="Manager"):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE purchase_orders
            SET status='APPROVED', approved_by=:approved_by,
                approved_at=:approved_at
            WHERE po_reference=:po_ref
        """), {
            "approved_by":  approved_by,
            "approved_at":  datetime.utcnow(),
            "po_ref":       po_reference
        })
    print(f" PO {po_reference} approved by {approved_by}")

def reject_po(po_reference, rejected_by="Manager"):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE purchase_orders
            SET status='REJECTED', approved_by=:rejected_by,
                approved_at=:approved_at
            WHERE po_reference=:po_ref
        """), {
            "rejected_by":  rejected_by,
            "approved_at":  datetime.utcnow(),
            "po_ref":       po_reference
        })
    print(f"PO {po_reference} rejected by {rejected_by}")

if __name__ == "__main__":
    print("Current Purchase Orders:")
    print("=" * 60)
    pos = get_all_pos()
    if len(pos) == 0:
        print("No POs yet")
    else:
        for _, po in pos.iterrows():
            print(f"{po['po_reference']} | {po['product_name']:15} | "
                  f"{po['supplier_name']:15} | {po['quantity']:4} units | "
                  f"Rs {po['total_cost']:8,.0f} | {po['status']}")