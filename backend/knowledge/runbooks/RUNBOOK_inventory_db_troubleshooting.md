# Troubleshooting Runbook: Inventory Database & HikariCP Connection Pool
**Document ID:** RUNBOOK-INV-001  
**Category:** troubleshooting_runbook  
**Affected Service:** inventory-service  
**Resolution Status:** VERIFIED  
**Classification:** Operational Guide Fixture  

## Diagnostic Checklist
When `inventory-service` emits connection timeout logs or database latency warnings, execute these diagnostic checks in sequence:

1. **Verify Connection Pool Saturation:**
   Check the Hikari pool metrics via Actuator or Prometheus:
   - `hikaricp_active_connections`: If equal to `maximum-pool-size` (e.g. 10/10), pool is fully saturated.
   - `hikaricp_pending_threads`: If > 0, requests are queuing and timing out.

2. **Inspect Slow Queries & Table Locks:**
   Execute database diagnostics to identify long-running transactions:
   ```sql
   SELECT pid, now() - query_start AS duration, query, state
   FROM pg_stat_activity
   WHERE state != 'idle' ORDER BY duration DESC LIMIT 5;
   ```

3. **Check Connection Leak Indicators:**
   Look for `Apparent connection leak detected` in `inventory-service` logs. This indicates open sessions not wrapped in `try-with-resources` or `@Transactional` blocks.

## Immediate Mitigation Steps
- **Emergency Restart:** Bounce the `inventory-service` container instances to immediately release orphaned pool connections:
  ```bash
  kubectl rollout restart deployment/inventory-service
  ```
- **Scale Pool Capacity:** If traffic demand is elevated, increase maximum pool size to 30 in config server and perform rolling reload.
- **Circuit Breaker:** Throttle upstream checkout requests at `order-service` to allow connection pool drainage.
