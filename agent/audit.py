import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import json
from datetime import datetime
from sqlalchemy import text
from api.db import engine

def log_decision(state: dict, auto_executed: bool):
    try:
        decision_json = json.dumps(state.get("decision", {}))
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO agent_decisions (
                    product_id, trigger_stock, forecast_demand,
                    selected_supplier, recommended_qty, confidence,
                    po_id, auto_executed, decision_json, created_at
                ) VALUES (
                    :product_id, :trigger_stock, :forecast_demand,
                    :selected_supplier, :recommended_qty, :confidence,
                    :po_id, :auto_executed, :decision_json, :created_at
                )
            """), {
                "product_id":       state["product_id"],
                "trigger_stock":    state["current_stock"],
                "forecast_demand":  state["forecast"].get("ensemble", 0),
                "selected_supplier": state["decision"].get("selected_supplier", "unknown"),
                "recommended_qty":  state["decision"].get("recommended_qty", 0),
                "confidence":       state["confidence"],
                "po_id":            state.get("po_reference", "PENDING"),
                "auto_executed":    auto_executed,
                "decision_json":    decision_json,
                "created_at":       datetime.utcnow()
            })
        print(f" Decision logged to audit trail")
    except Exception as e:
        print(f"Audit log failed: {e}")