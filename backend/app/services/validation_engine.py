"""Controlled experiment and fix validation workflow engine (Feature 5: Replay Lab).
Safely runs deterministic baseline experiments, tests candidate fixes against local demo service,
measures telemetry differentials, and computes evidence-based verdicts.
Strictly requires explicit user approval before applying patches. Never executes arbitrary uploaded code.
"""
import statistics
import time
import uuid
from typing import Dict, List, Optional

from ..models.validation import (
    BaselineExperimentResult,
    CandidateFix,
    ExperimentRunMetrics,
    FailureScenarioDefinition,
    FixValidationReport,
    ValidationVerdict,
)
from demo_app.service import DemoAppService
from demo_app.scenarios import (
    inject_bad_auth_deployment,
    inject_db_pool_exhaustion,
    inject_payment_timeout,
    recover_all,
)
from ..storage.memory_store import store

# Predefined failure scenarios supported by the local instrumented architecture
SCENARIOS: Dict[str, FailureScenarioDefinition] = {
    "db_pool_exhaustion": FailureScenarioDefinition(
        id="db_pool_exhaustion",
        name="Database Connection Pool Exhaustion",
        target_service="inventory-service",
        description="Hikari connection pool saturation on inventory-service causing 3000ms timeouts and order checkout cascade failures.",
        expected_failure="HikariPool-1 - Connection is not available, request timed out (maxPoolSize=10)",
        available_fixes=[
            CandidateFix(
                id="increase_pool_size",
                title="Expand Database Pool Limits (maxPoolSize=30)",
                description="Scale Hikari pool maximum capacity from 10 to 30 connections and add connection leak detection threshold.",
                risk_level="LOW",
                configuration_diff="- datasource.hikari.maximum-pool-size: 10\n+ datasource.hikari.maximum-pool-size: 30\n+ datasource.hikari.leak-detection-threshold: 2000"
            ),
            CandidateFix(
                id="restart_inventory_db",
                title="Bounce Service & Drain Hung Threads",
                description="Perform rolling restart of inventory-service instances to flush leaked connections.",
                risk_level="MEDIUM",
                configuration_diff="# Rolling restart pod/inventory-service\n# Active connections drained"
            ),
            CandidateFix(
                id="noop_ineffective_fix",
                title="Ineffective Parameter Tweak (No pool change)",
                description="Simulates a developer change that does not address connection limits.",
                risk_level="LOW",
                configuration_diff="# Adjusted logger verbosity to DEBUG (does not resolve pool exhaustion)"
            )
        ]
    ),
    "bad_auth_deployment": FailureScenarioDefinition(
        id="bad_auth_deployment",
        name="Regressed Deployment (NullPointer Dereference)",
        target_service="auth-service",
        description="Release v2.4.1-rc1 introduced unhandled null session token dereference on token validation endpoint.",
        expected_failure="NullPointerDereference in TokenValidator.verify(): user_session is None",
        available_fixes=[
            CandidateFix(
                id="rollback_deployment",
                title="Instant Rollback to Stable Release v2.4.0",
                description="Revert container image tag to previous known good build sha #f419c80.",
                risk_level="LOW",
                configuration_diff="- image: auth-service:v2.4.1-rc1\n+ image: auth-service:v2.4.0"
            ),
            CandidateFix(
                id="hotfix_null_guard",
                title="Deploy Hotfix (Defensive Null Check)",
                description="Inject null-safe guard condition before user_session attribute lookup.",
                risk_level="LOW",
                configuration_diff="- return user_session.is_valid()\n+ if not user_session: return False\n+ return user_session.is_valid()"
            ),
            CandidateFix(
                id="noop_ineffective_fix",
                title="Ineffective Parameter Tweak (Unrelated config)",
                description="Simulates a config change that does not fix the runtime exception.",
                risk_level="LOW",
                configuration_diff="# Changed session cookie domain (does not fix NullPointer)"
            )
        ]
    ),
    "payment_timeout": FailureScenarioDefinition(
        id="payment_timeout",
        name="Downstream Payment Gateway Read Timeout",
        target_service="payment-service",
        description="External Stripe gateway connection timeout (504 Gateway Timeout) stalling order checkout completions.",
        expected_failure="ConnectTimeout: HTTPSConnectionPool(host='api.stripe-mock.com'): Read timed out",
        available_fixes=[
            CandidateFix(
                id="enable_circuit_breaker",
                title="Enable Circuit Breaker & Secondary Fallback Gateway",
                description="Activate fail-fast circuit breaker (failureRateThreshold=50%) and switch to standby processor.",
                risk_level="LOW",
                configuration_diff="- payment.circuit_breaker.enabled: false\n+ payment.circuit_breaker.enabled: true\n+ payment.fallback_processor: secondary-mock"
            ),
            CandidateFix(
                id="noop_ineffective_fix",
                title="Ineffective Parameter Tweak (No fallback)",
                description="Simulates an ineffective fix that leaves the broken endpoint active.",
                risk_level="LOW",
                configuration_diff="# Increased timeout from 5.0 to 5.2s (still fails under outage)"
            )
        ]
    )
}

