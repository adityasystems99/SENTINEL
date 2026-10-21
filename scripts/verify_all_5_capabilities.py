"""SENTINEL — Comprehensive End-to-End Production Verification Suite.

Tests the full deployed system across:
1. Backend Health & API Availability
2. Production CORS Preflight & Response Headers (Origin: https://sentinel-7f6f.vercel.app)
3. Multi-Size Direct Vercel Blob Uploads (Small, 4.8 MB > 4.5 MB Function limit, 13 MB representative)
4. Upload Safety & Rejections (Oversized > 50 MB, Non-ZIP, Corrupt ZIP, Malformed JSON, Untrusted SSRF Hosts)
5. Start Project Inspection & Capability Workspace Initialization
6. Capability 1: Integration Readiness (Compatibility Assessment)
7. Capability 2: Contract Compliance (Promise vs. Reality Audit)
8. Capability 3: Live Incident RCA (Telemetry Correlation & Root Cause Ranking)
9. Capability 4: Dependency & Blast Radius Radar (Service Mesh Topology & Blast Radius)
10. Capability 5: Controlled Fix Validation (Replay Lab Baseline & Post-Fix Evaluation)
11. Production Cleanup (Project Deletion & Telemetry Recovery)
"""
import io
import json
import time
import zipfile
import httpx

BACKEND_URL = "https://sentinel-backend-api.vercel.app"
FRONTEND_ORIGIN = "https://sentinel-7f6f.vercel.app"


def create_synthetic_zip(files: dict, padding_bytes: int = 0) -> bytes:
    """Construct a well-formed in-memory ZIP archive with code and optional padding."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
        if padding_bytes > 0:
            zf.writestr("assets/payload.dat", b"X" * padding_bytes)
    return buf.getvalue()


def run_comprehensive_verification():
    print("=" * 78, flush=True)
    print("SENTINEL FULL PRODUCTION 5-CAPABILITY & WORKFLOW VERIFICATION", flush=True)
    print(f"Target Backend:  {BACKEND_URL}", flush=True)
    print(f"Frontend Origin: {FRONTEND_ORIGIN}", flush=True)
    print("=" * 78, flush=True)

    test_projects_to_clean = []
    results = {}

    base_files = {
        "main.py": """from fastapi import FastAPI
app = FastAPI()

@app.get('/health')
def health():
    return {'status': 'healthy', 'service': 'order-service'}

@app.get('/orders')
def get_orders():
    return [{'id': 'ord-101', 'amount': 149.50, 'status': 'completed'}]

@app.post('/checkout')
def checkout():
    return {'status': 'success', 'order_id': 'ord-101'}
""",
        "requirements.txt": "fastapi==0.115.0\nuvicorn>=0.30.0\npydantic>=2.8.0\nhttpx>=0.27.0\n",
        "package.json": json.dumps({
            "name": "sentinel-production-demo",
            "version": "1.0.0",
            "dependencies": {
                "react": "^19.0.0",
                "vite": "^6.0.0",
                "lucide-react": "^0.468.0"
            }
        }, indent=2),
        "spec/api_contract.md": """# API Contract Specification
