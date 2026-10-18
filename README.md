# SENTINEL — Developer Intelligence Platform

**Repository:** [https://github.com/adityasystems99/SENTINEL](https://github.com/adityasystems99/SENTINEL)

SENTINEL (Self-Investigating Production Engineer) is an autonomous developer intelligence platform designed to ingest distributed application telemetry, construct causal incident graphs using NetworkX, rank root causes of cascading failures, and provide interactive investigation dashboards.

## Architecture

* **Backend**: Python 3.14 + FastAPI (`backend/app/main.py`)
  * **Project Ingestion & Workspace Isolation**:
    * Secure upload and validation of project ZIP archives (`POST /api/projects/upload`).
    * Defense-in-depth: Zip Slip path traversal protection, symlink prohibition, binary executable rejection, and size/entry limits.
    * Secret and dependency filtering: `.env`, private keys, `node_modules`, and virtual environments are automatically excluded.
    * Isolated filesystem workspaces (`data/projects/{project_id}/source`) with separate `metadata.json` storage.
    * Capability matrix and inspection endpoints (`/api/projects/{project_id}/capabilities`, `/inspect`).
  * **Telemetry Ingestion & Store**:
    * Structured event schemas and fingerprint deduplication (`POST /api/telemetry/ingest`).
    * In-memory thread-safe store with zero external database dependencies (strictly no SQLite, no message queues).
  * **Incident Correlation & Graph Engine**:
    * NetworkX directed causal graphs (`backend/app/graph/builder.py`).
    * Root Cause Ranking: Reversed PageRank + topology source detection + anomaly heuristics (`backend/app/graph/ranker.py`).
* **Frontend**: React 19 + Vite (`frontend/`)
  * Active project workspace selector and upload modal with drag-and-drop.
  * Interactive dark-mode dashboard with glassmorphism design tokens.
  * Real-time telemetry status, active incident lists, and root-cause cards with confidence metrics.
  * SVG NetworkX topology graph visualizer with clickable nodes.
  * Chronological trace and log event stream.
* **Demo Application & Chaos Scenarios**:
  * Simulated multi-tier microservice architecture: `web-gateway`, `auth-service`, `order-service`, `inventory-service`, `payment-service`.
  * Failure injection scenarios:
    * `db_pool_exhaustion`: HikariPool connection starvation on inventory service.
    * `bad_auth_deployment`: Deployment marker + null pointer session error.
    * `payment_timeout`: Upstream gateway timeout cascade.
    * `healthy_traffic`: Normal traffic generation.
    * `recover`: Reset failure toggles.

## Quickstart

### 1. Run Automated Backend Tests
```bash
& "backend_venv\Scripts\pytest.exe" -c pytest.ini -v
```

### 2. Start Backend API Server
```bash
& "backend_venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API docs available at: `http://127.0.0.1:8000/docs`

### 3. Build & Run Frontend
```bash
cd frontend
npm install
npm run build
npm run dev
```
Dashboard available at: `http://localhost:5173`
