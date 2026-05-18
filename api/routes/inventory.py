from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.db import get_db
from api.models import Product, StockLevel, SalesHistory
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/inventory/stock")
def get_stock(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    result = []

    for p in products:
        # Get current stock
        stock = db.query(StockLevel).filter(
            StockLevel.product_id == p.id
        ).first()

        current_stock = stock.quantity if stock else 0

        # Get 7-day average daily sales
        seven_days_ago = datetime.now() - timedelta(days=7)
        total_sold = db.query(func.sum(SalesHistory.qty_sold)).filter(
            SalesHistory.product_id == p.id,
            SalesHistory.sale_date >= seven_days_ago
        ).scalar() or 0

        avg_daily_sales = total_sold / 7

        # Calculate days of inventory
        doi = round(current_stock / avg_daily_sales, 2) if avg_daily_sales > 0 else 999

        # Status
        status = "low" if current_stock < p.reorder_threshold else "ok"

        result.append({
            "product_id": p.id,
            "product_name": p.name,
            "sku": p.sku,
            "current_stock": current_stock,
            "reorder_threshold": p.reorder_threshold,
            "avg_daily_sales": round(avg_daily_sales, 2),
            "days_of_inventory": doi,
            "status": status
        })

    return result