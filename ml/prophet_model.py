import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import pandas as pd
import numpy as np
import pickle
import os
import mlflow
from sqlalchemy import text
from api.db import engine

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("demand-forecast")

os.makedirs("ml/models", exist_ok=True)

def train_prophet(product_id, product_name):
    with engine.connect() as conn:
        df = pd.read_sql(
            f"SELECT sale_date, qty_sold FROM sales_history WHERE product_id = {product_id} ORDER BY sale_date",
            conn
        )

    df['sale_date'] = pd.to_datetime(df['sale_date'])
    df = df.sort_values('sale_date').reset_index(drop=True)

    split = int(len(df) * 0.85)
    train = df[:split]
    test  = df[split:]

    # Rolling average model (replaces Prophet on Windows)
    # Uses 7-day and 30-day weighted rolling average
    window_7  = train['qty_sold'].rolling(7,  min_periods=1).mean()
    window_30 = train['qty_sold'].rolling(30, min_periods=1).mean()

    last_7  = window_7.iloc[-1]
    last_30 = window_30.iloc[-1]

    # Add weekly seasonality manually
    daily_avg = train.copy()
    daily_avg['dow'] = daily_avg['sale_date'].dt.dayofweek
    dow_factors = daily_avg.groupby('dow')['qty_sold'].mean()
    overall_mean = daily_avg['qty_sold'].mean()
    dow_factors = dow_factors / overall_mean  # seasonality multiplier per weekday

    # Predict test set
    predictions = []
    for _, row in test.iterrows():
        dow = row['sale_date'].dayofweek
        factor = dow_factors.get(dow, 1.0)
        pred = (last_7 * 0.6 + last_30 * 0.4) * factor
        predictions.append(max(0, pred))

    pred_arr   = np.array(predictions)
    actual_arr = test['qty_sold'].values

    mae  = np.mean(np.abs(pred_arr - actual_arr))
    mape = np.mean(np.abs((pred_arr - actual_arr) / (actual_arr + 1))) * 100

    # Save model as dict (contains everything needed to predict)
    model_data = {
        'product_id':   product_id,
        'product_name': product_name,
        'last_7_avg':   last_7,
        'last_30_avg':  last_30,
        'dow_factors':  dow_factors.to_dict(),
        'type':         'rolling_seasonal'
    }

    with mlflow.start_run(run_name=f"prophet_{product_name}"):
        mlflow.log_param("product_id",   product_id)
        mlflow.log_param("product_name", product_name)
        mlflow.log_param("model_type",   "rolling_seasonal")
        mlflow.log_metric("mae",  round(mae,  2))
        mlflow.log_metric("mape", round(mape, 2))

    with open(f"ml/models/prophet_{product_id}.pkl", "wb") as f:
        pickle.dump(model_data, f)

    print(f" Prophet(rolling) {product_name} | MAE={mae:.1f} | MAPE={mape:.1f}%")

def predict_prophet(product_id, days=7):
    with open(f"ml/models/prophet_{product_id}.pkl", "rb") as f:
        model = pickle.load(f)

    last_7  = model['last_7_avg']
    last_30 = model['last_30_avg']
    factors = model['dow_factors']

    from datetime import datetime, timedelta
    preds = []
    for i in range(days):
        dow    = (datetime.today() + timedelta(days=i)).weekday()
        factor = factors.get(dow, 1.0)
        pred   = (last_7 * 0.6 + last_30 * 0.4) * factor
        preds.append(max(0, pred))

    return round(sum(preds), 1)

def train_all_prophet():
    with engine.connect() as conn:
        products = pd.read_sql("SELECT id, name FROM products", conn)

    print(f"Training Prophet(rolling) for {len(products)} products...")
    for _, row in products.iterrows():
        train_prophet(row['id'], row['name'])
    print(" All Prophet models trained!")

if __name__ == "__main__":
    train_all_prophet()