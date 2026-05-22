import sys
import os
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import pandas as pd
import numpy as np
from sqlalchemy import text
from api.db import engine

def extract():
    print("Step 1: Extracting sales data...")
    query = """
        SELECT s.product_id, s.qty_sold, s.sale_date, 
               s.price, s.channel, s.promo_flag,
               p.name as product_name, p.category
        FROM sales_history s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.product_id, s.sale_date
    """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    df.to_parquet("data/raw_sales.parquet")
    print(f" Extracted {len(df)} rows")
    return df

def clean(df):
    print("🧹 Step 2: Cleaning data...")
    
    def remove_outliers(group):
        mean = group["qty_sold"].mean()
        std = group["qty_sold"].std()
        return group[group["qty_sold"] <= mean + 3 * std]
    
    df = df.groupby("product_id", group_keys=False).apply(remove_outliers)
    
    df["price"] = df.groupby("product_id")["price"].transform(
        lambda x: x.fillna(x.median())
    )
    
    print(f" Cleaned data: {len(df)} rows remaining")
    return df

def feature_engineer(df):
    print(" Step 3: Engineering features...")
    
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    
    # Calendar features
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["quarter"] = df["sale_date"].dt.quarter
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_month_end"] = df["sale_date"].dt.is_month_end.astype(int)
    df["week_of_year"] = df["sale_date"].dt.isocalendar().week.astype(int)

    # Lag features
    df = df.sort_values(["product_id", "sale_date"])
    for lag in [1, 3, 7, 14, 30]:
        df[f"lag_{lag}"] = df.groupby("product_id")["qty_sold"].shift(lag)

    # Rolling stats
    for window in [7, 14, 30]:
        df[f"roll_mean_{window}"] = df.groupby("product_id")["qty_sold"].transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
    
    df["roll_std_7"] = df.groupby("product_id")["qty_sold"].transform(
        lambda x: x.rolling(7, min_periods=1).std()
    )

    df = df.fillna(0)
    print(f" Features engineered: {df.shape[1]} columns")
    return df

def load_features(df):
    print(" Step 4: Loading to feature store...")
    
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS feature_store"))
        df.to_sql("feature_store", conn, if_exists="replace", index=False)
    
    print(f" Loaded {len(df)} rows to feature_store table!")

def run_etl():
    print(" Starting ETL Pipeline...")
    df = extract()
    df = clean(df)
    df = feature_engineer(df)
    load_features(df)
    print(" ETL Pipeline Complete!")

if __name__ == "__main__":
    run_etl()