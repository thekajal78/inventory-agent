import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000';

export default function DecisionLog() {
  const [decisions, setDecisions] = useState([]);
  const [loading,   setLoading]   = useState(true);

  const fetchDecisions = async () => {
    try {
      const res = await axios.get(`${API}/api/decisions`);
      setDecisions(res.data.decisions || res.data);
    } catch (e) {
      console.error('Decisions fetch failed:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDecisions(); }, []);

  const handleApprove = async (id) => {
    await axios.patch(`${API}/api/decisions/${id}/approve`);
    fetchDecisions();
  };

  const handleReject = async (id) => {
    await axios.patch(`${API}/api/decisions/${id}/reject`);
    fetchDecisions();
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>Loading decisions...</div>;

  return (
    <div>
      <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #334155' }}>
          <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>AI Agent Decisions</h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#64748b' }}>Every autonomous decision made by the agent</p>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#0f172a' }}>
              {['Product ID', 'Stock at Trigger', 'Forecast', 'Supplier', 'Qty', 'Confidence', 'PO Ref', 'Status', 'Actions'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#64748b', fontWeight: '500', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {decisions.length === 0 ? (
              <tr><td colSpan={9} style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>No decisions yet — run the agent to see decisions here</td></tr>
            ) : decisions.map((d) => (
              <tr key={d.id} style={{ borderTop: '1px solid #334155' }}>
                <td style={{ padding: '12px 16px', color: '#94a3b8' }}>#{d.product_id}</td>
                <td style={{ padding: '12px 16px', color: '#ef4444', fontWeight: '600' }}>{d.trigger_stock}</td>
                <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{d.forecast_demand}</td>
                <td style={{ padding: '12px 16px', color: '#e2e8f0', fontSize: '13px' }}>{d.selected_supplier}</td>
                <td style={{ padding: '12px 16px', color: '#38bdf8', fontWeight: '600' }}>{d.recommended_qty}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ color: d.confidence > 0.8 ? '#22c55e' : '#f59e0b' }}>
                    {Math.round(d.confidence * 100)}%
                  </span>
                </td>
                <td style={{ padding: '12px 16px', color: '#64748b', fontSize: '12px' }}>{d.po_id}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{
                    padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: '500',
                    background: d.auto_executed ? 'rgba(34,197,94,0.15)' : 'rgba(245,158,11,0.15)',
                    color: d.auto_executed ? '#22c55e' : '#f59e0b'
                  }}>
                    {d.auto_executed ? '✓ Auto' : '⏳ Pending'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  {!d.auto_executed && (
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button onClick={() => handleApprove(d.id)}
                        style={{ padding: '4px 10px', background: '#22c55e', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}>
                        Approve
                      </button>
                      <button onClick={() => handleReject(d.id)}
                        style={{ padding: '4px 10px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}>
                        Reject
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}