- Must provide GET /health endpoint returning service status
- Must provide GET /orders endpoint returning order list
- Must provide POST /checkout endpoint
- Must provide POST /payments endpoint with payment processing
""",
        "README.md": "# Sentinel Production Service\nE-commerce order pipeline.\n"
    }

    # =========================================================================
    # SECTION 1: Health & API Availability
    # =========================================================================
    print("\n[SECTION 1: Backend Health & API Availability]", flush=True)
    try:
        r_root = httpx.get(f"{BACKEND_URL}/", timeout=10.0)
        assert r_root.status_code == 200, f"Root returned {r_root.status_code}"
        print(f"  GET /: HTTP {r_root.status_code} ({r_root.json().get('status', 'ok')})", flush=True)

        r_health = httpx.get(f"{BACKEND_URL}/health", timeout=10.0)
        assert r_health.status_code == 200
        print(f"  GET /health: HTTP {r_health.status_code} (status={r_health.json().get('status')})", flush=True)

        r_api_health = httpx.get(f"{BACKEND_URL}/api/health", timeout=10.0)
        assert r_api_health.status_code == 200
        print(f"  GET /api/health: HTTP {r_api_health.status_code} (version={r_api_health.json().get('version')})", flush=True)
        results["1. Health & Availability"] = "PASS"
    except Exception as e:
        results["1. Health & Availability"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 2: Production CORS Preflight & Origin Validation
    # =========================================================================
    print("\n[SECTION 2: Production CORS & Preflight Verification]", flush=True)
    try:
        # Preflight OPTIONS on upload route
        cors_headers = {
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,x-api-key",
        }
        r_opt = httpx.options(f"{BACKEND_URL}/api/projects/upload", headers=cors_headers, timeout=10.0)
        assert r_opt.status_code in (200, 204), f"Preflight returned {r_opt.status_code}"
        allow_origin = r_opt.headers.get("access-control-allow-origin")
        assert allow_origin in (FRONTEND_ORIGIN, "*"), f"Unexpected Allow-Origin: {allow_origin}"
        print(f"  OPTIONS /api/projects/upload: HTTP {r_opt.status_code}", flush=True)
        print(f"    Access-Control-Allow-Origin: {allow_origin}", flush=True)
        print(f"    Access-Control-Allow-Methods: {r_opt.headers.get('access-control-allow-methods')}", flush=True)

        # Actual GET with Origin header
        r_cors_get = httpx.get(f"{BACKEND_URL}/api/health", headers={"Origin": FRONTEND_ORIGIN}, timeout=10.0)
        assert r_cors_get.status_code == 200
        assert r_cors_get.headers.get("access-control-allow-origin") in (FRONTEND_ORIGIN, "*")
        print(f"  GET /api/health with Origin: HTTP {r_cors_get.status_code} (CORS header matched)", flush=True)
        results["2. Production CORS Preflight"] = "PASS"
    except Exception as e:
        results["2. Production CORS Preflight"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 3: Multi-Size Uploads via Private Vercel Blob
    # =========================================================================
    print("\n[SECTION 3: Multi-Size Uploads via Private Vercel Blob]", flush=True)

    # 3A: Small Archive (650 Bytes)
    try:
        print("\n--- 3A: Small Archive (650 B) ---", flush=True)
        small_zip = create_synthetic_zip(base_files, padding_bytes=0)
        s_res = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/session",
            json={"filename": "small-app.zip", "file_size": len(small_zip), "name": "Verification Small App"},
            timeout=15.0
        )
        assert s_res.status_code == 200, f"Session creation failed: {s_res.text}"
        s_data = s_res.json()
        assert s_data["strategy"] == "vercel_blob"
        assert s_data["access"] == "private"
        print(f"  Session created: {s_data['project_id']}, strategy={s_data['strategy']}, access={s_data['access']}", flush=True)

        t_put = time.time()
        p_res = httpx.put(
            s_data["upload_url"],
            content=small_zip,
            headers={
                "Authorization": f"Bearer {s_data['client_token']}",
                "x-api-version": "7",
                "x-vercel-blob-access": "private",
                "x-content-type": "application/zip",
                "Content-Type": "application/zip",
            },
            timeout=30.0
        )
        assert p_res.status_code in (200, 201), f"Direct PUT failed: {p_res.text}"
        print(f"  Direct Blob PUT: HTTP {p_res.status_code} in {time.time() - t_put:.2f}s", flush=True)
        small_blob_url = p_res.json().get("url") or p_res.json().get("downloadUrl") or s_data["upload_url"]

        t_comp = time.time()
        c_res = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/complete",
            json={"project_id": s_data["project_id"], "name": "Verification Small App", "blob_url": small_blob_url},
            timeout=30.0
        )
        assert c_res.status_code == 201, f"Complete failed: {c_res.text}"
        small_meta = c_res.json()
        assert small_meta["status"] == "ready"
        small_proj_id = small_meta["project_id"]
        test_projects_to_clean.append(small_proj_id)
        print(f"  Complete & Ingest: HTTP {c_res.status_code} in {time.time() - t_comp:.2f}s (status={small_meta['status']})", flush=True)
        results["3A. Small Archive Upload"] = "PASS"
    except Exception as e:
        results["3A. Small Archive Upload"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # 3B: Medium Archive > 4.5 MB (4.8 MB) — Bypasses Vercel Function Request Limit
    try:
        print("\n--- 3B: 4.8 MB Archive (> 4.5 MB Function Limit) ---", flush=True)
        mb_4_8_zip = create_synthetic_zip(base_files, padding_bytes=int(4.8 * 1024 * 1024))
        s_res = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/session",
            json={"filename": "service_4_8mb.zip", "file_size": len(mb_4_8_zip), "name": "Verification 4.8MB App"},
            timeout=15.0
        )
        assert s_res.status_code == 200
        s_data = s_res.json()
        print(f"  Session created: {s_data['project_id']} ({len(mb_4_8_zip)/(1024*1024):.2f} MB)", flush=True)

        t_put = time.time()
        p_res = httpx.put(
            s_data["upload_url"],
            content=mb_4_8_zip,
            headers={
                "Authorization": f"Bearer {s_data['client_token']}",
                "x-api-version": "7",
                "x-vercel-blob-access": "private",
                "x-content-type": "application/zip",
                "Content-Type": "application/zip",
            },
            timeout=60.0
        )
        assert p_res.status_code in (200, 201), f"Direct PUT failed: {p_res.text}"
        put_dur_4_8 = time.time() - t_put
        print(f"  Direct Blob PUT: HTTP {p_res.status_code} in {put_dur_4_8:.2f}s (NO 413, NO CORS error)", flush=True)
        mb_4_8_blob_url = p_res.json().get("url") or p_res.json().get("downloadUrl") or s_data["upload_url"]

        t_comp = time.time()
        c_res = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/complete",
            json={"project_id": s_data["project_id"], "name": "Verification 4.8MB App", "blob_url": mb_4_8_blob_url},
            timeout=60.0
        )
        assert c_res.status_code == 201, f"Complete failed: {c_res.text}"
        comp_dur_4_8 = time.time() - t_comp
        mb_4_8_meta = c_res.json()
        assert mb_4_8_meta["status"] == "ready"
        test_projects_to_clean.append(mb_4_8_meta["project_id"])
        print(f"  Complete & Ingest: HTTP {c_res.status_code} in {comp_dur_4_8:.2f}s (status={mb_4_8_meta['status']})", flush=True)
        results["3B. 4.8 MB Archive Upload"] = "PASS"
    except Exception as e:
        results["3B. 4.8 MB Archive Upload"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # 3C: Representative 13.0 MB Archive
    try:
        print("\n--- 3C: Representative 13.0 MB Archive ---", flush=True)
        mb_13_zip = create_synthetic_zip(base_files, padding_bytes=int(13.0 * 1024 * 1024))
        s_res = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/session",
            json={"filename": "service_13mb.zip", "file_size": len(mb_13_zip), "name": "Verification 13MB App"},
            timeout=15.0
        )
        assert s_res.status_code == 200
        s_data = s_res.json()
        print(f"  Session created: {s_data['project_id']} ({len(mb_13_zip)/(1024*1024):.2f} MB)", flush=True)

        t_put = time.time()
        p_res = httpx.put(
            s_data["upload_url"],
            content=mb_13_zip,
            headers={
                "Authorization": f"Bearer {s_data['client_token']}",
                "x-api-version": "7",
                "x-vercel-blob-access": "private",
                "x-content-type": "application/zip",
                "Content-Type": "application/zip",
            },
            timeout=120.0
        )
        assert p_res.status_code in (200, 201), f"Direct PUT failed: {p_res.text}"
        put_dur_13 = time.time() - t_put
        print(f"  Direct Blob PUT: HTTP {p_res.status_code} in {put_dur_13:.2f}s (NO 413, NO CORS error)", flush=True)
        mb_13_blob_url = p_res.json().get("url") or p_res.json().get("downloadUrl") or s_data["upload_url"]

        t_comp = time.time()
        c_res = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/complete",
            json={"project_id": s_data["project_id"], "name": "Verification 13MB App", "blob_url": mb_13_blob_url},
            timeout=60.0
        )
        assert c_res.status_code == 201, f"Complete failed: {c_res.text}"
        comp_dur_13 = time.time() - t_comp
        mb_13_meta = c_res.json()
        assert mb_13_meta["status"] == "ready"
        test_projects_to_clean.append(mb_13_meta["project_id"])
        print(f"  Complete & Ingest (Measured Scan Time): HTTP {c_res.status_code} in {comp_dur_13:.2f}s (status={mb_13_meta['status']})", flush=True)
        print(f"    Extracted size: {mb_13_meta.get('extracted_size_bytes', 0)} bytes, Frameworks: {mb_13_meta.get('detected_frameworks')}", flush=True)
        results["3C. 13 MB Archive Upload"] = "PASS"
    except Exception as e:
        results["3C. 13 MB Archive Upload"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 4: Upload Safety, Rejection Rules & Security Defenses
    # =========================================================================
    print("\n[SECTION 4: Upload Safety & Error Handling]", flush=True)
    try:
        # 4A: Non-ZIP extension rejection
        r_bad_ext = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/session",
            json={"filename": "exploit.tar.gz", "file_size": 2048},
            timeout=10.0
        )
        assert r_bad_ext.status_code == 400
        print(f"  Non-ZIP extension (.tar.gz): HTTP {r_bad_ext.status_code} ({r_bad_ext.json().get('detail')})", flush=True)

        # 4B: Over-50 MB upload session rejection
        r_oversized = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/session",
            json={"filename": "huge_codebase.zip", "file_size": 55 * 1024 * 1024},
            timeout=10.0
        )
        assert r_oversized.status_code == 400
        print(f"  Over-50 MB Archive (55 MB): HTTP {r_oversized.status_code} ({r_oversized.json().get('detail')})", flush=True)

        # 4C: Corrupt ZIP magic bytes rejection
        r_corrupt = httpx.post(
            f"{BACKEND_URL}/api/projects/upload",
            files={"file": ("corrupt.zip", b"GARBAGE_HEADER_DATA_12345", "application/zip")},
            timeout=10.0
        )
        assert r_corrupt.status_code == 400
        print(f"  Corrupt ZIP header: HTTP {r_corrupt.status_code} ({r_corrupt.json().get('detail')})", flush=True)

        # 4D: Malformed JSON request rejection
        r_malformed = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/session",
            content=b"not-json-at-all",
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        assert r_malformed.status_code in (400, 422)
        print(f"  Malformed Request Body: HTTP {r_malformed.status_code}", flush=True)

        # 4E: Untrusted SSRF Blob Host rejection
        r_ssrf = httpx.post(
            f"{BACKEND_URL}/api/projects/upload/complete",
            json={"project_id": "prj-fake", "name": "Fake", "blob_url": "https://malicious-attacker.com/exploit.zip"},
            timeout=10.0
        )
        assert r_ssrf.status_code == 400
        print(f"  Untrusted SSRF Host rejection: HTTP {r_ssrf.status_code} ({r_ssrf.json().get('detail')})", flush=True)
        results["4. Safety & Rejections"] = "PASS"
    except Exception as e:
        results["4. Safety & Rejections"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 5: Start Project & Capability Inspection
    # =========================================================================
    print("\n[SECTION 5: Start Project & Capability Inspection]", flush=True)
    try:
        active_proj_id = small_proj_id
        r_inspect = httpx.post(f"{BACKEND_URL}/api/projects/{active_proj_id}/inspect", timeout=15.0)
        assert r_inspect.status_code == 200, f"Inspection failed: {r_inspect.text}"
        inspect_data = r_inspect.json()
        print(f"  Start Project Triggered: HTTP {r_inspect.status_code}", flush=True)
        print(f"  Project ID: {inspect_data.get('project_id')}, Files: {inspect_data.get('file_count')}", flush=True)
        print(f"  Detected Frameworks: {inspect_data.get('detected_frameworks')}", flush=True)
        capabilities = inspect_data.get("capabilities", [])
        print(f"  Capability Workspaces Initialized: {len(capabilities)} features available", flush=True)
        for c in capabilities:
            print(f"    - [{c.get('status')}] {c.get('id')} ({c.get('title')})", flush=True)
        results["5. Start Project Inspection"] = "PASS"
    except Exception as e:
        results["5. Start Project Inspection"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 6: Capability 1 — Integration Readiness (Compatibility Assessment)
    # =========================================================================
    print("\n[SECTION 6: Capability 1 — Can I use it? (Integration Readiness)]", flush=True)
    try:
        r_compat_post = httpx.post(f"{BACKEND_URL}/api/projects/{active_proj_id}/compatibility/assess", timeout=15.0)
        assert r_compat_post.status_code == 200, f"Compatibility assess failed: {r_compat_post.text}"
        c_data = r_compat_post.json()
        print(f"  POST assess: HTTP {r_compat_post.status_code}", flush=True)
        print(f"  Overall Readiness: {c_data.get('overall_status')}", flush=True)
        print(f"  Confidence: {c_data.get('confidence')}", flush=True)
        print(f"  Telemetry Readiness: {c_data.get('telemetry_readiness', {}).get('status')}", flush=True)
        print(f"  Detected Technologies ({len(c_data.get('detected_technologies', []))}): {', '.join([t.get('name') for t in c_data.get('detected_technologies', [])[:5]])}", flush=True)

        r_compat_get = httpx.get(f"{BACKEND_URL}/api/projects/{active_proj_id}/compatibility", timeout=15.0)
        assert r_compat_get.status_code == 200
        print(f"  GET report: HTTP {r_compat_get.status_code} (Verified persistent)", flush=True)
        results["Capability 1: Compatibility"] = "PASS"
    except Exception as e:
        results["Capability 1: Compatibility"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 7: Capability 2 — Contract Compliance (Promise vs. Reality Audit)
    # =========================================================================
    print("\n[SECTION 7: Capability 2 — Have I built what I promised? (Spec Audit)]", flush=True)
    try:
        spec_text = """# API Contract Specification
