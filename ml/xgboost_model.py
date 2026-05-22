import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import pandas as pd
import numpy as np
import pickle
import os
import mlflow
from xgboost import XGBRegressor
from sqlalchemy import text
from api.db import engine

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("demand-forecast")

os.makedirs("ml/models", exist_ok=True)

FEATURES = [
    "day_of_week", "month", "quarter", "is_weekend",
    "is_month_end", "week_of_year",
    "lag_1", "lag_7", "lag_14", "lag_30",
    "roll_mean_7", "roll_mean_14", "roll_mean_30"
]

def train_xgboost(product_id, product_name):
    with engine.connect() as conn:
        df = pd.read_sql(
            f"SELECT * FROM feature_store WHERE product_id = {product_id} ORDER BY sale_date",
            conn
        )

    if len(df) < 50:
        print(f" Skipping {product_name} — not enough data")
        return

    available = [f for f in FEATURES if f in df.columns]
    X = df[available]
    y = df["qty_sold"]

    split = int(len(df) * 0.85)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train)

    pred   = model.predict(X_test)
    mae    = np.mean(np.abs(pred - y_test.values))
    mape   = np.mean(np.abs((pred - y_test.values) / (y_test.values + 1))) * 100

    with mlflow.start_run(run_name=f"xgboost_{product_name}"):
        mlflow.log_param("product_id",   product_id)
        mlflow.log_param("product_name", product_name)
        mlflow.log_metric("mae",  round(mae,  2))
        mlflow.log_metric("mape", round(mape, 2))

    with open(f"ml/models/xgboost_{product_id}.pkl", "wb") as f:
        pickle.dump(model, f)

    print(f" XGBoost {product_name} | MAE={mae:.1f} | MAPE={mape:.1f}%")

def predict_xgboost(product_id, days=7):
    with open(f"ml/models/xgboost_{product_id}.pkl", "rb") as f:
        model = pickle.load(f)

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

def train_all_xgboost():
    with engine.connect() as conn:
        products = pd.read_sql("SELECT id, name FROM products", conn)

    print(f"Training XGBoost for {len(products)} products...")
    for _, row in products.iterrows():
        train_xgboost(row['id'], row['name'])
    print(" All XGBoost models trained!")

if __name__ == "__main__":
    train_all_xgboost()