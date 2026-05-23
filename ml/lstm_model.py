import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import pandas as pd
import numpy as np
import pickle
import os
import mlflow
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from api.db import engine

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("demand-forecast")

os.makedirs("ml/models", exist_ok=True)

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

def make_sequences(data, seq_len, pred_len):
    X, y = [], []
    for i in range(len(data) - seq_len - pred_len + 1):
        X.append(data[i : i + seq_len])
        y.append(data[i + seq_len : i + seq_len + pred_len])
    return np.array(X), np.array(y)

def train_lstm(product_id, product_name):
    with engine.connect() as conn:
        df = pd.read_sql(
            f"SELECT sale_date, qty_sold FROM sales_history WHERE product_id = {product_id} ORDER BY sale_date",
            conn
        )

    if len(df) < SEQ_LEN + PRED_LEN + 10:
        print(f" Skipping {product_name} — not enough data")
        return

    values = df['qty_sold'].values.astype(float)
    vmax   = values.max() if values.max() > 0 else 1
    norm   = values / vmax

    X, y = make_sequences(norm, SEQ_LEN, PRED_LEN)

    split   = int(len(X) * 0.85)
    X_train = torch.FloatTensor(X[:split]).unsqueeze(-1)
    y_train = torch.FloatTensor(y[:split])
    X_test  = torch.FloatTensor(X[split:]).unsqueeze(-1)
    y_test  = torch.FloatTensor(y[split:])

    loader = DataLoader(TensorDataset(X_train, y_train), batch_size=16, shuffle=True)

    model     = LSTMModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(50):
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        pred   = model(X_test).numpy() * vmax
        actual = y_test.numpy() * vmax

    mae  = np.mean(np.abs(pred - actual))
    mape = np.mean(np.abs((pred - actual) / (actual + 1))) * 100

    with mlflow.start_run(run_name=f"lstm_{product_name}"):
        mlflow.log_param("product_id",   product_id)
        mlflow.log_param("product_name", product_name)
        mlflow.log_metric("mae",  round(mae,  2))
        mlflow.log_metric("mape", round(mape, 2))

    torch.save({
        'model_state': model.state_dict(),
        'vmax':        vmax,
        'last_seq':    norm[-SEQ_LEN:].tolist()
    }, f"ml/models/lstm_{product_id}.pt")

    print(f" LSTM {product_name} | MAE={mae:.1f} | MAPE={mape:.1f}%")

def predict_lstm(product_id, days=7):
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

def train_all_lstm():
    with engine.connect() as conn:
        products = pd.read_sql("SELECT id, name FROM products", conn)

    print(f"Training LSTM for {len(products)} products...")
    for _, row in products.iterrows():
        train_lstm(row['id'], row['name'])
    print(" All LSTM models trained!")

if __name__ == "__main__":
    train_all_lstm()