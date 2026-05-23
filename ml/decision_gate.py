import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

from ml.ensemble import predict_demand

def should_trigger_agent(product_id, current_stock, threshold, daily_demand=None):
    forecast     = predict_demand(product_id, days=7)
    ensemble_7d  = forecast["ensemble"]

    # Days of inventory remaining
    burn_rate = daily_demand if daily_demand else (ensemble_7d / 7)
    doi       = current_stock / burn_rate if burn_rate > 0 else 999

    condition_1 = current_stock < threshold           # raw threshold breach
    condition_2 = doi < 3                             # stockout in less than 3 days
    condition_3 = ensemble_7d > current_stock * 1.5  # demand far exceeds stock

    triggered = condition_1 or condition_2 or condition_3

    return {
        "triggered":     triggered,
        "current_stock": current_stock,
        "threshold":     threshold,
        "doi":           round(doi, 1),
        "forecast_7d":   ensemble_7d,
        "confidence":    forecast["confidence_pct"],
        "reason":        (
            "Stock below threshold" if condition_1 else
            "Stockout in <3 days"   if condition_2 else
            "Demand exceeds stock"  if condition_3 else
            "Stock sufficient"
        )
    }

if __name__ == "__main__":
    from api.db import engine
    import pandas as pd

    with engine.connect() as conn:
        rows = pd.read_sql("""
            SELECT p.id, p.name, p.reorder_threshold, p.reorder_qty,
                   s.quantity as current_stock
            FROM products p
            JOIN stock_levels s ON s.product_id = p.id
        """, conn)

    print("Running decision gate for all products...\n")
    triggered_count = 0
    for _, row in rows.iterrows():
        result = should_trigger_agent(
            row['id'], row['current_stock'], row['reorder_threshold']
        )
        status = " TRIGGER" if result['triggered'] else "OK"
        print(f"{status} {row['name']:15} | stock={row['current_stock']:4} | "
              f"doi={result['doi']:5.1f}d | forecast={result['forecast_7d']:6.1f} | "
              f"{result['reason']}")
        if result['triggered']:
            triggered_count += 1

    print(f"\n{triggered_count}/{len(rows)} products need reordering")