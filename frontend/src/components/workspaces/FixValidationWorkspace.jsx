import React, { useState, useEffect } from 'react';
import {
  RotateCcw,
  ChevronLeft,
  CheckCircle2,
  Clock,
  FlaskConical,
  Activity,
  AlertCircle,
  Play,
  Check,
  XCircle,
  HelpCircle,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  FileCode,
} from 'lucide-react';
import {
  fetchValidationScenarios,
  runValidationBaseline,
  runValidationFix,
} from '../../api/client';

export default function FixValidationWorkspace({ project, onBackToDashboard }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('db_pool_exhaustion');
  const [workloadCount, setWorkloadCount] = useState(5);

  const [baselineResult, setBaselineResult] = useState(null);
  const [selectedFixId, setSelectedFixId] = useState('');
  const [userApproved, setUserApproved] = useState(false);
  const [validationReport, setValidationReport] = useState(null);

  const [loadingBaseline, setLoadingBaseline] = useState(false);
  const [loadingValidation, setLoadingValidation] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadScenarios();
  }, []);

  async function loadScenarios() {
    try {
      const list = await fetchValidationScenarios();
      setScenarios(list);
      if (list.length > 0) {
        setSelectedScenarioId(list[0].id);
        if (list[0].available_fixes?.length > 0) {
          setSelectedFixId(list[0].available_fixes[0].id);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch failure scenarios');
    }
  }

  const currentScenario = scenarios.find((s) => s.id === selectedScenarioId);

  async function handleRunBaseline() {
    setLoadingBaseline(true);
    setError(null);
    setValidationReport(null);
    setUserApproved(false);

    try {
      const baseline = await runValidationBaseline(selectedScenarioId, workloadCount);
      setBaselineResult(baseline);
      if (baseline.available_fixes?.length > 0) {
        setSelectedFixId(baseline.available_fixes[0].id);
      }
    } catch (err) {
      setError(err.message || 'Baseline experiment failed');
    } finally {
      setLoadingBaseline(false);
    }
  }

  async function handleRunValidation() {
    if (!userApproved) {
      setError('Safety check: You must check the approval box before applying the patch configuration.');
      return;
    }

    setLoadingValidation(true);
    setError(null);

    try {
      const report = await runValidationFix(
        baselineResult.experiment_id,
        selectedFixId,
        userApproved,
        workloadCount
      );
      setValidationReport(report);
    } catch (err) {
      setError(err.message || 'Validation experiment failed');
    } finally {
      setLoadingValidation(false);
    }
  }

  const selectedFix = currentScenario?.available_fixes?.find((f) => f.id === selectedFixId);

  const getVerdictBadge = (verdict) => {
    switch (verdict) {
      case 'supported_by_evidence':
        return (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(52, 211, 153, 0.15)', border: '1.5px solid #34d399', color: '#34d399', padding: '8px 16px', borderRadius: '8px', fontWeight: '700', fontSize: '0.95rem' }}>
            <CheckCircle2 size={18} /> SUPPORTED BY EVIDENCE
          </div>
        );
      case 'not_supported_by_evidence':
        return (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(239, 68, 68, 0.15)', border: '1.5px solid #f87171', color: '#f87171', padding: '8px 16px', borderRadius: '8px', fontWeight: '700', fontSize: '0.95rem' }}>
            <XCircle size={18} /> NOT SUPPORTED BY EVIDENCE
          </div>
        );
      default:
        return (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(255, 211, 110, 0.15)', border: '1.5px solid #ffd36e', color: '#ffd36e', padding: '8px 16px', borderRadius: '8px', fontWeight: '700', fontSize: '0.95rem' }}>
            <HelpCircle size={18} /> INCONCLUSIVE (MORE DATA NEEDED)
          </div>
        );
    }
  };

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header Bar */}
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
              cursor: 'pointer',
            }}
          >
            <ChevronLeft size={16} /> Back to Dashboard
          </button>
          <div style={{ width: '1px', height: '24px', background: 'var(--border)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(52, 211, 153, 0.15)', padding: '6px 8px', borderRadius: '8px', color: '#34d399' }}>
              <RotateCcw size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: '800' }}>
                  Feature 5 — Replay Lab & Controlled Fix Validation
                </h2>
                <span className="badge badge-low">Does my fix work?</span>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                Project: <strong>{project?.name || 'Active Workspace'}</strong> · Pre/Post Patch Telemetry Differential
              </p>
            </div>
          </div>
        </div>

        {baselineResult && (
          <button
            onClick={() => {
              setBaselineResult(null);
              setValidationReport(null);
              setUserApproved(false);
            }}
            className="btn-secondary"
            style={{ padding: '8px 16px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
          >
            <RefreshCw size={14} /> Reset Experiment
          </button>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div
          className="glass-panel"
          style={{
            padding: '16px 20px',
            marginBottom: '24px',
            borderLeft: '4px solid #f87171',
            background: 'rgba(239, 68, 68, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={20} color="#f87171" />
            <span style={{ fontSize: '0.86rem', color: '#fca5a5' }}>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            style={{ background: 'transparent', border: 'none', color: '#fca5a5', cursor: 'pointer', fontSize: '0.8rem' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Step 1: Scenario Selection & Baseline */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <FlaskConical size={18} color="#34d399" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>
            Step 1: Select Deterministic Failure Scenario & Run Baseline
          </h3>
        </div>

        {/* Scenario Selection Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px', marginBottom: '20px' }}>
          {scenarios.map((scen) => {
            const isSelected = selectedScenarioId === scen.id;
            return (
              <div
                key={scen.id}
                onClick={() => {
                  if (!baselineResult) {
                    setSelectedScenarioId(scen.id);
                  }
                }}
                style={{
                  background: isSelected ? 'rgba(52, 211, 153, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                  border: isSelected ? '1.5px solid #34d399' : '1px solid var(--border)',
                  borderRadius: '10px',
                  padding: '16px',
                  cursor: baselineResult ? 'default' : 'pointer',
                  transition: 'all 0.2s ease',
                  opacity: baselineResult && !isSelected ? 0.5 : 1,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <strong style={{ fontSize: '0.92rem', color: isSelected ? '#34d399' : 'var(--text-primary)' }}>
                    {scen.name}
                  </strong>
                  <span className="badge" style={{ fontSize: '0.7rem' }}>
                    {scen.target_service}
                  </span>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0 0 10px 0', lineHeight: '1.4' }}>
                  {scen.description}
                </p>
                <div style={{ fontSize: '0.72rem', color: '#f87171', fontFamily: 'monospace' }}>
                  Trigger: {scen.expected_failure.slice(0, 55)}...
                </div>
              </div>
            );
          })}
        </div>

        {/* Workload Count & Run Button */}
        {!baselineResult && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Workload Requests:</span>
              <select
                value={workloadCount}
                onChange={(e) => setWorkloadCount(Number(e.target.value))}
                style={{
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.82rem',
                }}
              >
                <option value={1}>1 request (Inconclusive test)</option>
                <option value={3}>3 requests</option>
                <option value={5}>5 requests (Recommended)</option>
                <option value={10}>10 requests</option>
              </select>
            </div>

            <button
              onClick={handleRunBaseline}
              disabled={loadingBaseline}
              className="btn-primary"
              style={{ padding: '8px 20px', fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: '8px', cursor: loadingBaseline ? 'not-allowed' : 'pointer' }}
            >
              <Play size={15} />
              {loadingBaseline ? 'Executing Baseline Workload...' : 'Run Baseline Experiment'}
            </button>
          </div>
        )}
      </div>

      {/* Baseline Results Metrics Card */}
      {baselineResult && (
        <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', borderLeft: '4px solid #f87171' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={18} color="#f87171" />
              <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>
                Pre-Fix Baseline Experiment Recorded ({baselineResult.experiment_id})
              </h3>
            </div>
            <span className="badge badge-critical">Active Incident State</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '16px' }}>
            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '12px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>TOTAL REQUESTS</span>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                {baselineResult.metrics.total_requests}
              </div>
            </div>

            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '12px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>FAILED REQUESTS</span>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#f87171' }}>
                {baselineResult.metrics.failed_requests}
              </div>
            </div>

            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '12px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>BASELINE ERROR RATE</span>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#f87171' }}>
                {Math.round(baselineResult.metrics.error_rate * 100)}%
              </div>
            </div>

            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '12px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>P95 LATENCY</span>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#ffd36e' }}>
                {baselineResult.metrics.latency_p95_ms}ms
              </div>
            </div>
          </div>

          {/* Captured Error Messages */}
          {baselineResult.metrics.error_messages?.length > 0 && (
            <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '10px 14px', borderRadius: '6px', fontSize: '0.76rem', color: '#fca5a5', fontFamily: 'monospace' }}>
              Observed Failure: {baselineResult.metrics.error_messages.join(' | ')}
            </div>
          )}
        </div>
      )}

      {/* Step 2: Fix Candidate Selection & Approval */}
      {baselineResult && !validationReport && (
        <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <ShieldCheck size={18} color="var(--accent)" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>
              Step 2: Select Candidate Patch & Explicitly Approve Sandbox Application
            </h3>
          </div>

          {/* Candidate Fix Radio Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
            {baselineResult.available_fixes?.map((fix) => {
              const isSelected = selectedFixId === fix.id;
              return (
                <div
                  key={fix.id}
                  onClick={() => setSelectedFixId(fix.id)}
                  style={{
                    background: isSelected ? 'rgba(115, 217, 245, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                    border: isSelected ? '1.5px solid var(--accent)' : '1px solid var(--border)',
                    borderRadius: '8px',
                    padding: '14px 16px',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <input
                        type="radio"
                        checked={isSelected}
                        onChange={() => setSelectedFixId(fix.id)}
                        style={{ cursor: 'pointer' }}
                      />
                      <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                        {fix.title}
                      </strong>
                    </div>
                    <span className="badge" style={{ fontSize: '0.7rem' }}>
                      Risk: {fix.risk_level}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0 0 10px 24px' }}>
                    {fix.description}
                  </p>
                  {fix.configuration_diff && (
                    <pre
                      style={{
                        marginLeft: '24px',
                        background: 'rgba(0, 0, 0, 0.4)',
                        border: '1px solid var(--border)',
                        padding: '10px',
                        borderRadius: '6px',
                        fontSize: '0.74rem',
                        fontFamily: 'monospace',
                        color: '#73D9F5',
                        overflowX: 'auto',
                      }}
                    >
                      {fix.configuration_diff}
                    </pre>
                  )}
                </div>
              );
            })}
          </div>

          {/* Explicit User Approval Checkbox (Safety Constraint) */}
          <div
            style={{
              background: 'rgba(255, 211, 110, 0.08)',
              border: '1px solid rgba(255, 211, 110, 0.3)',
              borderRadius: '8px',
              padding: '14px 18px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <input
              type="checkbox"
              id="fix-approval-checkbox"
              checked={userApproved}
              onChange={(e) => setUserApproved(e.target.checked)}
              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
            />
            <label htmlFor="fix-approval-checkbox" style={{ fontSize: '0.84rem', color: '#ffd36e', cursor: 'pointer' }}>
              <strong>User Approval Required:</strong> I explicitly approve applying the candidate configuration to the local test sandbox. (Sentinel will never automatically deploy to production).
            </label>
          </div>

          <button
            onClick={handleRunValidation}
            disabled={loadingValidation || !userApproved}
            className="btn-primary"
            style={{
              padding: '10px 24px',
              fontSize: '0.9rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              cursor: loadingValidation || !userApproved ? 'not-allowed' : 'pointer',
              opacity: !userApproved ? 0.6 : 1,
            }}
          >
            <Play size={16} />
            {loadingValidation ? 'Executing Fix Replay...' : 'Run Fix Validation Experiment'}
          </button>
        </div>
      )}

      {/* Step 3: Comparative Telemetry Differential Report */}
      {validationReport && (
        <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
            <div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Fix Verification Outcome
              </span>
              <div style={{ marginTop: '6px' }}>
                {getVerdictBadge(validationReport.verdict)}
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Evidence Confidence
              </span>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--accent)', marginTop: '2px' }}>
                {Math.round(validationReport.confidence * 100)}%
              </div>
            </div>
          </div>

          {/* Before vs After Comparison Table */}
          <div style={{ background: 'rgba(0, 0, 0, 0.35)', border: '1px solid var(--border)', borderRadius: '10px', padding: '16px', marginBottom: '20px' }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: '700', marginBottom: '12px' }}>
              Before-and-After Metric Differential
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '12px', fontSize: '0.82rem', paddingBottom: '8px', borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
              <span>Signal</span>
              <span>Pre-Fix Baseline</span>
              <span>Post-Fix Replay</span>
              <span>Delta</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '12px', fontSize: '0.82rem', padding: '10px 0', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <strong>Error Rate</strong>
              <span style={{ color: '#f87171' }}>{Math.round(validationReport.baseline_metrics.error_rate * 100)}%</span>
              <span style={{ color: validationReport.post_fix_metrics.error_rate === 0 ? '#34d399' : '#f87171' }}>
                {Math.round(validationReport.post_fix_metrics.error_rate * 100)}%
              </span>
              <strong style={{ color: validationReport.error_rate_delta > 0 ? '#34d399' : '#f87171' }}>
                {validationReport.error_rate_delta > 0 ? `-${Math.round(validationReport.error_rate_delta * 100)}%` : '0%'}
              </strong>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '12px', fontSize: '0.82rem', padding: '10px 0', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <strong>Successful Invocations</strong>
              <span>{validationReport.baseline_metrics.successful_requests} / {validationReport.baseline_metrics.total_requests}</span>
              <span>{validationReport.post_fix_metrics.successful_requests} / {validationReport.post_fix_metrics.total_requests}</span>
              <strong style={{ color: '#34d399' }}>
                +{validationReport.post_fix_metrics.successful_requests - validationReport.baseline_metrics.successful_requests}
              </strong>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '12px', fontSize: '0.82rem', padding: '10px 0' }}>
              <strong>P95 Latency</strong>
              <span>{validationReport.baseline_metrics.latency_p95_ms}ms</span>
              <span>{validationReport.post_fix_metrics.latency_p95_ms}ms</span>
              <span style={{ color: 'var(--accent)' }}>
                {validationReport.post_fix_metrics.latency_p95_ms && validationReport.baseline_metrics.latency_p95_ms
                  ? `${Math.round(validationReport.post_fix_metrics.latency_p95_ms - validationReport.baseline_metrics.latency_p95_ms)}ms`
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Measurements Explanation Card */}
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px', marginBottom: '20px' }}>
            <h4 style={{ fontSize: '0.88rem', fontWeight: '700', marginBottom: '6px' }}>
              Telemetry Evidence Explanation
            </h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.5', margin: 0 }}>
              {validationReport.explanation}
            </p>
          </div>

          {/* Safety Verification Notes */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
            {validationReport.safety_notes?.map((note, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Check size={12} color="#34d399" />
                <span>{note}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
