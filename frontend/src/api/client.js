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
  const res = await fetch(`${BASE_URL}/projects`);
  if (!res.ok) throw new Error(`Failed to list projects: ${res.statusText}`);
  return res.json();
}

export async function fetchProjectMetadata(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}`);
  if (!res.ok) throw new Error(`Failed to get project: ${res.statusText}`);
  return res.json();
}

export async function inspectProject(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/inspect`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Inspection failed');
  }
  return res.json();
}

export async function fetchProjectCapabilities(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/capabilities`);
  if (!res.ok) throw new Error(`Failed to fetch capabilities: ${res.statusText}`);
  return res.json();
}

export async function deleteProject(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete project: ${res.statusText}`);
  return res.json();
}
