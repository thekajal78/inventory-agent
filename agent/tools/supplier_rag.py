import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import os
import chromadb
import pandas as pd
from api.db import engine

# Local ChromaDB — no account needed, stores data in a folder
CHROMA_PATH = "data/chroma_db"
COLLECTION  = "suppliers"

def get_chroma_client():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client

def build_supplier_doc(row):
    return (
        f"Supplier: {row['name']}. "
        f"Lead time: {row['lead_time_days']} business days. "
        f"Reliability: {int(row['reliability']*100)}% on-time delivery. "
        f"Cost per unit: Rs {row['cost_per_unit']}. "
        f"Minimum order quantity: {row['min_order_qty']} units. "
        f"Payment terms: {row['payment_terms']}. "
        f"Good for urgent orders: {'yes' if row['lead_time_days'] <= 2 else 'no'}. "
        f"Good for large orders: {'yes' if row['min_order_qty'] >= 100 else 'no'}. "
        f"Budget friendly: {'yes' if row['cost_per_unit'] < 300 else 'no'}."
    )

def index_all_suppliers():
    print("Indexing suppliers into ChromaDB...")

    with engine.connect() as conn:
        suppliers = pd.read_sql("SELECT * FROM suppliers", conn)

    if len(suppliers) == 0:
        print(" No suppliers found in database")
        return

    client     = get_chroma_client()

    # Delete existing collection if it exists
    try:
        client.delete_collection(COLLECTION)
    except:
        pass

    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

    documents = []
    ids       = []
    metadatas = []

    for _, row in suppliers.iterrows():
        doc = build_supplier_doc(row)
        documents.append(doc)
        ids.append(str(row['id']))
        metadatas.append({
            "name":           row['name'],
            "lead_time_days": int(row['lead_time_days']),
            "reliability":    float(row['reliability']),
            "cost_per_unit":  float(row['cost_per_unit']),
            "min_order_qty":  int(row['min_order_qty'])
        })

    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )

    print(f" Indexed {len(suppliers)} suppliers into ChromaDB")
    for doc in documents:
        print(f"   → {doc[:80]}...")

def query_best_supplier(product_name, urgency="normal", qty=50):
    client = get_chroma_client()

    try:
        collection = client.get_collection(COLLECTION)
    except:
        print("ChromaDB collection not found — run index_all_suppliers() first")
        return "No supplier data available"

    # Build semantic search query
    urgency_text = "urgent fast delivery needed" if urgency in ["CRITICAL", "WARNING"] else "standard delivery"
    query = (
        f"supplier for {product_name} {urgency_text} "
        f"quantity {qty} units reliable on-time delivery good price"
    )

    results = collection.query(
        query_texts=[query],
        n_results=min(3, collection.count())
    )

    if not results["documents"][0]:
        return "No suppliers found"

    # Format results for LLM context
    formatted = []
    for i, (doc, meta) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0]
    )):
        score = 1 - results["distances"][0][i]
        formatted.append(
            f"[Rank {i+1} | Match: {score:.0%}]\n{doc}"
        )

    return "\n\n".join(formatted)

if __name__ == "__main__":
    # Step 1 — index suppliers
    index_all_suppliers()

    print("\nTesting semantic search...")
    print("\nQuery 1 — urgent small order:")
    print(query_best_supplier("electronics", urgency="CRITICAL", qty=50))

    print("\nQuery 2 — large budget order:")
    print(query_best_supplier("laptop", urgency="NORMAL", qty=200))