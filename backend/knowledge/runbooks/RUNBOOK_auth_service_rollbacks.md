# Troubleshooting Runbook: Auth Service Verification & Emergency Rollback
**Document ID:** RUNBOOK-AUTH-002  
**Category:** troubleshooting_runbook  
**Affected Service:** auth-service  
**Resolution Status:** VERIFIED  
**Classification:** Operational Guide Fixture  

## Diagnostic Checklist
When `auth-service` reports 500 errors or token validation exceptions following a release, follow this verification flow:

1. **Correlate Deployment Timestamps:**
   Determine whether errors coincided with a recent deployment event:
   - Query telemetry for `event_type: DEPLOYMENT` within 15 minutes of first error.
   - Note the deployed image tag or git commit hash (e.g. `v2.4.1-rc1` / `#a8f9c21`).

2. **Inspect Exception Stack Traces:**
   Look for `NullPointerDereference` or `AttributeError` in `TokenValidator.verify()`:
   - Check if error occurs on both valid and invalid session tokens.
   - If 100% of sessions fail, the issue is an unhandled null check in the token parser.

3. **Verify Upstream Impact:**
   Observe HTTP status codes returned to `web-gateway`. If gateway reports upstream 500 from auth-service, public authentication is completely blocked.

## Emergency Rollback Procedure
If errors began immediately after deployment and cannot be remediated via feature flag:

1. **Rollback Container Image:**
   ```bash
   kubectl rollout undo deployment/auth-service
   ```
2. **Verify Pod Status & Liveness Probe:**
   Ensure previous image replica starts successfully and passes `/health` liveness checks.
3. **Validate Session Traffic:**
   Send a synthetic verification request through `web-gateway` (`POST /api/v1/checkout`) to confirm session validation succeeds with HTTP 200.
