# Incident Postmortem: Payment Gateway HTTP 504 Connect Timeout
**Document ID:** INC-2026-0115  
**Category:** incident_postmortem  
**Affected Service:** payment-service  
**Resolution Status:** RESOLVED  
**Timestamp:** 1736942400 (2026-01-15)  
**Classification:** Synthetic Fixture Example  

## Executive Summary
An outage at our third-party payment processing provider resulted in HTTP connection timeouts on outgoing HTTPS calls from `payment-service`. Because no circuit breaker was configured, caller worker threads in `order-service` blocked indefinitely until timing out after 5.0 seconds.

## Symptoms & Observed Telemetry
- `payment-service` logged `ConnectTimeout: HTTPSConnectionPool(host='api.stripe-mock.com'): Read timed out (timeout=5.0)`.
- `order-service` logged `Payment capture timed out` with HTTP status code 504.
- End-to-end checkout transactions failed with 504 Gateway Timeout.

## Root Cause
Upstream payment API edge routers became unreachable due to a cloud provider BGP routing malfunction. The payment client library lacked circuit breaking and fail-fast timeouts.

## Resolution & Preventative Action
1. Enabled Resilience4j circuit breaker on outgoing payment API invocations.
2. Configured automatic failover to mock secondary provider under sustained error conditions:
   ```yaml
   payment:
     circuit-breaker:
       enabled: true
       failure-rate-threshold: 50
       wait-duration-in-open-state: 10000ms
     fallback-processor: secondary-mock
   ```
3. Decreased connection timeout from 5.0s to 1.5s to fail fast.