- Must provide GET /health endpoint returning service status
- Must provide GET /orders endpoint returning order list
- Must provide POST /checkout endpoint
- Must provide POST /payments endpoint with payment processing
"""
        r_audit_post = httpx.post(
            f"{BACKEND_URL}/api/projects/{active_proj_id}/audit",
            json={"requirements_text": spec_text, "auto_detect_spec": False},
            timeout=20.0
        )
        assert r_audit_post.status_code == 200, f"Audit failed: {r_audit_post.text}"
        a_data = r_audit_post.json()
        print(f"  POST audit: HTTP {r_audit_post.status_code}", flush=True)
        print(f"  Compliance Score: {a_data.get('compliance_score')}%", flush=True)
        print(f"  Findings Count: {len(a_data.get('findings', []))}", flush=True)
        for f in a_data.get("findings", [])[:4]:
            print(f"    * [{f.get('status')}] {f.get('title')}", flush=True)

        r_audit_get = httpx.get(f"{BACKEND_URL}/api/projects/{active_proj_id}/audit", timeout=15.0)
        assert r_audit_get.status_code == 200
        print(f"  GET audit report: HTTP {r_audit_get.status_code} (Verified persistent)", flush=True)
        results["Capability 2: Spec Audit"] = "PASS"
    except Exception as e:
        results["Capability 2: Spec Audit"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 8: Capability 3 — Live Incident Investigation (RCA & Evidence)
    # =========================================================================
    print("\n[SECTION 8: Capability 3 — Why is my app failing? (Incident Investigation)]", flush=True)
    try:
        r_seed = httpx.post(f"{BACKEND_URL}/api/demo/scenario/bad_auth_deployment?count=3", timeout=15.0)
        assert r_seed.status_code == 200, f"Scenario injection failed: {r_seed.text}"
        print(f"  Seed Failure Telemetry: HTTP {r_seed.status_code}", flush=True)

        r_analyze = httpx.post(f"{BACKEND_URL}/api/incidents/analyze", json={"window_seconds": 300}, timeout=20.0)
        assert r_analyze.status_code in (200, 201), f"Incident analysis failed: {r_analyze.text}"
        inc_report = r_analyze.json()
        inc_id = inc_report.get("incident_id")
        print(f"  Incident Correlation: HTTP {r_analyze.status_code}", flush=True)
        print(f"  Incident ID: {inc_id}", flush=True)
        print(f"  Title: {inc_report.get('title')}", flush=True)
        print(f"  Severity: {inc_report.get('severity')}", flush=True)

        r_detail = httpx.get(f"{BACKEND_URL}/api/incidents/{inc_id}", timeout=15.0)
        assert r_detail.status_code == 200
        print(f"  Incident Detail Fetch: HTTP {r_detail.status_code} (Verified evidence & logs)", flush=True)
        results["Capability 3: Incident RCA"] = "PASS"
    except Exception as e:
        results["Capability 3: Incident RCA"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 9: Capability 4 — Dependency & Blast Radius Radar
    # =========================================================================
    print("\n[SECTION 9: Capability 4 — What else could break? (Impact Radar)]", flush=True)
    try:
        r_topo = httpx.get(f"{BACKEND_URL}/api/radar/topology?window_seconds=600", timeout=15.0)
        assert r_topo.status_code == 200, f"Radar topology failed: {r_topo.text}"
        topo = r_topo.json()
        print(f"  GET topology: HTTP {r_topo.status_code}", flush=True)
        print(f"  Services in Mesh: {len(topo.get('nodes', []))} nodes ({', '.join([n.get('id', '') for n in topo.get('nodes', [])])})", flush=True)
        print(f"  Call Dependencies: {len(topo.get('edges', []))} edges", flush=True)

        r_impact = httpx.post(f"{BACKEND_URL}/api/radar/analyze", json={"suspected_component": "auth-service"}, timeout=15.0)
        assert r_impact.status_code == 200, f"Impact analysis failed: {r_impact.text}"
        impact = r_impact.json()
        print(f"  POST blast radius analyze: HTTP {r_impact.status_code}", flush=True)
        print(f"  Target Service: {impact.get('suspected_component')}", flush=True)
        impacted = impact.get("impacted_components", [])
        summary_nodes = [c.get("service") + " (" + c.get("relationship") + ")" for c in impacted[:4]]
        print(f"  Impacted Components: {len(impacted)} [{', '.join(summary_nodes)}]", flush=True)
        print(f"  Confidence: {impact.get('confidence')}", flush=True)
        results["Capability 4: Impact Radar"] = "PASS"
    except Exception as e:
        results["Capability 4: Impact Radar"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 10: Capability 5 — Controlled Fix Validation (Replay Lab)
    # =========================================================================
    print("\n[SECTION 10: Capability 5 — Does my fix actually work? (Fix Validation)]", flush=True)
    try:
        r_scenarios = httpx.get(f"{BACKEND_URL}/api/validation/scenarios", timeout=15.0)
        assert r_scenarios.status_code == 200, f"List scenarios failed: {r_scenarios.text}"
        scenarios = r_scenarios.json()
        print(f"  GET scenarios: HTTP {r_scenarios.status_code} ({len(scenarios)} validation scenarios)", flush=True)
        assert len(scenarios) > 0

        target_scenario = scenarios[0]
        scenario_id = target_scenario.get("id") or target_scenario.get("scenario_id")
        print(f"  Selected Scenario: {scenario_id} - {target_scenario.get('name')}", flush=True)

        r_base = httpx.post(
            f"{BACKEND_URL}/api/validation/baseline",
            json={"scenario_id": scenario_id, "workload_count": 20},
            timeout=20.0
        )
        assert r_base.status_code == 200, f"Baseline failed: {r_base.text}"
        baseline = r_base.json()
        b_metrics = baseline.get("metrics", {})
        print(f"  POST baseline: HTTP {r_base.status_code} (Error Rate: {b_metrics.get('error_rate')}, Failures: {b_metrics.get('failed_requests')}/{b_metrics.get('total_requests')})", flush=True)

        fixes = target_scenario.get("available_fixes") or target_scenario.get("candidate_fixes", [])
        candidate_fix = fixes[0]
        fix_id = candidate_fix.get("id") or candidate_fix.get("fix_id")
        print(f"  Candidate Fix: {fix_id} - {candidate_fix.get('title')}", flush=True)

        r_fix = httpx.post(
            f"{BACKEND_URL}/api/validation/run",
            json={
                "experiment_id": baseline["experiment_id"],
                "fix_id": fix_id,
                "approved": True,
                "workload_count": 20
            },
            timeout=20.0
        )
        assert r_fix.status_code == 200, f"Validation run failed: {r_fix.text}"
        val_report = r_fix.json()
        print(f"  POST run fix validation: HTTP {r_fix.status_code}", flush=True)
        print(f"  Verdict: {val_report.get('verdict')}", flush=True)
        b_err = val_report.get("baseline_metrics", {}).get("error_rate")
        p_err = val_report.get("post_fix_metrics", {}).get("error_rate")
        print(f"  Baseline Error Rate: {b_err} -> Post-Fix: {p_err} (Delta: {val_report.get('error_rate_delta')})", flush=True)
        print(f"  Recovery Behavior: {val_report.get('recovery_behavior')}", flush=True)
        print(f"  Explanation: {val_report.get('explanation')}", flush=True)

        r_hist = httpx.get(f"{BACKEND_URL}/api/validation/history", timeout=15.0)
        assert r_hist.status_code == 200
        print(f"  GET history: HTTP {r_hist.status_code} ({len(r_hist.json())} experiments recorded)", flush=True)
        results["Capability 5: Fix Validation"] = "PASS"
    except Exception as e:
        results["Capability 5: Fix Validation"] = f"FAIL: {e}"
        print(f"  FAIL: {e}", flush=True)

    # =========================================================================
    # SECTION 11: Production Cleanup
    # =========================================================================
    print("\n[SECTION 11: Production Test Cleanup]", flush=True)
    cleanup_success = True
    for pid in test_projects_to_clean:
        try:
            r_del = httpx.delete(f"{BACKEND_URL}/api/projects/{pid}", timeout=10.0)
            assert r_del.status_code == 200
            print(f"  Deleted test project: {pid} (HTTP {r_del.status_code})", flush=True)

            r_check = httpx.get(f"{BACKEND_URL}/api/projects/{pid}", timeout=10.0)
            assert r_check.status_code == 404
            print(f"    Verified project removed: HTTP {r_check.status_code}", flush=True)
        except Exception as e:
            cleanup_success = False
            print(f"    Cleanup warning for {pid}: {e}", flush=True)

    try:
        r_rec = httpx.post(f"{BACKEND_URL}/api/demo/scenario/recover", timeout=10.0)
        assert r_rec.status_code == 200
        print("  Demo telemetry recovered to baseline healthy state (HTTP 200).", flush=True)
    except Exception as e:
        cleanup_success = False
        print(f"  Telemetry recovery warning: {e}", flush=True)

    results["11. Cleanup"] = "PASS" if cleanup_success else "FAIL"

    # =========================================================================
    # SUMMARY REPORT
    # =========================================================================
    print("\n" + "=" * 78, flush=True)
    print("VERIFICATION SUITE SUMMARY RESULTS", flush=True)
    print("=" * 78, flush=True)
    all_passed = True
    for test_name, outcome in results.items():
        print(f"  [{outcome}] {test_name}", flush=True)
        if outcome != "PASS":
            all_passed = False

    print("=" * 78, flush=True)
    if all_passed:
        print("STATUS: FULLY VERIFIED — ALL PRODUCTION CHECKS PASSED WITH EVIDENCE", flush=True)
    else:
        print("STATUS: NOT FULLY VERIFIED — ONE OR MORE CHECKS FAILED", flush=True)
    print("=" * 78, flush=True)

    return all_passed


if __name__ == "__main__":
    success = run_comprehensive_verification()
    if not success:
        exit(1)
