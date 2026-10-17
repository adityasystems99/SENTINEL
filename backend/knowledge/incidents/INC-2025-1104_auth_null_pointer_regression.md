# Incident Postmortem: Regressed Deployment NullPointer on Auth Service
**Document ID:** INC-2025-1104  
**Category:** incident_postmortem  
**Affected Service:** auth-service  
**Resolution Status:** RESOLVED  
**Timestamp:** 1730721600 (2025-11-04)  
**Classification:** Synthetic Fixture Example  

## Executive Summary
Shortly after rolling out release `v2.4.1-rc1` to production, `auth-service` began throwing unhandled `NullPointerDereference` / `AttributeError` exceptions when validating user session tokens. This prevented `web-gateway` from authenticating any incoming checkout transactions, causing complete checkout failure.

## Symptoms & Observed Telemetry
- Production deployment event logged: `Deployed release v2.4.1-rc1 (commit #a8f9c21) to production`.
- Within 10 seconds of rollout, `auth-service` emitted `CRITICAL: NullPointerDereference in TokenValidator.verify(): user_session is None`.
- Upstream `web-gateway` reported `Auth check failed: Upstream 500 from auth-service`.
- 100% of checkout transactions were rejected.

## Root Cause
A commit in `v2.4.1-rc1` refactored session caching but omitted a null-safety check before invoking `.verify()` on the session instance. When an anonymous or expired session token was evaluated, `user_session` evaluated to `None`, triggering an unhandled exception.

## Resolution & Preventative Action
1. Initiated immediate rollback of `auth-service` container image to stable release `v2.4.0`.
2. Applied a hotfix adding a defensive guard:
   ```python
   if not user_session:
       logger.warning("Session token missing or expired")
       return False
   return user_session.is_valid()
   ```
3. Added automated regression unit tests covering null session token validation.
