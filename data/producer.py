from kafka import KafkaProducer
import json
from datetime import datetime, timezone

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all"
)

def publish_stock_event(product_id, delta, reason, reference=""):
    event = {
        "product_id": product_id,
        "delta": delta,
        "reason": reason,
        "reference": reference,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    producer.send("stock-events", key=str(product_id).encode(), value=event)
    producer.flush()
    print(f"Published: product={product_id} delta={delta} reason={reason}")