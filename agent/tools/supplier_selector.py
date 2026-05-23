import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import pandas as pd
import numpy as np
from api.db import engine

def score_suppliers(reorder_qty=50):
    with engine.connect() as conn:
        suppliers = pd.read_sql("SELECT * FROM suppliers", conn)

    if len(suppliers) == 0:
        return []

    scores = []
    for _, s in suppliers.iterrows():

        # 1. Reliability score (weight 35%)
        reliability_score = float(s['reliability']) * 100

        # 2. Lead time score (weight 30%)
        # 1 day = 100, 10+ days = 0
        lead_score = max(0, 100 - (int(s['lead_time_days']) - 1) * 12.5)

        # 3. Cost score (weight 25%)
        # Will normalize after collecting all costs
        cost_raw = float(s['cost_per_unit'])

        # 4. MOQ fit score (weight 10%)
        moq = int(s['min_order_qty'])
        if reorder_qty >= moq:
            moq_score = 100
        else:
            moq_score = max(0, (reorder_qty / moq) * 100)

        scores.append({
            'id':               int(s['id']),
            'name':             s['name'],
            'lead_time_days':   int(s['lead_time_days']),
            'reliability':      float(s['reliability']),
            'cost_per_unit':    cost_raw,
            'min_order_qty':    moq,
            'payment_terms':    s['payment_terms'],
            'reliability_score': reliability_score,
            'lead_score':        lead_score,
            'cost_raw':          cost_raw,
            'moq_score':         moq_score
        })

    df = pd.DataFrame(scores)

    # Normalize cost score — cheapest gets 100, most expensive gets 0
    min_cost = df['cost_raw'].min()
    max_cost = df['cost_raw'].max()
    if max_cost > min_cost:
        df['cost_score'] = (1 - (df['cost_raw'] - min_cost) / (max_cost - min_cost)) * 100
    else:
        df['cost_score'] = 100

    # Weighted total score
    df['total_score'] = (
        df['reliability_score'] * 0.35 +
        df['lead_score']        * 0.30 +
        df['cost_score']        * 0.25 +
        df['moq_score']         * 0.10
    )

    df = df.sort_values('total_score', ascending=False).reset_index(drop=True)

    return df.to_dict('records')

def format_scored_suppliers(reorder_qty=50):
    suppliers = score_suppliers(reorder_qty)
    if not suppliers:
        return "No suppliers available"

    lines = []
    for i, s in enumerate(suppliers):
        lines.append(
            f"[Rank {i+1} | Score: {s['total_score']:.1f}/100]\n"
            f"Supplier: {s['name']}\n"
            f"  Reliability: {int(s['reliability']*100)}% "
            f"(score: {s['reliability_score']:.0f})\n"
            f"  Lead time: {s['lead_time_days']} days "
            f"(score: {s['lead_score']:.0f})\n"
            f"  Cost: Rs {s['cost_per_unit']}/unit "
            f"(score: {s['cost_score']:.0f})\n"
            f"  MOQ: {s['min_order_qty']} units "
            f"(score: {s['moq_score']:.0f})\n"
            f"  Payment: {s['payment_terms']}"
        )
    return "\n\n".join(lines)

if __name__ == "__main__":
    print("Supplier Scoring Results")
    print("=" * 50)

    print("\nFor order qty = 50 units:")
    print(format_scored_suppliers(50))

    print("\n" + "=" * 50)
    print("\nFor order qty = 200 units:")
    print(format_scored_suppliers(200))