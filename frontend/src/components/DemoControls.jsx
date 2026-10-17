import React, { useState } from 'react';
import { Database, AlertTriangle, Clock, CheckCircle2, Play, Flame } from 'lucide-react';
import { triggerDemoScenario, triggerIncidentAnalysis } from '../api/client';

export default function DemoControls({ onActionComplete }) {
  const [loadingScenario, setLoadingScenario] = useState(null);

  const handleScenario = async (name) => {
    try {
      setLoadingScenario(name);
      await triggerDemoScenario(name, 3);
      // Automatically trigger incident analysis after failure injection
      if (name !== 'healthy_traffic') {
        try {
          await triggerIncidentAnalysis(300);
        } catch (e) {
          console.warn('Auto-analyze non-critical:', e);
        }
      }
      onActionComplete();
    } catch (err) {
      alert(`Error triggering scenario: ${err.message}`);
    } finally {
      setLoadingScenario(null);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Flame size={18} color="#f59e0b" />
          <h2 style={{ fontSize: '1rem', fontWeight: '700' }}>Telemetry & Failure Injection Harness</h2>
        </div>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Simulates distributed microservice traffic & deliberate chaos
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
        {/* Scenario 1: DB Pool */}
        <button
          onClick={() => handleScenario('db_pool_exhaustion')}
          disabled={loadingScenario !== null}
          style={{
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            borderRadius: '10px',
            padding: '12px 14px',
            textAlign: 'left',
            color: 'var(--text-primary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Database size={16} color="#ef4444" />
            <strong style={{ fontSize: '0.85rem' }}>DB Pool Exhaustion</strong>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            HikariPool exhaustion on inventory-service causing cascading 503s
          </p>
        </button>

        {/* Scenario 2: Bad Deployment */}
        <button
          onClick={() => handleScenario('bad_auth_deployment')}
          disabled={loadingScenario !== null}
          style={{
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: '10px',
            padding: '12px 14px',
            textAlign: 'left',
            color: 'var(--text-primary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <AlertTriangle size={16} color="#f59e0b" />
            <strong style={{ fontSize: '0.85rem' }}>Bad Auth Deployment</strong>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Deploys v2.4.1 followed by NullPointer session exception in auth
          </p>
        </button>

        {/* Scenario 3: Payment Gateway Timeout */}
        <button
          onClick={() => handleScenario('payment_timeout')}
          disabled={loadingScenario !== null}
          style={{
            background: 'rgba(139, 92, 246, 0.08)',
            border: '1px solid rgba(139, 92, 246, 0.25)',
            borderRadius: '10px',
            padding: '12px 14px',
            textAlign: 'left',
            color: 'var(--text-primary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Clock size={16} color="#8b5cf6" />
            <strong style={{ fontSize: '0.85rem' }}>Payment Gateway 504</strong>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Upstream Stripe HTTP timeout causing order thread starvation
          </p>
        </button>

        {/* Scenario 4: Healthy Traffic */}
        <button
          onClick={() => handleScenario('healthy_traffic')}
          disabled={loadingScenario !== null}
          style={{
            background: 'rgba(59, 130, 246, 0.08)',
            border: '1px solid rgba(59, 130, 246, 0.25)',
            borderRadius: '10px',
            padding: '12px 14px',
            textAlign: 'left',
            color: 'var(--text-primary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Play size={16} color="#3b82f6" />
            <strong style={{ fontSize: '0.85rem' }}>Healthy Traffic (x5)</strong>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Normal checkout operations across gateway, auth, orders, inventory
          </p>
        </button>

        {/* Scenario 5: Reset / Recover */}
        <button
          onClick={() => handleScenario('recover')}
          disabled={loadingScenario !== null}
          style={{
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: '10px',
            padding: '12px 14px',
            textAlign: 'left',
            color: 'var(--text-primary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <CheckCircle2 size={16} color="#10b981" />
            <strong style={{ fontSize: '0.85rem' }}>System Recovery</strong>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Disable all active failure toggles and emit recovery telemetry
          </p>
        </button>
      </div>
    </div>
  );
}
