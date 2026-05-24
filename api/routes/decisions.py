from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.db import get_db

router = APIRouter()

@router.get("/decisions")
def get_decisions(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT id, product_id, trigger_stock, forecast_demand,
               selected_supplier, recommended_qty, confidence,
               po_id, auto_executed, created_at
        FROM agent_decisions
        ORDER BY created_at DESC
        LIMIT 50
    """))
    rows = [dict(row._mapping) for row in result]
    return {"decisions": rows, "total": len(rows)}

@router.patch("/decisions/{decision_id}/approve")
def approve_decision(decision_id: int, db: Session = Depends(get_db)):
    db.execute(text("""
        UPDATE agent_decisions
        SET auto_executed = true
        WHERE id = :id
    """), {"id": decision_id})
    db.commit()
    return {"message": "Decision approved", "id": decision_id}

@router.patch("/decisions/{decision_id}/reject")
def reject_decision(decision_id: int, db: Session = Depends(get_db)):
    db.execute(text("""
        UPDATE agent_decisions
        SET auto_executed = false
        WHERE id = :id
    """), {"id": decision_id})
    db.commit()
    return {"message": "Decision rejected", "id": decision_id}

@router.get("/purchase-orders")
def get_purchase_orders(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT po_reference, product_name, supplier_name,
               quantity, total_cost, status, urgency,
               agent_confidence, created_at, expected_delivery
        FROM purchase_orders
        ORDER BY created_at DESC
        LIMIT 50
    """))
    rows = [dict(row._mapping) for row in result]
    return {"orders": rows, "total": len(rows)}