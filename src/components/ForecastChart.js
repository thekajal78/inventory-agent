import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API = 'http://localhost:8000';

export default function ForecastChart() {
  const [products,   setProducts]   = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [forecast,   setForecast]   = useState(null);
  const [chartData,  setChartData]  = useState([]);
  const [loading,    setLoading]    = useState(false);

  useEffect(() => {
    axios.get(`${API}/api/inventory/stock`).then(res => {
      const prods = res.data;
      setProducts(prods);
      if (prods.length > 0) setSelectedId(prods[0].product_id);
    });
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    Promise.all([
      axios.get(`${API}/api/forecast/${selectedId}`),
      axios.get(`${API}/api/forecast/${selectedId}/chart`)
    ]).then(([fRes, cRes]) => {
      setForecast(fRes.data);
      const actual = cRes.data.actual || [];
      const data   = actual.slice(0, 14).reverse().map((d, i) => ({
        day:    `Day ${i + 1}`,
        actual: d.value,
      }));
      setChartData(data);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedId]);

  return (
    <div>
      {/* Product selector */}
      <div style={{ marginBottom: '20px' }}>
        <select value={selectedId || ''} onChange={e => setSelectedId(Number(e.target.value))}
          style={{ padding: '10px 16px', background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0', fontSize: '14px', cursor: 'pointer' }}>
          {products.map(p => (
            <option key={p.product_id} value={p.product_id}>{p.product_name}</option>
          ))}
        </select>
      </div>

      {/* Forecast summary cards */}
      {forecast && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
          {[
            { label: 'Prophet (Rolling)', value: forecast.prophet,  color: '#a78bfa' },
            { label: 'XGBoost',           value: forecast.xgboost,  color: '#38bdf8' },
            { label: 'LSTM',              value: forecast.lstm,     color: '#f59e0b' },
            { label: 'Ensemble',          value: forecast.ensemble, color: '#22c55e' },
          ].map(m => (
            <div key={m.label} style={{ background: '#1e293b', borderRadius: '12px', padding: '20px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: m.color }}>{m.value}</div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{m.label}</div>
              <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px' }}>units / 7 days</div>
            </div>
          ))}
        </div>
      )}

      {/* Confidence */}
      {forecast && (
        <div style={{ background: '#1e293b', borderRadius: '12px', padding: '16px 20px', border: '1px solid #334155', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: '#64748b', fontSize: '14px' }}>Model Agreement (Confidence):</span>
          <div style={{ flex: 1, background: '#0f172a', borderRadius: '99px', height: '8px' }}>
            <div style={{ width: `${forecast.confidence_pct}%`, background: forecast.confidence_pct > 80 ? '#22c55e' : '#f59e0b', height: '8px', borderRadius: '99px', transition: 'width 0.5s' }}></div>
          </div>
          <span style={{ color: forecast.confidence_pct > 80 ? '#22c55e' : '#f59e0b', fontWeight: '700', fontSize: '16px' }}>{forecast.confidence_pct}%</span>
        </div>
      )}

      {/* Chart */}
      <div style={{ background: '#1e293b', borderRadius: '12px', padding: '20px', border: '1px solid #334155' }}>
        <h3 style={{ margin: '0 0 20px 0', fontSize: '15px', fontWeight: '600' }}>Last 14 Days — Actual Sales</h3>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Loading chart...</div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="day" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#38bdf8" strokeWidth={2} dot={false} name="Actual Sales" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}