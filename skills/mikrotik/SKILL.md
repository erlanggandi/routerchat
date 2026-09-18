---
name: mikrotik
description: Monitor and manage MikroTik routers via RouterOS API.
version: 0.1.0
author: Kangoding, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mikrotik, routeros, networking, router, monitoring]
---

# MikroTik RouterOS Skill for Hermes

Use this skill when the user asks to monitor, troubleshoot, or configure MikroTik routers (RouterOS).

The MikroTik Backend Service runs locally on port **3010** (`http://localhost:3010` or `http://10.10.70.251:3010`).

## When to Use
- Checking router health, CPU load, memory/RAM usage, uptime, or RouterOS version.
- Monitoring real-time bandwidth / traffic on interfaces (e.g., `ether1`, `wlan1`).
- Viewing connected client devices (DHCP Server leases).
- Checking active firewall filter rules or router logs.
- Proposing or executing network configuration changes with human-in-the-loop approval.

## Multi-Router Operations (Input & Selection)

Users can manage multiple routers simultaneously.

### A. List All Registered Routers
```bash
curl -s http://localhost:3010/api/v1/routers
```

### B. Add / Register a New Router
```bash
curl -s -X POST http://localhost:3010/api/v1/routers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cabang-surabaya",
    "host": "192.168.10.1",
    "port": 8728,
    "username": "admin",
    "password": "Password123"
  }'
```

### C. Switch / Select Active Router for User
```bash
curl -s -X POST http://localhost:3010/api/v1/routers/select \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "router_id": 2}'
```

### D. Check Current Active Router
```bash
curl -s "http://localhost:3010/api/v1/routers/active?user_id=1"
```

---

## Quick Monitoring Operations

The MikroTik Service exposes lightweight REST endpoints returning JSON. Use `curl` to query them directly. Replace `1` with the target `router_id` or active router ID.

### 1. System Health (CPU, RAM, Uptime)
```bash
curl -s http://localhost:3010/api/v1/routers/1/monitoring/resource
```
Returns: `cpu_load`, `total_memory_mb`, `used_memory_mb`, `free_memory_mb`, `memory_usage_pct`, `uptime`, `board_name`, `version`.

### 2. Interface Traffic & Bandwidth
```bash
curl -s "http://localhost:3010/api/v1/routers/1/monitoring/traffic?interface=ether1"
```
Returns: `rx_mbps`, `tx_mbps`, `rx_packets`, `tx_packets`.

### 3. List Network Interfaces
```bash
curl -s http://localhost:3010/api/v1/routers/1/monitoring/interfaces
```
Returns list of interfaces, `running` link state, and `disabled` flags.

### 4. Connected Devices (DHCP Leases)
```bash
curl -s http://localhost:3010/api/v1/routers/1/monitoring/dhcp-leases
```
Returns list of connected IP addresses, MAC addresses, and hostnames.

### 5. Firewall Filter Rules
```bash
curl -s http://localhost:3010/api/v1/routers/1/monitoring/firewall-filters
```
Returns active chains (`forward`, `input`), action (`accept`, `drop`), source/destination addresses.

### 6. Router System Logs
```bash
curl -s "http://localhost:3010/api/v1/routers/1/monitoring/logs?limit=10"
```

---

## Conversational & Complex Queries

If the user asks complex network questions, you can pass the message to the AI engine:
```bash
curl -s -X POST http://localhost:3010/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analisa apakah ada IP yang mencurigakan di DHCP", "user_id": 1}'
```

---

## Safety & Approval Workflow (Human-in-the-Loop)

⚠️ **CRITICAL RULE**: Never directly execute mutating commands (like dropping ports, disabling interfaces, or changing IP) without user confirmation.

1. Check pending approvals:
   ```bash
   curl -s http://localhost:3010/api/v1/approvals
   ```
2. When user confirms/approves:
   ```bash
   curl -s -X POST http://localhost:3010/api/v1/approvals/<APPROVAL_ID>/approve \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1}'
   ```
3. When user rejects:
   ```bash
   curl -s -X POST http://localhost:3010/api/v1/approvals/<APPROVAL_ID>/reject \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1}'
   ```

---

## Response Formatting Guidelines
- Format CPU and memory usage clearly with percentages and MB.
- Highlight any interface that is down or disabled when asked about interface status.
- Answer in the same language as the user (default: Bahasa Indonesia).
