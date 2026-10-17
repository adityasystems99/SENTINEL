import React from 'react';
import {
  Share2,
  ChevronLeft,
  ShieldAlert,
  Layers,
  Network,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';

export default function DependencyRadarWorkspace({ project, onBackToDashboard }) {
  // Demo service topology derived from telemetry
  const services = [
    { name: 'web-gateway', tier: 'High Risk (Public Facing)', downstreamCount: 4, status: 'Active' },
    { name: 'auth-service', tier: 'High Risk (Critical Path)', downstreamCount: 3, status: 'Active' },
    { name: 'order-service', tier: 'High Risk (Business Logic)', downstreamCount: 2, status: 'Active' },
    { name: 'inventory-service', tier: 'Medium Risk (Database)', downstreamCount: 1, status: 'Active' },
    { name: 'payment-service', tier: 'Medium Risk (External API)', downstreamCount: 1, status: 'Active' },
  ];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 20px',
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={onBackToDashboard}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              color: 'var(--text-secondary)',
              padding: '6px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8rem',
            }}
          >
            <ChevronLeft size={16} /> Back to Dashboard
          </button>
          <div style={{ width: '1px', height: '24px', background: 'var(--border)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(167, 139, 250, 0.15)', padding: '6px 8px', borderRadius: '8px', color: '#a78bfa' }}>
              <Share2 size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: '800' }}>
                  Feature 4 — Dependency & Impact Radar
                </h2>
                <span className="badge badge-medium" style={{ color: '#a78bfa', borderColor: 'rgba(167, 139, 250, 0.3)' }}>
                  What else breaks?
                </span>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                Project: <strong>{project?.name || 'Active Project'}</strong> · Downstream Blast-Radius & Service Topology
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <Network size={18} color="#a78bfa" />
          <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Service Dependency Topology & Blast Radius</h3>
        </div>
        <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: '1.5' }}>
          When an anomaly or failure occurs in a microservice, SENTINEL evaluates the directed call-graph to identify which downstream components are in the blast zone.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {services.map((svc) => (
            <div
              key={svc.name}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '14px 18px',
                background: 'rgba(0, 0, 0, 0.35)',
                border: '1px solid var(--border)',
                borderRadius: '10px',
              }}
            >
              <div>
                <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>[{svc.name}]</strong>
                <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {svc.tier} · Downstream fan-out: {svc.downstreamCount} connected nodes
                </p>
              </div>
              <span className="badge badge-low">{svc.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
