import React, { useState } from 'react';
import StockTable from './components/StockTable';
import DecisionLog from './components/DecisionLog';
import ForecastChart from './components/ForecastChart';
import Metrics from './components/Metrics';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('stock');

  const tabs = [
    { id: 'stock',     label: 'Live Stock' },
    { id: 'decisions', label: 'AI Decisions' },
    { id: 'forecast',  label: 'Forecast' },
    { id: 'metrics',   label: 'Metrics' },
  ];

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#e2e8f0' }}>

      {/* Header */}
      <div style={{ background: '#1e293b', borderBottom: '1px solid #334155', padding: '16px 24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: '700', color: '#38bdf8', margin: 0 }}>
              🤖 Autonomous Inventory Agent
            </h1>
            <p style={{ fontSize: '12px', color: '#64748b', margin: '2px 0 0 0' }}>
              AI-powered • RAG • LangGraph • Real-time
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e', animation: 'pulse 2s infinite' }}></div>
            <span style={{ fontSize: '12px', color: '#22c55e' }}>System Active</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ background: '#1e293b', borderBottom: '1px solid #334155' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex' }}>
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '12px 24px', border: 'none', cursor: 'pointer',
                background: activeTab === tab.id ? '#0f172a' : 'transparent',
                color: activeTab === tab.id ? '#38bdf8' : '#64748b',
                borderBottom: activeTab === tab.id ? '2px solid #38bdf8' : '2px solid transparent',
                fontSize: '14px', fontWeight: '500', transition: 'all 0.2s'
              }}>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
        {activeTab === 'stock'     && <StockTable />}
        {activeTab === 'decisions' && <DecisionLog />}
        {activeTab === 'forecast'  && <ForecastChart />}
        {activeTab === 'metrics'   && <Metrics />}
      </div>
    </div>
  );
}

export default App;