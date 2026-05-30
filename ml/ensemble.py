import pickle
import os
import torch
import torch.nn as nn
import numpy as np

SEQ_LEN  = 30
PRED_LEN = 7

class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm   = nn.LSTM(1, 64, num_layers=2, batch_first=True, dropout=0.2)
        self.linear = nn.Linear(64, PRED_LEN)
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.linear(out[:, -1, :])

def predict_prophet(product_id, days=7):
    path = f"ml/models/prophet_{product_id}.pkl"
    if not os.path.exists(path):
        return 0.0
    with open(path, "rb") as f:
        model = pickle.load(f)

    from datetime import datetime, timedelta
    last_7  = model['last_7_avg']
    last_30 = model['last_30_avg']
    factors = model['dow_factors']

    preds = []
    for i in range(days):
        dow    = (datetime.today() + timedelta(days=i)).weekday()
        factor = factors.get(dow, 1.0)
        pred   = (last_7 * 0.6 + last_30 * 0.4) * factor
        preds.append(max(0, pred))
    return round(sum(preds), 1)

def predict_xgboost(product_id, days=7):
    path = f"ml/models/xgboost_{product_id}.pkl"
    if not os.path.exists(path):
        return 0.0

    from api.db import engine
    import pandas as pd

    with open(path, "rb") as f:
        model = pickle.load(f)

    FEATURES = [
        "day_of_week", "month", "quarter", "is_weekend",
        "is_month_end", "week_of_year",
        "lag_1", "lag_7", "lag_14", "lag_30",
        "roll_mean_7", "roll_mean_14", "roll_mean_30"
    ]

    with engine.connect() as conn:
        df = pd.read_sql(
            f"SELECT * FROM feature_store WHERE product_id = {product_id} ORDER BY sale_date DESC LIMIT 30",
            conn
        )
    df = df.sort_values("sale_date")
    available = [f for f in FEATURES if f in df.columns]
    last_row  = df[available].iloc[[-1]]
    pred_per_day = max(0, float(model.predict(last_row)[0]))
    return round(pred_per_day * days, 1)

def predict_lstm(product_id, days=7):
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    path = f"ml/models/lstm_{product_id}.pt"
    if not os.path.exists(path):
        return 0.0

    data  = torch.load(path, weights_only=False)
    vmax  = data['vmax']
    seq   = torch.FloatTensor(data['last_seq']).unsqueeze(0).unsqueeze(-1)

    model = LSTMModel()
    model.load_state_dict(data['model_state'])
    model.eval()

    with torch.no_grad():
        pred = model(seq).numpy()[0] * vmax

    return round(float(pred[:days].sum()), 1)

def predict_demand(product_id, days=7):
    p = predict_prophet(product_id,  days)
    x = predict_xgboost(product_id,  days)
    l = predict_lstm(product_id,     days)

    # Weighted ensemble
    ensemble = p * 0.30 + x * 0.45 + l * 0.25

    # Confidence — how much do the 3 models agree
    values   = [v for v in [p, x, l] if v > 0]
    if len(values) < 2:
        confidence = 70.0
    else:
        spread     = max(values) - min(values)
        avg        = sum(values) / len(values)
        confidence = max(60.0, min(95.0, 95.0 - (spread / (avg + 1)) * 30))

    return {
        "product_id":    product_id,
        "days":          days,
        "prophet":       round(p,        1),
        "xgboost":       round(x,        1),
        "lstm":          round(l,        1),
        "ensemble":      round(ensemble, 1),
        "confidence_pct": round(confidence, 1)
    }

if __name__ == "__main__":
    from api.db import engine
    import pandas as pd
    with engine.connect() as conn:
        products = pd.read_sql("SELECT id, name FROM products", conn)

    print("Testing ensemble predictions...")
    for _, row in products.iterrows():
        result = predict_demand(row['id'], days=7)
        print(f"  {row['name']:15} | ensemble={result['ensemble']:6.1f} | "
              f"confidence={result['confidence_pct']}%")