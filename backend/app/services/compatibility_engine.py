"""Static analysis engine for Feature 1: Compatibility & Integration Readiness.
Performs safe, read-only inspection without executing project code or installing dependencies.
"""
import json
import os
import re
import time
from typing import Dict, List, Set, Tuple
from ..models.compatibility import (
    CompatibilityReport,
    CompatibilityStatus,
    DetectedTechnology,
    TelemetryReadiness,
)

# Common endpoint regex patterns for Python and Node
PY_ROUTE_PATTERN = re.compile(
    r'@(?:app|router|api|bp)\.(?:get|post|put|delete|patch|route)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)
JS_ROUTE_PATTERN = re.compile(
    r'(?:app|router)\.(?:get|post|put|delete|patch|use)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)

# Telemetry patterns
OTEL_PATTERN = re.compile(r'(?:opentelemetry|@opentelemetry|tracer\.start_as_current_span)', re.IGNORECASE)
LOGGING_PATTERN = re.compile(r'(?:import\s+logging|structlog|winston|pino|console\.log|logger\.)', re.IGNORECASE)
HEALTH_PATTERN = re.compile(r'/(?:health|healthz|ping|status|live|ready)', re.IGNORECASE)

def analyze_project_compatibility(project_id: str, source_dir: str) -> CompatibilityReport:
    """Perform safe static inspection over the project workspace directory."""

    if not os.path.exists(source_dir):
        return CompatibilityReport(
            project_id=project_id,
            overall_status=CompatibilityStatus.UNVERIFIED,
            telemetry_readiness=TelemetryReadiness(
                status="not_configured",
                has_opentelemetry=False,
                has_structured_logging=False,
                has_health_endpoint=False,
                evidence=["Source directory not found"]
            ),
            limitations=["Workspace source directory does not exist or has been removed."],
            confidence=0.1
        )

    detected_techs: List[DetectedTechnology] = []
    entry_points: List[str] = []
    detected_routes: Set[str] = set()
    telemetry_evidence: List[str] = []
    has_otel = False
    has_logging = False
    has_health = False
    has_tests = False
    test_files_count = 0

    language_counts: Dict[str, int] = {}
    total_files = 0

    # Walk project source tree
    for root, dirs, files in os.walk(source_dir):
        # Exclude hidden and node_modules just in case
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]

        for file in files:
            total_files += 1
            rel_path = os.path.relpath(os.path.join(root, file), source_dir).replace("\\", "/")
            ext = os.path.splitext(file)[1].lower()

            # Tally languages
            if ext == ".py":
                language_counts["Python"] = language_counts.get("Python", 0) + 1
            elif ext in (".js", ".jsx", ".mjs", ".cjs"):
                language_counts["JavaScript"] = language_counts.get("JavaScript", 0) + 1
            elif ext in (".ts", ".tsx"):
                language_counts["TypeScript"] = language_counts.get("TypeScript", 0) + 1
            elif ext == ".go":
                language_counts["Go"] = language_counts.get("Go", 0) + 1
            elif ext == ".java":
                language_counts["Java"] = language_counts.get("Java", 0) + 1
            elif ext == ".rs":
                language_counts["Rust"] = language_counts.get("Rust", 0) + 1

            # Check Entry Points
            if file in ("main.py", "app.py", "server.py", "wsgi.py", "asgi.py", "server.js", "index.js", "src/main.jsx", "src/index.ts"):
                entry_points.append(rel_path)

            # Check Test files
            if (
                file.startswith("test_") or file.endswith("_test.py") or
                ".test." in file or ".spec." in file or
                "tests/" in rel_path or "test/" in rel_path
            ):
                has_tests = True
                test_files_count += 1

            # Check Manifests
            full_path = os.path.join(root, file)
            if file == "package.json":
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        detected_techs.append(DetectedTechnology(
                            name="Node.js", category="language", evidence_file=rel_path
                        ))
                        for dep, ver in deps.items():
                            dep_lower = dep.lower()
                            if "react" in dep_lower:
                                detected_techs.append(DetectedTechnology(name="React", category="framework", version=str(ver), evidence_file=rel_path))
                            elif "express" in dep_lower:
                                detected_techs.append(DetectedTechnology(name="Express", category="framework", version=str(ver), evidence_file=rel_path))
                            elif "vite" in dep_lower:
                                detected_techs.append(DetectedTechnology(name="Vite", category="framework", version=str(ver), evidence_file=rel_path))
                            elif "next" in dep_lower:
                                detected_techs.append(DetectedTechnology(name="Next.js", category="framework", version=str(ver), evidence_file=rel_path))
                            elif "winston" in dep_lower or "pino" in dep_lower:
                                has_logging = True
                                telemetry_evidence.append(f"Logging dependency [{dep}] in {rel_path}")
                            elif "opentelemetry" in dep_lower:
                                has_otel = True
                                telemetry_evidence.append(f"OpenTelemetry SDK [{dep}] in {rel_path}")
                except Exception:
                    pass

            elif file in ("requirements.txt", "pyproject.toml", "Pipfile"):
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        detected_techs.append(DetectedTechnology(
                            name="Python", category="language", evidence_file=rel_path
                        ))
                        if "fastapi" in content:
                            detected_techs.append(DetectedTechnology(name="FastAPI", category="framework", evidence_file=rel_path))
                        if "flask" in content:
                            detected_techs.append(DetectedTechnology(name="Flask", category="framework", evidence_file=rel_path))
                        if "django" in content:
                            detected_techs.append(DetectedTechnology(name="Django", category="framework", evidence_file=rel_path))
                        if "opentelemetry" in content:
                            has_otel = True
                            telemetry_evidence.append(f"OpenTelemetry detected in {rel_path}")
                        if "prometheus" in content:
                            telemetry_evidence.append(f"Prometheus metrics detected in {rel_path}")
                        if "pytest" in content:
                            detected_techs.append(DetectedTechnology(name="Pytest", category="testing", evidence_file=rel_path))
                except Exception:
                    pass

            elif file in ("Dockerfile", "docker-compose.yml"):
                detected_techs.append(DetectedTechnology(
                    name="Docker", category="deployment", evidence_file=rel_path
                ))

            # Inspect code files for routes, telemetry, health endpoints
            if ext in (".py", ".js", ".ts", ".jsx", ".tsx") and os.path.getsize(full_path) < 1_000_000:
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        code_content = f.read()

                        # Routes
                        pattern = PY_ROUTE_PATTERN if ext == ".py" else JS_ROUTE_PATTERN
                        for match in pattern.finditer(code_content):
                            route = match.group(1)
                            detected_routes.add(route)
                            if HEALTH_PATTERN.search(route):
                                has_health = True
                                telemetry_evidence.append(f"Health endpoint route [{route}] in {rel_path}")

                        # OpenTelemetry usage in code
                        if not has_otel and OTEL_PATTERN.search(code_content):
                            has_otel = True
                            telemetry_evidence.append(f"OpenTelemetry API call in {rel_path}")

                        # Logging usage in code
                        if not has_logging and LOGGING_PATTERN.search(code_content):
                            has_logging = True
                            telemetry_evidence.append(f"Structured logging usage in {rel_path}")

                except Exception:
                    pass

    # Record dominant language technologies if not already listed via manifest
    for lang in language_counts:
        if not any(t.name == lang for t in detected_techs):
            detected_techs.append(DetectedTechnology(
                name=lang,
                category="language",
                evidence_file=f"{language_counts[lang]} {lang} source file(s)",
            ))

    # Evaluate Telemetry Readiness
    if has_otel and has_logging and has_health:
        telemetry_status = "ready"
    elif has_otel or has_logging or has_health:
        telemetry_status = "partial"
    else:
        telemetry_status = "not_configured"

    # Evaluate Overall Compatibility Status
    missing_prerequisites = []
    integration_requirements = []
    recommended_steps = []

    if not has_otel:
        missing_prerequisites.append("OpenTelemetry SDK instrumentation for trace propagation")
        recommended_steps.append("Add OpenTelemetry tracing SDK (e.g. `opentelemetry-instrumentation-fastapi` or `@opentelemetry/sdk-node`).")

    if not has_health:
        missing_prerequisites.append("Standard healthcheck route (/health or /healthz)")
        recommended_steps.append("Expose a lightweight `/health` GET endpoint reporting service liveness.")

    if not has_logging:
        missing_prerequisites.append("Structured JSON logger (e.g. Winston/Pino or Python Structlog)")
        recommended_steps.append("Enable structured JSON logging to allow SENTINEL to extract trace IDs and error severity.")

    integration_requirements.append("Target service must be able to communicate with SENTINEL telemetry sink at `/api/telemetry/ingest`.")
    integration_requirements.append("Outgoing HTTP/RPC requests should propagate trace_id and span_id headers.")

    if total_files == 0:
        overall_status = CompatibilityStatus.UNVERIFIED
    elif len(detected_techs) > 0 and len(entry_points) > 0 and telemetry_status == "ready":
        overall_status = CompatibilityStatus.COMPATIBLE
    elif len(detected_techs) > 0 and (len(entry_points) > 0 or len(detected_routes) > 0):
        overall_status = CompatibilityStatus.PARTIALLY_READY
    elif len(detected_techs) > 0:
        overall_status = CompatibilityStatus.NEEDS_CONFIGURATION
    else:
        overall_status = CompatibilityStatus.UNVERIFIED

    confidence = 0.90 if len(detected_techs) > 0 and len(entry_points) > 0 else 0.70

    limitations = [
        "Static inspection only: runtime environment variables, external microservices, and databases are not queried.",
        "Dynamic route generation (e.g. reflection, runtime metaprogramming) may not appear in static endpoint lists.",
        "Third-party SaaS dependencies (Stripe, AWS, Auth0) are identified from manifests but not validated live."
    ]

    return CompatibilityReport(
        project_id=project_id,
        overall_status=overall_status,
        detected_technologies=detected_techs,
        entry_points=sorted(entry_points),
        detected_routes=sorted(list(detected_routes))[:50],  # Top 50 routes
        telemetry_readiness=TelemetryReadiness(
            status=telemetry_status,
            has_opentelemetry=has_otel,
            has_structured_logging=has_logging,
            has_health_endpoint=has_health,
            evidence=telemetry_evidence[:10],
        ),
        integration_requirements=integration_requirements,
        missing_prerequisites=missing_prerequisites,
        recommended_setup_steps=recommended_steps,
        confidence=confidence,
        limitations=limitations,
        inspected_at=time.time(),
    )

run_compatibility_assessment = analyze_project_compatibility
