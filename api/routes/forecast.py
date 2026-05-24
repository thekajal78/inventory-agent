import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.db import get_db
from ml.ensemble import predict_demand

router = APIRouter()

@router.get("/forecast/{product_id}")
def get_forecast(product_id: int):
    result = predict_demand(product_id, days=7)
    return result

@router.get("/forecast/{product_id}/chart")
def get_forecast_chart(product_id: int, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT sale_date, qty_sold
        FROM sales_history
        WHERE product_id = :pid
        ORDER BY sale_date DESC
        LIMIT 30
    """), {"pid": product_id})
    actual = [{"date": str(r.sale_date), "value": r.qty_sold}
              for r in result]
    forecast = predict_demand(product_id, days=7)
    return {
        "actual":   actual,
        "forecast": forecast
    }