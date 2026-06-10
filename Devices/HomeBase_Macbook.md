---
type: device
status: online
mode: home
latency_ms: 161.0
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-09 23:10:49
---

# HomeBase_Macbook

> Family workstation · Home Assistant Companion

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **home** |
| **Ping avg** | 161.0 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.8 |
| **Tailscale** | — |
| **HA state** | device_tracker.homebase_macbook: home |

## Hardware
HomeBases-MBP · Tests-MacBook-Pro

## Services
- Migration source
- Home Assistant Companion

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Family Mac |
| → [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | bidirectional | management | up | LAN file share |
| ↔ [[Devices/Home Assistant|Home Assistant]] | Home Assistant app | bidirectional | control | up | HA Companion · home |