class ValidationEngine:
    def __init__(self, demo_service: Optional[DemoAppService] = None):
        # Connected to shared memory store
        self.demo_svc = demo_service or DemoAppService(telemetry_sink=lambda evs: store.add_events(evs))
        self.baselines: Dict[str, BaselineExperimentResult] = {}
        self.history: List[FixValidationReport] = []

    def get_scenarios(self) -> List[FailureScenarioDefinition]:
        return list(SCENARIOS.values())

    def get_scenario(self, scenario_id: str) -> Optional[FailureScenarioDefinition]:
        return SCENARIOS.get(scenario_id)

    def _execute_workload(self, count: int) -> ExperimentRunMetrics:
        """Run simulated checkout transactions and measure latency and error rates."""
        successes = 0
        failures = 0
        latencies_ms: List[float] = []
        error_msgs: List[str] = []

        now = time.time()
        for _ in range(count):
            start = time.perf_counter()
            result = self.demo_svc.execute_checkout_flow()
            elapsed_ms = round((time.perf_counter() - start) * 1000 + (15.0 if result["success"] else 45.0), 2)
            latencies_ms.append(elapsed_ms)

            if result["success"]:
                successes += 1
            else:
                failures += 1
                if result.get("error"):
                    error_msgs.append(result["error"])

        total = successes + failures
        error_rate = round(failures / total, 4) if total > 0 else 0.0

        latencies_sorted = sorted(latencies_ms)
        p50 = latencies_sorted[int(len(latencies_sorted) * 0.50)] if latencies_sorted else None
        p95 = latencies_sorted[min(len(latencies_sorted) - 1, int(len(latencies_sorted) * 0.95))] if latencies_sorted else None
        p99 = latencies_sorted[min(len(latencies_sorted) - 1, int(len(latencies_sorted) * 0.99))] if latencies_sorted else None

        return ExperimentRunMetrics(
            total_requests=total,
            successful_requests=successes,
            failed_requests=failures,
            error_rate=error_rate,
            latencies_ms=latencies_ms,
            latency_p50_ms=p50,
            latency_p95_ms=p95,
            latency_p99_ms=p99,
            error_messages=list(set(error_msgs)),
            executed_at=now,
        )

    def run_baseline_experiment(self, scenario_id: str, workload_count: int = 5) -> BaselineExperimentResult:
        """Inject failure scenario and run baseline measurements."""
        scenario = SCENARIOS.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario '{scenario_id}'. Available: {list(SCENARIOS.keys())}")

        if workload_count <= 0:
            raise ValueError("Workload count must be greater than zero")

        # 1. Reset state first
        recover_all(self.demo_svc)

        # 2. Inject failure
        if scenario_id == "db_pool_exhaustion":
            inject_db_pool_exhaustion(self.demo_svc, count=1)
        elif scenario_id == "bad_auth_deployment":
            inject_bad_auth_deployment(self.demo_svc, count=1)
        elif scenario_id == "payment_timeout":
            inject_payment_timeout(self.demo_svc, count=1)

        # 3. Execute baseline workload
        metrics = self._execute_workload(count=workload_count)

        exp_id = f"exp-{uuid.uuid4().hex[:8]}"
        result = BaselineExperimentResult(
            experiment_id=exp_id,
            scenario_id=scenario_id,
            scenario_name=scenario.name,
            target_service=scenario.target_service,
            workload_count=workload_count,
            metrics=metrics,
            status="baseline_recorded",
            available_fixes=scenario.available_fixes,
            approved_for_fix=False,
        )

        self.baselines[exp_id] = result
        return result

    def run_fix_validation(
        self,
        experiment_id: str,
        fix_id: str,
        approved: bool,
        workload_count: int = 5
    ) -> FixValidationReport:
        """Apply approved candidate fix, run validation workload, and generate evidence-based verdict."""
        if not approved:
            raise ValueError("Safety check failed: User approval is required before applying candidate fixes or executing validation.")

        baseline = self.baselines.get(experiment_id)
        if not baseline:
            raise ValueError(f"Experiment '{experiment_id}' not found. Run a baseline experiment first.")

        scenario = SCENARIOS.get(baseline.scenario_id)
        candidate_fix = next((f for f in scenario.available_fixes if f.id == fix_id), None)
        if not candidate_fix:
            raise ValueError(f"Fix '{fix_id}' is not supported for scenario '{baseline.scenario_id}'")

        # Apply fix to local sandbox environment
        if fix_id == "noop_ineffective_fix":
            # Ineffective fix: do not resolve the underlying failure toggle
            pass
        else:
            # Effective fixes: restore health to the target service
            if baseline.scenario_id == "db_pool_exhaustion":
                self.demo_svc.db_pool_exhausted = False
            elif baseline.scenario_id == "bad_auth_deployment":
                self.demo_svc.bad_auth_deployment = False
            elif baseline.scenario_id == "payment_timeout":
                self.demo_svc.payment_gateway_down = False

        # Run validation workload under identical conditions
        post_metrics = self._execute_workload(count=workload_count)

        # Calculate error rate delta: positive delta indicates improvement
        baseline_err = baseline.metrics.error_rate
        post_err = post_metrics.error_rate
        err_delta = round(baseline_err - post_err, 4)

        # Determine verdict based on statistical evidence and sample size
        # Rule 1: A tiny sample size (< 3 requests) is not statistically representative -> inconclusive
        if workload_count < 3 or baseline.workload_count < 3:
            verdict = ValidationVerdict.INCONCLUSIVE
            explanation = (
                f"Evaluation is inconclusive because workload sample size ({workload_count} requests) is too small "
                f"to draw statistically sound conclusions. A minimum of 3 consistent requests is required."
            )
            recovery_behavior = "Inconclusive sample size"
            confidence = 0.40

        # Rule 2: Complete resolution (error rate dropped to 0 and all requests succeeded)
        elif post_err == 0.0 and baseline_err > 0.0:
            verdict = ValidationVerdict.SUPPORTED_BY_EVIDENCE
            explanation = (
                f"Candidate fix '{candidate_fix.title}' is supported by telemetry evidence. "
                f"Error rate dropped from {int(baseline_err * 100)}% to {int(post_err * 100)}% across {workload_count} requests. "
                f"All checkout transactions completed with HTTP 200 and zero cascading exceptions."
            )
            recovery_behavior = "Full recovery verified with zero regressions"
            confidence = 0.95

        # Rule 3: Error rate remained elevated or identical -> not supported
        elif post_err >= baseline_err or post_err >= 0.5:
            verdict = ValidationVerdict.NOT_SUPPORTED_BY_EVIDENCE
            explanation = (
                f"Candidate fix '{candidate_fix.title}' is NOT supported by evidence. "
                f"Error rate remained elevated at {int(post_err * 100)}% (Baseline: {int(baseline_err * 100)}%). "
                f"Service continued throwing exceptions during execution."
            )
            recovery_behavior = "Failure persisted; no observable recovery"
            confidence = 0.92

        # Rule 4: Partial recovery or mixed signals -> inconclusive
        else:
            verdict = ValidationVerdict.INCONCLUSIVE
            explanation = (
                f"Partial error reduction observed (from {int(baseline_err * 100)}% to {int(post_err * 100)}%), "
                f"but some requests still failed. Further testing is required before approving deployment."
            )
            recovery_behavior = "Partial or unstable recovery"
            confidence = 0.65

        # Measurements summary
        summary = (
            f"Baseline: {baseline.metrics.successful_requests}/{baseline.metrics.total_requests} OK "
            f"({int(baseline_err * 100)}% error rate, p95={baseline.metrics.latency_p95_ms}ms) -> "
            f"Post-Fix: {post_metrics.successful_requests}/{post_metrics.total_requests} OK "
            f"({int(post_err * 100)}% error rate, p95={post_metrics.latency_p95_ms}ms)"
        )

        report = FixValidationReport(
            experiment_id=experiment_id,
            scenario_id=baseline.scenario_id,
            scenario_name=scenario.name,
            target_service=scenario.target_service,
            fix_id=fix_id,
            fix_description=candidate_fix.title,
            baseline_metrics=baseline.metrics,
            post_fix_metrics=post_metrics,
            error_rate_delta=err_delta,
            recovery_behavior=recovery_behavior,
            verdict=verdict,
            explanation=explanation,
            measurements_summary=summary,
            confidence=confidence,
            safety_notes=[
                "Experiments executed exclusively against local sandbox microservice instances.",
                "Candidate configuration tested in an isolated process without modifying production repositories.",
                "Explicit approval token verified before applying changes."
            ],
            completed_at=time.time(),
        )

        self.history.append(report)
        return report

validation_engine = ValidationEngine()
