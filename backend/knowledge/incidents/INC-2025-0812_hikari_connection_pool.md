# Incident Postmortem: HikariCP Connection Pool Saturation on Inventory Service
**Document ID:** INC-2025-0812  
**Category:** incident_postmortem  
**Affected Service:** inventory-service  
**Resolution Status:** RESOLVED  
**Timestamp:** 1723464000 (2025-08-12)  
**Classification:** Synthetic Fixture Example  

## Executive Summary
During a flash promotion event, `inventory-service` experienced sudden database connection starvation. All 10 connections in the default HikariCP connection pool were occupied by unindexed queries, causing subsequent checkout reservations to time out after 3000ms. This triggered cascading HTTP 503 failures in `order-service` and HTTP 500 errors in `web-gateway`.

## Symptoms & Observed Telemetry
- `inventory-service` logged `CRITICAL: HikariPool-1 - Connection is not available, request timed out after 3000ms (maxPoolSize=10)`.
- Active database connections reached 10 with 0 idle connections.
- Downstream callers in `order-service` logged `Inventory reservation failed: 503 Service Unavailable`.
- User checkout latency spiked from 45ms to >3200ms.

## Root Cause
The default Hikari pool size (`maximum-pool-size: 10`) was insufficient for concurrent reservation workloads. Database connections remained blocked while awaiting table locks during multi-item SKU decrement operations.

## Resolution & Preventative Action
1. Increased Hikari maximum pool size from 10 to 30 in `application.yml`:
   ```yaml
   datasource:
     hikari:
       maximum-pool-size: 30
       minimum-idle: 10
       connection-timeout: 3000
       leak-detection-threshold: 2000
   ```
2. Added index on `inventory_items.sku` to eliminate full table scans.
3. Configured Prometheus alerts on `hikaricp_pending_threads > 5`.
