from kafka import KafkaConsumer
from api.db import SessionLocal
from api.models import StockLevel, Product
import json

consumer = KafkaConsumer(
    "stock-events",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    group_id="monitor-v1",
    auto_offset_reset="latest"
)

def update_stock(db, product_id, delta):
    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if stock:
        stock.quantity += delta
        db.commit()
        db.refresh(stock)
        return stock.quantity
    return None

print("Monitor started. Waiting for events...")

for message in consumer:
    event = message.value
    pid   = event["product_id"]
    delta = event["delta"]

    db = SessionLocal()
    try:
        new_stock = update_stock(db, pid, delta)
        product   = db.query(Product).filter(Product.id == pid).first()

        if new_stock is not None and product:
            print(f"[EVENT] product={pid} ({product.name}) | delta={delta} | new_stock={new_stock} | threshold={product.reorder_threshold}")

            if new_stock < product.reorder_threshold:
                print(f"[ALERT] {product.name} is LOW! Stock={new_stock} < Threshold={product.reorder_threshold} → agent will fire on Day 7")
    finally:
        db.close()