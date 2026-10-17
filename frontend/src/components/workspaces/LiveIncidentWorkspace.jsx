import React from 'react';
import { Radio, ChevronLeft, RefreshCw } from 'lucide-react';
import DemoControls from '../DemoControls';
import IncidentList from '../IncidentList';
import RootCauseCard from '../RootCauseCard';
import IncidentGraph from '../IncidentGraph';
import Timeline from '../Timeline';

export default function LiveIncidentWorkspace({
  project,
  incidents,
  selectedIncident,
  selectedIncidentId,
  onSelectIncident,
  onAnalyze,
  isAnalyzing,
  onRefresh,
  isRefreshing,
  onBackToDashboard,
}) {
  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Workspace Header / Breadcrumb */}
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
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.15)',
                padding: '6px 8px',
                borderRadius: '8px',
                color: '#f87171',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <Radio size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: '800' }}>
                  Feature 3 — Live Incident Investigation
                </h2>
                <span className="badge badge-low">Live Engine</span>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                Project: <strong>{project?.name || 'Active Project'}</strong> · NetworkX Causal Graph & PageRank Active
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border)',
            color: 'var(--text-primary)',
            padding: '7px 14px',
            borderRadius: '8px',
            fontSize: '0.8rem',
          }}
        >
          <RefreshCw size={13} className={isRefreshing ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Failure Injection Harness */}
      <DemoControls onActionComplete={onRefresh} />

      {/* Main Investigation Split */}
      <main style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', alignItems: 'start' }}>
        <div>
          <IncidentList
            incidents={incidents}
            selectedId={selectedIncidentId}
            onSelect={onSelectIncident}
            onAnalyze={onAnalyze}
            isAnalyzing={isAnalyzing}
          />
        </div>

        <div>
          <RootCauseCard incident={selectedIncident} />
          {selectedIncident && (
            <>
              <IncidentGraph
                nodes={selectedIncident.nodes}
                edges={selectedIncident.edges}
              />
              <Timeline nodes={selectedIncident.nodes} />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
