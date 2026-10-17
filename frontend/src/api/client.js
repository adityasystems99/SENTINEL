/**
 * API client for interacting with the SENTINEL FastAPI backend.
 * Provides token authentication, configurable base URL, and consistent error handling.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Retrieve current client authentication token without embedding secrets into production bundles.
 * Checks runtime session storage first, then URL query parameter, and falls back to dev-only env.
 */
export function getAuthToken() {
  if (typeof window !== 'undefined') {
    // 1. Session storage (set at runtime after user provides token)
    const sessionToken = window.sessionStorage?.getItem('sentinel_token');
    if (sessionToken) return sessionToken;

    // 2. Query param for private demo links (?token=...)
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const queryToken = urlParams.get('token') || urlParams.get('key');
      if (queryToken) {
        window.sessionStorage?.setItem('sentinel_token', queryToken);
        return queryToken;
      }
    } catch (_) {}
  }

  // 3. In Vite development mode only (tree-shaken out in production build)
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_SENTINEL_API_KEY || 'demo-sentinel-key-2026';
  }

  return null;
}

export function setAuthToken(token) {
  if (typeof window !== 'undefined' && window.sessionStorage) {
    if (token) {
      window.sessionStorage.setItem('sentinel_token', token);
    } else {
      window.sessionStorage.removeItem('sentinel_token');
    }
  }
}

function authHeaders(extraHeaders = {}) {
  const token = getAuthToken();
  const headers = { ...extraHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
    headers['X-API-Key'] = token;
  }
  return headers;
}

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchIncidents() {
  const res = await fetch(`${BASE_URL}/incidents`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch incidents: ${res.statusText}`);
  return res.json();
}

export async function fetchIncidentDetail(incidentId) {
  const res = await fetch(`${BASE_URL}/incidents/${incidentId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch incident ${incidentId}: ${res.statusText}`);
  return res.json();
}

export async function triggerIncidentAnalysis(windowSeconds = 300) {
  const res = await fetch(`${BASE_URL}/incidents/analyze`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
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
    headers: authHeaders(),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to trigger scenario ${scenarioName}`);
  }
  return res.json();
}

export async function fetchTelemetryEvents(limit = 50) {
  const res = await fetch(`${BASE_URL}/telemetry/events?limit=${limit}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch telemetry: ${res.statusText}`);
  return res.json();
}

export async function clearAllData() {
  const res = await fetch(`${BASE_URL}/telemetry/events`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to reset telemetry: ${res.statusText}`);
  return res.json();
}

/* ================= Project Ingestion & Workspace APIs ================= */

export async function uploadProjectArchive(file, name, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (evt) => {
        if (evt.lengthComputable) {
          const percent = Math.round((evt.loaded / evt.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.open('POST', `${BASE_URL}/projects/upload`);
    const token = getAuthToken();
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.setRequestHeader('X-API-Key', token);
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          resolve(data);
        } catch (e) {
          reject(new Error('Invalid JSON response from server'));
        }
      } else {
        let errorMsg = `Upload failed with status ${xhr.status}`;
        try {
          const errData = JSON.parse(xhr.responseText);
          if (errData.detail) errorMsg = errData.detail;
        } catch (_) {}
        reject(new Error(errorMsg));
      }
    };

    xhr.onerror = () => {
      reject(new Error('Network error during project archive upload'));
    };

    xhr.send(formData);
  });
}

export async function fetchProjects() {
  const res = await fetch(`${BASE_URL}/projects`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to list projects: ${res.statusText}`);
  return res.json();
}

export async function fetchProjectMetadata(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to get project: ${res.statusText}`);
  return res.json();
}

export async function inspectProject(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/inspect`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Inspection failed');
  }
  return res.json();
}

export async function fetchProjectCapabilities(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/capabilities`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch capabilities: ${res.statusText}`);
  return res.json();
}

export async function deleteProject(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to delete project: ${res.statusText}`);
  return res.json();
}

/* ================= Compatibility Engine APIs (Feature 1) ================= */

export async function assessCompatibility(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/compatibility/assess`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Compatibility assessment failed');
  }
  return res.json();
}

export async function fetchCompatibilityReport(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/compatibility`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    if (res.status === 404) return null;
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch compatibility report');
  }
  return res.json();
}

/* ================= Promise vs Reality Audit APIs (Feature 2) ================= */

export async function runAudit(projectId, requirementsText, acceptanceCriteria = '', autoDetectSpec = false) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/audit`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      requirements_text: requirementsText,
      acceptance_criteria: acceptanceCriteria,
      auto_detect_spec: autoDetectSpec,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Audit execution failed');
  }
  return res.json();
}

export async function runAuditWithFile(projectId, file, acceptanceCriteria = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (acceptanceCriteria) {
    formData.append('acceptance_criteria', acceptanceCriteria);
  }

  const res = await fetch(`${BASE_URL}/projects/${projectId}/audit/file`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'File-based audit execution failed');
  }
  return res.json();
}

export async function fetchAuditReport(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/audit`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    if (res.status === 404) return null;
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch audit report');
  }
  return res.json();
}

/* ================= Feature 4: Impact Radar APIs ================= */

export async function fetchRadarTopology(windowSeconds = 600) {
  const res = await fetch(`${BASE_URL}/radar/topology?window_seconds=${windowSeconds}`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch service topology');
  }
  return res.json();
}

export async function analyzeRadarImpact(suspectedComponent, windowSeconds = 600) {
  const res = await fetch(`${BASE_URL}/radar/analyze`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      suspected_component: suspectedComponent,
      window_seconds: windowSeconds,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to analyze impact');
  }
  return res.json();
}

/* ================= Feature 5: Controlled Fix Validation APIs ================= */

export async function fetchValidationScenarios() {
  const res = await fetch(`${BASE_URL}/validation/scenarios`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch validation scenarios');
  }
  return res.json();
}

export async function runValidationBaseline(scenarioId, workloadCount = 5) {
  const res = await fetch(`${BASE_URL}/validation/baseline`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      scenario_id: scenarioId,
      workload_count: workloadCount,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to run baseline experiment');
  }
  return res.json();
}

export async function runValidationFix(experimentId, fixId, approved, workloadCount = 5) {
  const res = await fetch(`${BASE_URL}/validation/run`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      experiment_id: experimentId,
      fix_id: fixId,
      approved: approved,
      workload_count: workloadCount,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to run fix validation');
  }
  return res.json();
}

export async function fetchValidationHistory() {
  const res = await fetch(`${BASE_URL}/validation/history`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch validation history');
  }
  return res.json();
}
