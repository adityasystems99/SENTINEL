/**
 * API client for interacting with the SENTINEL FastAPI backend.
 */
const BASE_URL = '/api';

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchIncidents() {
  const res = await fetch(`${BASE_URL}/incidents`);
  if (!res.ok) throw new Error(`Failed to fetch incidents: ${res.statusText}`);
  return res.json();
}

export async function fetchIncidentDetail(incidentId) {
  const res = await fetch(`${BASE_URL}/incidents/${incidentId}`);
  if (!res.ok) throw new Error(`Failed to fetch incident ${incidentId}: ${res.statusText}`);
  return res.json();
}

export async function triggerIncidentAnalysis(windowSeconds = 300) {
  const res = await fetch(`${BASE_URL}/incidents/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ window_seconds: windowSeconds }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Incident analysis failed');
  }
  return res.json();
}

export async function triggerDemoScenario(scenarioName, count = 3) {
  const res = await fetch(`${BASE_URL}/demo/scenario/${scenarioName}?count=${count}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to trigger scenario ${scenarioName}`);
  }
  return res.json();
}

export async function fetchTelemetryEvents(limit = 50) {
  const res = await fetch(`${BASE_URL}/telemetry/events?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch telemetry: ${res.statusText}`);
  return res.json();
}

export async function clearAllData() {
  const res = await fetch(`${BASE_URL}/telemetry/events`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to reset telemetry: ${res.statusText}`);
  return res.json();
}
