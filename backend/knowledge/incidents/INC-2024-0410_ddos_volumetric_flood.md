# Incident Postmortem: Edge Gateway Volumetric UDP Flood (External DDoS)
**Document ID:** INC-2024-0410  
**Category:** incident_postmortem  
**Affected Service:** edge-lb  
**Resolution Status:** RESOLVED  
**Timestamp:** 1712750400 (2024-04-10)  
**Classification:** Historical Distractor Record  

## Executive Summary
An external botnet targeted edge IP endpoints with 40 Gbps DNS amplification and UDP flood. Packet drops occurred at the border gateway routers before reaching application microservices.

## Symptoms & Observed Telemetry
- Border firewall ingress bandwidth spiked beyond NIC threshold.
- SYN flood warnings logged at external proxy.
- No internal microservice exceptions or database pool issues detected.

## Root Cause
Distributed volumetric Denial of Service originating from compromised NTP/DNS reflection servers.

## Resolution & Preventative Action
1. Activated Cloudflare Magic Transit and BGP Anycast scrubbing.
2. Rate-limited incoming UDP ingress on edge routers.
3. Updated edge ACLs to drop fragmented UDP packets.
