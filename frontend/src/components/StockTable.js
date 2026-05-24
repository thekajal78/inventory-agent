import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000';

export default function StockTable() {
  const [products, setProducts] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [lastUpdate, setLastUpdate] = useState('');

  const fetchStock = async () => {
    try {
      const res = await axios.get(`${API}/api/inventory/stock`);
      setProducts(res.data);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (e) {
      console.error('Stock fetch failed:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStock();
    const interval = setInterval(fetchStock, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>
      Loading stock data...
    </div>
  );

  const low = products.filter(p => p.status === 'low').length;
  const ok  = products.filter(p => p.status === 'ok').length;

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: '#1e293b', borderRadius: '12px', padding: '20px', border: '1px solid #334155' }}>
          <div style={{ fontSize: '28px', fontWeight: '700', color: '#38bdf8' }}>{products.length}</div>
          <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>Total Products</div>
        </div>
        <div style={{ background: '#1e293b', borderRadius: '12px', padding: '20px', border: '1px solid #ef4444' }}>
          <div style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444' }}>{low}</div>
          <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>Low Stock</div>
        </div>
        <div style={{ background: '#1e293b', borderRadius: '12px', padding: '20px', border: '1px solid #22c55e' }}>
          <div style={{ fontSize: '28px', fontWeight: '700', color: '#22c55e' }}>{ok}</div>
          <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>Stock OK</div>
        </div>
      </div>

      <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>Live Stock Levels</h2>
          <span style={{ fontSize: '12px', color: '#64748b' }}>Updated: {lastUpdate} • Refreshes every 5s</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#0f172a' }}>
              {['Product', 'SKU', 'Stock', 'Threshold', 'Daily Sales', 'Days Left', 'Status'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#64748b', fontWeight: '500', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.product_id} style={{ borderTop: '1px solid #334155', background: p.status === 'low' ? 'rgba(239,68,68,0.05)' : 'transparent' }}>
                <td style={{ padding: '14px 16px', fontWeight: '500', color: '#e2e8f0' }}>{p.product_name}</td>
                <td style={{ padding: '14px 16px', color: '#64748b', fontSize: '13px' }}>{p.sku}</td>
                <td style={{ padding: '14px 16px' }}>
                  <span style={{ fontWeight: '700', color: p.status === 'low' ? '#ef4444' : '#22c55e', fontSize: '16px' }}>{p.current_stock}</span>
                  <span style={{ color: '#64748b', fontSize: '12px' }}> units</span>
                </td>
                <td style={{ padding: '14px 16px', color: '#94a3b8' }}>{p.reorder_threshold}</td>
                <td style={{ padding: '14px 16px', color: '#94a3b8' }}>{p.avg_daily_sales}/day</td>
                <td style={{ padding: '14px 16px' }}>
                  <span style={{ color: p.days_of_inventory < 3 ? '#ef4444' : p.days_of_inventory < 7 ? '#f59e0b' : '#22c55e', fontWeight: '600' }}>
                    {p.days_of_inventory === 999 ? '∞' : `${p.days_of_inventory}d`}
                  </span>
                </td>
                <td style={{ padding: '14px 16px' }}>
                  <span style={{
                    padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: '500',
                    background: p.status === 'low' ? 'rgba(239,68,68,0.15)' : 'rgba(34,197,94,0.15)',
                    color: p.status === 'low' ? '#ef4444' : '#22c55e'
                  }}>
                    {p.status === 'low' ? '⚠ Low' : '✓ OK'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}