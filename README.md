# 🤖 Autonomous Inventory Management System

> An end-to-end agentic AI system that autonomously monitors inventory, predicts demand using ensemble ML models, selects the best supplier via RAG, and raises Purchase Orders — with zero human intervention.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-inventory--agent--psi.vercel.app-blue)](https://inventory-agent-psi.vercel.app)
[![API Docs](https://img.shields.io/badge/API%20Docs-onrender.com-green)](https://inventory-agent-iaqa.onrender.com/docs)
[![GitHub](https://img.shields.io/badge/GitHub-thekajal78-black)](https://github.com/thekajal78)

---

## 🎯 Overview

This system autonomously manages inventory by:

1. **Detecting** low stock in real time via Apache Kafka event streaming
2. **Predicting** future demand using an ensemble of Prophet + XGBoost + LSTM models
3. **Retrieving** relevant supplier context via RAG (ChromaDB vector database)
4. **Reasoning** with Groq LLM (LLaMA 3) to select the best supplier
5. **Raising** Purchase Orders automatically with full audit trail
6. **Notifying** via Slack + Email when orders are placed

---

## 🚀 Live Links

| | Link |
|--|--|
| 🌐 Frontend Dashboard | https://inventory-agent-psi.vercel.app |
| ⚡ API Docs | https://inventory-agent-iaqa.onrender.com/docs |
| 💻 GitHub Repo | https://github.com/thekajal78/inventory-agent |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│           Layer 0 — React Dashboard                  │
│   Live Stock │ AI Decisions │ Forecast │ Metrics     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│           Layer 1 — FastAPI Backend                  │
│         REST API · CORS · SQLAlchemy ORM             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│        Layer 2 — Data Infrastructure                 │
│   PostgreSQL · TimescaleDB · Apache Kafka · Redis    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│        Layer 3 — ETL Pipeline                        │
│   Extract · Clean · Feature Engineer · Load          │
│   Lag features · Rolling avg · Calendar features     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│        Layer 4 — ML Forecasting Engine               │
│   Prophet (30%) + XGBoost (45%) + LSTM (25%)         │
│   Ensemble prediction · 75-85% confidence            │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  Decision Gate  │
              │ Stock below     │
              │  threshold?     │
              └────────┬────────┘
                YES    │    NO → Keep monitoring
                       │
┌──────────────────────▼──────────────────────────────┐
│        Layer 5 — LangGraph AI Agent                  │
│                                                      │
│  [Forecast] → [RAG Search] → [LLM Decide]            │
│            → [Auto Execute / Escalate]               │
│                                                      │
│  Node 1: Predict 7-day demand                        │
│  Node 2: RAG semantic supplier search                │
│  Node 3: Groq LLM reasoning → JSON decision          │
│  Node 4: Auto-raise PO (confidence >= 80%)           │
│  Node 5: Escalate to human (confidence < 80%)        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│        Layer 6 — RAG System                          │
│   ChromaDB vector DB · sentence-transformers         │
│   Semantic search · Top-3 supplier retrieval         │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│        Layer 7 — Supplier Scoring                    │
│   Reliability 35% · Lead time 30%                    │
│   Cost 25% · MOQ fit 10%                             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│        Layer 8 — ERP / PO System                     │
│   Purchase Orders · Stock movements · Audit trail    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│        Layer 9 — Notifications                       │
│   Slack Webhook · Email (Brevo SMTP) · SMS (Twilio)  │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Frontend** | React, Recharts, Axios |
| **Backend** | FastAPI, SQLAlchemy, Uvicorn |
| **ML Models** | Prophet, XGBoost, LSTM (PyTorch) |
| **AI Agent** | LangGraph, Groq LLM (LLaMA 3 70B) |
| **RAG** | ChromaDB, sentence-transformers |
| **Streaming** | Apache Kafka, Zookeeper |
| **Database** | PostgreSQL, TimescaleDB |
| **Experiment Tracking** | MLflow |
| **Notifications** | Slack Webhook, Brevo SMTP, Twilio |
| **Deployment** | Docker, Render, Vercel |

---

## ✨ Features

- 📦 **Live Stock Dashboard** — auto-refreshes every 5 seconds
- 🤖 **AI Decisions Log** — every agent decision with approve/reject buttons
- 📈 **Demand Forecast** — Prophet, XGBoost, LSTM predictions per product
- 📊 **Metrics Dashboard** — stockout rate, auto-action rate, avg confidence
- 🧾 **Purchase Orders** — full PO table with urgency, cost, expected delivery
- ⚡ **Autonomous Agent** — detects low stock and raises POs without human input
- 📢 **Multi-channel Notifications** — Slack + Email + SMS on every PO raised
- 🐳 **Fully Dockerized** — entire stack runs with `docker-compose up`
- 🌐 **Permanently Deployed** — live on Vercel + Render

---

## 📊 Dataset

**Superstore Sales Dataset** (Kaggle)

| Property | Value |
|----------|-------|
| Total rows | 9,800 transactions |
| Products used | 150 SKUs (top by sales volume) |
| Date range | 2014 – 2018 (4 years) |
| Categories | Furniture, Office Supplies, Technology |
| Size | ~2 MB |

---

## 🤖 ML Models

### Ensemble Formula

```
Ensemble = Prophet (30%) + XGBoost (45%) + LSTM (25%)
```

| Model | Type | Strength |
|-------|------|----------|
| Prophet | Time series | Seasonal patterns, weekly trends |
| XGBoost | Gradient boosting | Feature-rich tabular prediction |
| LSTM | Deep learning (PyTorch) | Long-term temporal dependencies |

### Features Engineered

- Calendar: `day_of_week`, `month`, `quarter`, `is_weekend`, `is_month_end`
- Lag: `lag_1`, `lag_3`, `lag_7`, `lag_14`, `lag_30`
- Rolling: `roll_mean_7`, `roll_mean_14`, `roll_mean_30`, `roll_std_7`

### Confidence Score

- Models agreement → confidence percentage (60–95%)
- Auto-execute if confidence ≥ 80%
- Escalate to human if confidence < 80%

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health check |
| GET | `/api/inventory/stock` | All products with stock levels |
| GET | `/api/inventory/metrics` | Dashboard metrics |
| GET | `/api/forecast/{product_id}` | ML forecast for a product |
| GET | `/api/forecast/{product_id}/chart` | Chart data for product |
| GET | `/api/decisions` | All agent decisions |
| PATCH | `/api/decisions/{id}/approve` | Approve pending decision |
| PATCH | `/api/decisions/{id}/reject` | Reject pending decision |
| GET | `/api/purchase-orders` | All purchase orders |

---

## 🚀 Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop
- Conda

### Step 1 — Clone

```bash
git clone https://github.com/thekajal78/inventory-agent.git
cd inventory-agent
```

### Step 2 — Environment

```bash
conda create -n inventory python=3.11
conda activate inventory
pip install -r requirements-docker.txt
```

### Step 3 — Environment variables

Create `.env` file:

```env
DB_URL=postgresql://user:pass@localhost:5432/inventory
GROQ_API_KEY=gsk_your_key_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
BREVO_SMTP_SERVER=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SMTP_LOGIN=your_login
BREVO_SMTP_PASSWORD=your_password
EMAIL_ADDRESS=your@email.com
```

### Step 4 — Start Docker

```bash
docker-compose up -d
```

### Step 5 — Seed database

```bash
python data/pipelines/load_superstore.py
python data/etl_pipeline.py
```

### Step 6 — Train models

```bash
python ml/prophet_model.py
python ml/xgboost_model.py
python ml/lstm_model.py
```

### Step 7 — Index suppliers

```bash
python agent/tools/supplier_rag.py
```

### Step 8 — Open dashboard

```
http://localhost:3000
```

---

## 💻 Usage

### Run AI Agent manually

```bash
python agent/graph.py
```

### Run agent in continuous loop

```bash
python run_agent_loop.py
```

### Simulate low stock for testing

```python
from api.db import engine
from sqlalchemy import text
with engine.begin() as conn:
    conn.execute(text(
        'UPDATE stock_levels SET quantity = 3 '
        'WHERE product_id = (SELECT id FROM products LIMIT 1)'
    ))
```

### Start MLflow tracking UI

```bash
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db
```

Open http://localhost:5000

---

## 📁 Project Structure

```
inventory-agent/
├── api/                          # FastAPI backend
│   ├── main.py                   # App entry point + CORS
│   ├── db.py                     # Database connection
│   ├── models.py                 # SQLAlchemy models
│   └── routes/
│       ├── inventory.py          # Stock endpoints
│       ├── decisions.py          # Agent decision endpoints
│       └── forecast.py           # ML forecast endpoints
│
├── agent/                        # LangGraph AI agent
│   ├── graph.py                  # 5-node agent graph
│   ├── state.py                  # Agent state definition
│   ├── audit.py                  # Decision audit trail
│   ├── notifications.py          # Slack + Email + SMS
│   └── tools/
│       ├── erp.py                # Purchase Order system
│       ├── supplier_rag.py       # ChromaDB RAG system
│       └── supplier_selector.py  # Weighted scoring
│
├── ml/                           # Machine learning
│   ├── prophet_model.py          # Prophet forecasting
│   ├── xgboost_model.py          # XGBoost forecasting
│   ├── lstm_model.py             # LSTM deep learning
│   ├── ensemble.py               # Ensemble combiner
│   ├── decision_gate.py          # Trigger logic
│   └── models/                   # Saved model files (.pkl, .pt)
│
├── data/                         # Data pipeline
│   ├── etl_pipeline.py           # ETL + feature engineering
│   └── pipelines/
│       ├── seed.py               # Synthetic data seeder
│       └── load_superstore.py    # Real dataset loader
│
├── frontend/                     # React dashboard
│   └── src/
│       ├── App.js                # Main app with tabs
│       └── components/
│           ├── StockTable.js     # Live stock table
│           ├── DecisionLog.js    # AI decisions + approve/reject
│           ├── ForecastChart.js  # ML forecast charts
│           └── Metrics.js        # Metrics + PO table
│
├── docker-compose.yml            # Full stack Docker config
├── Dockerfile                    # API Docker image
├── requirements-docker.txt       # Python dependencies
├── render.yaml                   # Render deployment config
└── render_seed.py                # Render DB seeder
```

---

## 🌐 Deployment

### Frontend — Vercel

- Auto-deploys on every `git push` to main
- URL: https://inventory-agent-psi.vercel.app

### Backend — Render

- Docker-based deployment
- URL: https://inventory-agent-iaqa.onrender.com
- Note: Free tier sleeps after 15min inactivity, wakes in ~50s

### Full local stack — Docker

```bash
docker-compose up -d    # Start all 6 services
docker-compose down     # Stop all services
docker-compose logs -f  # View logs
```