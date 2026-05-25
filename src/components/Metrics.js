import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000';

export default function Metrics() {
  const [metrics, setMetrics] = useState(null);
  const [orders,  setOrders]  = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [mRes, oRes] = await Promise.all([
          axios.get(`${API}/api/inventory/metrics`),
          axios.get(`${API}/api/purchase-orders`)
        ]);
        setMetrics(mRes.data);
        setOrders(oRes.data.orders || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>Loading metrics...</div>;

  const cards = metrics ? [
    { label: 'Total Products',    value: metrics.total_products,    color: '#38bdf8', suffix: '' },
    { label: 'Low Stock Items',   value: metrics.low_stock_count,   color: '#ef4444', suffix: '' },
    { label: 'Stockout Rate',     value: metrics.stockout_rate_pct, color: '#f59e0b', suffix: '%' },
    { label: 'Total POs Raised',  value: metrics.total_pos_raised,  color: '#a78bfa', suffix: '' },
    { label: 'Auto Action Rate',  value: metrics.auto_action_rate,  color: '#22c55e', suffix: '%' },
    { label: 'Avg Confidence',    value: metrics.avg_confidence,    color: '#38bdf8', suffix: '%' },
  ] : [];

  return (
    <div>
      {/* Metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
        {cards.map(c => (
          <div key={c.label} style={{ background: '#1e293b', borderRadius: '12px', padding: '24px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '32px', fontWeight: '700', color: c.color }}>{c.value}{c.suffix}</div>
            <div style={{ fontSize: '13px', color: '#64748b', marginTop: '6px' }}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* Purchase Orders table */}
      <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #334155' }}>
          <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>Purchase Orders</h2>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#0f172a' }}>
              {['PO Reference', 'Product', 'Supplier', 'Qty', 'Total Cost', 'Status', 'Urgency', 'Expected'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#64748b', fontWeight: '500', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr><td colSpan={8} style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>No purchase orders yet</td></tr>
            ) : orders.map((o, i) => (
              <tr key={i} style={{ borderTop: '1px solid #334155' }}>
                <td style={{ padding: '12px 16px', color: '#38bdf8', fontSize: '12px', fontFamily: 'monospace' }}>{o.po_reference}</td>
                <td style={{ padding: '12px 16px', color: '#e2e8f0' }}>{o.product_name}</td>
                <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{o.supplier_name}</td>
                <td style={{ padding: '12px 16px', color: '#38bdf8', fontWeight: '600' }}>{o.quantity}</td>
                <td style={{ padding: '12px 16px', color: '#22c55e' }}>₹{Number(o.total_cost).toLocaleString()}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ padding: '3px 8px', borderRadius: '12px', fontSize: '11px', background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>
                    {o.status}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ color: o.urgency === 'CRITICAL' ? '#ef4444' : o.urgency === 'WARNING' ? '#f59e0b' : '#22c55e', fontSize: '12px', fontWeight: '600' }}>
                    {o.urgency}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', color: '#64748b', fontSize: '12px' }}>
                  {o.expected_delivery ? new Date(o.expected_delivery).toLocaleDateString() : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}