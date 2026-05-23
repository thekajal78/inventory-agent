import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import os
import json
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.audit import log_decision
from agent.tools.erp import raise_purchase_order
from ml.ensemble import predict_demand
from api.db import engine
import pandas as pd

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─── NODE 1: Forecast ───────────────────────────────────────────
def forecast_node(state: AgentState) -> AgentState:
    print(f"\n Node 1: Forecasting demand for {state['product_name']}...")
    forecast = predict_demand(state["product_id"], days=7)
    state["forecast"] = forecast
    print(f"   Ensemble forecast: {forecast['ensemble']} units | Confidence: {forecast['confidence_pct']}%")
    return state

# ─── NODE 2: RAG (supplier retrieval) ───────────────────────────
def rag_node(state: AgentState) -> AgentState:
    print(f" Node 2: RAG semantic search for best supplier...")
    try:
        from agent.tools.supplier_rag import query_best_supplier

        urgency = "CRITICAL" if state["doi"] < 3 else "WARNING" if state["doi"] < 7 else "NORMAL"

        supplier_docs = query_best_supplier(
            product_name=state["product_name"],
            urgency=urgency,
            qty=state["reorder_qty"]
        )

        state["supplier_docs"] = supplier_docs
        print(f"   RAG retrieved top 3 suppliers via semantic search")
    except Exception as e:
        state["supplier_docs"] = "No supplier data available"
        print(f"   ⚠️ RAG failed: {e}")
    return state

