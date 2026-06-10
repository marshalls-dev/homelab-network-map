---
type: device
status: online
mode: active
latency_ms: 5.3
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-07 16:38:28
---

# Chromecast

> Cast target

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 5.3 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.14 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
Google Cast

## Services
- Cast :8009

## Port check
- **8009**: open


## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Cast discovery |
| → [[Devices/Kitchen speaker|Kitchen speaker]] | Google Cast protocol | downstream | data | degraded | Speaker group / Cast route |