# ─── NODE 3: LLM Decision ────────────────────────────────────────
def decide_node(state: AgentState) -> AgentState:
    print(f" Node 3: LLM reasoning with Groq...")

    forecast  = state["forecast"]
    doi       = state["doi"]
    urgency   = "CRITICAL" if doi < 3 else "WARNING" if doi < 7 else "NORMAL"

    prompt = f"""You are an autonomous inventory management AI agent.
Analyze this inventory situation and decide whether to reorder.

PRODUCT: {state['product_name']} (ID: {state['product_id']})
CURRENT STOCK: {state['current_stock']} units
REORDER THRESHOLD: {state['threshold']} units
DAYS OF INVENTORY LEFT: {doi} days
URGENCY: {urgency}

ML FORECAST (next 7 days):
- Ensemble prediction: {forecast['ensemble']} units needed
- Prophet model: {forecast['prophet']} units
- XGBoost model: {forecast['xgboost']} units
- LSTM model: {forecast['lstm']} units
- Forecast confidence: {forecast['confidence_pct']}%

AVAILABLE SUPPLIERS:
{state['supplier_docs']}

REORDER QUANTITY NEEDED: {state['reorder_qty']} units

Respond ONLY with a valid JSON object, no explanation, no markdown:
{{
  "should_reorder": true,
  "recommended_qty": <integer>,
  "selected_supplier": "<supplier name>",
  "reason": "<one clear sentence why this supplier>",
  "confidence": <float between 0.5 and 0.99>,
  "stockout_in_days": <integer>,
  "urgency": "<CRITICAL|WARNING|NORMAL>"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        raw = response.choices[0].message.content.strip()

        # Clean markdown if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        decision = json.loads(raw)

        state["decision"]   = decision
        state["confidence"] = float(decision.get("confidence", 0.75))
        print(f"   Decision: reorder={decision['should_reorder']} | "
              f"qty={decision['recommended_qty']} | "
              f"supplier={decision['selected_supplier']} | "
              f"confidence={state['confidence']:.0%}")
    except Exception as e:
        print(f"    LLM failed: {e} — using fallback decision")
        state["decision"] = {
            "should_reorder":    True,
            "recommended_qty":   state["reorder_qty"],
            "selected_supplier": "Default Supplier",
            "reason":            "Fallback decision due to LLM error",
            "confidence":        0.70,
            "stockout_in_days":  int(doi),
            "urgency":           urgency
        }
        state["confidence"] = 0.70
    return state

# ─── NODE 4: Auto Execute ────────────────────────────────────────
def auto_act_node(state: AgentState) -> AgentState:
    print(f" Node 4: Auto-executing decision...")
    decision = state["decision"]

    po_ref = raise_purchase_order(
        product_id=    state["product_id"],
        product_name=  state["product_name"],
        supplier_name= decision["selected_supplier"],
        qty=           decision["recommended_qty"]
    )

    state["po_reference"]  = po_ref
    state["auto_executed"] = True

    log_decision(state, auto_executed=True)

    print(f"    AUTO EXECUTED | PO: {po_ref}")
    print(f"    Alert: {state['product_name']} — {decision['recommended_qty']} units "
          f"ordered from {decision['selected_supplier']}")
    print(f"   Reason: {decision['reason']}")
    return state

# ─── NODE 5: Escalate ────────────────────────────────────────────
def escalate_node(state: AgentState) -> AgentState:
    print(f" Node 5: Escalating — confidence too low for auto-execution")
    state["auto_executed"] = False
    state["po_reference"]  = f"PENDING-APPROVAL-{state['product_id']}"

    log_decision(state, auto_executed=False)

    print(f"    NEEDS HUMAN APPROVAL | Product: {state['product_name']}")
    print(f"   Suggested: {state['decision']['recommended_qty']} units "
          f"from {state['decision']['selected_supplier']}")
    return state

# ─── ROUTING ────────────────────────────────────────────────────
def route(state: AgentState) -> str:
    if state["confidence"] >= 0.80:
        return "auto_act"
    return "escalate"

# ─── BUILD GRAPH ────────────────────────────────────────────────
def build_agent():
    g = StateGraph(AgentState)
    g.add_node("forecast",  forecast_node)
    g.add_node("rag",       rag_node)
    g.add_node("decide",    decide_node)
    g.add_node("auto_act",  auto_act_node)
    g.add_node("escalate",  escalate_node)

    g.set_entry_point("forecast")
    g.add_edge("forecast", "rag")
    g.add_edge("rag",      "decide")
    g.add_conditional_edges("decide", route, {
        "auto_act": "auto_act",
        "escalate": "escalate"
    })
    g.add_edge("auto_act", END)
    g.add_edge("escalate", END)

    return g.compile()

agent = build_agent()

def trigger_agent(product_id, product_name, current_stock, threshold, reorder_qty, doi):
    print(f"\n{'='*55}")
    print(f"🤖 AGENT TRIGGERED: {product_name}")
    print(f"   Stock: {current_stock} | Threshold: {threshold} | DOI: {doi}d")
    print(f"{'='*55}")

    initial_state: AgentState = {
        "product_id":        product_id,
        "product_name":      product_name,
        "current_stock":     current_stock,
        "threshold":         threshold,
        "reorder_qty":       reorder_qty,
        "doi":               doi,
        "forecast":          {},
        "supplier_docs":     "",
        "decision":          {},
        "confidence":        0.0,
        "po_reference":      "",
        "auto_executed":     False,
        "notification_sent": False,
        "error":             None
    }

    result = agent.invoke(initial_state)
    print(f"{'='*55}\n")
    return result

# ─── TEST ────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    with engine.connect() as conn:
        products = pd.read_sql("""
            SELECT p.id, p.name, p.reorder_threshold, p.reorder_qty,
                   s.quantity as current_stock
            FROM products p
            JOIN stock_levels s ON s.product_id = p.id
            WHERE s.quantity < p.reorder_threshold
            LIMIT 3
        """, conn)

    if len(products) == 0:
        print("No products below threshold right now — testing with first product")
        with engine.connect() as conn:
            products = pd.read_sql("""
                SELECT p.id, p.name, p.reorder_threshold, p.reorder_qty,
                       s.quantity as current_stock
                FROM products p
                JOIN stock_levels s ON s.product_id = p.id
                LIMIT 1
            """, conn)

    for _, row in products.iterrows():
        burn  = row['current_stock'] / 7
        doi   = round(row['current_stock'] / burn if burn > 0 else 999, 1)
        trigger_agent(
            product_id=    row['id'],
            product_name=  row['name'],
            current_stock= row['current_stock'],
            threshold=     row['reorder_threshold'],
            reorder_qty=   row['reorder_qty'],
            doi=           doi
        )